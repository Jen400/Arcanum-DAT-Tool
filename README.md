# Arcanum DAT Tool

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Jen400/ArcanumDatUnpacker)](https://github.com/Jen400/ArcanumDatUnpacker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Jen400/ArcanumDatUnpacker?style=social)](https://github.com/Jen400/ArcanumDatUnpacker)

This README.md has been generated through AI because I'm lazy, but I read it to make sure it is correct :P

## Overview

A Python command-line tool for packing and unpacking `.dat` archive files used by
*Arcanum: Of Steamworks and Magick Obscura*.

## Known Limitations

- **Compression:** Archives created with zlib compression may not be fully
  compatible with the game. Use `compress` at your own risk.
- **Unknown field:** A 4-byte field in each entry is written as zeros. The
  1st party tool writes non-zero values (likely runtime memory addresses).
  This does not appear to affect compatibility.
- **Multiple directories:** I tested the tool and works when passing a single directory (e.g. art\*) passing multiple directories will generate a broken .dat file, I'm still trying to figure out the issue.

## Features

- **Unpack** `.dat` archives to disk, preserving the original directory structure.
- **Pack** one or more folders into a game-compatible `.dat` archive.
- Handles both stored and zlib-compressed entries during extraction.
- Cross-platform — runs anywhere Python 3.10+ is available; work on both Linux and Windows
## Project Structure

| File             | Description                                                |
| ---------------- | ---------------------------------------------------------- |
| `dattool.py`     | CLI entry point (`pack` and `unpack` subcommands)          |
| `datpacker.py`   | Archive creation logic (`DatPacker`)                       |
| `datunpacker.py` | Archive extraction logic (`DatUnpacker`)                   |
| `datformat.py`   | Shared constants, binary I/O helpers, and data structures  |

## Requirements

- Python 3.10 or later.
- No third-party dependencies — only the standard library is used.

## Usage

### Unpacking

Extract the contents of a `.dat` archive:

python dattool.py unpack <archive.dat> -o <output_dir>


| Option           | Description                              |
| ---------------- | ---------------------------------------- |
| `-o`, `--output` | Output directory (default: `out`)        |
| `-v`, `--verbose`| Print each entry as it is extracted      |

Example:

python dattool.py unpack Arcanum1.dat -o extracted


### Packing

Create a `.dat` archive from one or more input directories. Each directory's
**name** becomes the top-level path component inside the archive.

python dattool.py pack \<dir\> [\<dir\> ...] -o <archive.dat> [options]

| Option                | Description                                         |
|-----------------------|-----------------------------------------------------|
| `-o`, `--output`      | Output `.dat` file (required)                       |
| `compress`            | Store files compressed (UNSUPPORTED!)               |
| `--flatten`           | Use immediate subdirectories of each input as roots |
| `-v`, `--verbose`     | Print each entry as it is packed                    |

Examples:

Pack the "art" folder — archive paths will start with "art"\
`python dattool.py pack art -o Arcanum1.dat`

Pack multiple top-level folders\
`python dattool.py pack art sound rules -o Arcanum1.dat`

Flatten: treat subdirectories of "extracted" as individual roots\
`python dattool.py pack extracted --flatten -o Arcanum1.dat`


#### The --flatten option

When your extracted files sit inside a wrapper directory like `extracted/`,
passing `--flatten` promotes each of its immediate subdirectories to a root:

extracted/
├── art/
├── rules/
└── sound/

Without --flatten: paths would be "extracted\art...", "extracted\rules..."
With --flatten: paths are "art...", "rules..."

`python dattool.py pack extracted --flatten -o Arcanum1.dat`


Loose files sitting directly inside a flattened directory are skipped with a
warning.

## DAT File Format

The binary layout of an Arcanum `.dat` archive:

+------------------------------+ offset 0\
| Data blob | Concatenated file contents\ | (stored or zlib-compressed) |\
+------------------------------+\
| uint32: entry table offset | 4 bytes\
+------------------------------+\
| Entry table | uint32 count, followed by entries\
+------------------------------+\
| Footer (28 bytes) | GUID + format tag + lengths\
+------------------------------+ EOF



### Entry format

Each entry in the table:

| Field             | Size     | Description                                            |
| ----------------- | -------- | ------------------------------------------------------ |
| `string_length`   | 4 bytes  | Length of filename including null terminator            |
| `file_name`       | variable | Null-terminated filename (backslash-separated)         |
| `unknown`         | 4 bytes  | Unknown field (written as zeros by this tool)          |
| `flags`           | 4 bytes  | `0x0001` = file, `0x0002` = compressed, `0x0400` = dir|
| `full_size`       | 4 bytes  | Uncompressed file size (0 for directories)             |
| `compressed_size` | 4 bytes  | Size on disk (0 for directories)                       |
| `data_offset`     | 4 bytes  | Offset into the data blob (0 for directories)          |

### Footer format (28 bytes)

| Field             | Size     | Description                                        |
| ----------------- | -------- | -------------------------------------------------- |
| GUID              | 16 bytes | Unique archive identifier (little-endian)          |
| Format tag        | 4 bytes  | `0x44415431` — ASCII "DAT1" as a LE uint32        |
| File names length | 4 bytes  | Sum of all `string_length` values                  |
| Offset from end   | 4 bytes  | Byte distance from EOF to entry table start        |