#!/bin/bash

# Enhanced script to convert QMD slides to PPTX with better compatibility
# Usage: ./qmd_to_pptx_enhanced.sh input.qmd

# Check if input file is provided
if [ $# -eq 0 ]; then
    echo "Error: No input file provided"
    echo "Usage: $0 <input.qmd>"
    exit 1
fi

# Check if input file exists
INPUT_FILE="$1"
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' does not exist"
    exit 1
fi

# Check if input file has .qmd extension
if [[ "$INPUT_FILE" != *.qmd ]]; then
    echo "Error: Input file must have .qmd extension"
    exit 1
fi

# Get the base filename without extension
BASE_NAME=$(basename "$INPUT_FILE" .qmd)
TEMP_FILE="${BASE_NAME}_pptx_temp.qmd"
OUTPUT_FILE="${BASE_NAME}.pptx"

echo "Processing: $INPUT_FILE"
echo "Creating PowerPoint-compatible temporary file: $TEMP_FILE"

# Create temporary file with PowerPoint-friendly modifications
# Step 1: Basic cleanup - remove incremental separators only
sed '/^\. \. \.$/d' "$INPUT_FILE" > "$TEMP_FILE"

# Step 2: Fix the error-causing code block by commenting it out
sed -i '' 's/^result = arr3 + arr4$/# result = arr3 + arr4  # This would cause an error - incompatible shapes/' "$TEMP_FILE"

# Step 3: Remove column layout markup that doesn't work in PowerPoint
sed -i '' '/^::::/d' "$TEMP_FILE"
sed -i '' '/^:::/d' "$TEMP_FILE"

# Step 4: Remove footnotes that don't convert well
sed -i '' 's/\^\[[^]]*\]//g' "$TEMP_FILE"

# Check if temporary file was created successfully
if [ ! -f "$TEMP_FILE" ]; then
    echo "Error: Failed to create temporary file"
    exit 1
fi

echo "Rendering to PowerPoint: $OUTPUT_FILE"

# Render to PPTX using quarto
if quarto render "$TEMP_FILE" --to pptx; then
    echo "Successfully rendered: $OUTPUT_FILE"
else
    echo "Error: Failed to render PPTX"
    rm -f "$TEMP_FILE"
    exit 1
fi

# Clean up temporary file
echo "Cleaning up temporary file: $TEMP_FILE"
rm -f "$TEMP_FILE"

echo "Done! Output file: $OUTPUT_FILE"
echo "Note: Some LaTeX math expressions may not display perfectly in PowerPoint"
