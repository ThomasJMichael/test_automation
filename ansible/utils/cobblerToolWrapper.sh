#!/bin/bash

# Create a temporary file to capture the output
tempfile=$(mktemp)

# Run cobblerTool and redirect its output to the temporary file
/usr/local/bin/cobblerTool "$@" > "$tempfile" 2>&1

# Use the script command to record the output from the temporary file
script -q -c "cat $tempfile"

# Clean up the temporary file
rm -f "$tempfile"
