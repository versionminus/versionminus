#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Paths to the Copilot prompt files
PROMPT_FILE="$SCRIPT_DIR/copilot-system-prompt.md"
CODING_STANDARDS_FILE="$SCRIPT_DIR/copilot-coding-standards.md"

# Check if the files exist
if [ ! -f "$PROMPT_FILE" ]; then
  echo "Error: System prompt file not found at $PROMPT_FILE"
  exit 1
fi

if [ ! -f "$CODING_STANDARDS_FILE" ]; then
  echo "Error: Coding standards file not found at $CODING_STANDARDS_FILE"
  exit 1
fi

# Display instructions on how to use the system prompt
echo "=================================================="
echo "GitHub Copilot System Prompt and Coding Standards"
echo "=================================================="
echo
echo "Copy and paste this into your Copilot Chat window:"
echo
echo "/system Please read and follow the instructions in the files at $PROMPT_FILE and $CODING_STANDARDS_FILE throughout our conversation."
echo
echo "This will instruct Copilot to:"
echo "1. Ask for permission before staging and committing changes after task completion"
echo "2. Follow the project's coding standards for utility functions, hardcoded values, and centralization"
echo "=================================================="
