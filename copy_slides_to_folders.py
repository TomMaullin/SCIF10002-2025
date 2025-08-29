import os
import shutil
import re

# Define the root and slides directory
root_dir = os.path.dirname(os.path.abspath(__file__))
slides_dir = os.path.join(root_dir, 'quarto', '_site', 'slides')

# List all html files in the slides directory
for filename in os.listdir(slides_dir):
    # Match files with a numerical prefix and underscore, e.g., 07_intro_numpy_slides.html or 07_intro_numpy_slides.pptx
    match = re.match(r'^(\d+)_([\w\-]+)\.(html|pptx)$', filename)
    if match:
        num_prefix = match.group(1)
        rest = match.group(2)
        ext = match.group(3)
        # Prepend 'slides_' and remove the numerical prefix and underscore
        new_filename = f"slides_{rest}.{ext}"
        # Destination folder (e.g., 07/)
        dest_folder = os.path.join(root_dir, num_prefix)
        os.makedirs(dest_folder, exist_ok=True)
        src_path = os.path.join(slides_dir, filename)
        dest_path = os.path.join(dest_folder, new_filename)
        shutil.copy2(src_path, dest_path)
        print(f"Copied {src_path} to {dest_path}")
