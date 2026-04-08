#!/usr/bin/env python3
"""Generate Sphinx pages and SVG tree diagrams for emulation XML contexts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

ALLOWED_TAGS = {
    "context",
    "context-attribute",
    "device",
    "channel",
    "attribute",
    "debug-attribute",
    "buffer-attribute",
    "scan-element",
}

CHILD_TAG_ORDER = {
    "context-attribute": 0,
    "device": 1,
    "channel": 2,
    "scan-element": 3,
    "attribute": 4,
    "debug-attribute": 5,
    "buffer-attribute": 6,
}

DISPLAY_ATTRS: Dict[str, Sequence[str]] = {
    "context": ("name", "description"),
    "context-attribute": ("name", "value"),
    "device": ("id", "name"),
    "channel": ("id", "type", "name"),
    "attribute": ("name", "filename", "value"),
    "debug-attribute": ("name", "value"),
    "buffer-attribute": ("name", "value"),
    "scan-element": ("index", "format", "scale"),
}

SVG_STYLE = """<style>
.bg { fill: #f7fafc; }
.edge { stroke: #7a8aa1; stroke-width: 1.4; fill: none; }
.node { stroke-width: 1.1; rx: 10; ry: 10; }
.node-context { fill: #d7e9ff; stroke: #457b9d; }
.node-device { fill: #d9f3e4; stroke: #2d6a4f; }
.node-channel { fill: #fff1cf; stroke: #b08900; }
.node-summary { fill: #efe8ff; stroke: #6c4dbf; }
.node-error { fill: #ffd7d7; stroke: #b3261e; }
.title { font: 700 13px "DejaVu Sans", "Arial", sans-serif; fill: #1f2a37; }
.subtitle { font: 12px "DejaVu Sans Mono", "Consolas", monospace; fill: #3d4b60; }
.legend-title { font: 700 12px "DejaVu Sans", "Arial", sans-serif; fill: #1f2a37; }
.legend-text { font: 11px "DejaVu Sans", "Arial", sans-serif; fill: #3d4b60; }
</style>"""

TAG_DISPLAY_NAMES = {
    "attribute": "Attributes",
    "debug-attribute": "Debug Attributes",
    "buffer-attribute": "Buffer Attributes",
    "scan-element": "Scan Elements",
    "context-attribute": "Context Attributes",
}


class DiagramNode:
    """Simple tree model used for deterministic diagram layout."""

    def __init__(
        self,
        node_type: str,
        title: str,
        subtitle: str = "",
        children: Optional[List["DiagramNode"]] = None,
    ) -> None:
        self.node_type = node_type
        self.title = title
        self.subtitle = subtitle
        self.children = children or []
        self.x = 0.0
        self.y = 0.0
        self.depth = 0


def _rreplace(text: str, old: str, new: str, count: int) -> str:
    return new.join(text.rsplit(old, count))


def _slug_from_xml_name(xml_name: str) -> str:
    stem = Path(xml_name).stem.lower()
    allowed = []
    for char in stem:
        if char.isalnum() or char in {"-", "_"}:
            allowed.append(char)
        else:
            allowed.append("-")
    return "".join(allowed).strip("-")


def _node_sort_key(elem: ET.Element) -> Tuple[str, ...]:
    attrs = elem.attrib
    return (
        attrs.get("id", ""),
        attrs.get("name", ""),
        attrs.get("filename", ""),
        attrs.get("index", ""),
        attrs.get("type", ""),
        attrs.get("value", ""),
        attrs.get("format", ""),
    )


def _sorted_children(elem: ET.Element) -> List[ET.Element]:
    children = [child for child in elem if child.tag in ALLOWED_TAGS]
    children.sort(
        key=lambda child: (
            CHILD_TAG_ORDER.get(child.tag, 99),
            _node_sort_key(child),
        )
    )
    return children


def _format_node(elem: ET.Element) -> str:
    attrs = DISPLAY_ATTRS.get(elem.tag, ())
    parts = []
    for attr in attrs:
        value = elem.attrib.get(attr)
        if value:
            parts.append(f"{attr}={value}")
    suffix = " " + " ".join(parts) if parts else ""
    return f"{elem.tag}{suffix}"


def _truncate(text: str, max_len: int = 64) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _summary_node(tag: str, count: int) -> DiagramNode:
    name = TAG_DISPLAY_NAMES.get(tag, tag)
    label = f"{count} {'entry' if count == 1 else 'entries'}"
    return DiagramNode("summary", name, label)


def _build_channel_node(channel: ET.Element) -> DiagramNode:
    parts = [channel.attrib.get("id", "(no id)"), channel.attrib.get("type", "unknown")]
    if channel.attrib.get("name"):
        parts.append(channel.attrib["name"])
    subtitle = " | ".join(parts)

    bucket_counts: Dict[str, int] = {tag: 0 for tag in TAG_DISPLAY_NAMES}
    for child in _sorted_children(channel):
        if child.tag in bucket_counts:
            bucket_counts[child.tag] += 1

    children = [
        _summary_node(tag, count)
        for tag, count in bucket_counts.items()
        if count > 0 and tag != "context-attribute"
    ]
    return DiagramNode("channel", "Channel", _truncate(subtitle), children)


def _build_device_node(device: ET.Element) -> DiagramNode:
    device_id = device.attrib.get("id", "(no id)")
    device_name = device.attrib.get("name", "")
    subtitle = f"{device_id} | {device_name}" if device_name else device_id

    channels = [child for child in _sorted_children(device) if child.tag == "channel"]
    channel_nodes = [_build_channel_node(channel) for channel in channels]

    bucket_counts: Dict[str, int] = {tag: 0 for tag in TAG_DISPLAY_NAMES}
    for child in _sorted_children(device):
        if child.tag in bucket_counts:
            bucket_counts[child.tag] += 1
    summary_nodes = [
        _summary_node(tag, count)
        for tag, count in bucket_counts.items()
        if count > 0 and tag != "channel" and tag != "context-attribute"
    ]

    return DiagramNode("device", "Device", _truncate(subtitle), channel_nodes + summary_nodes)


def _build_compact_tree(root: ET.Element) -> DiagramNode:
    root_name = root.attrib.get("name", "(no name)")
    root_desc = root.attrib.get("description", "")
    subtitle = f"{root_name} | {root_desc}" if root_desc else root_name

    context_attrs = [child for child in _sorted_children(root) if child.tag == "context-attribute"]
    devices = [child for child in _sorted_children(root) if child.tag == "device"]

    children: List[DiagramNode] = []
    if context_attrs:
        children.append(_summary_node("context-attribute", len(context_attrs)))
    children.extend(_build_device_node(device) for device in devices)
    return DiagramNode("context", "Context", _truncate(subtitle), children)


def _collect_nodes(root: DiagramNode) -> List[DiagramNode]:
    nodes: List[DiagramNode] = []

    def walk(node: DiagramNode, depth: int) -> None:
        node.depth = depth
        nodes.append(node)
        for child in node.children:
            walk(child, depth + 1)

    walk(root, 0)
    return nodes


def _layout_tree(root: DiagramNode) -> Tuple[List[DiagramNode], List[Tuple[DiagramNode, DiagramNode]]]:
    nodes = _collect_nodes(root)
    edges: List[Tuple[DiagramNode, DiagramNode]] = []

    x_spacing = 280.0
    y_spacing = 90.0
    y_cursor = 0.0

    def place(node: DiagramNode, depth: int) -> None:
        nonlocal y_cursor
        node.x = depth * x_spacing
        if not node.children:
            node.y = y_cursor
            y_cursor += y_spacing
            return

        for child in node.children:
            edges.append((node, child))
            place(child, depth + 1)
        node.y = (node.children[0].y + node.children[-1].y) / 2.0

    place(root, 0)
    return nodes, edges


def _node_class(node: DiagramNode) -> str:
    if node.node_type == "context":
        return "node-context"
    if node.node_type == "device":
        return "node-device"
    if node.node_type == "channel":
        return "node-channel"
    if node.node_type == "error":
        return "node-error"
    return "node-summary"


def render_svg_tree(root: ET.Element) -> str:
    diagram = _build_compact_tree(root)
    nodes, edges = _layout_tree(diagram)

    node_width = 235.0
    node_height = 56.0
    margin = 30.0

    max_depth = max(node.depth for node in nodes) if nodes else 0
    max_y = max(node.y for node in nodes) if nodes else 0.0
    width = int((max_depth + 1) * 280 + node_width + margin * 2)
    height = int(max(180.0, max_y + node_height + margin * 2))

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Emulation XML tree diagram">',
        SVG_STYLE,
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}"/>',
    ]

    for parent, child in edges:
        x1 = margin + parent.x + node_width
        y1 = margin + parent.y + node_height / 2.0
        x2 = margin + child.x
        y2 = margin + child.y + node_height / 2.0
        mid = x1 + (x2 - x1) * 0.5
        path = f"M {x1:.1f} {y1:.1f} C {mid:.1f} {y1:.1f}, {mid:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}"
        parts.append(f'<path class="edge" d="{path}"/>')

    for node in nodes:
        x = margin + node.x
        y = margin + node.y
        parts.append(
            f'<rect class="node {_node_class(node)}" x="{x:.1f}" y="{y:.1f}" '
            f'width="{node_width:.1f}" height="{node_height:.1f}"/>'
        )
        parts.append(
            f'<text class="title" x="{x + 12:.1f}" y="{y + 22:.1f}">{xml_escape(_truncate(node.title, 30))}</text>'
        )
        if node.subtitle:
            parts.append(
                f'<text class="subtitle" x="{x + 12:.1f}" y="{y + 41:.1f}">'
                f"{xml_escape(_truncate(node.subtitle, 42))}</text>"
            )

    legend_x = width - 255
    legend_y = 16
    parts.append(
        f'<rect x="{legend_x}" y="{legend_y}" width="230" height="92" '
        'fill="#ffffff" stroke="#c6cfdb" rx="8" ry="8"/>'
    )
    parts.append(f'<text class="legend-title" x="{legend_x + 12}" y="{legend_y + 20}">Node Types</text>')
    legend_items = [
        ("node-context", "Context"),
        ("node-device", "Device"),
        ("node-channel", "Channel"),
        ("node-summary", "Grouped Attributes"),
    ]
    for idx, (klass, label) in enumerate(legend_items):
        ly = legend_y + 34 + idx * 14
        parts.append(
            f'<rect class="node {klass}" x="{legend_x + 12}" y="{ly - 9}" width="14" height="10" rx="2" ry="2"/>'
        )
        parts.append(f'<text class="legend-text" x="{legend_x + 32}" y="{ly}">{label}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def render_svg_error(message: str) -> str:
    error = DiagramNode("error", "Parse Error", _truncate(message, 80))
    nodes, _ = _layout_tree(error)
    node = nodes[0]
    width = 560
    height = 160
    x = 30 + node.x
    y = 40 + node.y
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="XML parse error">\n'
        f"{SVG_STYLE}\n"
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}"/>\n'
        f'<rect class="node node-error" x="{x:.1f}" y="{y:.1f}" width="500" height="56"/>\n'
        f'<text class="title" x="{x + 12:.1f}" y="{y + 22:.1f}">Parse Error</text>\n'
        f'<text class="subtitle" x="{x + 12:.1f}" y="{y + 41:.1f}">{xml_escape(_truncate(message, 64))}</text>\n'
        "</svg>\n"
    )


def render_ascii_tree(root: ET.Element) -> str:
    lines = [_format_node(root)]

    def walk(node: ET.Element, prefix: str) -> None:
        children = _sorted_children(node)
        for index, child in enumerate(children):
            is_last = index == len(children) - 1
            branch = "`-- " if is_last else "|-- "
            lines.append(f"{prefix}{branch}{_format_node(child)}")
            next_prefix = f"{prefix}{'    ' if is_last else '|   '}"
            walk(child, next_prefix)

    walk(root, "")
    return "\n".join(lines)


def _parse_context_root(xml_path: Path) -> ET.Element:
    try:
        return ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raw = xml_path.read_bytes()
        text_candidates = []
        for encoding in ("utf-8", "utf-16", "utf-16le", "utf-16be", "latin-1"):
            try:
                text = raw.decode(encoding)
            except UnicodeDecodeError:
                continue
            if text not in text_candidates:
                text_candidates.append(text)

        for text in text_candidates:
            normalized = re.sub(r"^\s*<\?xml[^>]*\?>", "", text, count=1).strip()
            try:
                return ET.fromstring(normalized)
            except ET.ParseError as inner_exc:
                if "mismatched tag" in str(inner_exc):
                    open_channels = normalized.count("<channel ")
                    close_channels = normalized.count("</channel>")
                    if open_channels > close_channels and "</device>" in normalized:
                        repaired = _rreplace(
                            normalized,
                            "</device>",
                            "</channel>" * (open_channels - close_channels)
                            + "</device>",
                            1,
                        )
                        try:
                            return ET.fromstring(repaired)
                        except ET.ParseError:
                            pass

        raise ValueError(
            f"Unable to parse XML context {xml_path.name}: {exc}"
        ) from exc


def tree_from_xml_path(xml_path: Path) -> str:
    root = _parse_context_root(xml_path)
    if root.tag != "context":
        raise ValueError(f"Expected root tag 'context' in {xml_path}, got {root.tag!r}")
    return render_ascii_tree(root)


def _page_content(xml_rel_path: Path, xml_name: str, svg_filename: str, tree_text: str) -> str:
    title = f"Emulation Context: {xml_name}"
    underline = "=" * len(title)
    preview_lines = tree_text.splitlines()[:20]
    preview = "\n".join(f"   {line}" for line in preview_lines)

    return (
        ".. This file is auto-generated by doc/gen_emu_xml_trees.py.\n"
        "   Do not edit manually.\n\n"
        f"{title}\n"
        f"{underline}\n\n"
        f"Source XML: ``{xml_rel_path.as_posix()}``\n\n"
        "Diagram\n"
        "-------\n\n"
        ".. Note:: The diagram intentionally groups large attribute lists to keep\n"
        "   the structure readable.\n\n"
        f".. image:: {svg_filename}\n"
        "   :alt: Emulation context tree diagram\n"
        "   :width: 100%\n\n"
        "Text Preview\n"
        "------------\n\n"
        ".. code-block:: text\n\n"
        f"{preview}\n"
    )


def _index_content(entries: Iterable[Tuple[str, str]]) -> str:
    title = "Emulation XML Context Trees"
    underline = "=" * len(title)
    toctree_entries = "\n".join(f"   {slug}" for slug, _ in entries)
    return (
        ".. This file is auto-generated by doc/gen_emu_xml_trees.py.\n"
        "   Do not edit manually.\n\n"
        f"{title}\n"
        f"{underline}\n\n"
        "These pages are generated from ``test/emu/devices/*.xml`` and show a\n"
        "deterministically sorted compact tree diagram of each emulation context.\n\n"
        ".. toctree::\n"
        "   :maxdepth: 1\n\n"
        f"{toctree_entries}\n"
    )


def _write_if_changed(path: Path, content: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def generate_emu_xml_tree_docs(
    repo_root: Optional[Path] = None,
    xml_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> List[Path]:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    source_xml_dir = xml_dir or (repo_root / "test" / "emu" / "devices")
    target_dir = output_dir or (repo_root / "doc" / "source" / "emu_contexts")

    xml_files = sorted(source_xml_dir.glob("*.xml"), key=lambda path: path.name.lower())
    target_dir.mkdir(parents=True, exist_ok=True)

    entries: List[Tuple[str, str]] = []
    written_files: List[Path] = []
    valid_page_filenames = {"index.rst"}

    for xml_file in xml_files:
        slug = _slug_from_xml_name(xml_file.name)
        page_path = target_dir / f"{slug}.rst"
        svg_path = target_dir / f"{slug}.svg"
        xml_rel = xml_file.relative_to(repo_root)
        try:
            root = _parse_context_root(xml_file)
            if root.tag != "context":
                raise ValueError(f"Expected root tag 'context' in {xml_file}, got {root.tag!r}")
            tree_text = render_ascii_tree(root)
            svg_text = render_svg_tree(root)
        except Exception as exc:
            message = (
                "parse-error "
                f"file={xml_file.name} "
                f"message={str(exc).replace(chr(10), ' ')}"
            )
            tree_text = message
            svg_text = render_svg_error(message)
        page = _page_content(xml_rel, xml_file.name, svg_path.name, tree_text)
        _write_if_changed(page_path, page)
        _write_if_changed(svg_path, svg_text)

        entries.append((slug, xml_file.name))
        written_files.append(page_path)
        valid_page_filenames.add(page_path.name)
        valid_page_filenames.add(svg_path.name)

    index_path = target_dir / "index.rst"
    _write_if_changed(index_path, _index_content(entries))
    written_files.append(index_path)

    for stale_path in target_dir.iterdir():
        if stale_path.suffix not in {".rst", ".svg"}:
            continue
        if stale_path.name not in valid_page_filenames:
            stale_path.unlink()

    return sorted(written_files)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate emulation context tree docs from test/emu/devices XML files."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root path",
    )
    args = parser.parse_args()

    generate_emu_xml_tree_docs(repo_root=args.repo_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
