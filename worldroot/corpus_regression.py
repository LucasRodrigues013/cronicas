"""Read-only historical corpus comparison; accepts exact episode source files."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .reader_experience import preview_reader_review


def compare(reference: str, chapter4: list[str], chapter5: list[str]) -> dict:
    if len(chapter4) != 5 or len(chapter5) != 5:
        raise ValueError("Five parts per chapter required")
    samples = [reference, *chapter4, *chapter5]
    if any(not isinstance(x, str) or not x.strip() for x in samples):
        raise ValueError("Literal corpus passage required")
    history, reports = [], []
    for text in samples:
        data = preview_reader_review(text, previous_counts=history[-2:])
        history.append(data["total_scenes"])
        reports.append(data)
    return {"reference": reports[0], "c04": reports[1:6], "c05": reports[6:],
            "source": "STORY_ARCHIVE_LITERAL_READ_ONLY",
            "canon_changed": False, "literary_certification": False}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs=11)
    args = parser.parse_args(argv)
    content = [Path(x).read_text(encoding="utf-8") for x in args.files]
    result = compare(content[0], content[1:6], content[6:11])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
