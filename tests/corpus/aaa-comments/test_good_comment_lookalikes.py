"""Near-misses: text that looks like an AAA comment but isn't one (in a string, a
docstring, after code, or prose that starts with a section's name), and comments
inside an opened `with` block. Analysed, never run."""


def test_render_banner(banner):
    """# Assert in a docstring heads nothing."""
    # Arrange
    text = "# Act is only a string here"
    # Act as a reader would: this is prose under Arrange
    banner.theme = "plain"
    # Act
    html = banner.render(text)
    # Assert
    assert html == "<h1># Act is only a string here</h1>"


def test_signup_inside_a_transaction(db, signup):
    # Arrange
    with db.transaction():
        # Act
        signup.register("ada@example.com")
        # Assert
        assert db.count("users") == 1


def test_store_counts(store):
    # Arrange
    store.put("k", 1)  # Assert after code is a trailing comment
    # Act
    size = store.size()
    # Assert
    assert size == 1


def test_job_marks_itself_done(job):
    """An `assert*` call asserts under `# Assert` as an `assert` does."""
    # Act
    job.run()
    # Assert
    job.done.assert_called_once()
