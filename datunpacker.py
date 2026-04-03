"""Extract Arcanum .dat archive files."""

from __future__ import annotations

import zlib
from pathlib import Path

from datformat import DatEntry, DatFooter, FOOTER_LENGTH, read_uint32


class DatUnpacker:
    """Extracts the contents of an Arcanum .dat archive."""

    def unpack(
        self,
        dat_file: Path,
        export_dir: Path,
        *,
        verbose: bool = False,
    ) -> int:
        dat_bytes = dat_file.read_bytes()
        footer = DatFooter(dat_bytes[-FOOTER_LENGTH:])
        entries = self._read_entries(dat_bytes, footer)
        count = 0

        for entry in entries:
            safe_name = entry.file_name.replace("\\", "/")
            output_path = export_dir / safe_name

            if entry.is_directory:
                output_path.mkdir(parents=True, exist_ok=True)
                if verbose:
                    print(f"  DIR  {entry.file_name}")
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                size = (
                    entry.compressed_size
                    if entry.is_compressed
                    else entry.full_size
                )
                raw = dat_bytes[entry.data_offset : entry.data_offset + size]
                if entry.is_compressed:
                    try:
                        raw = zlib.decompress(raw)
                    except zlib.error as exc:
                        print(f"  ERROR decompressing {entry.file_name}: {exc}")
                        continue
                output_path.write_bytes(raw)
                if verbose:
                    tag = " (compressed)" if entry.is_compressed else ""
                    print(
                        f"  FILE {entry.file_name}"
                        f" [{entry.full_size} bytes]{tag}"
                    )
            count += 1

        return count

    @staticmethod
    def _read_entries(dat_bytes: bytes, footer: DatFooter) -> list[DatEntry]:
        start = len(dat_bytes) - footer.bytes_to_file_names_start
        entries_data = dat_bytes[start:]
        offset = 0
        num_entries, offset = read_uint32(entries_data, offset)
        entries: list[DatEntry] = []
        for _ in range(num_entries):
            entry, offset = DatEntry.read(entries_data, offset)
            entries.append(entry)
        return entries
