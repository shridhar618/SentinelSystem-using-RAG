# 2. Face Unlock & Face Attendance

## Overview
Two features share one face-recognition pipeline:
- **Face Unlock**: after password/login-code sign-in, the user verifies their face against the credential enrolled for *their own* account before entering the app.
- **Face Attendance**: users check in / check out by scanning their face; consecutive scans alternate check-in and check-out each UTC day.

Admins/HR enrol a face when creating a user (see [doc 3](03-rbac-and-user-provisioning.md)) or via `/api/face/register`.

## Who can use it
Every user with an enrolled face. Enrolment and the full attendance list: Admin/HR (manager roles).

## Tech stack
| Concern | Technology |
|---|---|
| Camera capture | Browser `getUserMedia` → canvas → base64 JPEG (`FaceUnlockPage.jsx`, `FaceAttendancePage.jsx`) |
| Face detection | **OpenCV** — **YuNet** DNN detector (`FaceDetectorYN`, ONNX model in `backend/app/data/face_models/`), falling back to **Haar cascade** |
| Face embedding | **LBPH** (Local Binary Pattern Histogram) computed with **NumPy**: 8×8 cells × 256 bins = 16,384-dim L2-normalised vector |
| Image decoding | **Pillow** |
| Matching | Cosine similarity, threshold `FACE_MATCH_TOLERANCE` (default **0.90**) |
| Storage | SQLAlchemy `face_profiles`, `attendance_records` |

## How it works
```
Enrolment (admin/HR):  image → detect largest face (YuNet → Haar) → crop + margin
                       → greyscale → LBP codes → per-cell 256-bin histograms
                       → concatenate → L2-normalise → store embedding + sample hash

Verification:          image → same embedding pipeline
                       → cosine similarity vs. the *requesting user's own* profile only
                       → score ≥ 0.90 ? verified : 403 (with confidence)
```
**Face Unlock** (`POST /api/auth/face-verify`): runs the match scoped to the authenticated user. On success the frontend marks the session face-verified (`AuthContext.markFaceVerified`) and continues to `/welcome`.

**Attendance** (`POST /api/attendance/mark`):
1. Requires an enrolled profile for the caller (403 otherwise).
2. Matches **only against the caller's own profile**, so a face can never select a different account (not even for Admin/HR).
3. Looks at the caller's last event *today (UTC)*: none or `check_out` → `check_in`, else `check_out`.
4. Stores `AttendanceRecord(event_type, confidence, source="face_recognition")`.

Attendance also feeds other features: work-management **capacity risk** flags assignees with no attendance in the last 3 days (doc 14).

## Key files
- `backend/app/services/face_attendance.py` — detection, LBPH embedding, matching
- `backend/app/routes/attendance.py`, `backend/app/routes/auth.py` (`face-verify`)
- `backend/app/models/face_profile.py`, `attendance_record.py`
- `frontend/src/pages/FaceUnlockPage.jsx`, `FaceAttendancePage.jsx`

## API
| Method | Path | Access |
|---|---|---|
| POST | `/api/face/register` | Admin/HR |
| POST | `/api/attendance/mark` | Any user (own face only) |
| GET | `/api/attendance` | Admin/HR: everyone's records |
| GET | `/api/attendance/me` | Own records |
| POST | `/api/auth/face-verify` | Any user (own face only) |

## Data model
- `face_profiles` — `user_id` (unique), embedding, sample hash
- `attendance_records` — `user_id`, `event_type` (`check_in`/`check_out`), `confidence`, `source`, `created_at`

## Security
- Account-scoped matching prevents one person's face from authenticating as another enrolled user.
- No raw images are persisted, only the derived embedding and a hash of the sample.
- Conservative 0.90 threshold because LBPH is an appearance descriptor, not a deep identity embedding.

## Configuration
`FACE_MATCH_TOLERANCE` (default 0.90), `FACE_BACKEND=test` (deterministic embeddings for the test suite).

## Limitations
- LBPH is sensitive to large lighting/pose changes; there is no liveness (anti-spoofing) check, so a photo of the user could pass.
- The YuNet model is downloaded on first use if missing (network access required once).
