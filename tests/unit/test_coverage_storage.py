"""Tests for coverage data storage and retrieval functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData
from pytest_drill_sergeant.core.analyzers.car_calculator import CARResult
from pytest_drill_sergeant.core.analyzers.coverage_signature import CoverageSignature
from pytest_drill_sergeant.plugin.coverage_storage import (
    CoverageStorage,
    CoverageStorageConfig,
    SessionData,
    CoverageTestData,
    FileData,
    CoverageSignatureData,
    SignaturesCollection,
    get_coverage_storage,
)


class TestCoverageStorageConfig:
    """Test CoverageStorageConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CoverageStorageConfig()
        
        assert config.storage_path == Path(".drill-sergeant/coverage")
        assert config.retention_days == 30
        assert config.compression is True
        assert config.enabled is True
        
        # Check subdirectories are created
        assert config.sessions_dir == config.storage_path / "sessions"
        assert config.tests_dir == config.storage_path / "tests"
        assert config.files_dir == config.storage_path / "files"
        assert config.signatures_dir == config.storage_path / "signatures"
    
    def test_custom_config(self):
        """Test custom configuration values."""
        custom_path = Path("/tmp/test-coverage")
        config = CoverageStorageConfig(
            storage_path=custom_path,
            retention_days=7,
            compression=False,
            enabled=False
        )
        
        assert config.storage_path == custom_path
        assert config.retention_days == 7
        assert config.compression is False
        assert config.enabled is False
        
        # Check subdirectories use custom path
        assert config.sessions_dir == custom_path / "sessions"
        assert config.tests_dir == custom_path / "tests"
        assert config.files_dir == custom_path / "files"
        assert config.signatures_dir == custom_path / "signatures"


class TestPydanticModels:
    """Test Pydantic model serialization and validation."""
    
    def test_session_data_model(self):
        """Test SessionData model creation and serialization."""
        session_data = SessionData(
            session_id="test_session_123",
            total_tests=10,
            average_car_score=85.5,
            coverage_files=5,
            violations_found=2,
            duration="2m 30s",
            config={"threshold": 75.0}
        )
        
        # Test model creation
        assert session_data.session_id == "test_session_123"
        assert session_data.total_tests == 10
        assert session_data.average_car_score == 85.5
        assert session_data.coverage_files == 5
        assert session_data.violations_found == 2
        assert session_data.duration == "2m 30s"
        assert session_data.config == {"threshold": 75.0}
        assert isinstance(session_data.timestamp, datetime)
        
        # Test serialization
        data = session_data.model_dump()
        assert isinstance(data, dict)
        assert data["session_id"] == "test_session_123"
        assert data["total_tests"] == 10
        assert data["average_car_score"] == 85.5
    
    def test_test_data_model(self):
        """Test CoverageTestData model creation and serialization."""
        test_data = CoverageTestData(
            test_name="test_user_authentication",
            test_file="tests/test_auth.py",
            car_score=92.3,
            car_grade="A",
            efficiency_level="high",
            coverage_percentage=95.0,
            coverage_signature="abc123def456",
            covered_lines=[1, 2, 5, 8, 12],
            missing_lines=[3, 6, 9],
            violations=["DS302: Missing assertion"],
            session_id="test_session_123"
        )
        
        # Test model creation
        assert test_data.test_name == "test_user_authentication"
        assert test_data.test_file == "tests/test_auth.py"
        assert test_data.car_score == 92.3
        assert test_data.car_grade == "A"
        assert test_data.efficiency_level == "high"
        assert test_data.coverage_percentage == 95.0
        assert test_data.coverage_signature == "abc123def456"
        assert test_data.covered_lines == [1, 2, 5, 8, 12]
        assert test_data.missing_lines == [3, 6, 9]
        assert test_data.violations == ["DS302: Missing assertion"]
        assert test_data.session_id == "test_session_123"
        assert isinstance(test_data.timestamp, datetime)
        
        # Test serialization
        data = test_data.model_dump()
        assert isinstance(data, dict)
        assert data["test_name"] == "test_user_authentication"
        assert data["car_score"] == 92.3
        assert data["covered_lines"] == [1, 2, 5, 8, 12]
    
    def test_file_data_model(self):
        """Test FileData model creation and serialization."""
        file_data = FileData(
            file_path="src/auth/user.py",
            total_coverage=87.5,
            tests_covering=["test_user_auth", "test_user_creation"],
            car_scores=[85.5, 78.2],
            average_car_score=81.85,
            session_id="test_session_123"
        )
        
        # Test model creation
        assert file_data.file_path == "src/auth/user.py"
        assert file_data.total_coverage == 87.5
        assert file_data.tests_covering == ["test_user_auth", "test_user_creation"]
        assert file_data.car_scores == [85.5, 78.2]
        assert file_data.average_car_score == 81.85
        assert file_data.session_id == "test_session_123"
        assert isinstance(file_data.last_updated, datetime)
        
        # Test serialization
        data = file_data.model_dump()
        assert isinstance(data, dict)
        assert data["file_path"] == "src/auth/user.py"
        assert data["total_coverage"] == 87.5
        assert data["tests_covering"] == ["test_user_auth", "test_user_creation"]
    
    def test_coverage_signature_data_model(self):
        """Test CoverageSignatureData model creation and serialization."""
        signature_data = CoverageSignatureData(
            test_name="test_user_authentication",
            signature_hash="abc123def456",
            signature_vector=[0.1, 0.2, 0.3, 0.4],
            signature_pattern="pattern123",
            session_id="test_session_123"
        )
        
        # Test model creation
        assert signature_data.test_name == "test_user_authentication"
        assert signature_data.signature_hash == "abc123def456"
        assert signature_data.signature_vector == [0.1, 0.2, 0.3, 0.4]
        assert signature_data.signature_pattern == "pattern123"
        assert signature_data.session_id == "test_session_123"
        assert isinstance(signature_data.timestamp, datetime)
        
        # Test serialization
        data = signature_data.model_dump()
        assert isinstance(data, dict)
        assert data["test_name"] == "test_user_authentication"
        assert data["signature_hash"] == "abc123def456"
        assert data["signature_vector"] == [0.1, 0.2, 0.3, 0.4]
    
    def test_signatures_collection_model(self):
        """Test SignaturesCollection model creation and serialization."""
        signature1 = CoverageSignatureData(
            test_name="test1",
            signature_hash="hash1",
            signature_vector=[0.1, 0.2],
            signature_pattern="pattern1",
            session_id="session1"
        )
        signature2 = CoverageSignatureData(
            test_name="test2",
            signature_hash="hash2",
            signature_vector=[0.3, 0.4],
            signature_pattern="pattern2",
            session_id="session2"
        )
        
        collection = SignaturesCollection(signatures=[signature1, signature2])
        
        # Test model creation
        assert len(collection.signatures) == 2
        assert collection.signatures[0].test_name == "test1"
        assert collection.signatures[1].test_name == "test2"
        
        # Test serialization
        data = collection.model_dump()
        assert isinstance(data, dict)
        assert len(data["signatures"]) == 2
        assert data["signatures"][0]["test_name"] == "test1"
        assert data["signatures"][1]["test_name"] == "test2"


class TestCoverageStorage:
    """Test CoverageStorage class functionality."""
    
    @pytest.fixture
    def temp_storage_path(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def storage_config(self, temp_storage_path):
        """Create a test storage configuration."""
        return CoverageStorageConfig(
            storage_path=temp_storage_path,
            retention_days=7,
            compression=False,
            enabled=True
        )
    
    @pytest.fixture
    def storage(self, storage_config):
        """Create a CoverageStorage instance for testing."""
        return CoverageStorage(storage_config)
    
    @pytest.fixture
    def mock_coverage_data(self):
        """Create mock coverage data."""
        coverage_data = Mock(spec=CoverageData)
        coverage_data.coverage_percentage = 95.0
        coverage_data.covered_lines = {1, 2, 5, 8, 12}
        coverage_data.missing_lines = {3, 6, 9}
        return coverage_data
    
    @pytest.fixture
    def mock_car_result(self):
        """Create mock CAR result."""
        car_result = Mock(spec=CARResult)
        car_result.car_score = 92.3
        car_result.grade = "A"
        car_result.efficiency_level = "high"
        return car_result
    
    @pytest.fixture
    def mock_coverage_signature(self):
        """Create mock coverage signature."""
        signature = Mock(spec=CoverageSignature)
        signature.signature_hash = "abc123def456"
        signature.signature_vector = [0.1, 0.2, 0.3, 0.4]
        signature.coverage_pattern = "pattern123"
        return signature
    
    def test_storage_initialization(self, storage_config):
        """Test storage initialization and directory creation."""
        storage = CoverageStorage(storage_config)
        
        # Check that directories were created
        assert storage_config.sessions_dir.exists()
        assert storage_config.tests_dir.exists()
        assert storage_config.files_dir.exists()
        assert storage_config.signatures_dir.exists()
    
    def test_storage_disabled(self, temp_storage_path):
        """Test storage when disabled."""
        config = CoverageStorageConfig(
            storage_path=temp_storage_path,
            enabled=False
        )
        storage = CoverageStorage(config)
        
        # Directories should not be created when disabled
        assert not config.sessions_dir.exists()
        assert not config.tests_dir.exists()
        assert not config.files_dir.exists()
        assert not config.signatures_dir.exists()
    
    def test_store_session_data(self, storage, temp_storage_path):
        """Test storing session data."""
        session_id = "test_session_123"
        
        storage.store_session_data(
            session_id=session_id,
            total_tests=10,
            average_car_score=85.5,
            coverage_files=5,
            violations_found=2,
            duration="2m 30s",
            config={"threshold": 75.0}
        )
        
        # Check that file was created
        session_file = storage.config.sessions_dir / f"{session_id}.json"
        assert session_file.exists()
        
        # Check file contents
        with open(session_file, 'r') as f:
            data = json.load(f)
        
        assert data["session_id"] == session_id
        assert data["total_tests"] == 10
        assert data["average_car_score"] == 85.5
        assert data["coverage_files"] == 5
        assert data["violations_found"] == 2
        assert data["duration"] == "2m 30s"
        assert data["config"] == {"threshold": 75.0}
        assert "timestamp" in data
    
    def test_store_test_data(self, storage, mock_coverage_data, mock_car_result, mock_coverage_signature):
        """Test storing test data."""
        test_name = "test_user_authentication"
        test_file = Path("tests/test_auth.py")
        session_id = "test_session_123"
        violations = ["DS302: Missing assertion"]
        
        storage.store_test_data(
            test_name=test_name,
            test_file=test_file,
            coverage_data=mock_coverage_data,
            car_result=mock_car_result,
            coverage_signature=mock_coverage_signature,
            violations=violations,
            session_id=session_id
        )
        
        # Check that file was created
        safe_test_name = storage._sanitize_filename(test_name)
        test_file_path = storage.config.tests_dir / f"{safe_test_name}.json"
        assert test_file_path.exists()
        
        # Check file contents
        with open(test_file_path, 'r') as f:
            data = json.load(f)
        
        assert data["test_name"] == test_name
        assert data["test_file"] == str(test_file)
        assert data["car_score"] == 92.3
        assert data["car_grade"] == "A"
        assert data["efficiency_level"] == "high"
        assert data["coverage_percentage"] == 95.0
        assert data["coverage_signature"] == "abc123def456"
        assert data["covered_lines"] == [1, 2, 5, 8, 12]
        assert set(data["missing_lines"]) == {3, 6, 9}
        assert data["violations"] == violations
        assert data["session_id"] == session_id
        assert "timestamp" in data
    
    def test_store_file_data(self, storage):
        """Test storing file data."""
        file_path = Path("src/auth/user.py")
        total_coverage = 87.5
        tests_covering = ["test_user_auth", "test_user_creation"]
        car_scores = [85.5, 78.2]
        session_id = "test_session_123"
        
        storage.store_file_data(
            file_path=file_path,
            total_coverage=total_coverage,
            tests_covering=tests_covering,
            car_scores=car_scores,
            session_id=session_id
        )
        
        # Check that file was created
        safe_file_name = storage._sanitize_filename(str(file_path))
        file_storage_path = storage.config.files_dir / f"{safe_file_name}.json"
        assert file_storage_path.exists()
        
        # Check file contents
        with open(file_storage_path, 'r') as f:
            data = json.load(f)
        
        assert data["file_path"] == str(file_path)
        assert data["total_coverage"] == total_coverage
        assert data["tests_covering"] == tests_covering
        assert data["car_scores"] == car_scores
        assert data["average_car_score"] == 81.85  # (85.5 + 78.2) / 2
        assert data["session_id"] == session_id
        assert "last_updated" in data
    
    def test_store_coverage_signature(self, storage, mock_coverage_signature):
        """Test storing coverage signature."""
        test_name = "test_user_authentication"
        session_id = "test_session_123"
        
        storage.store_coverage_signature(
            test_name=test_name,
            signature=mock_coverage_signature,
            session_id=session_id
        )
        
        # Check that signatures file was created
        signatures_file = storage.config.signatures_dir / "signatures.json"
        assert signatures_file.exists()
        
        # Check file contents
        with open(signatures_file, 'r') as f:
            data = json.load(f)
        
        assert "signatures" in data
        assert len(data["signatures"]) == 1
        
        signature_data = data["signatures"][0]
        assert signature_data["test_name"] == test_name
        assert signature_data["signature_hash"] == "abc123def456"
        assert signature_data["signature_vector"] == [0.1, 0.2, 0.3, 0.4]
        assert signature_data["signature_pattern"] == "pattern123"
        assert signature_data["session_id"] == session_id
        assert "timestamp" in signature_data
    
    def test_get_session_data(self, storage):
        """Test retrieving session data."""
        session_id = "test_session_123"
        
        # Store session data first
        storage.store_session_data(
            session_id=session_id,
            total_tests=10,
            average_car_score=85.5,
            coverage_files=5,
            violations_found=2,
            duration="2m 30s"
        )
        
        # Retrieve session data
        session_data = storage.get_session_data(session_id)
        
        assert session_data is not None
        assert isinstance(session_data, SessionData)
        assert session_data.session_id == session_id
        assert session_data.total_tests == 10
        assert session_data.average_car_score == 85.5
        assert session_data.coverage_files == 5
        assert session_data.violations_found == 2
        assert session_data.duration == "2m 30s"
    
    def test_get_session_data_not_found(self, storage):
        """Test retrieving non-existent session data."""
        session_data = storage.get_session_data("non_existent_session")
        assert session_data is None
    
    def test_get_test_data(self, storage, mock_coverage_data, mock_car_result, mock_coverage_signature):
        """Test retrieving test data."""
        test_name = "test_user_authentication"
        test_file = Path("tests/test_auth.py")
        session_id = "test_session_123"
        violations = ["DS302: Missing assertion"]
        
        # Store test data first
        storage.store_test_data(
            test_name=test_name,
            test_file=test_file,
            coverage_data=mock_coverage_data,
            car_result=mock_car_result,
            coverage_signature=mock_coverage_signature,
            violations=violations,
            session_id=session_id
        )
        
        # Retrieve test data
        test_data = storage.get_test_data(test_name)
        
        assert test_data is not None
        assert isinstance(test_data, CoverageTestData)
        assert test_data.test_name == test_name
        assert test_data.test_file == str(test_file)
        assert test_data.car_score == 92.3
        assert test_data.car_grade == "A"
        assert test_data.efficiency_level == "high"
        assert test_data.coverage_percentage == 95.0
        assert test_data.coverage_signature == "abc123def456"
        assert test_data.covered_lines == [1, 2, 5, 8, 12]
        assert set(test_data.missing_lines) == {3, 6, 9}
        assert test_data.violations == violations
        assert test_data.session_id == session_id
    
    def test_get_test_data_not_found(self, storage):
        """Test retrieving non-existent test data."""
        test_data = storage.get_test_data("non_existent_test")
        assert test_data is None
    
    def test_get_file_data(self, storage):
        """Test retrieving file data."""
        file_path = Path("src/auth/user.py")
        total_coverage = 87.5
        tests_covering = ["test_user_auth", "test_user_creation"]
        car_scores = [85.5, 78.2]
        session_id = "test_session_123"
        
        # Store file data first
        storage.store_file_data(
            file_path=file_path,
            total_coverage=total_coverage,
            tests_covering=tests_covering,
            car_scores=car_scores,
            session_id=session_id
        )
        
        # Retrieve file data
        file_data = storage.get_file_data(file_path)
        
        assert file_data is not None
        assert isinstance(file_data, FileData)
        assert file_data.file_path == str(file_path)
        assert file_data.total_coverage == total_coverage
        assert file_data.tests_covering == tests_covering
        assert file_data.car_scores == car_scores
        assert file_data.average_car_score == 81.85
        assert file_data.session_id == session_id
    
    def test_get_file_data_not_found(self, storage):
        """Test retrieving non-existent file data."""
        file_data = storage.get_file_data(Path("non_existent_file.py"))
        assert file_data is None
    
    def test_get_all_signatures(self, storage, mock_coverage_signature):
        """Test retrieving all signatures."""
        test_name1 = "test_user_authentication"
        test_name2 = "test_user_creation"
        session_id = "test_session_123"
        
        # Store multiple signatures
        storage.store_coverage_signature(test_name1, mock_coverage_signature, session_id)
        
        # Create a second signature
        signature2 = Mock(spec=CoverageSignature)
        signature2.signature_hash = "def456ghi789"
        signature2.signature_vector = [0.5, 0.6, 0.7, 0.8]
        signature2.coverage_pattern = "pattern456"
        
        storage.store_coverage_signature(test_name2, signature2, session_id)
        
        # Retrieve all signatures
        signatures = storage.get_all_signatures()
        
        assert len(signatures) == 2
        assert all(isinstance(sig, CoverageSignatureData) for sig in signatures)
        
        # Check that both signatures are present
        test_names = [sig.test_name for sig in signatures]
        assert test_name1 in test_names
        assert test_name2 in test_names
    
    def test_find_similar_signatures(self, storage, mock_coverage_signature):
        """Test finding similar signatures."""
        test_name = "test_user_authentication"
        session_id = "test_session_123"
        
        # Store a signature
        storage.store_coverage_signature(test_name, mock_coverage_signature, session_id)
        
        # Create a similar signature
        similar_signature = Mock(spec=CoverageSignature)
        similar_signature.signature_hash = "abc123def456"  # Same hash = 100% similarity
        
        # Find similar signatures
        similar_signatures = storage.find_similar_signatures(similar_signature, similarity_threshold=0.8)
        
        assert len(similar_signatures) == 1
        assert similar_signatures[0]["test_name"] == test_name
        assert similar_signatures[0]["similarity_score"] == 1.0
    
    def test_get_recent_sessions(self, storage):
        """Test getting recent sessions."""
        # Store multiple sessions
        for i in range(5):
            session_id = f"session_{i}"
            storage.store_session_data(
                session_id=session_id,
                total_tests=10 + i,
                average_car_score=80.0 + i,
                coverage_files=5,
                violations_found=2,
                duration=f"{i}m"
            )
        
        # Get recent sessions
        recent_sessions = storage.get_recent_sessions(limit=3)
        
        assert len(recent_sessions) == 3
        assert all(isinstance(session, SessionData) for session in recent_sessions)
        
        # Should be sorted by timestamp (most recent first)
        # Since we created them in sequence, the most recent should have the highest session number
        assert recent_sessions[0].session_id == "session_4"
        assert recent_sessions[1].session_id == "session_3"
        assert recent_sessions[2].session_id == "session_2"
    
    def test_get_coverage_trends(self, storage):
        """Test getting coverage trends."""
        # Store multiple sessions
        for i in range(3):
            session_id = f"session_{i}"
            storage.store_session_data(
                session_id=session_id,
                total_tests=10,
                average_car_score=80.0 + i * 5,  # Increasing scores
                coverage_files=5,
                violations_found=5 - i,  # Decreasing violations
                duration=f"{i}m"
            )
        
        # Get trends
        trends = storage.get_coverage_trends(days=7)
        
        assert trends["period_days"] == 7
        assert trends["session_count"] == 3
        assert trends["average_car_score"] == 85.0  # (80 + 85 + 90) / 3
        assert trends["total_violations"] == 12  # 5 + 4 + 3 = 12
        assert trends["car_score_trend"] == "improving"  # 80 -> 85 -> 90
        assert trends["violation_trend"] == "improving"  # 5 -> 4 -> 3
    
    def test_sanitize_filename(self, storage):
        """Test filename sanitization."""
        # Test various problematic characters
        test_cases = [
            ("test/with/slashes", "test_with_slashes"),
            ("test\\with\\backslashes", "test_with_backslashes"),
            ("test:with:colons", "test_with_colons"),
            ("test*with*asterisks", "test_with_asterisks"),
            ("test?with?questions", "test_with_questions"),
            ('test"with"quotes', "test_with_quotes"),
            ("test<with>brackets", "test_with_brackets"),
            ("test|with|pipes", "test_with_pipes"),
        ]
        
        for input_name, expected in test_cases:
            result = storage._sanitize_filename(input_name)
            assert result == expected
        
        # Test length limiting
        long_name = "a" * 150
        result = storage._sanitize_filename(long_name)
        assert len(result) == 100
    
    def test_calculate_similarity(self, storage):
        """Test similarity calculation."""
        # Test identical hashes
        similarity = storage._calculate_similarity("abc123", "abc123")
        assert similarity == 1.0
        
        # Test completely different hashes
        similarity = storage._calculate_similarity("abc123", "def456")
        assert similarity == 0.0
        
        # Test partial similarity
        similarity = storage._calculate_similarity("abc123", "abc456")
        assert 0.0 < similarity < 1.0
        
        # Test empty hashes
        similarity = storage._calculate_similarity("", "")
        assert similarity == 0.0
        
        similarity = storage._calculate_similarity("abc123", "")
        assert similarity == 0.0


class TestGlobalStorage:
    """Test global storage functionality."""
    
    def test_get_coverage_storage_singleton(self):
        """Test that get_coverage_storage returns a singleton."""
        storage1 = get_coverage_storage()
        storage2 = get_coverage_storage()
        
        assert storage1 is storage2
        assert isinstance(storage1, CoverageStorage)


class TestStorageIntegration:
    """Test integration scenarios."""
    
    @pytest.fixture
    def temp_storage_path(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def storage_config(self, temp_storage_path):
        """Create a test storage configuration."""
        return CoverageStorageConfig(
            storage_path=temp_storage_path,
            retention_days=1,  # Short retention for testing
            enabled=True
        )
    
    @pytest.fixture
    def storage(self, storage_config):
        """Create a CoverageStorage instance for testing."""
        return CoverageStorage(storage_config)
    
    def test_full_workflow(self, storage):
        """Test a complete workflow: store data, retrieve it, and analyze it."""
        # Create mock objects
        mock_coverage_data = Mock(spec=CoverageData)
        mock_coverage_data.coverage_percentage = 95.0
        mock_coverage_data.covered_lines = {1, 2, 5, 8, 12}
        mock_coverage_data.missing_lines = {3, 6, 9}
        
        mock_car_result = Mock(spec=CARResult)
        mock_car_result.car_score = 92.3
        mock_car_result.grade = "A"
        mock_car_result.efficiency_level = "high"
        
        mock_coverage_signature = Mock(spec=CoverageSignature)
        mock_coverage_signature.signature_hash = "abc123def456"
        mock_coverage_signature.signature_vector = [0.1, 0.2, 0.3, 0.4]
        mock_coverage_signature.coverage_pattern = "pattern123"
        
        session_id = "integration_test_session"
        test_name = "test_integration_workflow"
        test_file = Path("tests/test_integration.py")
        file_path = Path("src/integration/module.py")
        violations = ["DS302: Missing assertion"]
        
        # 1. Store session data
        storage.store_session_data(
            session_id=session_id,
            total_tests=1,
            average_car_score=90.0,
            coverage_files=1,
            violations_found=1,
            duration="1m"
        )
        
        # 2. Store test data
        storage.store_test_data(
            test_name=test_name,
            test_file=test_file,
            coverage_data=mock_coverage_data,
            car_result=mock_car_result,
            coverage_signature=mock_coverage_signature,
            violations=violations,
            session_id=session_id
        )
        
        # 3. Store file data
        storage.store_file_data(
            file_path=file_path,
            total_coverage=95.0,
            tests_covering=[test_name],
            car_scores=[92.3],
            session_id=session_id
        )
        
        # 4. Store coverage signature
        storage.store_coverage_signature(test_name, mock_coverage_signature, session_id)
        
        # 5. Retrieve and verify all data
        session_data = storage.get_session_data(session_id)
        assert session_data is not None
        assert session_data.total_tests == 1
        assert session_data.average_car_score == 90.0
        
        test_data = storage.get_test_data(test_name)
        assert test_data is not None
        assert test_data.car_score == 92.3
        assert test_data.violations == violations
        
        file_data = storage.get_file_data(file_path)
        assert file_data is not None
        assert file_data.total_coverage == 95.0
        assert test_name in file_data.tests_covering
        
        signatures = storage.get_all_signatures()
        assert len(signatures) == 1
        assert signatures[0].test_name == test_name
        
        # 6. Test analysis features
        recent_sessions = storage.get_recent_sessions(limit=5)
        assert len(recent_sessions) == 1
        assert recent_sessions[0].session_id == session_id
        
        trends = storage.get_coverage_trends(days=7)
        assert trends["session_count"] == 1
        assert trends["average_car_score"] == 90.0
        assert trends["total_violations"] == 1
    
    def test_error_handling(self, storage):
        """Test error handling scenarios."""
        # Test storing with invalid data (should raise validation errors)
        with pytest.raises(Exception):
            storage.store_session_data(
                session_id="",  # Empty session ID
                total_tests=-1,  # Invalid test count
                average_car_score=150.0,  # Invalid CAR score
                coverage_files=-1,  # Invalid file count
                violations_found=-1,  # Invalid violation count
                duration=""  # Empty duration
            )
        
        # Test retrieving from non-existent files
        session_data = storage.get_session_data("non_existent")
        assert session_data is None
        
        test_data = storage.get_test_data("non_existent")
        assert test_data is None
        
        file_data = storage.get_file_data(Path("non_existent.py"))
        assert file_data is None
        
        signatures = storage.get_all_signatures()
        assert signatures == []
    
    def test_storage_disabled_workflow(self, temp_storage_path):
        """Test workflow when storage is disabled."""
        config = CoverageStorageConfig(
            storage_path=temp_storage_path,
            enabled=False
        )
        storage = CoverageStorage(config)
        
        # All storage operations should be no-ops
        storage.store_session_data(
            session_id="disabled_session",
            total_tests=10,
            average_car_score=85.0,
            coverage_files=5,
            violations_found=2,
            duration="2m"
        )
        
        # No files should be created
        assert not config.sessions_dir.exists()
        assert not config.tests_dir.exists()
        assert not config.files_dir.exists()
        assert not config.signatures_dir.exists()
        
        # Retrieval should return None/empty
        session_data = storage.get_session_data("disabled_session")
        assert session_data is None
        
        signatures = storage.get_all_signatures()
        assert signatures == []