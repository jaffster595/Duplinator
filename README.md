```markdown
# Duplicate Image Finder

A small tool (using Python and Tkinter) which finds any duplicate images within a particular folder. It returns any duplicate image pairs and allows you to delete one of them from within the application.

## Features

- Evolving at the moment. TBC

## Requirements

1. **Python**: Made using Python 3.10, but any recent version should work fine.

2. **Dependencies**: Install the required Python packages using pip:

   ```bash
   pip install pillow imagehash
   ```

3. **Tkinter**: Tkinter is usually included with Python. If it’s not installed, you may need to install it separately. For example, on Ubuntu:

   ```bash
   sudo apt-get install python3-tk
   ```

## Usage

1. **Run the Script**: Open a terminal or command prompt, navigate to the directory containing the script, and run:

   ```bash
   python duplicate_image_finder.py
   ```

2. **Select Folder**: Click the "Browse" button to choose the folder you want to scan for duplicates.

3. **Adjust Parameters**: Optionally, modify the hash size and threshold values using the spinbox controls. The defaults are hash size = 8 and threshold = 5.

4. **Find Duplicates**: Click the "Find Duplicates" button to start scanning. A progress window will appear during the process.

5. **Review Duplicates**: Once the scan completes, duplicate image pairs will be displayed with thumbnails and file information (size, resolution, creation date, and modification date). Use the checkboxes to select the images you want to delete.

6. **Delete Duplicates**: 
   - Click the "Delete" button to remove the selected images.
   - Click "Delete and Rescan" to delete the selected images and immediately rescan the folder for any remaining duplicates.

## Parameters

- **Hash Size**: Controls the size of the perceptual hash. A larger value increases accuracy but also increases computation time. Default is 8.
- **Threshold**: The maximum hash difference for two images to be considered duplicates. A lower value means stricter matching. Default is 5.

Experiment with these values based on your needs. For example, a lower threshold detects only very similar images, while a higher threshold may include more variations.

## How It Works

The application uses the `imagehash` library to compute perceptual hashes of images based on their visual content. These hashes are compared, and if the difference is below the specified threshold, the images are flagged as duplicates. This approach allows the detection of visually similar images, even if they differ in file format, resolution, or have slight modifications.

## Notes

- **Supported Formats**: The application scans for images with the following extensions: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp`.
- **Thumbnails**: Thumbnails are generated (resized to 100x100 pixels) for visual comparison.
- **File Information**: Displays size (in KB), resolution, creation date, and modification date to help decide which duplicate to keep.
- **Error Handling**: If an image fails to load or file info cannot be retrieved, an error message will appear in place of the thumbnail or details.

## Important

- **Backup Your Data**: Before deleting any files, ensure you back up important images. The deletion process is irreversible, and files are permanently removed from the folder.

## Contributing

If you encounter issues or have suggestions for improvements, please open an issue on this GitHub repository. Contributions are welcome!


```
