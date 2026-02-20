"""Unit tests for write_markers_to_files helper."""

from pathlib import Path

import pytest

from pytest_drill_sergeant.utils import write_markers_to_files


@pytest.mark.unit
class TestWriteMarkersToFiles:
    """Verify write_markers_to_files inserts or replaces correctly."""

    @pytest.fixture
    def test_file_with_blank_line_before_def(self, tmp_path: Path) -> Path:
        """File with blank line then def (decorator should replace the blank)."""
        path = tmp_path / "test_bar.py"
        # Line 1: blank, Line 2: blank, Line 3: def (so def at 1-based line 3)
        path.write_text(
            "\n"
            "\n"
            "def test_bar() -> None:\n"
            "    assert True\n",
            encoding="utf-8",
        )
        return path

    @pytest.fixture
    def test_file_no_blank_before_def(self, tmp_path: Path) -> Path:
        """File with no blank before def (decorator should be inserted)."""
        path = tmp_path / "test_baz.py"
        path.write_text(
            "def test_baz() -> None:\n"
            "    pass\n",
            encoding="utf-8",
        )
        return path

    def test_replaces_blank_line_with_decorator_no_extra_blank(
        self, test_file_with_blank_line_before_def: Path
    ) -> None:
        """# Arrange - File has blank line before def
        # Act - write_markers_to_files with unit marker at def line
        # Assert - Blank is replaced by decorator; no blank between decorator and def
        """
        # Arrange - Use fixture file with blank line then def at 1-based line 3
        path = test_file_with_blank_line_before_def

        # Act - Write unit marker at def line
        write_markers_to_files([(path, 3, "unit")])

        # Assert - Decorator replaced blank; no lines between decorator and def
        content = path.read_text()
        lines = content.splitlines()
        assert "@pytest.mark.unit" in content
        assert "def test_bar()" in content
        def_idx = next(i for i, line in enumerate(lines) if "def test_bar()" in line)
        assert def_idx >= 1
        assert lines[def_idx - 1].strip() == "@pytest.mark.unit"
        # Explicit: no lines between the decorator and the def (decorator must be immediately above)
        decorator_idx = next(
            i for i in range(def_idx) if "@pytest.mark.unit" in lines[i]
        )
        assert def_idx == decorator_idx + 1, "no lines between annotation and def"

    def test_inserts_decorator_when_no_blank_before_def(
        self, test_file_no_blank_before_def: Path
    ) -> None:
        """# Arrange - File has no blank before def
        # Act - write_markers_to_files with unit marker at def line
        # Assert - Decorator inserted; def on next line
        """
        # Arrange - Use fixture file with def at 1-based line 1
        path = test_file_no_blank_before_def

        # Act - Write unit marker at def line
        write_markers_to_files([(path, 1, "unit")])

        # Assert - import pytest added; decorator immediately above def; no lines between
        content = path.read_text()
        assert "import pytest" in content
        lines = content.splitlines()
        decorator_idx = next(
            i for i, line in enumerate(lines) if "@pytest.mark.unit" in line
        )
        def_idx = next(i for i, line in enumerate(lines) if "def test_baz()" in line)
        assert def_idx == decorator_idx + 1, "no lines between annotation and def"

    def test_skips_when_marker_already_present(self, tmp_path: Path) -> None:
        """# Arrange - File already has @pytest.mark.unit above def
        # Act - write_markers_to_files for same marker
        # Assert - No duplicate decorator; import pytest added if missing
        """
        # Arrange - File with decorator and def at 1-based line 2 (no import pytest)
        path = tmp_path / "test_qux.py"
        path.write_text(
            "@pytest.mark.unit\n"
            "def test_qux() -> None:\n"
            "    pass\n",
            encoding="utf-8",
        )

        # Act - Try to write same marker again
        write_markers_to_files([(path, 2, "unit")])

        # Assert - No duplicate decorator; import pytest added so annotation is valid
        content = path.read_text()
        assert content.count("@pytest.mark.unit") == 1
        assert "import pytest" in content
        assert "def test_qux()" in content

    def test_import_pytest_after_one_line_module_docstring(self, tmp_path: Path) -> None:
        """# Arrange - File with one-line module docstring then imports
        # Act - write_markers_to_files adds a marker
        # Assert - import pytest is after the docstring, not inside it
        """
        # Arrange - Module docstring on first line, then blank, then def
        path = tmp_path / "test_docstring.py"
        path.write_text(
            '"""Unit tests for CLI."""\n'
            "\n"
            "def test_cli() -> None:\n"
            "    pass\n",
            encoding="utf-8",
        )

        # Act - Write unit marker at def (1-based line 3)
        write_markers_to_files([(path, 3, "unit")])

        # Assert - import pytest after docstring; decorator above def
        content = path.read_text()
        assert "import pytest" in content
        assert "@pytest.mark.unit" in content
        # import pytest must not appear inside the docstring (first line only has docstring)
        first_line = content.splitlines()[0]
        assert "import pytest" not in first_line
        # import pytest should be after the blank following the docstring
        lines = content.splitlines()
        import_idx = next(i for i, line in enumerate(lines) if line.strip() == "import pytest")
        assert import_idx >= 1

    def test_import_pytest_never_inside_function_docstring(self, tmp_path: Path) -> None:
        """# Arrange - File with function that has a docstring (triple-quotes later in file)
        # Act - write_markers_to_files adds a marker
        # Assert - import pytest is at module level (no indent), not inside the function
        """
        # Arrange - No module docstring; a function with docstring; then a test def
        path = tmp_path / "test_func_docstring.py"
        path.write_text(
            "def _helper() -> None:\n"
            '    """Create fixture.\n'
            "    Args:\n"
            '        root: Path.\n'
            '    """\n'
            "    pass\n"
            "\n"
            "def test_thing() -> None:\n"
            "    pass\n",
            encoding="utf-8",
        )

        # Act - Write unit marker at test_thing (1-based line 8)
        write_markers_to_files([(path, 8, "unit")])

        # Assert - import pytest is at module level (no leading space), never indented
        content = path.read_text()
        assert "import pytest" in content
        for line in content.splitlines():
            if "import pytest" in line:
                assert not line.startswith(" ") and not line.startswith("\t"), (
                    "import pytest must be at module level, not inside a docstring/function"
                )
                break

    def test_adds_import_pytest_when_missing(self, tmp_path: Path) -> None:
        """# Arrange - File with no pytest import
        # Act - write_markers_to_files adds a marker
        # Assert - File contains 'import pytest' so the annotation is valid
        """
        # Arrange - File with def but no import pytest (e.g. only other imports)
        path = tmp_path / "test_no_pytest.py"
        path.write_text(
            "from pathlib import Path\n"
            "\n"
            "def test_thing() -> None:\n"
            "    pass\n",
            encoding="utf-8",
        )

        # Act - Write unit marker at def line (1-based line 3)
        write_markers_to_files([(path, 3, "unit")])

        # Assert - import pytest was added and decorator is present
        content = path.read_text()
        assert "import pytest" in content
        assert "@pytest.mark.unit" in content
        assert "def test_thing()" in content
        lines = content.splitlines()
        def_idx = next(i for i, line in enumerate(lines) if "def test_thing()" in line)
        decorator_idx = next(
            i for i in range(def_idx) if "@pytest.mark.unit" in lines[i]
        )
        assert def_idx == decorator_idx + 1, "no lines between annotation and def"

    def test_multiple_tests_same_file_reverse_order(self, tmp_path: Path) -> None:
        """# Arrange - Two defs in one file
        # Act - write_markers_to_files for both (reverse line order)
        # Assert - Both get decorator without shifting line numbers
        """
        # Arrange - File with two defs at 1-based lines 2 and 5
        path = tmp_path / "test_multi.py"
        path.write_text(
            "\n"
            "def test_first() -> None:\n"
            "    pass\n"
            "\n"
            "def test_second() -> None:\n"
            "    pass\n",
            encoding="utf-8",
        )

        # Act - Write markers for both (higher line first so reverse order)
        write_markers_to_files([(path, 5, "unit"), (path, 2, "unit")])

        # Assert - Both defs have decorator immediately above; no lines between
        content = path.read_text()
        assert content.count("@pytest.mark.unit") == 2
        lines = content.splitlines()
        first_def_idx = next(
            i for i, line in enumerate(lines) if "def test_first()" in line
        )
        second_def_idx = next(
            i for i, line in enumerate(lines) if "def test_second()" in line
        )
        # Decorator immediately above each def is the last marker line before that def
        first_decorator_idx = max(
            i for i in range(first_def_idx) if "@pytest.mark.unit" in lines[i]
        )
        second_decorator_idx = max(
            i for i in range(second_def_idx) if "@pytest.mark.unit" in lines[i]
        )
        assert first_def_idx == first_decorator_idx + 1, "no lines between annotation and first def"
        assert second_def_idx == second_decorator_idx + 1, "no lines between annotation and second def"
