# Analysis Algorithms

## Core Detection Algorithms

### 1. Behavior Integrity Score (BIS) - WHAT vs HOW Detection

**Purpose**: Detect tests that focus on implementation details rather than behavior.

**Algorithm Components**:

#### Private Surface Access Detection
```python
class PrivateAccessDetector:
    def detect(self, ast_tree: ast.AST, sut_package: str) -> List[Finding]:
        findings = []

        # Detect private imports
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(f"{sut_package}._"):
                    findings.append(Finding(
                        rule_id="private-import",
                        severity="warn",
                        message=f"Importing private module: {node.module}"
                    ))

            # Detect private attribute access
            elif isinstance(node, ast.Attribute):
                if node.attr.startswith("_"):
                    findings.append(Finding(
                        rule_id="private-attr",
                        severity="warn",
                        message=f"Accessing private attribute: {node.attr}"
                    ))

        return findings
```

#### Mock Over-Specification Detection
```python
class MockOverspecDetector:
    MOCK_ASSERTS = {
        "assert_called_once", "assert_called_with",
        "assert_has_calls", "assert_any_call"
    }

    def detect(self, ast_tree: ast.AST) -> List[Finding]:
        findings = []
        mock_assert_count = 0

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Attribute):
                if node.attr in self.MOCK_ASSERTS:
                    mock_assert_count += 1

        if mock_assert_count > 3:  # Threshold
            findings.append(Finding(
                rule_id="mock-overspec",
                severity="warn",
                message=f"Excessive mock assertions: {mock_assert_count}"
            ))

        return findings
```

#### Structural Equality Detection
```python
class StructuralEqualityDetector:
    STRUCTURAL_METHODS = {
        "__dict__", "vars", "dataclasses.asdict", "repr"
    }

    def detect(self, ast_tree: ast.AST) -> List[Finding]:
        findings = []

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Attribute):
                if node.attr in self.STRUCTURAL_METHODS:
                    findings.append(Finding(
                        rule_id="structural-equality",
                        severity="warn",
                        message=f"Comparing internal structure: {node.attr}"
                    ))

        return findings
```

#### BIS Calculation
```python
def calculate_bis(features: TestFeatures) -> float:
    score = 100.0

    # Penalize HOW smells
    score -= 15 * features.private_access_count
    score -= 10 * features.mock_assert_count
    score -= 15 * features.patched_internal_count
    score -= 8 * features.structural_compare_count
    score -= 5 * (features.exception_message_length // 40)

    # Reward WHAT behaviors
    score += 8 * min(features.public_api_assert_count, 5)

    return max(0, min(100, score))
```

### 2. Duplicate Test Detection

#### Static AST Similarity (SimHash)
```python
class ASTSimHashDetector:
    def __init__(self, threshold: int = 6):
        self.threshold = threshold

    def extract_features(self, ast_tree: ast.AST) -> List[str]:
        """Extract AST node type n-grams"""
        node_types = []
        for node in ast.walk(ast_tree):
            node_types.append(type(node).__name__)

        # Create 4-grams
        ngrams = []
        for i in range(len(node_types) - 3):
            ngrams.append("|".join(node_types[i:i+4]))

        return ngrams

    def compute_simhash(self, features: List[str]) -> int:
        """Compute SimHash of features"""
        bits = [0] * 128

        for feature in features:
            hash_val = int(hashlib.md5(feature.encode()).hexdigest(), 16)
            for i in range(128):
                bits[i] += 1 if (hash_val >> i) & 1 else -1

        simhash = 0
        for i, weight in enumerate(bits):
            if weight > 0:
                simhash |= (1 << i)

        return simhash

    def hamming_distance(self, a: int, b: int) -> int:
        return (a ^ b).bit_count()

    def find_clusters(self, test_files: List[Path]) -> List[Cluster]:
        """Find clusters of similar tests"""
        signatures = {}

        # Compute signatures
        for test_file in test_files:
            tree = ast.parse(test_file.read_text())
            features = self.extract_features(tree)
            signatures[test_file] = self.compute_simhash(features)

        # Find clusters
        clusters = []
        processed = set()

        for file1, sig1 in signatures.items():
            if file1 in processed:
                continue

            cluster = [file1]
            processed.add(file1)

            for file2, sig2 in signatures.items():
                if file2 in processed:
                    continue

                if self.hamming_distance(sig1, sig2) <= self.threshold:
                    cluster.append(file2)
                    processed.add(file2)

            if len(cluster) >= 3:  # Minimum cluster size
                clusters.append(Cluster(
                    kind="static",
                    members=cluster,
                    similarity=self.threshold
                ))

        return clusters
```

#### Dynamic Coverage Similarity (Jaccard)
```python
class CoverageSimilarityDetector:
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold

    def jaccard_similarity(self, set1: Set[int], set2: Set[int]) -> float:
        """Calculate Jaccard similarity between two sets"""
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def find_clusters(self, coverage_data: Dict[str, Set[int]]) -> List[Cluster]:
        """Find clusters based on coverage similarity"""
        clusters = []
        processed = set()

        for test1, cov1 in coverage_data.items():
            if test1 in processed:
                continue

            cluster = [test1]
            processed.add(test1)

            for test2, cov2 in coverage_data.items():
                if test2 in processed:
                    continue

                similarity = self.jaccard_similarity(cov1, cov2)
                if similarity >= self.threshold:
                    cluster.append(test2)
                    processed.add(test2)

            if len(cluster) >= 2:
                clusters.append(Cluster(
                    kind="dynamic",
                    members=cluster,
                    similarity=self.threshold
                ))

        return clusters
```

### 3. Parametrization Suggestion Algorithm

```python
class ParametrizationSuggester:
    def analyze_cluster(self, cluster: Cluster) -> Optional[ParametrizationSuggestion]:
        """Analyze a cluster and suggest parametrization"""
        if len(cluster.members) < 3:
            return None

        # Extract literal differences between tests
        literal_diffs = self.extract_literal_differences(cluster.members)

        if len(literal_diffs) <= 3:  # Only suggest if few differences
            return ParametrizationSuggestion(
                parameter_names=list(literal_diffs.keys()),
                test_values=self.generate_test_values(literal_diffs),
                original_tests=cluster.members
            )

        return None

    def extract_literal_differences(self, test_files: List[Path]) -> Dict[str, List[Any]]:
        """Extract different literal values between similar tests"""
        literal_maps = []

        for test_file in test_files:
            tree = ast.parse(test_file.read_text())
            literals = self.extract_literals(tree)
            literal_maps.append(literals)

        # Find positions that differ
        differing_positions = set()
        for i in range(len(literal_maps)):
            for j in range(i + 1, len(literal_maps)):
                for pos, (lit1, lit2) in enumerate(zip(literal_maps[i], literal_maps[j])):
                    if lit1 != lit2:
                        differing_positions.add(pos)

        # Group by position
        param_suggestions = {}
        for pos in differing_positions:
            values = [lit_map[pos] for lit_map in literal_maps]
            param_name = f"param_{pos}"
            param_suggestions[param_name] = values

        return param_suggestions
```

### 4. Fixture Extraction Algorithm

```python
class FixtureExtractor:
    def find_arrange_patterns(self, test_files: List[Path]) -> List[FixtureSuggestion]:
        """Find repeated arrange patterns that could become fixtures"""
        arrange_patterns = {}

        for test_file in test_files:
            tree = ast.parse(test_file.read_text())
            arrange_blocks = self.extract_arrange_blocks(tree)

            for arrange_block in arrange_blocks:
                # Create fingerprint of arrange block
                fingerprint = self.create_arrange_fingerprint(arrange_block)

                if fingerprint not in arrange_patterns:
                    arrange_patterns[fingerprint] = []
                arrange_patterns[fingerprint].append((test_file, arrange_block))

        # Find patterns with multiple occurrences
        suggestions = []
        for fingerprint, occurrences in arrange_patterns.items():
            if len(occurrences) >= 2:
                suggestion = self.create_fixture_suggestion(occurrences)
                suggestions.append(suggestion)

        return suggestions

    def create_arrange_fingerprint(self, arrange_block: ast.AST) -> str:
        """Create a normalized fingerprint of an arrange block"""
        # Strip variable names, keep structure and types
        normalized = []

        for node in ast.walk(arrange_block):
            if isinstance(node, ast.Assign):
                # Extract type hints and patterns
                type_info = self.extract_type_info(node)
                normalized.append(f"assign_{type_info}")
            elif isinstance(node, ast.Call):
                # Extract function patterns
                func_info = self.extract_function_info(node)
                normalized.append(f"call_{func_info}")

        return "|".join(normalized)

    def create_fixture_suggestion(self, occurrences: List[Tuple[Path, ast.AST]]) -> FixtureSuggestion:
        """Create a fixture suggestion from repeated patterns"""
        # Analyze common patterns
        common_patterns = self.analyze_common_patterns(occurrences)

        # Generate fixture name from context
        fixture_name = self.generate_fixture_name(common_patterns)

        # Generate fixture code
        fixture_code = self.generate_fixture_code(common_patterns)

        return FixtureSuggestion(
            fixture_name=fixture_name,
            fixture_code=fixture_code,
            usage_count=len(occurrences),
            original_tests=[path for path, _ in occurrences]
        )
```

### 5. AAA Comment Detection

```python
class AAADetector:
    def detect_aaa_structure(self, test_file: Path) -> List[Finding]:
        """Detect AAA comment structure in test functions"""
        tree = ast.parse(test_file.read_text())
        findings = []

        # Extract comments
        comments = self.extract_comments(test_file)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                aaa_analysis = self.analyze_aaa_structure(node, comments)

                if not aaa_analysis.has_aaa_comments:
                    findings.append(Finding(
                        rule_id="aaa-missing",
                        severity="advice",
                        message=f"Test {node.name} lacks AAA comments"
                    ))
                elif not aaa_analysis.correct_order:
                    findings.append(Finding(
                        rule_id="aaa-order",
                        severity="advice",
                        message=f"Test {node.name} has incorrect AAA order: {aaa_analysis.found_order}"
                    ))

        return findings

    def extract_comments(self, file_path: Path) -> Dict[int, str]:
        """Extract comments with line numbers"""
        comments = {}

        with open(file_path) as f:
            for line_num, line in enumerate(f, 1):
                if '#' in line:
                    comment = line.split('#')[1].strip().lower()
                    comments[line_num] = comment

        return comments

    def analyze_aaa_structure(self, func_node: ast.FunctionDef, comments: Dict[int, str]) -> AAAResult:
        """Analyze AAA structure of a test function"""
        aaa_sections = []

        # Find AAA comments within function
        start_line = func_node.lineno
        end_line = getattr(func_node, 'end_lineno', start_line)

        for line_num in range(start_line, end_line + 1):
            comment = comments.get(line_num, "")
            if any(keyword in comment for keyword in ['arrange', 'act', 'assert']):
                if 'arrange' in comment:
                    aaa_sections.append(('arrange', line_num))
                elif 'act' in comment:
                    aaa_sections.append(('act', line_num))
                elif 'assert' in comment:
                    aaa_sections.append(('assert', line_num))

        # Check order
        correct_order = ['arrange', 'act', 'assert']
        found_order = [section[0] for section in aaa_sections]

        has_aaa = len(aaa_sections) > 0
        correct = found_order == correct_order

        return AAAResult(
            has_aaa_comments=has_aaa,
            correct_order=correct,
            found_order=found_order,
            sections=aaa_sections
        )
```

## Performance Optimizations

### Caching Strategy
- AST parsing results cached by file modification time
- Analysis results cached with test file fingerprints
- Coverage data processed incrementally

### Parallel Processing
- Static analysis of independent files processed in parallel
- Coverage similarity computation uses multiprocessing for large test suites

### Memory Management
- AST trees discarded after feature extraction
- Large analysis results streamed to disk
- Coverage data processed in batches to avoid memory spikes
