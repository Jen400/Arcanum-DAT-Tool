"""Shared constants, helpers, and data structures for the Arcanum .dat format."""

from __future__ import annotations

import struct

FOOTER_LENGTH = 28

# "DAT1" FourCC stored as a little-endian uint32 (bytes on disk: 31 54 41 44).
DAT1_MAGIC = struct.pack("<I", 0x44415431)


# ---------------------------------------------------------------------------
# Binary I/O helpers
# ---------------------------------------------------------------------------

def read_uint32(data: bytes, offset: int) -> tuple[int, int]:
    """Read a little-endian unsigned 32-bit integer."""
    value = struct.unpack_from("<I", data, offset)[0]
    return value, offset + 4


def write_uint32(value: int) -> bytes:
    """Return *value* as 4 little-endian bytes."""
    return struct.pack("<I", value)


def read_string(data: bytes, offset: int, length: int) -> tuple[str, int]:
    """Read a fixed-length string, stopping at the first null byte."""
    if length <= 0:
        return "", offset
    raw = data[offset : offset + length]
    try:
        text = raw.decode("utf-8").split("\x00", 1)[0]
    except UnicodeDecodeError:
        text = raw.decode("latin-1").split("\x00", 1)[0]
    return text, offset + length


def read_guid(data: bytes, offset: int) -> tuple[str, int]:
    """Read a 16-byte GUID and return a formatted hex string."""
    b = data[offset : offset + 16]
    guid = (
        f"G_{b[3]:02X}{b[2]:02X}{b[1]:02X}{b[0]:02X}"
        f"_{b[5]:02X}{b[4]:02X}"
        f"_{b[7]:02X}{b[6]:02X}"
        f"_{b[8]:02X}{b[9]:02X}"
        f"_{b[10]:02X}{b[11]:02X}{b[12]:02X}{b[13]:02X}{b[14]:02X}{b[15]:02X}"
    )
    return guid, offset + 16


def normalize_dat_path(path: str) -> str:
    """Ensure a path uses Windows-style backslash separators."""
    return path.replace("/", "\\")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class DatFooter:
    """28-byte footer found at the end of a .dat archive."""

    def __init__(self, data: bytes) -> None:
        offset = 0
        self.guid, offset = read_guid(data, offset)
        self.format_raw = data[offset : offset + 4]
        self.format_uint32 = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        self.file_names_length, offset = read_uint32(data, offset)
        self.bytes_to_file_names_start, offset = read_uint32(data, offset)


class DatEntry:
    """A single file or directory entry inside a .dat archive."""

    DIR_FLAG = 0x400
    FILE_FLAG = 0x01
    COMPRESSED_FLAG = 0x02

    def __init__(self, data: bytes, offset: int) -> None:
        string_length, offset = read_uint32(data, offset)
        self.file_name, offset = read_string(data, offset, string_length - 1)
        self.unknown_field = struct.unpack_from("<I", data, offset + 1)[0]
        offset += 5  # null terminator + 4-byte unknown field
        self.flags, offset = read_uint32(data, offset)
        self.full_size, offset = read_uint32(data, offset)
        self.compressed_size, offset = read_uint32(data, offset)
        self.data_offset, offset = read_uint32(data, offset)
        self._end_offset = offset

    @property
    def is_directory(self) -> bool:
        return (self.flags & self.DIR_FLAG) != 0

    @property
    def is_compressed(self) -> bool:
        return (self.flags & self.COMPRESSED_FLAG) != 0

    @classmethod
    def read(cls, data: bytes, offset: int) -> tuple[DatEntry, int]:
        entry = cls(data, offset)
        return entry, entry._end_offset
