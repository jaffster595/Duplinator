## Duplinator

![image](https://github.com/user-attachments/assets/320ea32a-df77-4cf4-a3c3-f444e91d4acc)

A small tool which finds any duplicate images within a particular folder by comparing the hashes of every image file within a folder. It returns duplicate image pairs and allows you to delete one of them from within the application.
Supported image formats are: 

.png
.jpg
.jpeg
.gif
.bmp
.tiff
.webp

## Features

TBC

## Installation

Two options:

# OPTION 1 - RUN FROM AN EXECUTABLE:

Head to the releases page and download the standalone portable executable. This has Python and all its dependencies packaged in the .exe file so it just works without any configuration work.
You can also build this yourself if you like:

```bash
pip install pyinstaller
```
Then clone this repository, open a terminal/command prompt in the base directory and use:

```bash
pyinstaller --onefile --add-data "img;img" duplinatorqt.py
```
Head into the /dist/ folder and run your executable file.

# OPTION 2 - RUN WITH PYTHON:

1. **Python**: Made using Python 3.10, but any recent version should work fine.

2. **Dependencies**: Install the required Python packages using pip:

   ```bash
   pip install pillow imagehash PyQt6 
   ```
3. Clone this repository then run duplinator.py:

   ```bash
   python duplinatorqt.py
   ```

## Important

- **Backup Your Data**: Before deleting any files, ensure you back up important images. The deletion process is irreversible, and files are permanently removed from the folder.
   
## Usage

1. **Select Folder**: Click the "Browse" button to choose the folder you want to scan for duplicates.

2. **Adjust Parameters**: Here's some more information on the available parameters:
      - **Hash Size**: Controls the size of the perceptual hash. A larger value increases accuracy but also increases computation time. Default is 8.
      - **Threshold**: The maximum hash difference for two images to be considered duplicates. A lower value means stricter matching. Default is 5. This can be useful if you want to identify images which are similar but not identical.
      - **Include Sub-Folders**: This option will include any subfolders that exist within your search directory. This only goes down one-level, so if you have sub-folders within sub-folders, these won't be included.
  
        Experiment with these values based on your needs. For example, a lower threshold detects only very similar images, while a higher threshold may include more variations.

3. **Scan Now**: Click the 'Scan Now' button to start scanning, a progress window will appear during the process. Depending upon the number of images in the folder and the speed of your device, this can take a few moments to process. A folder with 100 images takes my machine around 10 seconds to process.

4. **Review Duplicates**: Once the scan completes, duplicate image pairs will be displayed with thumbnails and basic file information (such as size, resolution, creation date etc). Adjust the toggle for images that you no longer want, to get them ready for deletion.

5. **Delete Duplicates**: 
   - Click the "Delete" button to remove the specified images


## How It Works

The application uses the `imagehash` library to compute perceptual hashes of images based on their visual content. These hashes are compared, and if the difference is below the specified threshold, the images are flagged as duplicates. This approach allows the detection of visually similar images, even if they differ in file format, resolution, or have slight modifications.

## Notes

- **Supported Formats**: The application scans for images with the following extensions: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp`.
- **Thumbnails**: Thumbnails are generated (resized to 100x100 pixels) for visual comparison.
- **File Information**: Displays size (in KB), resolution, creation date, and modification date to help decide which duplicate to keep.
- **Error Handling**: If an image fails to load or file info cannot be retrieved, an error message will appear in place of the thumbnail or details.

## Contributing

If you encounter issues or have suggestions for improvements, please open an issue on this GitHub repository. Contributions are welcome!


```
