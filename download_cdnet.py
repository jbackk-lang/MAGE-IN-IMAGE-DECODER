"""Pobierz pojedynczą sekwencję CDnet 2014 z oficjalnego archiwum.

Domyślny magazyn surowych danych: katalog ../data/cdnet2014 obok repo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

BASE_URL = "https://changedetection.net/static/dataset/"
DEFAULT_DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "cdnet2014"
SEQUENCES = {
    "pedestrians": "baseline/pedestrians.zip",
    "highway": "baseline/highway.zip",
    "canoe": "dynamicBackground/canoe.zip",
    "fountain01": "dynamicBackground/fountain01.zip",
}
MAX_ARCHIVE_BYTES = 100_000_000
MAX_EXTRACTED_BYTES = 500_000_000


def download_sequence(name: str, root: str | Path | None = None) -> Path:
    if name not in SEQUENCES:
        raise ValueError(f"Dozwolone sekwencje: {', '.join(SEQUENCES)}")
    root = Path(root if root is not None else DEFAULT_DATA_ROOT).resolve()
    category = SEQUENCES[name].split("/", 1)[0]
    destination = root / category
    sequence_dir = destination / name
    if sequence_dir.exists():
        raise FileExistsError(f"Sekwencja już istnieje: {sequence_dir}")
    destination.mkdir(parents=True, exist_ok=True)
    url = BASE_URL + SEQUENCES[name]
    digest = hashlib.sha256()
    with tempfile.TemporaryFile() as archive:
        with urllib.request.urlopen(url, timeout=60) as response:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_ARCHIVE_BYTES:
                    raise ValueError("Archiwum przekracza limit 100 MB")
                archive.write(chunk)
                digest.update(chunk)
        archive.seek(0)
        with zipfile.ZipFile(archive) as zf:
            members = zf.infolist()
            if sum(info.file_size for info in members) > MAX_EXTRACTED_BYTES:
                raise ValueError("Rozpakowane dane przekroczą limit 500 MB")
            for info in members:
                path = PurePosixPath(info.filename.replace("\\", "/"))
                if (path.is_absolute() or ".." in path.parts or
                        not path.parts or path.parts[0] != name):
                    raise ValueError(f"Niebezpieczna lub obca ścieżka w ZIP: {info.filename}")
                if not (destination.joinpath(*path.parts).resolve().is_relative_to(destination)):
                    raise ValueError(f"Ścieżka poza katalogiem docelowym: {info.filename}")
            zf.extractall(destination)
    if not (sequence_dir / "input").is_dir():
        raise ValueError("Archiwum nie zawiera oczekiwanej struktury CDnet")
    metadata = {
        "dataset": "CDnet 2014",
        "sequence": name,
        "source_url": url,
        "archive_sha256": digest.hexdigest(),
        "archive_bytes": total,
    }
    (sequence_dir / "download_source.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return sequence_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sequence", choices=SEQUENCES)
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    print(download_sequence(args.sequence, args.root))


if __name__ == "__main__":
    main()
