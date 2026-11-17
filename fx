# fx
# Command-line JSON processing tool.
# Parse JSON from a file and pretty-print it
cat file.json | fx
# Extract a specific field from JSON
cat file.json | fx .fieldName
# Chain multiple operations to transform JSON data
cat file.json | fx .fieldName | fx 'sortBy(["key"])'
# Use fx to filter array elements
cat file.json | fx 'filter(e => e.key >= 10)'
# Transform JSON objects
cat file.json | fx 'map(e => ({ id: e.id, value: e.value }))'
# Convert JSON to CSV format
cat file.json | fx 'map(e => [e.id, e.value].join(","))' | fx 'join("\n")'
# Handle JSON data passed directly
echo '{"key": "value"}' | fx .key
# Use fx with an inline JSON array
echo '[{"key": 1}, {"key": 2}]' | fx 'filter(e => e.key > 1)'
# Use JavaScript expressions in fx
cat file.json | fx 'e => ({ ...e, newKey: e.oldKey * 2 })'
# Extract nested fields from JSON
cat file.json | fx '.parent.child'
# Count elements in a JSON array
cat file.json | fx 'length'
# Convert JSON array to a comma-separated list
cat file.json | fx 'join(",")'
# View a JSON file interactively:
fx path/to/file.json
# Open JSON data from a URL:
curl url | fx
# Filter JSON using JavaScript-like expressions:
fx path/to/file.json .name
# Parse a TOML input file into JSON:
fx --toml path/to/file.toml
# Parse a YAML input file into JSON:
fx --yaml path/to/file.yaml
