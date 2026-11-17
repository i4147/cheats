# hx
# This command is an alias of `helix`.
# View documentation for the original command:
tldr helix
# Open a file:
hx path/to/file
# Open files and show them one next each other:
hx --vsplit path/to/file1 path/to/file2 ...
# Show the tutorial to learn Helix (or access it within Helix by pressing `<Esc>` and typing `<:>tutor<Enter>`):
hx --tutor
# Change the Helix theme:
<:>theme theme_name
# Save and quit:
<:>wq<Enter>
# Force-quit without saving:
<:>q!<Enter>
# Search for a pattern in the file (press `<n>`/`<N>` to go to next/previous match):
</>search_pattern<Enter>
