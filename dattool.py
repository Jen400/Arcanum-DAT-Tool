"""CLI for packing and unpacking Arcanum .dat archives."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from datpacker import DatPacker
from datunpacker import DatUnpacker


def resolve_input_dirs(directories: list[Path], flatten: bool) -> list[Path]:
    """Optionally expand each directory to its immediate child directories."""

    # Force natural sorting, the game will complain otherwise
    directories = sorted(directories)

    if not flatten:
        return directories

    expanded: list[Path] = []
    for d in directories:
        if not d.is_dir():
            print(f"  Warning: {d} is not a directory — skipping.")
            continue

        children = sorted(d.iterdir())
        child_dirs = [c for c in children if c.is_dir()]
        loose_files = [c for c in children if c.is_file()]

        if loose_files:
            print(
                f"  Warning: --flatten is active — {len(loose_files)} file(s) "
                f"sitting directly in {d} will NOT be included:"
            )
            for f in loose_files:
                print(f"    - {f.name}")

        expanded.extend(child_dirs)

    return expanded


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pack and unpack Arcanum .dat archives.",
    )
    sub = parser.add_subparsers(dest="command")

    # -- unpack --------------------------------------------------------
    sp_unpack = sub.add_parser("unpack", help="Extract a .dat archive.")
    sp_unpack.add_argument("dat_file", type=Path)
    sp_unpack.add_argument("-o", "--output", type=Path, default=Path("out"))
    sp_unpack.add_argument("-v", "--verbose", action="store_true")

    # -- pack ----------------------------------------------------------
    sp_pack = sub.add_parser("pack", help="Create a .dat archive from folders.")
    sp_pack.add_argument("directories", type=Path, nargs="+")
    sp_pack.add_argument("-o", "--output", type=Path, required=True)
    sp_pack.add_argument(
        "--compress", action="store_true",
        help="Store files compressed (WARN: currently broken).",
    )
    sp_pack.add_argument(
        "--flatten", action="store_true",
        help="Use immediate subdirectories of each input as roots.",
    )
    sp_pack.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "unpack":
        if not args.dat_file.is_file():
            print(f"Error: {args.dat_file} does not exist.")
            sys.exit(1)
        n = DatUnpacker().unpack(
            args.dat_file, args.output, verbose=args.verbose,
        )
        print(f"Unpacked {n} entries from {args.dat_file} -> {args.output}")

    elif args.command == "pack":
        input_dirs = resolve_input_dirs(args.directories, args.flatten)
        if not input_dirs:
            print("Error: no directories to pack.")
            sys.exit(1)
        missing = [d for d in input_dirs if not d.is_dir()]
        if missing:
            for d in missing:
                print(f"Error: {d} is not a directory.")
            sys.exit(1)
        n = DatPacker().pack(
            input_dirs, args.output,
            compress=args.compress,
            verbose=args.verbose,
        )
        print(f"Packed {n} entries into {args.output}")


if __name__ == "__main__":
    main()
