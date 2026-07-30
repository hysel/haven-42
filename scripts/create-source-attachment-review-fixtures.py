#!/usr/bin/env python3
"""Create inert local files for the source-attachment UI review."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "dist" / "local-review" / "source-attachment-ui"

FILES = {
    "review-example.py": """\
def format_review_message(name: str) -> str:
    return f"Source attachment review: {name}"


INERT_MARKUP = "<script>fixture text only; never execute</script>"
""",
    "review-example.tsx": """\
type ReviewLabelProps = {
  label: string;
};

export function ReviewLabel({ label }: ReviewLabelProps) {
  return <span data-review="source-attachment">{label}</span>;
}

export const inertMarkup = "<img src=x onerror=alert('fixture text only')>";
""",
    "blocked-review.sh": """\
# Intentionally blocked Haven 42 review fixture.
# This file contains no command and must not be admitted as chat context.
""",
    "blocked-review.ps1": """\
# Intentionally blocked Haven 42 review fixture.
# This file contains no command and must not be admitted as chat context.
""",
    "renamed-powershell.txt": """\
Write-Host "This renamed PowerShell fixture must be rejected before attachment."
""",
    "REVIEW.md": """\
# Source Attachment UI Review

These sanitized files are local review artifacts. None contains credentials,
machine details, private endpoints, or executable test commands.

1. Start Haven 42 and reach the Chat page.
2. Select `review-example.py` and `review-example.tsx` with **Browse files**.
3. Confirm both entries are labeled **Source** and preview as literal text.
4. Confirm strings containing `<script>` or `<img>` remain visible text and do
   not create active page elements.
5. If the operating-system picker permits selecting all file types, try
   `blocked-review.sh` and `blocked-review.ps1`. Haven 42 must reject the entire
   selection. If the picker hides them, that filtering is expected; automated
   hostile tests independently exercise engine rejection.
6. Select `renamed-powershell.txt`. Haven 42 must report that the file contents
   do not match its name and must not add the file to the task.
7. Remove the files, use **Clear all**, and start a **New task** to confirm
   cleanup.

The files do not need to be sent to a model. Ollama is required only if the
connection wizard must be completed to reach Chat.
""",
}


def is_linklike(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", lambda: False)
    return path.is_symlink() or is_junction()


def create_fixtures(output: Path, force: bool = False) -> list[Path]:
    output = output.absolute()
    if output.exists() and is_linklike(output):
        raise ValueError("review output must not be a link or junction")
    output = output.resolve()
    if output.exists() and not output.is_dir():
        raise ValueError(f"review output exists and is not a directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    targets = [output / name for name in FILES]
    existing = [target for target in targets if target.exists()]
    if existing and not force:
        names = ", ".join(target.name for target in existing)
        raise FileExistsError(
            f"review fixtures already exist ({names}); rerun with --force"
        )

    for target, content in zip(targets, FILES.values(), strict=True):
        if target.parent.resolve() != output:
            raise ValueError("review fixture escaped the selected output directory")
        if target.exists() and (is_linklike(target) or not target.is_file()):
            raise ValueError(f"review fixture target is not a regular file: {target.name}")
        target.write_text(content, encoding="utf-8", newline="\n")
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="review directory (default: dist/local-review/source-attachment-ui)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace only the known generated fixture files",
    )
    args = parser.parse_args()

    created = create_fixtures(args.output, force=args.force)
    print(f"Created {len(created)} source-attachment review files in {args.output.resolve()}")
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
