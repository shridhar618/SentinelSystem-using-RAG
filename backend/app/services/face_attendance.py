"""
Face attendance service — OpenCV-based implementation (no dlib / face_recognition).

Uses a two-stage pipeline that works with opencv-python 4.x and 5.x,
numpy and Pillow (both already in requirements.txt):

  Stage 1 — Detection
    • OpenCV 5: YuNet DNN detector (FaceDetectorYN). The ONNX model file
      (~350 KB) is downloaded on first use to backend/app/data/face_models/
      and cached there for subsequent runs.
    • OpenCV 4 / fallback: Haar cascade (CascadeClassifier).  Included
      in the opencv-python 4.x wheel; not available in 5.0.

  Stage 2 — Embedding
    Local Binary Pattern Histogram (LBPH) over the detected face region,
    normalised to a fixed 16 384-dim (8 × 8 cells × 256 bins) L2-unit
    vector.  LBPH is a well-studied appearance descriptor that is robust
    to mild lighting variation, runs in milliseconds on CPU, and requires
    no external model weights.

  Matching
    Cosine similarity between L2-normalised embeddings (equivalent to
    Euclidean distance on unit vectors).  The MATCH_TOLERANCE threshold
    (0.90 cosine similarity) is intentionally conservative because this
    local descriptor is used for authentication and attendance.
"""

import base64
import hashlib
import io
import os
import urllib.request
from pathlib import Path

import numpy as np

from app.models.face_profile import FaceProfile

# Higher value = stricter match (cosine similarity, 0..1). A permissive
# threshold can accept a different person's face because LBPH is an
# appearance descriptor rather than a modern identity embedding.
MATCH_TOLERANCE = float(os.getenv("FACE_MATCH_TOLERANCE", "0.90"))

# ── YuNet model (OpenCV 5) ────────────────────────────────────────────────────
_YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
_MODEL_DIR = Path(__file__).parent.parent / "data" / "face_models"
_YUNET_PATH = _MODEL_DIR / "face_detection_yunet_2023mar.onnx"

# Module-level cache so cascade/detector objects are not reloaded per request.
_FACE_DETECTOR_YN = None   # OpenCV 5 YuNet detector
_FACE_CASCADE = None       # OpenCV 4 Haar cascade (fallback)


# ──────────────────────────────────────────────────────────────────────────────
# Detector helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ensure_yunet_model() -> Path:
    """Download the YuNet ONNX model on first use.  Cached locally."""
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not _YUNET_PATH.exists():
        try:
            urllib.request.urlretrieve(_YUNET_URL, _YUNET_PATH)
        except Exception as exc:
            raise RuntimeError(
                f"Could not download the YuNet face-detection model from {_YUNET_URL}. "
                "Check your internet connection, or place the .onnx file at "
                f"{_YUNET_PATH} manually."
            ) from exc
    return _YUNET_PATH


def _get_yunet_detector(width: int, height: int):
    """Return a cached YuNet FaceDetectorYN (OpenCV 5+) or None if unavailable."""
    import cv2
    global _FACE_DETECTOR_YN
    if not hasattr(cv2, "FaceDetectorYN_create"):
        return None
    try:
        model_path = _ensure_yunet_model()
        _FACE_DETECTOR_YN = cv2.FaceDetectorYN_create(
            str(model_path),
            "",
            (width, height),
            score_threshold=0.6,
            nms_threshold=0.3,
            top_k=5,
        )
        return _FACE_DETECTOR_YN
    except Exception:
        return None


def _get_haar_cascade():
    """Return a cached Haar CascadeClassifier (OpenCV 4.x) or None."""
    import cv2
    global _FACE_CASCADE
    if not hasattr(cv2, "CascadeClassifier"):
        return None
    if _FACE_CASCADE is None:
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            if not os.path.exists(cascade_path):
                return None
            _FACE_CASCADE = cv2.CascadeClassifier(cascade_path)
            if _FACE_CASCADE.empty():
                _FACE_CASCADE = None
        except Exception:
            _FACE_CASCADE = None
    return _FACE_CASCADE


def _detect_largest_face_yunet(rgb_array: np.ndarray) -> tuple[int, int, int, int]:
    """Detect face with YuNet (OpenCV 5+). Returns (x, y, w, h) with margin."""
    import cv2

    h, w = rgb_array.shape[:2]
    bgr = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    detector = _get_yunet_detector(w, h)
    if detector is None:
        raise RuntimeError("YuNet detector not available.")

    detector.setInputSize((w, h))
    _, faces = detector.detect(bgr)

    if faces is None or len(faces) == 0:
        raise ValueError(
            "No face detected in the image. "
            "Please ensure your face is clearly visible, well-lit, and centred."
        )

    # Each row: [x, y, w, h, ...landmarks..., score]
    # Pick highest-confidence detection.
    best = max(faces, key=lambda f: float(f[-1]))
    fx, fy, fw, fh = int(best[0]), int(best[1]), int(best[2]), int(best[3])

    margin = int(0.15 * max(fw, fh))
    x1 = max(0, fx - margin)
    y1 = max(0, fy - margin)
    x2 = min(w, fx + fw + margin)
    y2 = min(h, fy + fh + margin)
    return x1, y1, x2 - x1, y2 - y1


def _detect_largest_face_haar(rgb_array: np.ndarray) -> tuple[int, int, int, int]:
    """Detect face with Haar cascade (OpenCV 4). Returns (x, y, w, h) with margin."""
    import cv2

    cascade = _get_haar_cascade()
    if cascade is None:
        raise RuntimeError("Haar cascade not available.")

    bgr = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )

    if len(faces) == 0:
        raise ValueError(
            "No face detected in the image. "
            "Please ensure your face is clearly visible, well-lit, and centred."
        )

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    margin = int(0.15 * max(w, h))
    x1 = max(0, x - margin)
    y1 = max(0, y - margin)
    x2 = min(rgb_array.shape[1], x + w + margin)
    y2 = min(rgb_array.shape[0], y + h + margin)
    return x1, y1, x2 - x1, y2 - y1


def _detect_largest_face(rgb_array: np.ndarray) -> tuple[int, int, int, int]:
    """Try YuNet (cv2 5+) then Haar cascade (cv2 4). Raise ValueError on no face."""
    # Try YuNet first (OpenCV 5+)
    try:
        return _detect_largest_face_yunet(rgb_array)
    except (RuntimeError, ImportError):
        pass

    # Fall back to Haar cascade (OpenCV 4.x or contrib on 5)
    try:
        return _detect_largest_face_haar(rgb_array)
    except (RuntimeError, ImportError):
        pass

    raise ValueError(
        "Face detection is not available: neither YuNet (OpenCV 5) nor the "
        "Haar cascade (OpenCV 4) could be initialised. "
        "Ensure opencv-python is installed and (for OpenCV 5) that the "
        "face_detection_yunet_2023mar.onnx model can be downloaded."
    )


# ──────────────────────────────────────────────────────────────────────────────
# LBPH embedding
# ──────────────────────────────────────────────────────────────────────────────

def _compute_lbp(gray_patch: np.ndarray) -> np.ndarray:
    """8-neighbourhood LBP map for a greyscale patch."""
    lbp = np.zeros_like(gray_patch, dtype=np.uint8)
    center = gray_patch[1:-1, 1:-1].astype(np.int16)
    offsets = [
        (0, 1), (-1, 1), (-1, 0), (-1, -1),
        (0, -1), (1, -1), (1, 0), (1, 1),
    ]
    for bit, (dr, dc) in enumerate(offsets):
        neighbour = np.roll(np.roll(gray_patch, -dr, axis=0), -dc, axis=1)[1:-1, 1:-1]
        lbp[1:-1, 1:-1] |= (
            (neighbour.astype(np.int16) >= center).astype(np.uint8) << bit
        )
    return lbp


def _lbph_embedding(
    gray_face: np.ndarray,
    grid_x: int = 8,
    grid_y: int = 8,
) -> np.ndarray:
    """L2-normalised LBPH embedding of a greyscale face crop.

    Divides the face into grid_x × grid_y cells, computes a 256-bin LBP
    histogram per cell, concatenates them, and L2-normalises the result.

    Returns a float32 vector of length grid_x * grid_y * 256 = 16 384.
    """
    import cv2

    TARGET_SIZE = (128, 128)
    face_resized = cv2.resize(gray_face, TARGET_SIZE, interpolation=cv2.INTER_LANCZOS4)
    # Histogram equalisation reduces sensitivity to lighting level.
    try:
        face_eq = cv2.equalizeHist(face_resized)
    except Exception:
        face_eq = face_resized

    h, w = face_eq.shape
    cell_h = h // grid_y
    cell_w = w // grid_x

    histograms = []
    for row in range(grid_y):
        for col in range(grid_x):
            cell = face_eq[
                row * cell_h : (row + 1) * cell_h,
                col * cell_w : (col + 1) * cell_w,
            ]
            lbp = _compute_lbp(cell)
            hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
            histograms.append(hist.astype(np.float32))

    vec = np.concatenate(histograms)
    norm = np.linalg.norm(vec)
    if norm < 1e-10:
        return vec.astype(np.float32)
    return (vec / norm).astype(np.float32)


# ──────────────────────────────────────────────────────────────────────────────
# Image decoding helpers
# ──────────────────────────────────────────────────────────────────────────────

def _decode_image_bytes(image_payload: str) -> bytes:
    if not image_payload:
        raise ValueError("Image payload is required")

    payload = image_payload.strip()
    if "," in payload and payload.startswith("data:image"):
        payload = payload.split(",", 1)[1]

    try:
        return base64.b64decode(payload, validate=True)
    except Exception as exc:
        raise ValueError("Invalid base64 image payload") from exc


def _load_rgb_array(raw_bytes: bytes) -> np.ndarray:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError(
            "Pillow is required for image decoding. Install backend dependencies."
        ) from exc

    try:
        image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError("Unsupported image format") from exc

    return np.asarray(image, dtype=np.uint8)


# ──────────────────────────────────────────────────────────────────────────────
# Test backend (pytest only — never enabled in production)
# ──────────────────────────────────────────────────────────────────────────────

def _test_embedding(image_payload: str) -> tuple[np.ndarray, str]:
    """Deterministic stand-in used ONLY when FACE_BACKEND=test."""
    raw = _decode_image_bytes(image_payload)
    rgb = _load_rgb_array(raw)
    gray = rgb.mean(axis=2)
    h, w = gray.shape
    ys = np.linspace(0, h - 1, 16).astype(int)
    xs = np.linspace(0, w - 1, 16).astype(int)
    vec = gray[np.ix_(ys, xs)].astype(np.float32).flatten()
    vec -= vec.mean()
    norm = np.linalg.norm(vec) or 1.0
    return vec / norm, hashlib.sha256(raw).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def build_face_embedding(image_payload: str) -> tuple[np.ndarray, str]:
    """Detect the face in *image_payload* and return (embedding, image_hash).

    *image_payload* may be a raw base64 string or a data-URI.

    Returns:
        embedding  — float32 L2-normalised 1-D numpy array (16 384 dims).
        image_hash — SHA-256 hex digest of the raw bytes (for audit trail).

    Raises:
        ValueError  — bad payload, no face found, or degenerate embedding.
        RuntimeError — OpenCV / model initialisation failure.
    """
    if os.getenv("FACE_BACKEND", "real").lower() == "test":
        return _test_embedding(image_payload)

    try:
        import cv2  # noqa: F401
    except ImportError as exc:
        raise ValueError(
            "OpenCV is not installed. Run: pip install opencv-python"
        ) from exc

    raw = _decode_image_bytes(image_payload)
    rgb_array = _load_rgb_array(raw)
    image_hash = hashlib.sha256(raw).hexdigest()

    x, y, w, h = _detect_largest_face(rgb_array)
    face_crop = rgb_array[y : y + h, x : x + w]

    import cv2
    gray_face = cv2.cvtColor(face_crop, cv2.COLOR_RGB2GRAY)
    embedding = _lbph_embedding(gray_face)

    if np.linalg.norm(embedding) < 1e-10:
        raise ValueError(
            "Could not compute a usable face embedding from the detected region. "
            "Try a clearer, front-facing, well-lit photo."
        )

    return embedding, image_hash


def match_face(image_payload: str, tolerance: float = MATCH_TOLERANCE, user_id: int | None = None):
    """Compare *image_payload* against enrolled profiles, optionally one user.

    Returns:
        (best_profile_or_None, confidence)

    *confidence* is 0-1 (higher = better match).  Returns None profile
    when no enrolled face exceeds the *tolerance* threshold.
    """
    probe_embedding, _ = build_face_embedding(image_payload)
    profiles_query = FaceProfile.query
    if user_id is not None:
        profiles_query = profiles_query.filter_by(user_id=user_id)
    profiles = profiles_query.all()
    if not profiles:
        return None, 0.0

    best_profile = None
    best_similarity = -1.0

    for profile in profiles:
        known = profile.get_embedding()

        # Guard against embedding dimension mismatch (e.g. re-enrolled after
        # a config change that altered grid size).
        if known.shape != probe_embedding.shape:
            min_dim = min(len(known), len(probe_embedding))
            known_vec = known[:min_dim]
            probe_vec = probe_embedding[:min_dim]
        else:
            known_vec = known
            probe_vec = probe_embedding

        k_norm = np.linalg.norm(known_vec)
        p_norm = np.linalg.norm(probe_vec)
        if k_norm < 1e-10 or p_norm < 1e-10:
            similarity = 0.0
        else:
            similarity = float(np.dot(known_vec / k_norm, probe_vec / p_norm))

        if similarity > best_similarity:
            best_similarity = similarity
            best_profile = profile

    confidence = max(0.0, min(1.0, best_similarity))
    if best_profile is None or best_similarity < tolerance:
        return None, confidence
    return best_profile, confidence
