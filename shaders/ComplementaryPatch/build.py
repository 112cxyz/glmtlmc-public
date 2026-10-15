#!/usr/bin/env python3
"""Download upstream Complementary Reimagined, apply the included patch, zip it."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

UPSTREAM_URL = (
    "https://cdn.modrinth.com/data/HVnmMxH1/versions/Bqen1mJX/"
    "ComplementaryReimagined_r5.9.3.zip"
)
# The pristine upstream archive, as documented in README.md. A reissued or
# tampered download must fail here, before patch(1) ever sees it.
UPSTREAM_SHA512 = (
    "45304b1d7862afdb2177b7e6226fc9c6737911d17a4ad46cc9c519ca4deb935f05072"
    "cd337cd8b19a15bb8062b57b54eceec7bdee4cd572d94858e2946d37d85"
)
PACK_NAME = "ComplementaryReimagined_r5.9.3"


def extract_upstream(archive: bytes, destination: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        for member in source.infolist():
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"unsafe path in upstream archive: {member.filename}")
            source.extract(member, destination)


def main() -> int:
    tool_dir = Path(__file__).resolve().parent
    patch_file = tool_dir / "patches" / "001-remove-apple-device-gating.patch"
    if not patch_file.is_file():
        # Single source of truth lives with the shader fork; a local
        # patches/ dir (as staged into release packages) wins when present.
        patch_file = (tool_dir / ".." / ".." / "OPC" / "shader-forks"
                      / "ComplementaryReimagined_r5.9.3" / "patches"
                      / "001-remove-apple-device-gating.patch")
    if not patch_file.is_file():
        raise FileNotFoundError(f"required patch not found: {patch_file}")
    if shutil.which("patch") is None:
        raise RuntimeError("'patch' is required but was not found on PATH")

    output_dir = tool_dir / "dist"
    output_zip = output_dir / f"{PACK_NAME}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="complementary-patch-") as temporary:
        source_dir = Path(temporary) / "source"
        source_dir.mkdir()
        with urllib.request.urlopen(UPSTREAM_URL, timeout=60) as response:
            archive_bytes = response.read()
        downloaded = hashlib.sha512(archive_bytes).hexdigest()
        if downloaded != UPSTREAM_SHA512:
            raise RuntimeError(
                "upstream archive is not the pinned build\n"
                f"    expected sha512 {UPSTREAM_SHA512}\n"
                f"    downloaded sha512 {downloaded}"
            )
        extract_upstream(archive_bytes, source_dir)
        completed = subprocess.run(
            ["patch", "-p1", "-i", str(patch_file)],
            cwd=source_dir,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"'patch' failed:\n{completed.stdout}{completed.stderr}")
        if "with fuzz" in completed.stdout or "offset" in completed.stdout:
            raise RuntimeError(
                "patch applied with fuzz/offset, not cleanly -- inputs drifted:\n"
                + completed.stdout
            )
        rejects = sorted(path.relative_to(source_dir).as_posix()
                         for path in source_dir.rglob("*.rej"))
        if rejects:
            raise RuntimeError("patch left rejects: " + ", ".join(rejects))

        temporary_zip = Path(temporary) / output_zip.name
        with zipfile.ZipFile(
            temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for path in sorted(source_dir.rglob("*")):
                if not path.is_file() or path.name == ".DS_Store" or path.name == ".gitkeep":
                    continue
                archive.write(path, path.relative_to(source_dir).as_posix())
        temporary_zip.replace(output_zip)

    print(f"built: {output_zip}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
