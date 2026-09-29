"""Document-level representation for the two WPML XML files.

The previewer keeps the original XML text for inspection while exposing a
small, JSON-safe tree for the field explanation view.  The tree is bounded by
the parser limits and never executes XML content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
from typing import Any


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def namespace(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


@dataclass
class XmlNode:
    name: str
    path: str
    namespace: str = ""
    text: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)
    children: list["XmlNode"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "namespace": self.namespace,
            "text": self.text,
            "attributes": self.attributes,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class DocumentFile:
    name: str
    namespace: str
    raw_text: str
    root: XmlNode
    fields: list[dict[str, Any]]
    route: Any | None = None

    @property
    def version(self) -> str:
        return self.namespace.rsplit("/", 1)[-1] if self.namespace else "未知"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "namespace": self.namespace,
            "version": self.version,
            "rawText": self.raw_text,
            "root": self.root.to_dict(),
            "fields": self.fields,
            "route": self.route.to_dict() if self.route is not None else None,
        }


@dataclass
class KmzDocument:
    source_file: str
    files: dict[str, DocumentFile]
    route: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceFile": self.source_file,
            "files": {name: value.to_dict() for name, value in self.files.items()},
            "route": self.route.to_dict(),
        }


def build_tree(element: ET.Element, *, path: str = "", counts: list[int] | None = None) -> XmlNode:
    """Convert a safe ElementTree into a bounded JSON tree."""
    if counts is not None:
        counts[0] += 1
    name = local_name(element.tag)
    current = f"{path}/{name}" if path else f"/{name}"
    attrs = {local_name(key): value for key, value in element.attrib.items()}
    text = (element.text or "").strip() or None
    children = [build_tree(child, path=current, counts=counts) for child in list(element)]
    return XmlNode(name=name, path=current, namespace=namespace(element.tag), text=text, attributes=attrs, children=children)


def flatten_fields(node: XmlNode, *, max_fields: int = 20000) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def visit(current: XmlNode) -> None:
        if len(result) >= max_fields:
            return
        if current.text is not None or current.attributes:
            result.append({
                "path": current.path,
                "name": current.name,
                "namespace": current.namespace,
                "value": current.text,
                "attributes": current.attributes,
            })
        for child in current.children:
            visit(child)

    visit(node)
    return result
