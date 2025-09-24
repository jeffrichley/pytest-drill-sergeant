"""Analysis modules for detecting test quality issues."""

from .aaa_comment_detector import AAACommentDetector
from .car_calculator import CARCalculator
from .coverage_collector import CoverageCollector
from .coverage_signature import CoverageSignatureGenerator
from .mock_overspec_detector import MockOverspecDetector
from .private_access_detector import Detector, PrivateAccessDetector
from .structural_equality_detector import StructuralEqualityDetector

__all__: list[str] = [
    "AAACommentDetector",
    "CARCalculator",
    "CoverageCollector",
    "CoverageSignatureGenerator",
    "Detector",
    "MockOverspecDetector",
    "PrivateAccessDetector",
    "StructuralEqualityDetector",
]
