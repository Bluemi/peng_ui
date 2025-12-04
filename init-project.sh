#!/bin/bash

# Initialize project
# - replace PROJECT_NAME in pyproject.toml
# - rename lib dir

# --- Configuration ---
# The string to be searched for and replaced.
PLACEHOLDER="PROJECT_NAME"

# A space-separated list of files where the replacement should occur.
# IMPORTANT: Adjust this list to match the files in your project.
FILES_TO_PROCESS=(
    "README.md"
    "pyproject.toml"
    "run.sh"
)

# --- Script Logic ---

# Check if the replacement argument is provided
if [ -z "$1" ]; then
    echo "Error: Missing replacement string." >&2
    echo "Usage: $0 <new_project_name>" >&2
    exit 1
fi

# Store the replacement string
NEW_NAME="$1"

echo "Initialize project \"${NEW_NAME}\""

# Iterate over the list of files
for FILE in "${FILES_TO_PROCESS[@]}"; do
    # Check if the file exists before attempting to modify it
    if [ -f "$FILE" ]; then
        echo "Processing file: $FILE"

        # Use sed to perform the in-place replacement.
        # The 'i' flag modifies the file in place. We use a non-standard
        # delimiter (e.g., '|') instead of '/' to avoid issues if the
        # replacement string ($NEW_NAME) contains slashes (e.g., 'path/to/project').
        # The 'g' flag ensures all occurrences on a line are replaced (global).
        sed -i "s|${PLACEHOLDER}|${NEW_NAME}|g" "$FILE"
        
        # Check if sed was successful
        if [ $? -eq 0 ]; then
            echo "- rewrite $FILE."
        else
            echo "Warning: sed failed for $FILE"
        fi
    else
        echo "Warning: File not found: $FILE (Skipping)"
    fi
done

echo "renaming ./project_name to \"$NEW_NAME\""
git mv project_name "$NEW_NAME"

# add venv
echo "creating venv"
python -m venv venv
echo ""
echo "please run"
echo "    . venv/bin/activate"

echo "removing this script"
rm init-project.sh

echo "happy coding :)"
