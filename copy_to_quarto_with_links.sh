#!/bin/bash

# Script to copy all folders with numerical names from the current directory to the "quarto" folder
# convert .ipynb files to .qmd files and fix internal links
# Usage: ./copy_to_quarto_with_links.sh

SOURCE_DIR="."
DEST_DIR="quarto"

# Check if quarto command is available
if ! command -v quarto &> /dev/null; then
    echo "Error: Quarto is not installed or not in PATH. Please install Quarto first."
    echo "Visit: https://quarto.org/docs/get-started/"
    exit 1
fi

# Check if destination directory exists, create if it doesn't
if [ ! -d "$DEST_DIR" ]; then
    echo "Creating destination directory: $DEST_DIR"
    mkdir -p "$DEST_DIR"
fi

# Counters
copied_count=0
converted_count=0
links_fixed=0

echo "Looking for folders with numerical names in current directory..."

# Find and copy folders with numerical names
for folder in "$SOURCE_DIR"/*; do
    # Check if it's a directory and not the quarto directory itself
    if [ -d "$folder" ] && [ "$folder" != "./quarto" ]; then
        # Get just the folder name (basename)
        folder_name=$(basename "$folder")
        
        # Check if folder name is purely numerical (matches pattern of one or more digits)
        if [[ "$folder_name" =~ ^[0-9]+$ ]]; then
            echo "Found numerical folder: $folder_name"
            
            # Copy the folder to quarto directory
            if cp -r "$folder" "$DEST_DIR/"; then
                echo "  ✓ Copied '$folder_name' to '$DEST_DIR/'"
                ((copied_count++))
                
                # Convert .ipynb files to .qmd files in the copied folder
                echo "  Converting .ipynb files to .qmd in $DEST_DIR/$folder_name/"
                
                for notebook in "$DEST_DIR/$folder_name"/*.ipynb; do
                    if [ -f "$notebook" ]; then
                        # Get the base name without extension
                        base_name=$(basename "$notebook" .ipynb)
                        qmd_file="$DEST_DIR/$folder_name/$base_name.qmd"
                        
                        echo "    Converting: $base_name.ipynb → $base_name.qmd"
                        
                        # Use quarto to convert notebook to qmd
                        if quarto convert "$notebook" --output "$qmd_file" 2>/dev/null; then
                            echo "    ✓ Successfully converted $base_name.ipynb"
                            
                            # Fix links in the converted qmd file
                            # Convert .ipynb links to .qmd links
                            link_changes=$(sed -i.bak 's/\.ipynb)/\.qmd)/g; s/\.ipynb#/\.qmd#/g' "$qmd_file" && rm "$qmd_file.bak" 2>/dev/null; echo $?)
                            if [ "$link_changes" -eq 0 ]; then
                                echo "    ✓ Fixed .ipynb links to .qmd links in $base_name.qmd"
                                ((links_fixed++))
                            fi
                            
                            # Remove the original .ipynb file after successful conversion
                            rm "$notebook"
                            echo "    ✓ Removed original $base_name.ipynb file"
                            ((converted_count++))
                        else
                            echo "    ✗ Failed to convert $base_name.ipynb"
                        fi
                    fi
                done
            else
                echo "  ✗ Failed to copy '$folder_name'"
            fi
        fi
    fi
done

# Summary
echo ""
echo "Summary:"
echo "- Source directory: current directory (.)"
echo "- Destination directory: $DEST_DIR"
echo "- Folders copied: $copied_count"
echo "- Notebooks converted: $converted_count"
echo "- Files with links fixed: $links_fixed"

if [ $copied_count -eq 0 ]; then
    echo "No folders with numerical names were found in the current directory."
else
    echo "Successfully copied $copied_count numerical folder(s) to the quarto directory."
    if [ $converted_count -gt 0 ]; then
        echo "Successfully converted $converted_count .ipynb files to .qmd format."
        echo "Automatically converted .ipynb links to .qmd links in converted files."
        echo "Original .ipynb files remain in the source folders, but were removed from quarto subfolders."
    fi
fi
