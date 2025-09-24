"""Coverage Signature Generation for pytest-drill-sergeant.

This module implements coverage signature generation for similarity detection
between tests based on their coverage patterns.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.models import Finding


@dataclass
class CoverageSignature:
    """Coverage signature for similarity detection."""

    test_name: str
    file_path: Path
    signature_hash: str
    signature_vector: list[float]
    coverage_pattern: str
    similarity_threshold: float = 0.8


class CoverageSignatureGenerator:
    """Generates coverage signatures for test similarity detection."""

    def __init__(self) -> None:
        """Initialize the coverage signature generator."""
        self.logger = logging.getLogger("drill_sergeant.coverage_signature")
        self._signatures: dict[str, CoverageSignature] = {}

    def generate_signature(
        self, test_file_path: Path, test_name: str, coverage_data: CoverageData
    ) -> CoverageSignature:
        """Generate coverage signature for a test.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function
            coverage_data: Coverage data for the test

        Returns:
            CoverageSignature object
        """
        try:
            # Generate signature hash
            signature_hash = self._generate_signature_hash(coverage_data)

            # Generate signature vector
            signature_vector = self._generate_signature_vector(coverage_data)

            # Generate coverage pattern
            coverage_pattern = self._generate_coverage_pattern(coverage_data)

            signature = CoverageSignature(
                test_name=test_name,
                file_path=test_file_path,
                signature_hash=signature_hash,
                signature_vector=signature_vector,
                coverage_pattern=coverage_pattern,
            )

            # Store signature
            key = f"{test_file_path}:{test_name}"
            self._signatures[key] = signature

            return signature

        except Exception as e:
            self.logger.error("Failed to generate signature for %s: %s", test_name, e)
            # Return empty signature on error
            return CoverageSignature(
                test_name=test_name,
                file_path=test_file_path,
                signature_hash="",
                signature_vector=[],
                coverage_pattern="",
            )

    def _generate_signature_hash(self, coverage_data: CoverageData) -> str:
        """Generate hash signature from coverage data.

        Args:
            coverage_data: Coverage data for the test

        Returns:
            Hash signature string
        """
        try:
            # Create hash from coverage metrics
            hash_input = f"{coverage_data.lines_covered}:{coverage_data.lines_total}:{coverage_data.branches_covered}:{coverage_data.branches_total}:{coverage_data.coverage_percentage}"

            # Add covered lines to hash
            if coverage_data.covered_lines:
                lines_str = ",".join(
                    sorted(str(line) for line in coverage_data.covered_lines)
                )
                hash_input += f":{lines_str}"

            # Generate MD5 hash
            signature_hash = hashlib.md5(hash_input.encode()).hexdigest()

            return signature_hash

        except Exception as e:
            self.logger.error("Failed to generate signature hash: %s", e)
            return ""

    def _generate_signature_vector(self, coverage_data: CoverageData) -> list[float]:
        """Generate numerical signature vector from coverage data.

        Args:
            coverage_data: Coverage data for the test

        Returns:
            List of numerical values representing the signature
        """
        try:
            vector = []

            # Add basic coverage metrics
            vector.append(coverage_data.coverage_percentage / 100.0)  # Normalize to 0-1
            vector.append(
                coverage_data.lines_covered / max(coverage_data.lines_total, 1)
            )
            vector.append(
                coverage_data.branches_covered / max(coverage_data.branches_total, 1)
            )

            # Add coverage density metrics
            if coverage_data.covered_lines:
                # Calculate coverage density (how clustered the coverage is)
                lines = sorted(coverage_data.covered_lines)
                if len(lines) > 1:
                    gaps = [lines[i + 1] - lines[i] for i in range(len(lines) - 1)]
                    avg_gap = sum(gaps) / len(gaps) if gaps else 0
                    vector.append(
                        1.0 / (1.0 + avg_gap)
                    )  # Higher density = higher value
                else:
                    vector.append(1.0)
            else:
                vector.append(0.0)

            # Add coverage pattern metrics
            if coverage_data.covered_lines:
                # Calculate coverage spread
                min_line = min(coverage_data.covered_lines)
                max_line = max(coverage_data.covered_lines)
                spread = max_line - min_line
                vector.append(spread / max(coverage_data.lines_total, 1))
            else:
                vector.append(0.0)

            return vector

        except Exception as e:
            self.logger.error("Failed to generate signature vector: %s", e)
            return []

    def _generate_coverage_pattern(self, coverage_data: CoverageData) -> str:
        """Generate human-readable coverage pattern.

        Args:
            coverage_data: Coverage data for the test

        Returns:
            Coverage pattern string
        """
        try:
            pattern_parts = []

            # Add coverage percentage
            pattern_parts.append(f"coverage:{coverage_data.coverage_percentage:.1f}%")

            # Add line coverage
            pattern_parts.append(
                f"lines:{coverage_data.lines_covered}/{coverage_data.lines_total}"
            )

            # Add branch coverage
            pattern_parts.append(
                f"branches:{coverage_data.branches_covered}/{coverage_data.branches_total}"
            )

            # Add coverage signature if available
            if coverage_data.coverage_signature:
                pattern_parts.append(f"signature:{coverage_data.coverage_signature}")

            return "|".join(pattern_parts)

        except Exception as e:
            self.logger.error("Failed to generate coverage pattern: %s", e)
            return ""

    def calculate_similarity(
        self, signature1: CoverageSignature, signature2: CoverageSignature
    ) -> float:
        """Calculate similarity between two coverage signatures.

        Args:
            signature1: First coverage signature
            signature2: Second coverage signature

        Returns:
            Similarity score (0-1)
        """
        try:
            # Compare signature hashes first (exact match)
            if signature1.signature_hash == signature2.signature_hash:
                return 1.0

            # Compare signature vectors using cosine similarity
            if signature1.signature_vector and signature2.signature_vector:
                similarity = self._cosine_similarity(
                    signature1.signature_vector, signature2.signature_vector
                )
                return similarity

            # Fallback to pattern comparison
            return self._pattern_similarity(
                signature1.coverage_pattern, signature2.coverage_pattern
            )

        except Exception as e:
            self.logger.error("Failed to calculate similarity: %s", e)
            return 0.0

    def _cosine_similarity(self, vector1: list[float], vector2: list[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vector1: First vector
            vector2: Second vector

        Returns:
            Cosine similarity (0-1)
        """
        try:
            # Ensure vectors have same length
            min_len = min(len(vector1), len(vector2))
            if min_len == 0:
                return 0.0

            # Calculate dot product
            dot_product = sum(vector1[i] * vector2[i] for i in range(min_len))

            # Calculate magnitudes
            magnitude1 = sum(x * x for x in vector1[:min_len]) ** 0.5
            magnitude2 = sum(x * x for x in vector2[:min_len]) ** 0.5

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            # Calculate cosine similarity
            similarity = dot_product / (magnitude1 * magnitude2)

            return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]

        except Exception as e:
            self.logger.error("Failed to calculate cosine similarity: %s", e)
            return 0.0

    def _pattern_similarity(self, pattern1: str, pattern2: str) -> float:
        """Calculate similarity between coverage patterns.

        Args:
            pattern1: First coverage pattern
            pattern2: Second coverage pattern

        Returns:
            Pattern similarity (0-1)
        """
        try:
            if not pattern1 or not pattern2:
                return 0.0

            # Split patterns into components
            parts1 = set(pattern1.split("|"))
            parts2 = set(pattern2.split("|"))

            # Calculate Jaccard similarity
            intersection = len(parts1 & parts2)
            union = len(parts1 | parts2)

            if union == 0:
                return 0.0

            return intersection / union

        except Exception as e:
            self.logger.error("Failed to calculate pattern similarity: %s", e)
            return 0.0

    def find_similar_tests(
        self, target_signature: CoverageSignature, threshold: float = 0.8
    ) -> list[tuple[CoverageSignature, float]]:
        """Find tests with similar coverage signatures.

        Args:
            target_signature: Signature to compare against
            threshold: Similarity threshold (0-1)

        Returns:
            List of (signature, similarity_score) tuples
        """
        similar_tests = []

        try:
            for signature in self._signatures.values():
                if signature.test_name == target_signature.test_name:
                    continue  # Skip self

                similarity = self.calculate_similarity(target_signature, signature)

                if similarity >= threshold:
                    similar_tests.append((signature, similarity))

            # Sort by similarity score (highest first)
            similar_tests.sort(key=lambda x: x[1], reverse=True)

            return similar_tests

        except Exception as e:
            self.logger.error("Failed to find similar tests: %s", e)
            return []

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for coverage signature issues.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for coverage signature issues
        """
        findings: list[Finding] = []

        try:
            if not file_path.exists():
                self.logger.warning("File does not exist: %s", file_path)
                return findings

            if file_path.suffix != ".py":
                self.logger.debug("Skipping non-Python file: %s", file_path)
                return findings

            # Read and parse the file
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                self.logger.debug("Empty file: %s", file_path)
                return findings

            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                self.logger.warning("Syntax error in %s: %s", file_path, e)
                return findings

            # Find test functions and analyze them
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    func_findings = self._analyze_test_function_signature(
                        node, file_path
                    )
                    findings.extend(func_findings)

            self.logger.debug(
                "Coverage signature analysis of %s: %d findings", file_path, len(findings)
            )

        except Exception as e:
            self.logger.error("Error analyzing %s: %s", file_path, e)

        return findings

    def _analyze_test_function_signature(
        self, func_node: ast.FunctionDef, file_path: Path
    ) -> list[Finding]:
        """Analyze coverage signature aspects of a test function.

        Args:
            func_node: AST node for the test function
            file_path: Path to the file being analyzed

        Returns:
            List of findings for this function
        """
        findings: list[Finding] = []

        # This is a placeholder for coverage signature analysis
        # In practice, you'd analyze the test for signature-related issues
        # such as:
        # - Tests with identical coverage signatures (potential duplicates)
        # - Tests with very similar coverage patterns
        # - Tests that could be consolidated based on coverage similarity

        return findings
