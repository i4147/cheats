cheat:bat
# Display a single file on the terminal:
bat <file>
# Display multiple files at once:
bat <file> <file>
# Show and highlight non-printable characters:
bat -A <file>
# Display all supported languages:
bat --list-languages
# Set the language for syntax highlighting:
bat --language <language> <file.<language extension>>
 tldr:bat
# bat
# Print and concatenate files.
# A `cat` clone with syntax highlighting and Git integration.
# More information: <https://github.com/sharkdp/bat>.
# Print the contents of a file to the standard output:
bat path/to/file
# Concatenate several files into the target file:
bat file1 file2 > target_file
# Append several files into the target file:
bat file1 file2 >> target_file
# Number all output lines:
bat --number path/to/file
# Syntax highlight a JSON file:
bat --language json file.json
# Display all supported languages:
bat --list-languages
# See also: `cat`.
