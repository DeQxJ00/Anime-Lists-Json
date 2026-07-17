#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any


RAW_XML_URL = "https://raw.githubusercontent.com/Anime-Lists/anime-lists/master/anime-list-master.xml"


def compact_text(text: str | None) -> str | None:
    if text is None:
        return None
    value = text.strip()
    return value if value else None


def merge_child(target: dict[str, Any], key: str, value: Any) -> None:
    if key not in target:
        target[key] = value
        return
    if not isinstance(target[key], list):
        target[key] = [target[key]]
    target[key].append(value)


def element_to_json(element: ET.Element) -> Any:
    attrs = dict(element.attrib)
    children = list(element)
    text = compact_text(element.text)

    if not attrs and not children:
        return text or ""

    result: dict[str, Any] = {}
    result.update(attrs)

    for child in children:
        merge_child(result, child.tag, element_to_json(child))

    if text is not None:
        result["text"] = text

    return result


def build_api(xml_path: Path, output_dir: Path) -> dict[str, Any]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    api_root = output_dir / "api"
    anidb_dir = api_root / "anidb"
    imdb_dir = api_root / "imdb"
    for api_dir in (anidb_dir, imdb_dir):
        if api_dir.exists():
            shutil.rmtree(api_dir)
        api_dir.mkdir(parents=True, exist_ok=True)

    ids_seen: set[str] = set()
    index: dict[str, Any] = {
        "source": RAW_XML_URL,
        "count": 0,
        "ids": [],
    }
    imdb_items: dict[str, list[dict[str, Any]]] = defaultdict(list)
    duplicate_ids: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for anime in root.findall("anime"):
        item = element_to_json(anime)
        anidbid = item.get("anidbid")
        if not anidbid:
            continue

        if anidbid in ids_seen:
            duplicate_ids[anidbid].append(item)
            continue

        ids_seen.add(anidbid)
        index["ids"].append(anidbid)

        imdbid = item.get("imdbid")
        if imdbid:
            imdb_items[imdbid].append(item)

        output_file = anidb_dir / f"{anidbid}.json"
        output_file.write_text(
            json.dumps(item, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    index["ids"].sort(key=lambda value: int(value) if value.isdigit() else value)
    index["count"] = len(index["ids"])

    (anidb_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    imdb_index: dict[str, Any] = {
        "source": RAW_XML_URL,
        "count": len(imdb_items),
        "ids": sorted(imdb_items),
    }
    for imdbid, items in imdb_items.items():
        value: Any = items[0] if len(items) == 1 else items
        (imdb_dir / f"{imdbid}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    (imdb_dir / "index.json").write_text(
        json.dumps(imdb_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if duplicate_ids:
        (output_dir / "duplicate-anidbids.json").write_text(
            json.dumps(duplicate_ids, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    index["imdb_count"] = len(imdb_items)
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static AniDB JSON files for GitHub Pages.")
    parser.add_argument("--xml", required=True, type=Path, help="Path to anime-list-master.xml")
    parser.add_argument("--out", default=Path("."), type=Path, help="Output site directory")
    args = parser.parse_args()

    index = build_api(args.xml, args.out)
    print(f"Wrote {index['count']} AniDB JSON files to {args.out / 'api' / 'anidb'}")
    print(f"Wrote {index['imdb_count']} IMDb JSON files to {args.out / 'api' / 'imdb'}")


if __name__ == "__main__":
    main()
