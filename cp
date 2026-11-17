cheat:cp
# To copy a file:
cp ~/Desktop/foo.txt ~/Downloads/foo.txt
# To copy a directory:
cp -r ~/Desktop/cruise_pics/ ~/Pictures/
# To create a copy but ask to overwrite if the destination file already exists:
cp -i ~/Desktop/foo.txt ~/Documents/foo.txt
# To create a backup file with date:
cp foo.txt{,."$(date +%Y%m%d-%H%M%S)"}
# To copy a symlink that points to a directory (and is thus soft) and not
# 'expand' the symlink (aka, preserve its nature as a symlink):
# Note this does NOT work (note trailing '/'):  cp -P /path/to/symlink-dir/
cp -P <symlink-dir> <dest-dir>
# To copy sparsely:
cp --sparse=always <src> <dest>
 tldr:cp
# cp
# Copy files and directories.
# More information: <https://www.gnu.org/software/coreutils/cp>.
# Copy a file to another location:
cp path/to/source_file.ext path/to/target_file.ext
# Copy a file into another directory, keeping the filename:
cp path/to/source_file.ext path/to/target_parent_directory
# Recursively copy a directory's contents to another location (if the destination exists, the directory is copied inside it):
cp -R path/to/source_directory path/to/target_directory
# Copy a directory recursively, in verbose mode (shows files as they are copied):
cp -vR path/to/source_directory path/to/target_directory
# Copy multiple files at once to a directory:
cp -t path/to/destination_directory path/to/file1 path/to/file2 ...
# Copy text files to another location, in interactive mode (prompts user before overwriting):
cp -i *.txt path/to/target_directory
# Follow symbolic links before copying:
cp -L link path/to/target_directory
# Use the first argument as the destination directory (useful for `xargs ... | cp -t <DEST_DIR>`):
cp -t path/to/target_directory path/to/file_or_directory1 path/to/file_or_directory2 ...
