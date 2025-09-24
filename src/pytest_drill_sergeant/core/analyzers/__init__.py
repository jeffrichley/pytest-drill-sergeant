"""Analysis modules for detecting test quality issues."""

from .aaa_comment_detector import AAACommentDetector
from .mock_overspec_detector import MockOverspecDetector
from .private_access_detector import Detector, PrivateAccessDetector
from .structural_equality_detector import StructuralEqualityDetector

__all__: list[str] = ["AAACommentDetector", "Detector", "MockOverspecDetector", "PrivateAccessDetector", "StructuralEqualityDetector"]
