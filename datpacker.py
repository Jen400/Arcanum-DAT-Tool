"""Create Arcanum .dat archive files."""

from __future__ import annotations

import uuid
import zlib
from pathlib import Path

from datformat import (
    DAT1_MAGIC,
    FOOTER_LENGTH,
    DatEntry,
    normalize_dat_path,
    write_uint32,
)


class DatPacker:
    """Creates an Arcanum .dat archive from one or more directories."""

    def pack(
        self,
        input_dirs: list[Path],
        output_file: Path,
        compress: bool = True,
        verbose: bool = False,
    ) -> int:
        collected = self._collect_entries(input_dirs)

        if verbose:
            print(f"  Collected {len(collected)} entries to pack.")

        with open(output_file, "wb") as f:
            records: list[tuple[str, int, int, int, int]] = []
            data_cursor = 0

            for dat_path, is_dir, abs_path in collected:
                if is_dir:
                    records.append((dat_path, DatEntry.DIR_FLAG, 0, 0, 0))
                    if verbose:
                        print(f"  DIR  {dat_path}")
                    continue

                file_data = abs_path.read_bytes()
                full_size = len(file_data)
                to_write = file_data
                flags = DatEntry.FILE_FLAG

                if compress and full_size > 0:
                    compressed = zlib.compress(file_data)
                    if len(compressed) < full_size:
                        to_write = compressed
                        flags |= DatEntry.COMPRESSED_FLAG

                f.write(to_write)
                records.append((
                    dat_path, flags, full_size, len(to_write), data_cursor,
                ))
                if verbose:
                    tag = " (compressed)" if flags & DatEntry.COMPRESSED_FLAG else ""
                    print(
                        f"  FILE {dat_path}"
                        f" [{full_size} -> {len(to_write)} bytes]{tag}"
                    )
                data_cursor += len(to_write)

            # -- entry table offset marker --
            entry_table_offset = data_cursor + 4
            f.write(write_uint32(entry_table_offset))

            # -- entry table --
            entry_table, file_names_length = self._build_entry_table(records)
            f.write(entry_table)

            # -- footer --
            footer = self._build_footer(
                file_names_length=file_names_length,
                bytes_to_start=len(entry_table) + FOOTER_LENGTH,
            )
            f.write(footer)

        return len(records)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_entries(
        input_dirs: list[Path],
    ) -> list[tuple[str, bool, Path | None]]:
        """Walk input directories and collect entries.

        Each input directory's name is preserved as the first path component
        inside the archive.
        """
        entries: list[tuple[str, bool, Path | None]] = []

        for root in input_dirs:
            if not root.is_dir():
                print(f"  Warning: {root} is not a directory — skipping.")
                continue
            root_resolved = root.resolve()
            base = root_resolved.parent
            entries.extend(DatPacker._traverse(root_resolved, base))

        return entries

    @staticmethod
    def _traverse(
        directory: Path,
        base: Path,
    ) -> list[tuple[str, bool, Path | None]]:
        """Depth-first traversal matching Arcanum's entry order.

        Children are sorted alphabetically (case-insensitive) and processed
        in natural order: files are emitted directly; directories emit a
        directory entry then immediately recurse.
        """
        entries: list[tuple[str, bool, Path | None]] = []
        children = sorted(directory.iterdir(), key=lambda p: p.name.lower())

        for child in children:
            dat_path = normalize_dat_path(str(child.relative_to(base)))

            if child.is_file():
                entries.append((dat_path, False, child))
            elif child.is_dir():
                entries.append((dat_path, True, None))
                entries.extend(DatPacker._traverse(child, base))

        return entries

    @staticmethod
    def _build_entry_table(
        records: list[tuple[str, int, int, int, int]],
    ) -> tuple[bytes, int]:
        """Serialise entry records into the binary entry table.

        Returns ``(table_bytes, file_names_length)``.
        """
        buf = bytearray()
        buf.extend(write_uint32(len(records)))
        file_names_length = 0

        for path, flags, full_size, compressed_size, data_offset in records:
            encoded = path.encode("utf-8")
            string_length = len(encoded) + 1
            file_names_length += string_length

            buf.extend(write_uint32(string_length))
            buf.extend(encoded)
            buf.extend(b"\x00")      # null terminator
            buf.extend(b"\x00" * 4)  # unknown field
            buf.extend(write_uint32(flags))
            buf.extend(write_uint32(full_size))
            buf.extend(write_uint32(compressed_size))
            buf.extend(write_uint32(data_offset))

        return bytes(buf), file_names_length

    @staticmethod
    def _build_footer(file_names_length: int, bytes_to_start: int) -> bytes:
        """Build the 28-byte archive footer."""
        buf = bytearray()
        buf.extend(uuid.uuid4().bytes_le)
        buf.extend(DAT1_MAGIC)
        buf.extend(write_uint32(file_names_length))
        buf.extend(write_uint32(bytes_to_start))
        return bytes(buf)
