# Failure Catalog

This document maps each enforcement rule to its expected failures and fixes.

## Marker Rule

### Symptom

- Test fails with marker/classification issue.

### Typical causes

- Missing `@pytest.mark.<name>` marker.
- Test path does not map to expected marker.
- Marker not declared in pytest config.

### Fixes

1. Add explicit marker to the test.
2. Place test under a recognized path (for auto-detection).
3. Define marker declarations in `pytest.ini` or `[tool.pytest.ini_options]`.
4. Add custom mapping with `drill_sergeant_marker_mappings` or `[tool.drill_sergeant.marker_mappings]`.

## AAA Rule

### Symptom

- Test fails due to missing or invalid AAA structure.

### Typical causes

- Missing one or more AAA section comments.
- Invalid comment grammar (missing `-` separator, empty description).
- In `strict` mode: section order violations or duplicate section headers.

### Fixes

1. Use exact grammar: `# <Keyword> - <description>`.
2. Ensure all required sections exist.
3. In `strict` mode, keep section order: Arrange -> Act -> Assert.
4. If using alternate wording, enable and configure synonyms.

## File-Length Rule

### Symptom

- Test file fails or warns for excessive line count.

### Typical causes

- File exceeds `drill_sergeant_max_file_length`.
- Rule configured in `error` mode for current path.

### Fixes

1. Split large file into smaller focused test modules.
2. Use `drill_sergeant_file_length_exclude` for legacy paths.
3. Switch mode to `warn` for gradual migration.
4. Use inline ignore token for one-off legacy files if policy allows:
   - `# drill-sergeant: file-length ignore`

## Internal Plugin Error

### Symptom

- Failure mentions drill-sergeant internal error.

### Typical causes

- Runtime exception during plugin validation.

### Fixes

1. Run with `DRILL_SERGEANT_DEBUG_CONFIG=true` to inspect resolved config.
2. Confirm plugin options are valid and typed correctly.
3. Reproduce with minimal test case and file issue including stack trace.
