import mmap
import os
import sys
import time

from pathlib import Path

POINTER_HEADER_SIZE = 0x18 # Size of the header of the pointers 

ARCHIVE_HEADER_SIZE = 0x46 # Size of the header of the whole file

# Checking for valid input
if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <filename> <desination folder>")
    sys.exit(0)

source_file = sys.argv[1]
destination_folder = sys.argv[2]

# Checking if the input file exists
if os.path.isfile(source_file) == False:
    print("File %s does not exist", source_file)
    sys.exit(0)

def main():

    # Reading the file
    try:
        file = open(source_file, "rb")
    except IOError as exception:
        print(f"Failed to open source file {source_file}: {exception}")
        sys.exit(0)

    start_time = time.time()

    # Size of the whole archive file
    file_size = file.seek(0, os.SEEK_END) 

    # Basic header verification
    source_archive_header_size = int.from_bytes(read_range(file, 0x0, 0x4), 'little')
    if source_archive_header_size != ARCHIVE_HEADER_SIZE:
        print("Unsupported file format (some Compedia games use a different archive format)")
        sys.exit(0)

    # Pointer table offset
    pointer_table_offset = int.from_bytes(read_range(file, 0x42, 0x46), 'little') 
    index = pointer_table_offset

    # Counter for all the archive files
    file_counter = 0

    # Going through every single pointer entry
    while index < file_size:

        # Reading the pointer data
        curr_start_offset = int.from_bytes(read_range(file, index + 0x4, index + 0x8), 'little') # Start offset of the file within the archive
        curr_end_offset = curr_start_offset + int.from_bytes(read_range(file, index + 0xC, index + 0x10), 'little') # End offset of the file within the archive
        curr_file_name_size = int.from_bytes(read_range(file, index + 0x10, index + 0x14), 'little') # File name size 
        curr_path_size = int.from_bytes(read_range(file, index + 0x14, index + 0x18), 'little') # Path name size

        curr_file_name = read_range(file, index + POINTER_HEADER_SIZE, index + POINTER_HEADER_SIZE + curr_file_name_size - 1).decode("utf-8") # File name
        curr_path = read_range(file, index + POINTER_HEADER_SIZE + curr_file_name_size, index + POINTER_HEADER_SIZE + curr_file_name_size + curr_path_size - 1).decode("utf-8") # Path
        
        # Reading the current file data
        curr_data = read_range(file, curr_start_offset, curr_end_offset)

        # Formatting the path correctly and creating the subdirectories if they don't exist
        corrected_curr_path = Path(destination_folder + "/" + curr_path.split(":")[1].replace("\\", "", 1).replace("\\","/"))
        os.makedirs(corrected_curr_path, exist_ok=True)

        # Writing the file to the path in the destination folder 
        with open(os.path.join(corrected_curr_path, curr_file_name), "wb") as curr_file:
            print(f"Exporting file: {corrected_curr_path}/{curr_file_name}")
            try:
                curr_file.write(curr_data)
                file_counter = file_counter + 1
            except Exception as exception:
                print(f"Failed to export file {corrected_curr_path}/{curr_file_name}: {exception}")

        index = index + curr_file_name_size + curr_path_size + POINTER_HEADER_SIZE

    file.close()

    end_time = time.time()
    print(f"Finished writing {file_counter} files in {end_time - start_time} seconds")

def read_range(file, start, end):

    # Reading data from specified offset range

    with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
        mmapped_file.seek(start)
        data = mmapped_file.read(end - start)
    return data

main()
