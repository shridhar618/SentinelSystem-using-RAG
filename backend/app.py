import os
import sys

if sys.version_info < (3, 14):
    import eventlet

    eventlet.monkey_patch()

from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    # Phase 21: previously defaulted to ON. Flask's debug mode exposes the
    # interactive Werkzeug debugger and full stack traces to any client that
    # triggers an error -- combined with host="0.0.0.0" (all interfaces,
    # not just localhost), the old default meant a fresh checkout run with
    # zero configuration was reachable from the network with the debugger
    # console exposed. Now opt-in via DEBUG=1 for local development.
    debug = os.getenv("DEBUG", "0").lower() in {"1", "true", "yes", "on"}
    socketio.run(app, host="0.0.0.0", port=port, debug=debug, use_reloader=debug)
