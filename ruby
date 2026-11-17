# ruby
# Interpreter of object-oriented scripting language Ruby
# Invoke Ruby; a dynamic, reflective, object-oriented, general-purpose
# programming language; from the command line to run the provided script.
ruby foo.rb
# Execute Ruby code directly from the command-line.
ruby -e 'puts "Hello world"'
# The `-n` switch allows Ruby to execute code within a `while gets` loop.
ruby -ne 'puts $_' file.txt
# Beware that with the `-n` switch, `$_` contains newline character at the end.
# With the addition of the `-l` switch, each line read has the aforementioned
# newline character removed.
ls | ruby -lne 'File.rename($_, $_.upcase)'
# The `-p` switch acts similarly to `-n`, in that it loops over each of the
# lines in the input, after your code has finished; it always prints the value
# of `$_`.
#
# The following example replaces `e` with `a`.
echo "eats, shoots, and leaves" | ruby -pe '$_.gsub!("e", "a")'
# BEGIN block executed before the loop.
echo "foo\nbar\nbaz" | ruby -ne 'BEGIN { i = 1 }; puts "#{i} #{$_}"; i += 1'
# See also: `gem`, `bundler`, `rake`, `irb`, `ri`.
# Execute a single Ruby command in the command-line:
ruby -e "command"
# Check for syntax errors on a given Ruby script:
ruby -c path/to/script.rb
# Start the built-in HTTP server on port 8080 in the current directory:
ruby -run -e httpd
# Locally execute a Ruby binary without installing the required library it depends on:
ruby -I path/to/library_folder -r library_require_name path/to/bin_folder/bin_name
