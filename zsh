cheat:zsh
# A plain old glob
print -l *.txt
print -l **/*.txt
# Show text files that end in a number fr
om 1 to 10
print -l **/*<1-10>.txt
# Show text files that start with the let
ter a
print -l **/[a]*.txt
# Show text files that start with either
ab or bc
print -l **/(ab|bc)*.txt
# Show text files that don't start with a
lower or uppercase c
print -l **/[^cC]*.txt
# Show only directories
print -l **/*(/)
# Show only regular files
print -l **/*(.)
# Show empty files
print -l **/*(L0)
# Show files greater than 3 KB
print -l **/*(Lk+3)
# Show files modified in the last hour
print -l **/*(mh-1)
# Sort files from most to least recently
modified and show the last 3
print -l **/*(om[1,3])
# `.` show files, `Lm-2` smaller than 2MB
, `mh-1` modified in last hour,
# `om` sort by modification date, `[1,3]`
only first 3 files
print -l **/*(.Lm-2mh-1om[1,3])
# Show every directory that contain direc
tory `.git`
print -l **/*(e:'[[ -d $REPLY/.git ]]':)
# Return the file name (t stands for tail
)
print -l *.txt(:t)
# Return the file name without the extens
ion (r stands for remove_extension)
print -l *.txt(:t:r)
# Return the extension
print -l *.txt(:e)
# Return the parent folder of the file (h
stands for head)
print -l *.txt(:h)
# Return the parent folder of the parent
print -l *.txt(:h:h)
# Return the parent folder of the first f
ile
print -l *.txt([1]:h)
# Parameter expansion
files=(*.txt)          # store a glob in
a variable
print -l $files
print -l $files(:h)    # this is the synt
ax we saw before
print -l ${files:h}
print -l ${files(:h)}  # don't mix the tw
o, or you'll get an error
print -l ${files:u}    # the :u modifier
makes the text uppercase
# :s modifier
variable="path/aaabcd"
echo ${variable:s/bc/BC/}    # path/aaaBC
d
echo ${variable:s_bc_BC_}    # path/aaaBC
d
echo ${variable:s/\//./}     # path.aaabc
d (escaping the slash \/)
echo ${variable:s_/_._}      # path.aaabc
d (slightly more readable)
echo ${variable:s/a/A/}      # pAth/aaabc
d (only first A is replaced)
echo ${variable:gs/a/A/}     # pAth/AAAbc
d (all A is replaced)
# Split the file name at each underscore
echo ${(s._.)file}
# Join expansion flag, opposite of the sp
lit flag.
array=(a b c d)
echo ${(j.-.)array} # a-b-c-d
# Short if
if [[ ... ]] command
if [[ ... ]] { command ... }
# Short for
for i ( word ... ) command
for i ( word ... ) { command ... }
for i in word ... ; command
# Short while/until
while [[ ... ]] { command ... }
until [[ ... ]] { command ... }
# Use output of command, when using pipe
is not possible
<( command )
# Similar to <( ), but creates temporary
file (instead of FD or FIFO), when
# program needs to seek in output.
=( command )
tldr:zsh
# zsh
# Z SHell, a Bash-compatible command-line
interpreter.
# See also: `bash`, `histexpand`.
# More information: <https://www.zsh.org>
.
# Start an interactive shell session:
zsh
# Execute specific [c]ommands:
zsh -c "echo Hello world"
# Execute a specific script:
zsh path/to/script.zsh
# Check a specific script for syntax erro
rs without executing it:
zsh --no-exec path/to/script.zsh
# Execute specific commands from stdin:
echo Hello world | zsh
# Execute a specific script, printing eac
h command in the script before executing
it:
zsh --xtrace path/to/script.zsh
# Start an interactive shell session in v
erbose mode, printing each command before
executing it:
zsh --verbose
# Execute a specific command inside `zsh`
with disabled glob patterns:
noglob command
[zsh.d]
$
