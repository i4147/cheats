cheat.sheets:elm
# Elm
# Domain-specific programming language for declaratively creating
# web browser-based graphical user interfaces.
# Start Elm REPL
elm repl
# Default compilation
elm make HelloWorld.elm -> index.html
# Custom name
elm make HelloWorld.elm --output hw.js
# Compile multiple files
elm make HelloWorld.elm MyModule.elm --output hw.js
# Compile with warnings
elm make HelloWorld.elm --warn
# Save result to a HTML
elm make HelloWorld.elm --output hw.html
# Install a package
elm package install evancz/elm-html
# See also:
#   Elm language cheat sheets at /elm/
#   list of pages:      /elm/:list
#   learn Elm:          /elm/:learn
#   search in pages:    /elm/~keyword
 tldr:elm
# elm
# Compile and run Elm source files.
# More information: <https://elm-lang.org>.
# Initialize an Elm project, generates an elm.json file:
elm init
# Start interactive Elm shell:
elm repl
# Compile an Elm file, output the result to an `index.html` file:
elm make source
# Compile an Elm file, output the result to a JavaScript file:
elm make source --output=destination.js
# Start local web server that compiles Elm files on page load:
elm reactor
# Install Elm package from https://package.elm-lang.org:
elm install author/package
