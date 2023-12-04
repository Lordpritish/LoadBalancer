#!/bin/bash

# Source and destination directories
source_directory="."
destination_directory_external="/home/mininet//pox/ext"
destination_directory_examples="/home/mininet/mininet/examples"
file_to_exclude="mytop.py"
image_files_to_exclude="*.png"
directories_to_exclude=".git"


# Copy everything (excluding specified files and directories) from the source to the destination (external)
find "$source_directory" -type f -not -name "$file_to_exclude" -not -name "$image_files_to_exclude" -not -path "./$directories_to_exclude/*" -exec cp -u --parents {} "$destination_directory_external" \;

# Copy the specified file to the destination (examples)
cp -u "$source_directory/$file_to_exclude" "$destination_directory_examples"
