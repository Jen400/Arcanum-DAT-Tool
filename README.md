# Arcanum DAT Unpacker


[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Jen400/ArcanumDatUnpacker)](https://github.com/Jen400/ArcanumDatUnpacker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Jen400/ArcanumDatUnpacker?style=social)](https://github.com/Jen400/ArcanumDatUnpacker)


A fast Python-based tool to unpack ```.dat``` files from the game **Arcanum: Of Steamworks and Magick Obscura**.

This README.md has been generated through AI because I'm lazy, but I read it to make sure it is correct :P

## Overview

This tool was created to address the lack of fast and modern tools for unpacking ```.dat``` archives used by *Arcanum: Of Steamworks and Magick Obscura*. Most existing tools are either outdated, slow, or require Java or other dependencies.

This implementation was **converted from Java to Python** and is a **rough but working version**. It's significantly faster than legacy tools and runs natively in Python.

## Features

- Unpacks ```.dat``` files into a folder
- Handles both compressed and uncompressed entries
- Simple CLI interface
- No external dependencies beyond the Python standard library

## ️ Usage

### Requirements

- Python 3.8 or higher
- ```.dat``` file located in the current directory

### Instructions

1. Place the ```.dat``` file you want to unpack in the same directory as the script.
2. Run the script:

```bash
python datunpacker.py
```

3. When prompted, enter the name of the ```.dat``` file.
4. The contents will be extracted into a folder named ```out/``` in the same directory.

### Example

```bash
$ python datunpacker.py
Enter the name of the .dat file (must be in current directory): data.dat
Unpacked data.dat to ./out
```

## 📁 Project Structure

```
.
├── datunpacker.py     # Main unpacking script
├── README.md           # This file
└── out/                # Output directory (auto-created)
```

## ⚠️ Notes

- This is a **rough conversion** from Java to Python sorry if the code looks horrible!
- Contributions and improvements are welcome!

## 📜 License

This project is released under the **MIT License** — feel free to use, modify, and distribute it.