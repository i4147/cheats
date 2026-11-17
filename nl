cheat.sheets:nl
# nl
# Number lines of files
# Number lines given to nl(1) via STDIN.
printf "Here\nis\nsome\nexample\ntext." | nl
# Number (all) lines given to nl(1) via provided file(s).
nl -b a /path/to/file
# The above can also be achieved with cat(1), which is perhaps more portable:
cat -n /path/to/file
 tldr:nl
# nl
# A utility for numbering lines, either from a file, or from standard input.
# More information: <https://www.gnu.org/software/coreutils/nl>.
# Number non-blank lines in a file:
nl path/to/file
# Read from standard output:
cat path/to/file | nl options -
# Number only the lines with printable text:
nl -t path/to/file
# Number all lines including blank lines:
nl -b a path/to/file
# Number only the body lines that match a basic regular expression (BRE) pattern:
nl -b p'FooBar[0-9]' path/to/file
# Read from `stdin`:
command | nl -
# Use a specific [i]ncrement for line numbering:
nl -i increment path/to/file
# Specify the line numbering format to [r]ight or [l]eft justified, keeping leading [z]eros or [n]ot:
nl -n rz
# Specify the line numbering's [w]idth (6 by default):
nl -w col_width path/to/file
# Use a specific string to [s]eparate the line numbers from the lines (`TAB` by default):
nl -s separator path/to/file
