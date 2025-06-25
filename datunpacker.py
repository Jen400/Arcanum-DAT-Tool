import os
import zlib
from pathlib import Path

FOOTER_LENGTH = 28

class DatUnpacker:

    def unpack(self, dat_file, export_dir):
        with open(dat_file, "rb") as f:
            dat_bytes = bytearray(f.read())

        dat_footer = self.read_footer(dat_bytes)
        dat_entries = self.read_entries_info(dat_footer, dat_bytes)

        for dat_entry in dat_entries:
            output_file = Path(export_dir) / dat_entry.get_file_name()
            if dat_entry.is_directory():
                output_file.mkdir(parents=True, exist_ok=True)
            else:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                entry_size = (
                    dat_entry.get_compressed_size()
                    if dat_entry.is_compressed()
                    else dat_entry.get_full_size()
                )
                entry_data = self.read_byte_array_section(
                    dat_bytes, dat_entry.get_offset(), entry_size
                )
                if dat_entry.is_compressed():
                    # Decompress the data
                    decompressor = zlib.decompressobj()
                    try:
                        entry_data = decompressor.decompress(entry_data)
                    except zlib.error as e:
                        print(f"Decompression error for {dat_entry.get_file_name()}: {e}")
                        entry_data = decompressor.flush()

                with open(output_file, "wb") as os:
                    os.write(entry_data)

    def read_footer(self, dat_bytes):
        footer_bytes = dat_bytes[-FOOTER_LENGTH:]
        return self.DatFooter(footer_bytes)

    def read_entries_info(self, dat_footer, dat_bytes):
        bytes_to_file_names_start = dat_footer.get_bytes_to_file_names_start()
        entries_data = self.read_byte_array_section(
            dat_bytes,
            len(dat_bytes) - bytes_to_file_names_start,
            bytes_to_file_names_start,
        )
        offset = 0
        number_of_entries, offset = StreamReaderUtil.read_int(entries_data, offset)
        dat_entries = []
        for _ in range(number_of_entries):
            entry, offset = self.DatEntry.read(entries_data, offset)
            dat_entries.append(entry)
        return dat_entries

    def read_byte_array_section(self, byte_array, pos, bytes_to_read):
        return byte_array[pos : pos + bytes_to_read]

    class DatEntry:
        DIR_FLAG = 0x400
        COMPRESSED_FLAG = 0x2

        def __init__(self, data, offset):
            self.data = data
            self.offset = offset

            # Read string length
            string_length, self.offset = StreamReaderUtil.read_int(data, offset)

            # Read file name
            self.fileName, self.offset = StreamReaderUtil.read_string(data, self.offset, string_length - 1)

            # Skip null terminator (1 byte) and padding (4 bytes)
            self.offset += 1 + 4  # Skip null terminator and padding

            # Read flags
            self.flags, self.offset = StreamReaderUtil.read_bitmask(data, self.offset)

            # Read full size
            self.fullSize, self.offset = StreamReaderUtil.read_int(data, self.offset)

            # Read compressed size
            self.compressedSize, self.offset = StreamReaderUtil.read_int(data, self.offset)

            # Read offset
            self.offset_val, self.offset = StreamReaderUtil.read_int(data, self.offset)

        def get_file_name(self):
            return self.fileName

        def get_flags(self):
            return self.flags

        def get_full_size(self):
            return self.fullSize

        def get_compressed_size(self):
            return self.compressedSize

        def get_offset(self):
            return self.offset_val

        def is_directory(self):
            return (self.flags & self.DIR_FLAG) != 0

        def is_compressed(self):
            return (self.flags & self.COMPRESSED_FLAG) != 0

        @classmethod
        def read(cls, data, offset):
            return cls(data, offset), cls(data, offset).offset

    class DatFooter:
        def __init__(self, data):
            self.data = data

            # Read GUID
            self.guid, self.offset = StreamReaderUtil.read_guid(data, 0)

            # Read format (4 bytes)
            self.format, self.offset = StreamReaderUtil.read_string(data, self.offset, 4)

            # Read file names length
            self.fileNamesLength, self.offset = StreamReaderUtil.read_int(data, self.offset)

            # Read bytes to file names start
            self.bytesToFileNamesStart, self.offset = StreamReaderUtil.read_int(data, self.offset)

        def get_guid(self):
            return self.guid

        def get_format(self):
            return self.format

        def get_file_names_length(self):
            return self.fileNamesLength

        def get_bytes_to_file_names_start(self):
            return self.bytesToFileNamesStart

class StreamReaderUtil:
    @staticmethod
    def read_value_hex(data, offset, n):
        if offset + n > len(data):
            raise RuntimeError("Reached EOS while reading hex")
        bytes_ = data[offset:offset + n]
        hex_string = ""
        for x in reversed(range(n)):
            hex_string += f"{bytes_[x]:02X}"
        return hex_string, offset + n

    @classmethod
    def read_int(cls, data, offset):
        hex_str, new_offset = cls.read_value_hex(data, offset, 4)
        return int(hex_str, 16), new_offset

    @classmethod
    def read_string(cls, data, offset, length):
        if offset + length > len(data):
            raise RuntimeError(f"Reached EOS while reading string (length: {length}, remaining: {len(data) - offset})")

        # Handle special case where length is 0 or negative
        if length <= 0:
            return "", offset

        # Read bytes and convert to string
        bytes_ = data[offset:offset+length]
        try:
            # First try UTF-8 decoding
            string = bytes_.decode('utf-8')
        except UnicodeDecodeError:
            # If that fails, try individual byte decoding
            string = ""
            for i in range(length):
                b = bytes_[i]
                if b == 0:
                    break  # Stop at null terminator
                string += chr(b)
        return string, offset + length

    @classmethod
    def read_guid(cls, data, offset):
        if offset + 16 > len(data):
            raise RuntimeError("Reached EOS while reading GUID")

        bytes_ = data[offset:offset+16]
        guid = "G_"
        guid += f"{bytes_[3]:02X}{bytes_[2]:02X}{bytes_[1]:02X}{bytes_[0]:02X}_"
        guid += f"{bytes_[5]:02X}{bytes_[4]:02X}_"
        guid += f"{bytes_[7]:02X}{bytes_[6]:02X}_"
        guid += f"{bytes_[8]:02X}{bytes_[9]:02X}_"
        guid += f"{bytes_[10]:02X}{bytes_[11]:02X}"
        guid += f"{bytes_[12]:02X}{bytes_[13]:02X}"
        guid += f"{bytes_[14]:02X}{bytes_[15]:02X}"
        return guid, offset + 16

    @classmethod
    def read_bitmask(cls, data, offset):
        hex_str, new_offset = cls.read_value_hex(data, offset, 4)
        return int(hex_str, 16), new_offset

    @classmethod
    def read_byte(cls, data, offset):
        if offset >= len(data):
            raise RuntimeError("Reached EOS while reading byte")
        byte = data[offset]
        return byte, offset + 1

if __name__ == "__main__":
    import sys

    # Prompt user for the filename
    dat_filename = input("Enter the name of the .dat file to unpack (must be in current directory): ").strip()

    # Define the input and output paths
    current_dir = Path.cwd()
    dat_file = current_dir / dat_filename
    export_dir = current_dir / "out"

    # Check if the file exists
    if not dat_file.is_file():
        print(f"Error: The file {dat_file} does not exist.")
        sys.exit(1)

    # Create the unpacker instance and run
    try:
        unpacker = DatUnpacker()
        unpacker.unpack(dat_file, export_dir)
        print(f"Unpacked {dat_filename} to {export_dir}")
    except Exception as e:
        print(f"An error occurred during unpacking: {e}")
        sys.exit(1)