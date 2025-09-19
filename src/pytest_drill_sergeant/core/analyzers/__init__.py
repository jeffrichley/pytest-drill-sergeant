"""Analysis modules for detecting test quality issues."""

from .private_access_detector import Detector, PrivateAccessDetector

__all__: list[str] = ["Detector", "PrivateAccessDetector"]
