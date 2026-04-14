"""Utility helpers for reading, writing, and encoding images."""

import os
import uuid
import cv2
import numpy as np

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


def read_upload(file_bytes: bytes) -> np.ndarray:
    """Decode raw upload bytes into a BGR numpy image."""
    arr = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    return img


def save_image(image: np.ndarray, session_id: str, label: str) -> str:
    """Save image to outputs/<session_id>/ and return its URL path."""
    session_dir = os.path.join(OUTPUTS_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    filename = f"{label}_{uuid.uuid4().hex[:6]}.png"
    filepath = os.path.join(session_dir, filename)
    cv2.imwrite(filepath, image)

    # Return path relative to static mount
    return f"/outputs/{session_id}/{filename}"
