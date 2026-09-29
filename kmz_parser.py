"""Safe, dependency-free parsing of DJI WPML KMZ archives."""

from __future__ import annotations

from pathlib import PurePosixPath
import math
import posixpath
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from document_model import DocumentFile, KmzDocument, build_tree, flatten_fields
from field_catalog import annotate_fields
from route_model import RouteModel, Waypoint

try:  # PyInstaller bundles this dependency; the fallback keeps source tests usable.
    from defusedxml import ElementTree as SafeET
except ImportError:  # pragma: no cover - exercised only in a bare source checkout
    SafeET = ET


KML_NAMESPACE = "http://www.opengis.net/kml/2.2"
WPML_NAMESPACE = "http://www.dji.com/wpmz/1.0.2"
MAX_ENTRY_SIZE = 20 * 1024 * 1024
MAX_TOTAL_SIZE = 500 * 1024 * 1024
MAX_FILE_COUNT = 2_000
MAX_COMPRESSION_RATIO = 200
MAX_XML_SIZE = 20 * 1024 * 1024
MAX_XML_NODES = 50_000
MAX_XML_DEPTH = 100


class KmzParseError(ValueError):
    """An input archive cannot be safely or usefully parsed."""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    text = element.text.strip()
    return text or None


def _first_text(root: ET.Element, names: Iterable[str]) -> str | None:
    wanted = set(names)
    for element in root.iter():
        if _local_name(element.tag) in wanted:
            value = _text(element)
            if value is not None:
                return value
    return None


def _number(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _integer(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_coordinates(text: str | None) -> list[tuple[float, float]]:
    if not text:
        return []
    result: list[tuple[float, float]] = []
    for item in text.replace("\n", " ").split():
        parts = item.split(",")
        if len(parts) < 2:
            continue
        longitude = _number(parts[0])
        latitude = _number(parts[1])
        if longitude is None or latitude is None or not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            continue
        result.append((longitude, latitude))
    return result


def _coordinates(element: ET.Element) -> list[tuple[float, float]]:
    for child in element.iter():
        if _local_name(child.tag) == "coordinates":
            return _parse_coordinates(_text(child))
    return []


def _actions(placemark: ET.Element) -> list[str]:
    values: list[str] = []
    names = {"actionActuatorFunc", "actionType", "actionName"}
    for child in placemark.iter():
        if _local_name(child.tag) in names:
            value = _text(child)
            if value and value not in values:
                values.append(value)
    return values


def _parse_placemarks(root: ET.Element, source: str) -> tuple[list[Waypoint], list[list[tuple[float, float]]], list[list[tuple[float, float]]], list[str]]:
    waypoints: list[Waypoint] = []
    lines: list[list[tuple[float, float]]] = []
    polygons: list[list[tuple[float, float]]] = []
    warnings: list[str] = []
    for placemark in (element for element in root.iter() if _local_name(element.tag) == "Placemark"):
        point_element = next((element for element in placemark.iter() if _local_name(element.tag) == "Point"), None)
        if point_element is not None:
            coordinates = _coordinates(point_element)
            if not coordinates:
                warnings.append(f"{source} 中有航点缺少有效坐标")
            else:
                lon, lat = coordinates[0]
                if source == "waylines.wpml":
                    height = _number(_first_text(placemark, {"executeHeight"}))
                    height_mode = _first_text(placemark, {"executeHeightMode"})
                else:
                    height = _number(_first_text(placemark, {"height"}))
                    height_mode = _first_text(placemark, {"heightMode"})
                ellipsoid_height = _number(_first_text(placemark, {"ellipsoidHeight"}))
                speed = _number(_first_text(placemark, {"waypointSpeed", "speed"}))
                waypoints.append(
                    Waypoint(
                        index=_integer(_first_text(placemark, {"index"})) or len(waypoints),
                        longitude=lon,
                        latitude=lat,
                        height=height,
                        ellipsoid_height=ellipsoid_height,
                        height_mode=height_mode,
                        speed=speed,
                        heading=_first_text(placemark, {"waypointHeadingParam", "waypointHeadingMode"}),
                        turn_mode=_first_text(placemark, {"waypointTurnParam", "waypointTurnMode"}),
                        actions=_actions(placemark),
                        source=source,
                    )
                )
        for line in (element for element in placemark.iter() if _local_name(element.tag) == "LineString"):
            coordinates = _coordinates(line)
            if len(coordinates) >= 2:
                lines.append(coordinates)
        for polygon in (element for element in placemark.iter() if _local_name(element.tag) == "Polygon"):
            coordinates = _coordinates(polygon)
            if len(coordinates) >= 3:
                polygons.append(coordinates)
    return waypoints, lines, polygons, warnings


def _parse_xml(data: bytes, source: str) -> dict:
    if len(data) > MAX_XML_SIZE:
        raise KmzParseError(f"{source} XML 内容过大")
    lowered = data.upper()
    if b"<!DOCTYPE" in lowered or b"<!ENTITY" in lowered or b"<!NOTATION" in lowered:
        raise KmzParseError(f"{source} 包含不支持的 XML 实体声明")
    try:
        root = SafeET.fromstring(data)
    except (ET.ParseError, ValueError) as exc:
        raise KmzParseError(f"{source} XML 格式错误: {exc}") from exc
    nodes = 0
    stack: list[tuple[ET.Element, int]] = [(root, 1)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAX_XML_NODES:
            raise KmzParseError(f"{source} XML 节点数量超过安全限制")
        if depth > MAX_XML_DEPTH:
            raise KmzParseError(f"{source} XML 嵌套层级超过安全限制")
        stack.extend((child, depth + 1) for child in list(current))
    wpml_namespace = next((element.tag[1:].split("}", 1)[0] for element in root.iter() if element.tag.startswith("{http://www.dji.com/wpmz/")), "")
    waypoints, lines, polygons, warnings = _parse_placemarks(root, source)
    return {
        "root": root,
        "raw_text": data.decode("utf-8-sig", errors="replace"),
        "namespace": wpml_namespace or (root.tag[1:].split("}", 1)[0] if root.tag.startswith("{") else ""),
        "template_type": _first_text(root, {"templateType"}),
        "template_id": _integer(_first_text(root, {"templateId"})),
        "wayline_id": _integer(_first_text(root, {"waylineId"})),
        "height_mode": _first_text(root, {"heightMode"}),
        "execute_height_mode": _first_text(root, {"executeHeightMode"}),
        "global_speed": _number(_first_text(root, {"globalTransitionalSpeed", "globalSpeed"})),
        "waypoints": waypoints,
        "lines": lines,
        "polygons": polygons,
        "warnings": warnings,
    }


def _safe_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    if normalized.startswith("/"):
        raise KmzParseError(f"压缩包包含绝对路径: {name}")
    normalized = posixpath.normpath(normalized)
    path = PurePosixPath(normalized)
    if ".." in path.parts:
        raise KmzParseError(f"压缩包包含路径穿越: {name}")
    return normalized


def _select_entry(entries: list[tuple[str, zipfile.ZipInfo]], target: str) -> zipfile.ZipInfo | None:
    target = target.lower()
    ranked: list[tuple[int, int, zipfile.ZipInfo]] = []
    for normalized, info in entries:
        lower = normalized.lower()
        if lower == f"wpmz/{target}":
            ranked.append((0, len(normalized), info))
        elif lower == target:
            ranked.append((1, len(normalized), info))
        elif posixpath.basename(lower) == target:
            ranked.append((2, len(normalized), info))
    return min(ranked, key=lambda item: (item[0], item[1]))[2] if ranked else None


def parse_kmz_document(path: str | Path) -> KmzDocument:
    input_path = Path(path)
    if not input_path.is_file():
        raise KmzParseError(f"文件不存在: {input_path}")
    if input_path.suffix.lower() != ".kmz":
        raise KmzParseError("输入文件必须是 .kmz")
    try:
        archive = zipfile.ZipFile(input_path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise KmzParseError(f"无法打开 KMZ 压缩包: {exc}") from exc
    with archive as kmz:
        infos = kmz.infolist()
        if len(infos) > MAX_FILE_COUNT:
            raise KmzParseError("KMZ 文件数量超过安全限制")
        total_size = 0
        entries: list[tuple[str, zipfile.ZipInfo]] = []
        seen: set[str] = set()
        for info in infos:
            normalized = _safe_name(info.filename)
            key = normalized.lower()
            if key in seen:
                raise KmzParseError(f"压缩包包含重复路径: {info.filename}")
            seen.add(key)
            if info.file_size > MAX_ENTRY_SIZE:
                raise KmzParseError(f"压缩包条目过大: {info.filename}")
            if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
                raise KmzParseError(f"压缩包条目压缩比异常: {info.filename}")
            total_size += info.file_size
            if total_size > MAX_TOTAL_SIZE:
                raise KmzParseError("KMZ 解压总大小超过安全限制")
            entries.append((normalized, info))
        selected: dict[str, zipfile.ZipInfo] = {}
        for target in ("waylines.wpml", "template.kml"):
            info = _select_entry(entries, target)
            if info is not None:
                selected[target] = info
        if not selected:
            raise KmzParseError("未找到 template.kml 或 waylines.wpml")

        parsed: dict[str, dict] = {}
        for name, info in selected.items():
            try:
                data = kmz.read(info)
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                raise KmzParseError(f"读取 {name} 失败: {exc}") from exc
            parsed[name] = _parse_xml(data, name)

    wayline = parsed.get("waylines.wpml", {})
    template = parsed.get("template.kml", {})
    template_id = wayline.get("template_id") if wayline.get("template_id") is not None else template.get("template_id")
    global_speed = wayline.get("global_speed") if wayline.get("global_speed") is not None else template.get("global_speed")
    model = RouteModel(
        source_file=input_path.name,
        source_files=list(parsed),
        template_type=wayline.get("template_type") or template.get("template_type"),
        template_id=template_id,
        wayline_id=wayline.get("wayline_id"),
        height_mode=template.get("height_mode"),
        execute_height_mode=wayline.get("execute_height_mode"),
        global_speed=global_speed,
        waypoints=wayline.get("waypoints", []),
        template_waypoints=template.get("waypoints", []),
        lines=template.get("lines", []) + wayline.get("lines", []),
        polygons=template.get("polygons", []) + wayline.get("polygons", []),
        warnings=wayline.get("warnings", []) + template.get("warnings", []),
    )
    if not model.waypoints and not model.template_waypoints and not model.lines and not model.polygons:
        model.warnings.append("未找到可显示的航点、线路或区域")
    if wayline.get("template_id") is not None and template.get("template_id") is not None and wayline["template_id"] != template["template_id"]:
        model.warnings.append("templateId 在 template.kml 与 waylines.wpml 中不一致")
    model.compute_statistics()
    documents: dict[str, DocumentFile] = {}
    for name, value in parsed.items():
        is_template = name == "template.kml"
        source_route = RouteModel(
            source_file=input_path.name,
            source_files=[name],
            template_type=value.get("template_type"),
            template_id=value.get("template_id"),
            wayline_id=value.get("wayline_id"),
            height_mode=value.get("height_mode"),
            execute_height_mode=value.get("execute_height_mode"),
            global_speed=value.get("global_speed"),
            waypoints=[] if is_template else value.get("waypoints", []),
            template_waypoints=value.get("waypoints", []) if is_template else [],
            lines=value.get("lines", []),
            polygons=value.get("polygons", []),
            warnings=value.get("warnings", []),
        )
        source_route.compute_statistics()
        tree = build_tree(value["root"], counts=[0])
        documents[name] = DocumentFile(
            name=name,
            namespace=value.get("namespace", ""),
            raw_text=value.get("raw_text", ""),
            root=tree,
            fields=annotate_fields(flatten_fields(tree), name),
            route=source_route,
        )
    return KmzDocument(source_file=input_path.name, files=documents, route=model)


def parse_kmz(path: str | Path) -> RouteModel:
    """Backward-compatible route-only API used by the original MVP."""
    return parse_kmz_document(path).route
