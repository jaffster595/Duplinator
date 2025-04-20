## Duplinator

A passion project that I'm creating whilst I learn Python.

Duplinator is a small tool which finds any duplicate images within a particular folder by comparing the hashes of every image file within that folder. It returns duplicate image pairs and allows you to delete one of them from within the application. It uses the imagehash package to get hashes for all the images within the specified folder and uses PyQt6 for the GUI.

![image](https://github.com/user-attachments/assets/08f03ab7-a126-456e-b498-aa0e973b3787)

Supported image formats are: 

.png
.jpg
.jpeg
.gif
.bmp
.tiff
.webp

# Installation

Two options:

## OPTION 1 - RUN WITH PYTHON:

1. **Python**: Made using Python 3.10, but any supported version should work fine.

2. **Dependencies**: Install the required Python packages using pip:

   ```bash
   pip install pillow imagehash PyQt6 
   ```
3. Clone this repository then run duplinator.py:

   ```bash
   python duplinatorqt.py
   ```

## OPTION 2 - RUN FROM AN EXECUTABLE:

Head to the releases page and download the most recent standalone portable executable. This has Python and all its dependencies packaged in the .exe file so it should just work.
OR
You can also build this yourself if you so wish:

```bash
pip install pyinstaller
```
Then clone this repository, open a terminal/command prompt in the base directory and use:

```bash
pyinstaller --onefile --add-data "img;img" duplinatorqt.py
```
Head into the /dist/ folder and run your executable file.


## Important

- **Backup Your Data**: Before deleting any files, ensure you back up important images. The deletion process is irreversible, and files are permanently removed from the folder.
   
## Usage

1. **Select Folder**: Click the "Browse" button to choose the folder you want to scan for duplicates.

2. **Adjust Parameters**: Here's some more information on the available parameters:
      - **Hash Size**: Controls the size of the perceptual hash. A larger value increases accuracy but also increases computation time. Default is 8.
      - **Threshold**: The maximum hash difference for two images to be considered duplicates. A lower value means stricter matching. Default is 5. This can be useful if you want to identify images which are similar but not identical.
      - **Include Sub-Folders**: This option will include any subfolders that exist within your search directory. This only goes down one-level, so if you have sub-folders within sub-folders, these won't be included.
      - **Multi-Thread**: Allows you to run multiple hashing threads which massively speeds up the scanning process.
  
        Experiment with these values based on your needs. For example, a lower threshold detects only very similar images, while a higher threshold may include more variations.

3. **Scan Now**: Click the 'Scan Now' button to start scanning, a progress window will appear during the process. Depending upon the number of images in the folder and the speed of your device, this can take a few moments to process. A folder with 100 images takes my machine around 10 seconds to process.

4. **Review Duplicates**: Once the scan completes, duplicate image pairs will be displayed with thumbnails and basic file information (such as size, resolution, creation date etc). Adjust the toggle for images that you no longer want, to get them ready for deletion.

5. **Delete Duplicates**: 
   - Click the "Delete" button to remove the specified images

## Roadmap

**To-Do - Features to add next:**

- ~~Double clicking on a thumbnail will launch the native image application and open the image file from source~~ - DONE
- ~~Replace the radial tick boxes with a slider for left/right image choices. Also add a global left/right slider to toggle the choice on all resulting image pairs~~ - DONE
- ~~Multi-threaded hashing for faster scanning~~ - DONE
- ~~After deleting an image, the image pair should remain in the results box but should be greyed out so that the user knows which images have been actioned already without needing to rescan~~ - DONE
- Add a tick box for 'Save History' which stores scanned folder locations making it easier to revisit common folders (ENABLED BY DEFAULT)
- Add a tick box for 'Use Recycle Bin' so that the user can specify if they want images to be completely deleted or if they should go to the recycle bin (ENABLED BY DEFAULT)
- Ability to choose how many levels of subfolders the application should search through after ticking 'Include subfolders'
- Add sorting options to results page by various characteristics, such as sorting by date to get the oldest images at the top, sorting by largest files first or sort by the most certain duplicates first etc
- Ability to scan an entire drive instead of just a single folder
- Ability to provide a single image file which the application will attempt to locate duplicates of within a particular folder or drive.

  Suggestions are more than welcome.

## How It Works

The application uses the `imagehash` library to compute perceptual hashes of images based on their visual content. These hashes are compared, and if the difference is below the specified threshold, the images are flagged as duplicates. This approach allows the detection of visually similar images, even if they differ in file format, resolution, or have slight modifications.

## Contributing

If you encounter issues or have suggestions for improvements, please open an issue on this GitHub repository. Contributions are welcome.

