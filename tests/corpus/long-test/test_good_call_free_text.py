"""Near-misses modelled on networkx's GML and centrality tests: one act whose length is
call-free data, a multi-line input string, an f-string with only names in it and an
expected list. Each such literal counts as one line. Analysed, never run."""

import pytest
from graphs import parse_gml, render_label

pytestmark = pytest.mark.unit


def test_parse_reads_every_node_and_edge():
    source = """graph [
      directed 1
      node [
        id 0
        label "a"
      ]
      node [
        id 1
        label "b"
      ]
      node [
        id 2
        label "c"
      ]
      node [
        id 3
        label "d"
      ]
      node [
        id 4
        label "e"
      ]
      edge [
        source 0
        target 1
      ]
      edge [
        source 1
        target 2
      ]
      edge [
        source 2
        target 3
      ]
      edge [
        source 3
        target 4
      ]
      edge [
        source 4
        target 0
      ]
    ]"""

    graph = parse_gml(source)

    assert graph.edges == [
        ("a", "b"),
        ("b", "c"),
        ("c", "d"),
        ("d", "e"),
        ("e", "a"),
    ]


def test_render_label_lays_out_a_node(node):
    expected = f"""
    +------------------------------+
    | {node.name}
    |
    | kind: {node.kind}
    |
    | weight: {node.weight}
    |
    | in: {node.in_degree}
    |
    | out: {node.out_degree}
    |
    | colour: {node.colour}
    |
    | shape: {node.shape}
    |
    | group: {node.group}
    |
    | rank: {node.rank}
    |
    | label: {node.label}
    |
    | tooltip: {node.tooltip}
    |
    | url: {node.url}
    |
    | x: {node.x}
    |
    | y: {node.y}
    |
    | z: {node.z}
    |
    | border: {node.border}
    |
    | font: {node.font}
    |
    | size: {node.size}
    |
    | margin: {node.margin}
    |
    | padding: {node.padding}
    |
    | opacity: {node.opacity}
    |
    | layer: {node.layer}
    |
    | cluster: {node.cluster}
    +------------------------------+
    """

    assert render_label(node) == expected
