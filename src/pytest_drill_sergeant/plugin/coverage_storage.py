"""Coverage data storage and retrieval system using JSON files.

This module provides persistent storage for coverage data, CAR scores, and coverage signatures
using JSON files in a structured directory hierarchy.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from pytest_drill_sergeant.core.analyzers.car_calculator import CARResult
from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData
from pytest_drill_sergeant.core.analyzers.coverage_signature import CoverageSignature

logger = logging.getLogger(__name__)


class CoverageStorageConfig(BaseModel):
    """Configuration for coverage data storage."""

    storage_path: Path = Field(
        default=Path(".drill-sergeant/coverage"),
        description="Base directory for coverage data storage",
    )
    retention_days: int = Field(
        default=30, ge=0, description="Number of days to retain old data"
    )
    compression: bool = Field(
        default=True, description="Whether to compress stored data"
    )
    enabled: bool = Field(default=True, description="Whether storage is enabled")

    @property
    def sessions_dir(self) -> Path:
        """Directory for session data."""
        return self.storage_path / "sessions"

    @property
    def tests_dir(self) -> Path:
        """Directory for test data."""
        return self.storage_path / "tests"

    @property
    def files_dir(self) -> Path:
        """Directory for file data."""
        return self.storage_path / "files"

    @property
    def signatures_dir(self) -> Path:
        """Directory for signature data."""
        return self.storage_path / "signatures"


class SessionData(BaseModel):
    """Session-wide coverage data."""

    session_id: str = Field(description="Unique identifier for the test session")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the session was run"
    )
    total_tests: int = Field(ge=0, description="Total number of tests run")
    average_car_score: float = Field(
        ge=0.0, le=100.0, description="Average CAR score across all tests"
    )
    coverage_files: int = Field(ge=0, description="Number of files with coverage data")
    violations_found: int = Field(ge=0, description="Number of violations found")
    duration: str = Field(description="Duration of the test session")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Configuration used for this session"
    )


class CoverageTestData(BaseModel):
    """Per-test coverage data."""

    test_name: str = Field(description="Name of the test function")
    test_file: str = Field(description="Path to the test file")
    car_score: float = Field(ge=0.0, le=100.0, description="CAR score for this test")
    car_grade: str = Field(description="CAR grade (A-F)")
    efficiency_level: str = Field(description="Efficiency level")
    coverage_percentage: float = Field(
        ge=0.0, le=100.0, description="Coverage percentage"
    )
    coverage_signature: str = Field(description="Coverage signature hash")
    covered_lines: list[int] = Field(
        default_factory=list, description="Lines covered by this test"
    )
    missing_lines: list[int] = Field(
        default_factory=list, description="Lines not covered by this test"
    )
    violations: list[str] = Field(
        default_factory=list, description="Violations found for this test"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When this test was run"
    )
    session_id: str = Field(description="Session this test belongs to")


class FileData(BaseModel):
    """Per-file coverage data."""

    file_path: str = Field(description="Path to the source file")
    total_coverage: float = Field(
        ge=0.0, le=100.0, description="Total coverage percentage for this file"
    )
    tests_covering: list[str] = Field(
        default_factory=list, description="List of test names that cover this file"
    )
    car_scores: list[float] = Field(
        default_factory=list, description="CAR scores for tests covering this file"
    )
    average_car_score: float = Field(
        ge=0.0, le=100.0, description="Average CAR score for this file"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="When this data was last updated"
    )
    session_id: str = Field(description="Session this data belongs to")


class CoverageSignatureData(BaseModel):
    """Coverage signature data for similarity detection."""

    test_name: str = Field(description="Name of the test")
    signature_hash: str = Field(description="Hash of the coverage signature")
    signature_vector: list[float] = Field(
        default_factory=list, description="Vector representation of the signature"
    )
    signature_pattern: str = Field(
        description="Pattern representation of the signature"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When this signature was created"
    )
    session_id: str = Field(description="Session this signature belongs to")


class SignaturesCollection(BaseModel):
    """Collection of coverage signatures."""

    signatures: list[CoverageSignatureData] = Field(
        default_factory=list, description="List of all stored signatures"
    )


class CoverageStorage:
    """Persistent storage for coverage data using JSON files."""

    def __init__(self, config: CoverageStorageConfig | None = None):
        """Initialize coverage storage.

        Args:
            config: Storage configuration, uses defaults if None
        """
        self.config = config or CoverageStorageConfig()
        self.logger = logging.getLogger("drill_sergeant.coverage_storage")

        if self.config.enabled:
            self._ensure_directories()
            self._cleanup_old_data()

    def _ensure_directories(self) -> None:
        """Ensure all storage directories exist."""
        for directory in [
            self.config.storage_path,
            self.config.sessions_dir,
            self.config.tests_dir,
            self.config.files_dir,
            self.config.signatures_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {directory}")

    def _cleanup_old_data(self) -> None:
        """Remove data older than retention period."""
        if self.config.retention_days <= 0:
            return

        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        cutoff_timestamp = cutoff_date.timestamp()

        # Clean up session files
        for session_file in self.config.sessions_dir.glob("*.json"):
            try:
                if session_file.stat().st_mtime < cutoff_timestamp:
                    session_file.unlink()
                    self.logger.debug(f"Removed old session file: {session_file}")
            except OSError as e:
                self.logger.warning(
                    f"Failed to remove old session file {session_file}: {e}"
                )

        # Clean up test files
        for test_file in self.config.tests_dir.glob("*.json"):
            try:
                if test_file.stat().st_mtime < cutoff_timestamp:
                    test_file.unlink()
                    self.logger.debug(f"Removed old test file: {test_file}")
            except OSError as e:
                self.logger.warning(f"Failed to remove old test file {test_file}: {e}")

    def _write_json_file(
        self, file_path: Path, data: BaseModel | dict[str, Any]
    ) -> None:
        """Write data to JSON file with error handling.

        Args:
            file_path: Path to write the JSON file
            data: Data to serialize to JSON (Pydantic model or dict)
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert Pydantic model to dict if needed
            if isinstance(data, BaseModel):
                json_data = data.model_dump()
            else:
                json_data = data

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, default=str)

            self.logger.debug(f"Wrote JSON file: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to write JSON file {file_path}: {e}")
            raise

    def _read_json_file(self, file_path: Path) -> dict[str, Any] | None:
        """Read data from JSON file with error handling.

        Args:
            file_path: Path to read the JSON file from

        Returns:
            Parsed JSON data or None if file doesn't exist or is invalid
        """
        try:
            if not file_path.exists():
                return None

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            self.logger.debug(f"Read JSON file: {file_path}")
            return data
        except Exception as e:
            self.logger.warning(f"Failed to read JSON file {file_path}: {e}")
            return None

    def store_session_data(
        self,
        session_id: str,
        total_tests: int,
        average_car_score: float,
        coverage_files: int,
        violations_found: int,
        duration: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Store session-wide coverage data.

        Args:
            session_id: Unique identifier for the test session
            total_tests: Total number of tests run
            average_car_score: Average CAR score across all tests
            coverage_files: Number of files with coverage data
            violations_found: Number of violations found
            duration: Duration of the test session
            config: Configuration used for this session
        """
        if not self.config.enabled:
            return

        session_data = SessionData(
            session_id=session_id,
            total_tests=total_tests,
            average_car_score=average_car_score,
            coverage_files=coverage_files,
            violations_found=violations_found,
            duration=duration,
            config=config or {},
        )

        session_file = self.config.sessions_dir / f"{session_id}.json"
        self._write_json_file(session_file, session_data)
        self.logger.info(f"Stored session data: {session_id}")

    def store_test_data(
        self,
        test_name: str,
        test_file: Path,
        coverage_data: CoverageData,
        car_result: CARResult,
        coverage_signature: CoverageSignature,
        violations: list[str],
        session_id: str,
    ) -> None:
        """Store per-test coverage data.

        Args:
            test_name: Name of the test function
            test_file: Path to the test file
            coverage_data: Coverage data for this test
            car_result: CAR calculation result
            coverage_signature: Coverage signature for similarity detection
            violations: List of violations found for this test
            session_id: Session this test belongs to
        """
        if not self.config.enabled:
            return

        # Create safe filename from test name
        safe_test_name = self._sanitize_filename(test_name)

        test_data = CoverageTestData(
            test_name=test_name,
            test_file=str(test_file),
            car_score=car_result.car_score,
            car_grade=car_result.grade,
            efficiency_level=car_result.efficiency_level,
            coverage_percentage=coverage_data.coverage_percentage,
            coverage_signature=coverage_signature.signature_hash,
            covered_lines=list(coverage_data.covered_lines),
            missing_lines=list(coverage_data.missing_lines),
            violations=violations,
            session_id=session_id,
        )

        test_file_path = self.config.tests_dir / f"{safe_test_name}.json"
        self._write_json_file(test_file_path, test_data)
        self.logger.debug(f"Stored test data: {test_name}")

    def store_file_data(
        self,
        file_path: Path,
        total_coverage: float,
        tests_covering: list[str],
        car_scores: list[float],
        session_id: str,
    ) -> None:
        """Store per-file coverage data.

        Args:
            file_path: Path to the source file
            total_coverage: Total coverage percentage for this file
            tests_covering: List of test names that cover this file
            car_scores: CAR scores for tests covering this file
            session_id: Session this data belongs to
        """
        if not self.config.enabled:
            return

        # Create safe filename from file path
        safe_file_name = self._sanitize_filename(str(file_path))

        file_data = FileData(
            file_path=str(file_path),
            total_coverage=total_coverage,
            tests_covering=tests_covering,
            car_scores=car_scores,
            average_car_score=sum(car_scores) / len(car_scores) if car_scores else 0.0,
            session_id=session_id,
        )

        file_storage_path = self.config.files_dir / f"{safe_file_name}.json"
        self._write_json_file(file_storage_path, file_data)
        self.logger.debug(f"Stored file data: {file_path}")

    def store_coverage_signature(
        self, test_name: str, signature: CoverageSignature, session_id: str
    ) -> None:
        """Store coverage signature for similarity detection.

        Args:
            test_name: Name of the test
            signature: Coverage signature to store
            session_id: Session this signature belongs to
        """
        if not self.config.enabled:
            return

        signature_data = CoverageSignatureData(
            test_name=test_name,
            signature_hash=signature.signature_hash,
            signature_vector=signature.signature_vector,
            signature_pattern=signature.coverage_pattern,
            session_id=session_id,
        )

        # Append to signatures file
        signatures_file = self.config.signatures_dir / "signatures.json"
        self._append_to_signatures_file(signatures_file, signature_data)
        self.logger.debug(f"Stored coverage signature: {test_name}")

    def _append_to_signatures_file(
        self, file_path: Path, signature_data: CoverageSignatureData
    ) -> None:
        """Append signature data to the signatures file.

        Args:
            file_path: Path to the signatures file
            signature_data: Signature data to append
        """
        try:
            # Read existing signatures
            existing_data = self._read_json_file(file_path)
            if existing_data:
                signatures_collection = SignaturesCollection(**existing_data)
            else:
                signatures_collection = SignaturesCollection()

            # Append new signature
            signatures_collection.signatures.append(signature_data)

            # Write back to file
            self._write_json_file(file_path, signatures_collection)
        except Exception as e:
            self.logger.error(f"Failed to append signature to {file_path}: {e}")
            raise

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string to be safe for use as a filename.

        Args:
            name: String to sanitize

        Returns:
            Sanitized filename
        """
        # Replace problematic characters
        safe_name = name.replace("/", "_").replace("\\", "_").replace(":", "_")
        safe_name = safe_name.replace("*", "_").replace("?", "_").replace('"', "_")
        safe_name = safe_name.replace("<", "_").replace(">", "_").replace("|", "_")

        # Limit length
        if len(safe_name) > 100:
            safe_name = safe_name[:100]

        return safe_name

    # Retrieval methods

    def get_session_data(self, session_id: str) -> SessionData | None:
        """Retrieve session data by session ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        if not self.config.enabled:
            return None

        session_file = self.config.sessions_dir / f"{session_id}.json"
        data = self._read_json_file(session_file)
        return SessionData(**data) if data else None

    def get_test_data(self, test_name: str) -> CoverageTestData | None:
        """Retrieve test data by test name.

        Args:
            test_name: Name of the test

        Returns:
            Test data or None if not found
        """
        if not self.config.enabled:
            return None

        safe_test_name = self._sanitize_filename(test_name)
        test_file = self.config.tests_dir / f"{safe_test_name}.json"
        data = self._read_json_file(test_file)
        return CoverageTestData(**data) if data else None

    def get_file_data(self, file_path: Path) -> FileData | None:
        """Retrieve file data by file path.

        Args:
            file_path: Path to the source file

        Returns:
            File data or None if not found
        """
        if not self.config.enabled:
            return None

        safe_file_name = self._sanitize_filename(str(file_path))
        file_storage_path = self.config.files_dir / f"{safe_file_name}.json"
        data = self._read_json_file(file_storage_path)
        return FileData(**data) if data else None

    def get_all_signatures(self) -> list[CoverageSignatureData]:
        """Retrieve all stored coverage signatures.

        Returns:
            List of all signature data
        """
        if not self.config.enabled:
            return []

        signatures_file = self.config.signatures_dir / "signatures.json"
        data = self._read_json_file(signatures_file)
        if data:
            signatures_collection = SignaturesCollection(**data)
            return signatures_collection.signatures
        return []

    def find_similar_signatures(
        self, target_signature: CoverageSignature, similarity_threshold: float = 0.8
    ) -> list[dict[str, Any]]:
        """Find signatures similar to the target signature.

        Args:
            target_signature: Signature to compare against
            similarity_threshold: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of similar signatures with similarity scores
        """
        if not self.config.enabled:
            return []

        all_signatures = self.get_all_signatures()
        similar_signatures = []

        for signature_data in all_signatures:
            try:
                # Calculate similarity (simplified - would use proper similarity algorithm)
                similarity_score = self._calculate_similarity(
                    target_signature.signature_hash, signature_data.signature_hash
                )

                if similarity_score >= similarity_threshold:
                    # Convert to dict and add similarity score
                    signature_dict = signature_data.model_dump()
                    signature_dict["similarity_score"] = similarity_score
                    similar_signatures.append(signature_dict)
            except Exception as e:
                self.logger.warning(f"Failed to compare signature: {e}")
                continue

        # Sort by similarity score (highest first)
        similar_signatures.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_signatures

    def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two signature hashes.

        Args:
            hash1: First signature hash
            hash2: Second signature hash

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not hash1 or not hash2:
            return 0.0

        if hash1 == hash2:
            return 1.0

        # Simple similarity based on common characters
        # In a real implementation, this would use proper similarity algorithms
        common_chars = sum(1 for c1, c2 in zip(hash1, hash2, strict=False) if c1 == c2)
        max_length = max(len(hash1), len(hash2))

        return common_chars / max_length if max_length > 0 else 0.0

    def get_recent_sessions(self, limit: int = 10) -> list[SessionData]:
        """Get the most recent test sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of recent session data
        """
        if not self.config.enabled:
            return []

        session_files = list(self.config.sessions_dir.glob("*.json"))
        sessions = []

        for session_file in session_files:
            data = self._read_json_file(session_file)
            if data:
                try:
                    session_data = SessionData(**data)
                    sessions.append(session_data)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to parse session data from {session_file}: {e}"
                    )
                    continue

        # Sort by timestamp (most recent first)
        sessions.sort(key=lambda x: x.timestamp, reverse=True)
        return sessions[:limit]

    def get_coverage_trends(self, days: int = 7) -> dict[str, Any]:
        """Get coverage trends over the specified number of days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with trend data
        """
        if not self.config.enabled:
            return {}

        cutoff_date = datetime.now() - timedelta(days=days)
        recent_sessions = []

        for session_file in self.config.sessions_dir.glob("*.json"):
            session_data = self._read_json_file(session_file)
            if session_data:
                session_time = datetime.fromisoformat(session_data.get("timestamp", ""))
                if session_time >= cutoff_date:
                    recent_sessions.append(session_data)

        if not recent_sessions:
            return {}

        # Sort sessions by timestamp to ensure chronological order
        recent_sessions.sort(key=lambda s: s.get("timestamp", ""))

        # Calculate trends
        car_scores = [s.get("average_car_score", 0) for s in recent_sessions]
        violation_counts = [s.get("violations_found", 0) for s in recent_sessions]

        return {
            "period_days": days,
            "session_count": len(recent_sessions),
            "average_car_score": sum(car_scores) / len(car_scores) if car_scores else 0,
            "total_violations": sum(violation_counts),
            "car_score_trend": (
                "improving"
                if len(car_scores) > 1 and car_scores[-1] > car_scores[0]
                else "declining"
            ),
            "violation_trend": (
                "improving"
                if len(violation_counts) > 1
                and violation_counts[-1] < violation_counts[0]
                else "declining"
            ),
        }


# Global coverage storage instance
_coverage_storage: CoverageStorage | None = None


def get_coverage_storage() -> CoverageStorage:
    """Get the global coverage storage instance.

    Returns:
        CoverageStorage instance
    """
    global _coverage_storage
    if _coverage_storage is None:
        _coverage_storage = CoverageStorage()
    return _coverage_storage
