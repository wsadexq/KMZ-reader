"""Build a compact WPML field index from DJI Cloud API documentation.

Only short field labels, types, units and source locations are retained. The
full official descriptions stay in the upstream documentation. Supply either
the checked-out Markdown repository or three pasted current-page text files.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re


DOCUMENTS = {
    "template.kml": "20.template-kml.md",
    "waylines.wpml": "30.waylines-wpml.md",
    "common": "40.common-element.md",
}
FIELD_RE = re.compile(r"^\|\s*wpml:([A-Za-z][A-Za-z0-9]*)")
HTML_TAG_RE = re.compile(r"<[^>]+>")


def clean_cell(value: str) -> str:
    value = re.split(r"<br\s*/?>", value, maxsplit=1, flags=re.I)[0]
    value = HTML_TAG_RE.sub("", value)
    value = re.sub(r"\*\s*注.*$", "", value)
    return html.unescape(value).strip().strip("`")


def extract_rows(path: Path) -> dict[str, dict[str, object]]:
    fields: dict[str, dict[str, object]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = FIELD_RE.match(line)
        if not match:
            continue
        cells = line.split("|")
        if len(cells) < 5:
            continue
        name = match.group(1)
        label = clean_cell(cells[2])
        field_type = clean_cell(cells[3])
        unit = clean_cell(cells[4])
        if not label:
            continue
        entry = fields.setdefault(name, {"label": label, "type": field_type, "unit": unit if unit != "-" else "", "source": path.name, "lines": [], "ambiguous": False})
        entry["lines"].append(line_number)
        if entry["label"] != label:
            entry["ambiguous"] = True
        if entry["unit"] != (unit if unit != "-" else ""):
            entry["unit"] = ""
    return fields


def extract_pasted_rows(path: Path, source: str) -> dict[str, dict[str, object]]:
    fields: dict[str, dict[str, object]] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^wpml:([A-Za-z][A-Za-z0-9]*)\b", line)
        if not match:
            continue
        # Copied tables can wrap a field label and its note onto several lines.
        parts = line.split("\t")
        next_index = index + 1
        while len(parts) < 4 and next_index < len(lines) and not lines[next_index].startswith("wpml:"):
            parts = ("\n".join(lines[index : next_index + 1])).split("\t")
            next_index += 1
        if len(parts) < 4:
            raise ValueError(f"Incomplete field row in {path}:{index + 1}: {match.group(1)}")
        name = match.group(1)
        label = parts[1].splitlines()[0].strip()
        field_type = parts[2].strip()
        unit = parts[3].strip()
        entry = fields.setdefault(name, {"label": label, "type": field_type, "unit": unit if unit != "-" else "", "source": source, "lines": [], "ambiguous": False})
        entry["lines"].append(index + 1)
        if entry["label"] != label:
            entry["ambiguous"] = True
        if entry["unit"] != (unit if unit != "-" else ""):
            entry["unit"] = ""
    return fields


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the embedded WPML field index")
    parser.add_argument("docs_root", type=Path, nargs="?", help="Checked-out Cloud-API-Doc root")
    parser.add_argument("--pasted-template", type=Path, help="Pasted current template.kml page text")
    parser.add_argument("--pasted-waylines", type=Path, help="Pasted current waylines.wpml page text")
    parser.add_argument("--pasted-common", type=Path, help="Pasted current common-element page text")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "field_catalog_data.json")
    args = parser.parse_args()
    pasted = {"template.kml": args.pasted_template, "waylines.wpml": args.pasted_waylines, "common": args.pasted_common}
    if any(pasted.values()):
        if not all(pasted.values()):
            parser.error("Supply all three pasted page text files together")
        missing = [str(path) for path in pasted.values() if not path.is_file()]
        if missing:
            parser.error(f"Missing pasted documents: {', '.join(missing)}")
        data = {scope: extract_pasted_rows(path, {"template.kml": "template.kml 说明 (2026-03-19)", "waylines.wpml": "waylines.wpml 说明 (2026-03-19)", "common": "共用元素信息 (2026-03-19)"}[scope]) for scope, path in pasted.items()}
    else:
        if args.docs_root is None:
            parser.error("Supply a docs root or all three pasted page text files")
        chapter = args.docs_root / "docs" / "cn" / "60.api-reference" / "00.dji-wpml"
        missing = [name for name in DOCUMENTS.values() if not (chapter / name).is_file()]
        if missing:
            parser.error(f"Missing WPML documents: {', '.join(missing)}")
        data = {scope: extract_rows(chapter / name) for scope, name in DOCUMENTS.items()}
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}: {sum(len(group) for group in data.values())} scoped fields")


if __name__ == "__main__":
    main()
