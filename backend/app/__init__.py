from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO, join_room
from dotenv import load_dotenv
from sqlalchemy import inspect, text
import datetime as _datetime
import os
import secrets
import string
import sys
from importlib import import_module

from app.services.roles import ROLE_CATALOG, normalize_role_name

load_dotenv()

if not hasattr(_datetime, "UTC"):
    _datetime.UTC = _datetime.timezone.utc

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()
_LOGIN_CODE_ALPHABET = string.ascii_uppercase + string.digits


def _resolve_socketio_async_mode() -> str:
    configured_mode = (os.getenv("SOCKETIO_ASYNC_MODE") or "").strip().lower()
    if configured_mode:
        return configured_mode
    if sys.version_info >= (3, 14):
        return "threading"
    return "eventlet"


def create_app():
    app = Flask(__name__)

    # Config
    default_secret = "dev-secret-key"
    default_jwt_secret = "dev-jwt-secret"
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", default_secret)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", default_jwt_secret)
    if app.config["SECRET_KEY"] == default_secret or app.config["JWT_SECRET_KEY"] == default_jwt_secret:
        print(
            "\n"
            "*** WARNING: SECRET_KEY and/or JWT_SECRET_KEY are using their default "
            "development values. Set real, random values via environment variables "
            "before deploying this anywhere beyond your own machine -- see "
            ".env.example. ***\n"
        )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///secureai.db")

    # Phase 21: tokens previously never expired at all (JWT_ACCESS_TOKEN_EXPIRES
    # = False). A stolen or logged token remained valid forever. Now expires
    # after a configurable number of hours (default 8, a standard workday) --
    # see frontend/src/utils/api.js for the matching 401 -> redirect-to-login
    # handling this required on the client side.
    jwt_expiry_hours = float(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "8"))
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = _datetime.timedelta(hours=jwt_expiry_hours)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Phase 21: nothing capped request body size before this. A face-image
    # upload (or any other JSON body) with no size limit means Flask
    # buffers the entire request into memory before the route handler ever
    # runs -- a straightforward memory-exhaustion vector. 8MB comfortably
    # covers a single photo with room to spare.
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

    # Extensions
    db.init_app(app)
    jwt.init_app(app)

    # Phase 21: "*" combined with supports_credentials=True is actually an
    # invalid combination per the CORS spec (browsers reject wildcard origin
    # + credentials together), and was broader than needed regardless --
    # this app authenticates via a JWT sent in the Authorization header, not
    # cookies, so credentialed CORS was never actually required. Configurable
    # via CORS_ORIGINS (comma-separated) so a real deployment can set its
    # actual frontend origin; defaults cover the Vite dev server (port 3000 per
    # frontend/vite.config.js, plus Vite's stock 5173). NOTE: python-socketio
    # enforces this list server-side on the Origin header the Vite proxy
    # forwards, so the dev-server origin MUST be listed or real-time features
    # (messages, alerts, Ghost Mode) silently fail to connect.
    allowed_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
    socketio.init_app(
        app,
        cors_allowed_origins=allowed_origins,
        async_mode=_resolve_socketio_async_mode(),
        logger=False,
        engineio_logger=False,
    )

    # Blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.chat import chat_bp
    from app.routes.logs import logs_bp
    from app.routes.users import users_bp
    from app.routes.messages import messages_bp
    from app.routes.attendance import attendance_bp
    from app.routes.work_management import work_management_bp
    from app.routes.roles import roles_bp
    from app.routes.projects import projects_bp
    from app.routes.ai_tasks import ai_tasks_bp
    from app.routes.notifications import notifications_bp
    from app.routes.policies import policies_bp
    from app.routes.compliance import compliance_bp
    from app.routes.risk_config import risk_config_bp
    from app.routes.security_events import security_events_bp
    from app.routes.me import me_bp
    from app.routes.governance_cases import governance_cases_bp
    from app.ghost_routes import ghost_bp
    from app.attack_routes import attack_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(logs_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(messages_bp, url_prefix="/api")
    app.register_blueprint(attendance_bp, url_prefix="/api")
    app.register_blueprint(work_management_bp, url_prefix="/api")
    app.register_blueprint(roles_bp, url_prefix="/api")
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(ai_tasks_bp, url_prefix="/api")
    app.register_blueprint(notifications_bp, url_prefix="/api")
    app.register_blueprint(policies_bp, url_prefix="/api")
    app.register_blueprint(compliance_bp, url_prefix="/api")
    app.register_blueprint(risk_config_bp, url_prefix="/api")
    app.register_blueprint(security_events_bp, url_prefix="/api")
    app.register_blueprint(me_bp, url_prefix="/api")
    app.register_blueprint(governance_cases_bp, url_prefix="/api")
    app.register_blueprint(ghost_bp, url_prefix="/api")
    app.register_blueprint(attack_bp, url_prefix="/api")

    # Socket events
    from app.routes import socket_events  # noqa
    import_module("app.models")

    # ── Socket.IO room management ─────────────────────────────
    @socketio.on('join_admin_room')
    def handle_join_admin(data=None):
        join_room('admin_room')

    @socketio.on('join_user_room')
    def handle_join_user(data=None):
        # SECURITY: this handler takes an unauthenticated, client-supplied
        # value, so it must never be able to join a real user's private
        # room. Private messages and governance alerts are delivered to
        # `user_{id}` rooms, which are joined ONLY in socket_events.py's
        # connect handler after the JWT has been verified. Ghost Mode's
        # demo sessions get their own `ghost_user_{...}` namespace here --
        # previously both shared the `user_` prefix, which meant a client
        # could emit {"user": 5} and silently receive user #5's private
        # messages and alerts.
        data = data or {}
        user = data.get('user')
        if user:
            join_room(f"ghost_user_{user}")

    with app.app_context():
        db.create_all()
        _ensure_work_escalation_columns()
        _ensure_work_assignment_columns()
        _ensure_user_schema()
        _ensure_audit_log_columns()
        _seed_roles()
        _seed_demo_users()
        _sync_users_to_roles()
        _ensure_user_login_codes()
        _seed_permissions()
        _seed_role_permissions()
        _seed_risk_configuration()

    # Phase 21/23: this is a JSON API. Without these, an unhandled exception
    # (500) or an unmatched route (404) previously fell through to Flask's
    # default HTML error pages -- inconsistent for API clients to parse, and
    # (for 500s) meant the real exception was never explicitly logged
    # server-side, only whatever Werkzeug printed by default. The client
    # never sees exception details either way (no stack trace leaks), but
    # now every error is a consistent JSON shape and every 500 is logged.
    @app.errorhandler(404)
    def _handle_not_found(err):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def _handle_server_error(err):
        app.logger.exception("Unhandled server error")
        return jsonify({"error": "An internal error occurred. Please try again or contact an administrator."}), 500

    @app.errorhandler(Exception)
    def _handle_unexpected_error(err):
        from werkzeug.exceptions import HTTPException
        if isinstance(err, HTTPException):
            return jsonify({"error": err.description or err.name}), err.code
        app.logger.exception("Unhandled exception")
        return jsonify({"error": "An internal error occurred. Please try again or contact an administrator."}), 500

    return app


def _generate_login_code(length: int = 10) -> str:
    from app.models.user import User

    while True:
        candidate = ''.join(secrets.choice(_LOGIN_CODE_ALPHABET) for _ in range(length))
        if not User.query.filter_by(login_code=candidate).first():
            return candidate


def _ensure_user_schema():
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "role_id" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN role_id INTEGER"))
        db.session.commit()
    if "login_code" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN login_code VARCHAR(32)"))
        db.session.commit()


def _seed_roles():
    from app.models.role import Role

    existing = {role.name for role in Role.query.all()}
    for name in ROLE_CATALOG:
        if name not in existing:
            db.session.add(Role(name=name))
    db.session.commit()


def _seed_demo_users():
    from app.models.role import Role
    from app.models.user import User
    from werkzeug.security import generate_password_hash

    demo_users = [
        {"username": "admin", "email": "admin@secureai.com", "password": "admin123", "role": "admin", "login_code": "ADMINCODE1"},
        {"username": "hr_jane", "email": "hr@secureai.com", "password": "hr123", "role": "hr", "login_code": "HRCODE0001"},
        {"username": "intern_bob", "email": "intern@secureai.com", "password": "intern123", "role": "intern", "login_code": "INTCODE001"},
    ]

    for u in demo_users:
        existing_user = User.query.filter_by(username=u["username"]).first()
        role = Role.query.filter_by(name=normalize_role_name(u["role"])).first()
        if not existing_user:
            user = User(
                username=u["username"],
                email=u["email"],
                password_hash=generate_password_hash(u["password"]),
                role=u["role"],
                role_id=role.id if role else None,
                login_code=u["login_code"],
            )
            db.session.add(user)
        elif not existing_user.login_code:
            existing_user.login_code = u["login_code"]
            if role and not existing_user.role_id:
                existing_user.role_id = role.id
    db.session.commit()


def _ensure_audit_log_columns():
    inspector = inspect(db.engine)
    if not inspector.has_table("audit_logs"):
        return

    columns = {column["name"] for column in inspector.get_columns("audit_logs")}
    statements = []
    if "recommended_action" not in columns:
        statements.append("ALTER TABLE audit_logs ADD COLUMN recommended_action TEXT")
    if "policy_evidence" not in columns:
        statements.append("ALTER TABLE audit_logs ADD COLUMN policy_evidence TEXT")
    if "event_type" not in columns:
        statements.append("ALTER TABLE audit_logs ADD COLUMN event_type VARCHAR(40)")
    if "resource" not in columns:
        statements.append("ALTER TABLE audit_logs ADD COLUMN resource VARCHAR(255)")
    if "metadata" not in columns:
        statements.append("ALTER TABLE audit_logs ADD COLUMN metadata TEXT")

    # Phase 32: the dashboard and audit page sort/filter on these every
    # request; CREATE INDEX IF NOT EXISTS is idempotent and works on tables
    # that existed before the index was declared (create_all never alters
    # an existing table).
    statements += [
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp ON audit_logs (timestamp)",
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id)",
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_status ON audit_logs (status)",
    ]
    for statement in statements:
        db.session.execute(text(statement))
    db.session.commit()


def _ensure_work_escalation_columns():
    inspector = inspect(db.engine)
    if not inspector.has_table("work_escalations"):
        return

    columns = {column["name"] for column in inspector.get_columns("work_escalations")}
    if "status" not in columns:
        db.session.execute(text("ALTER TABLE work_escalations ADD COLUMN status VARCHAR(20) DEFAULT 'open'"))
        db.session.execute(text("UPDATE work_escalations SET status = 'open' WHERE status IS NULL"))
        db.session.commit()


def _ensure_work_assignment_columns():
    inspector = inspect(db.engine)
    if not inspector.has_table("work_assignments"):
        return

    columns = {column["name"] for column in inspector.get_columns("work_assignments")}
    statements = []
    if "project_id" not in columns:
        statements.append("ALTER TABLE work_assignments ADD COLUMN project_id INTEGER")
    if "parent_id" not in columns:
        statements.append("ALTER TABLE work_assignments ADD COLUMN parent_id INTEGER")
    if "github_issue_id" not in columns:
        statements.append("ALTER TABLE work_assignments ADD COLUMN github_issue_id VARCHAR(255)")
    if "github_branch" not in columns:
        statements.append("ALTER TABLE work_assignments ADD COLUMN github_branch VARCHAR(255)")

    for statement in statements:
        db.session.execute(text(statement))
    if statements:
        db.session.commit()


def _sync_users_to_roles():
    from app.models.role import Role
    from app.models.user import User

    role_map = {role.name.lower(): role.id for role in Role.query.all()}
    users = User.query.all()
    changed = False
    for user in users:
        normalized_role = (user.role or "").strip().lower() or "intern"
        desired_role_id = role_map.get(normalized_role)
        if user.role != normalized_role:
            user.role = normalized_role
            changed = True
        if desired_role_id and user.role_id != desired_role_id:
            user.role_id = desired_role_id
            changed = True
    if changed:
        db.session.commit()


def _ensure_user_login_codes():
    from app.models.user import User

    changed = False
    for user in User.query.all():
        if not user.login_code:
            user.login_code = _generate_login_code()
            changed = True
    if changed:
        db.session.commit()


def _seed_permissions():
    from app.models.permission import Permission
    from app.services.permissions import PERMISSION_CATALOG

    existing = {permission.name for permission in Permission.query.all()}
    for name, category, description in PERMISSION_CATALOG:
        if name not in existing:
            db.session.add(Permission(name=name, category=category, description=description))
    db.session.commit()


def _seed_role_permissions():
    from app.models.permission import Permission
    from app.models.role import Role
    from app.services.permissions import permissions_for_role

    permission_by_name = {permission.name: permission for permission in Permission.query.all()}
    for role in Role.query.all():
        desired_names = set(permissions_for_role(role.name))
        current_names = {permission.name for permission in role.permissions}
        for name in desired_names - current_names:
            permission = permission_by_name.get(name)
            if permission:
                role.permissions.append(permission)
    db.session.commit()


def _seed_risk_configuration():
    """Default admin-configurable weights/thresholds (Phase 9).

    These mirror the constants currently hardcoded in
    services/governance.py (RISK_LOW_MAX, RISK_MEDIUM_MAX, and the Layer-2
    keyword-group weights) so the risk engine has real, working defaults
    to migrate onto rather than inventing new numbers. Values are seeded
    once; existing rows are never overwritten so an admin's edits persist
    across restarts.
    """
    from app.models.risk_configuration import RiskConfiguration

    defaults = [
        ("risk_threshold_low_max", "threshold", 0.30, "Upper bound of LOW risk band"),
        ("risk_threshold_medium_max", "threshold", 0.70, "Upper bound of MEDIUM risk band (above is HIGH)"),
        ("cumulative_risk_case_threshold", "threshold", 1.50, "Cumulative risk score that opens a GovernanceCase"),
        ("weight_cybersecurity_threat", "weight", 0.6, "Weight: cybersecurity threat language"),
        ("weight_malware_attack_tooling", "weight", 0.8, "Weight: malware / attack tooling references"),
        ("weight_data_exfiltration", "weight", 1.0, "Weight: data exfiltration signals"),
        ("weight_sensitive_pii", "weight", 0.7, "Weight: sensitive PII disclosure requests"),
        ("weight_insider_threat", "weight", 1.0, "Weight: insider threat indicators"),
    ]
    existing = {config.key for config in RiskConfiguration.query.all()}
    for key, category, value, description in defaults:
        if key not in existing:
            db.session.add(RiskConfiguration(key=key, category=category, value=value, description=description))
    db.session.commit()
