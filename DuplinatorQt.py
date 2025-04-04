import os
import sys
import imagehash
from PIL import Image
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider, QCheckBox, QScrollArea, QProgressDialog, QMessageBox, QApplication, QWidget
from PyQt6.QtCore import QThread, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QFont, QImage, QPixmap, QIcon, QPalette, QColor, QDesktopServices
from datetime import datetime

# Helper function to get the correct path to resources
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

# Function to apply dark theme
def apply_dark_theme(app):
    # Set the style to Fusion
    app.setStyle("Fusion")

    # Defines the colour scheme via PyQt6
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

    # Apply the colour scheme
    app.setPalette(dark_palette)

# Function to find duplicate images
def find_duplicate_images(folder_path, hash_size, threshold, include_subfolders=False, included_extensions=None):
    included_extensions = tuple(included_extensions)
    image_hashes = {}
    duplicates = []
    if include_subfolders:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(included_extensions):
                    filepath = os.path.join(root, file)
                    try:
                        with Image.open(filepath) as img:
                            image_hash = imagehash.phash(img, hash_size=hash_size)
                            for other_filepath, other_hash in image_hashes.items():
                                if (image_hash - other_hash) <= threshold:
                                    duplicates.append((other_filepath, filepath))
                            image_hashes[filepath] = image_hash
                    except Exception as e:
                        print(f"Error processing {filepath}: {e}")
    else:
        for file in os.listdir(folder_path):
            if file.lower().endswith(included_extensions):
                filepath = os.path.join(folder_path, file)
                try:
                    with Image.open(filepath) as img:
                        image_hash = imagehash.phash(img, hash_size=hash_size)
                        for other_filepath, other_hash in image_hashes.items():
                            if (image_hash - other_hash) <= threshold:
                                duplicates.append((other_filepath, filepath))
                        image_hashes[filepath] = image_hash
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    return duplicates

# ScanThread class
class ScanThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, folder_path, hash_size, threshold, include_subfolders, included_extensions):
        super().__init__()
        self.folder_path = folder_path
        self.hash_size = hash_size
        self.threshold = threshold
        self.include_subfolders = include_subfolders
        self.included_extensions = included_extensions

    def run(self):
        try:
            duplicates = find_duplicate_images(self.folder_path, self.hash_size, self.threshold, self.include_subfolders, self.included_extensions)
            self.finished.emit(duplicates)
        except Exception as e:
            self.finished.emit(e)
            
#Make the thumbnail view clickable
class ClickableLabel(QLabel):
    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.show_large_image()

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.open_image()

    def show_large_image(self):
        image = QImage(self.filepath)
        if not image.isNull():
            large_pixmap = QPixmap.fromImage(image).scaled(
                400, 400,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation
            )
            popup = ImagePopup(large_pixmap)
            popup.show()

    def open_image(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.filepath))

#Larger preview popout functionality      
class ImagePopup(QWidget):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent, QtCore.Qt.WindowType.Popup)
        layout = QVBoxLayout(self)
        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)
        self.setGeometry(0, 0, pixmap.width(), pixmap.height())
        # Center on screen
        screen_geometry = QApplication.primaryScreen().geometry()
        self.move(screen_geometry.center() - self.rect().center())

    def mousePressEvent(self, event):
        self.close()
        
# Main application window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Duplinator")
        self.thumbnails = {}
        self.pairs = []
        self.setup_ui()
        self.resize(800, 600)

    def setup_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Folder selection frame
        folder_frame = QFrame()
        folder_layout = QHBoxLayout(folder_frame)
        folder_label = QLabel("Folder:")
        self.folder_entry = QLineEdit()
        self.folder_entry.setToolTip("Use the browse button or enter a complete directory path")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_entry)
        folder_layout.addWidget(browse_button)
        main_layout.addWidget(folder_frame)

        # File types frame
        file_types_frame = QFrame()
        file_types_layout = QHBoxLayout(file_types_frame)
        file_types_label = QLabel("File Types:")
        file_types_layout.addWidget(file_types_label)
        self.file_type_checkboxes = {}
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
            checkbox = QCheckBox(ext)
            checkbox.setChecked(True)
            file_types_layout.addWidget(checkbox)
            self.file_type_checkboxes[ext] = checkbox
        file_types_layout.addStretch()
        main_layout.addWidget(file_types_frame)

        # Parameters frame
        params_frame = QFrame()
        params_layout = QVBoxLayout(params_frame)
        hash_size_layout = QHBoxLayout()
        hash_size_label = QLabel("Hash Size:")
        self.hash_size_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.hash_size_slider.setRange(4, 32)
        self.hash_size_slider.setValue(8)
        self.hash_size_slider.setToolTip("Controls the size of the generated hash. A larger value increases accuracy but also increases computation time. Default is 8.")
        self.hash_size_value_label = QLabel("8")
        hash_size_layout.addWidget(hash_size_label)
        hash_size_layout.addWidget(self.hash_size_slider)
        hash_size_layout.addWidget(self.hash_size_value_label)
        params_layout.addLayout(hash_size_layout)
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Threshold:")
        self.threshold_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 20)
        self.threshold_slider.setValue(5)
        self.threshold_slider.setToolTip("The threshold for two images to be considered duplicates. A lower value means stricter matching and less results. Default is 5.")
        self.threshold_value_label = QLabel("5")
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_value_label)
        params_layout.addLayout(threshold_layout)
        self.include_subfolders_checkbox = QCheckBox("Include subfolders")
        self.include_subfolders_checkbox.setToolTip("Specifies if any subfolders within the specified folder should be included in the search.")
        params_layout.addWidget(self.include_subfolders_checkbox)
        main_layout.addWidget(params_frame)

        self.hash_size_slider.valueChanged.connect(lambda: self.hash_size_value_label.setText(str(self.hash_size_slider.value())))
        self.threshold_slider.valueChanged.connect(lambda: self.threshold_value_label.setText(str(self.threshold_slider.value())))

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.inner_widget = QtWidgets.QWidget()
        self.inner_layout = QVBoxLayout(self.inner_widget)
        self.scroll_area.setWidget(self.inner_widget)
        main_layout.addWidget(self.scroll_area)

        # New bottom layout with icon buttons
        bottom_layout = QHBoxLayout()
        
        bottom_layout.addStretch(1)

        # Scan button with icon
        self.start_button = QPushButton()
        scan_icon = QIcon(resource_path("img/SCAN128.png"))
        self.start_button.setIcon(scan_icon)
        self.start_button.setIconSize(QSize(90, 90))
        self.start_button.setToolTip("Start scanning the specified folder for duplicate images")
        self.start_button.clicked.connect(self.run_scan)
        bottom_layout.addWidget(self.start_button)

        bottom_layout.addStretch(1)

        # Delete button with icon
        self.delete_button = QPushButton()
        delete_icon = QIcon(resource_path("img/DELETE128.png"))
        self.delete_button.setIcon(delete_icon)
        self.delete_button.setIconSize(QSize(90, 90))
        self.delete_button.setToolTip("Delete selected files")
        self.delete_button.clicked.connect(self.delete_selected)
        self.delete_button.setEnabled(False)
        bottom_layout.addWidget(self.delete_button)
        
        bottom_layout.addStretch(1)

        main_layout.addLayout(bottom_layout)

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def select_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_entry.setText(folder)

    def run_scan(self):
        folder_path = self.folder_entry.text()
        if not folder_path or not os.path.isdir(folder_path):
            QMessageBox.critical(self, "Error", "Please select a valid folder.")
            return
        included_extensions = [ext for ext in self.file_type_checkboxes if self.file_type_checkboxes[ext].isChecked()]
        if not included_extensions:
            QMessageBox.critical(self, "Error", "No file types selected.")
            return
        self.thumbnails.clear()
        for widget in self.inner_widget.findChildren(QtWidgets.QWidget):
            widget.deleteLater()
        self.pairs = []
        self.start_button.setEnabled(True)
        self.status_bar.showMessage("Scanning...")
        self.progress_dialog = QProgressDialog("Scanning for duplicates...", None, 0, 0, self)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()
        hash_size = self.hash_size_slider.value()
        threshold = self.threshold_slider.value()
        include_subfolders = self.include_subfolders_checkbox.isChecked()
        self.scan_thread = ScanThread(folder_path, hash_size, threshold, include_subfolders, included_extensions)
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.start()

    def on_scan_finished(self, result):
        self.progress_dialog.hide()
        self.start_button.setEnabled(True)
        self.status_bar.showMessage("Done.")
        if isinstance(result, Exception):
            QMessageBox.critical(self, "Error", str(result))
        else:
            self.display_results(result)

    def display_results(self, duplicate_pairs):
        self.pairs = []
        if not duplicate_pairs:
            no_duplicates_label = QLabel("No duplicate images found.")
            self.inner_layout.addWidget(no_duplicates_label)
        else:
            folder_path = self.folder_entry.text()
            for i, (filepath1, filepath2) in enumerate(duplicate_pairs):
                if i > 0:
                    separator = QFrame()
                    separator.setFrameShape(QFrame.Shape.HLine)
                    self.inner_layout.addWidget(separator)
                pair_layout = QHBoxLayout()
                try:
                    stat1 = os.stat(filepath1)
                    size_kb1 = stat1.st_size / 1024
                    created1 = datetime.fromtimestamp(stat1.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    modified1 = datetime.fromtimestamp(stat1.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    with Image.open(filepath1) as img1:
                        width1, height1 = img1.size
                        if filepath1 not in self.thumbnails:
                            max_size = 150
                            if width1 > height1:
                                new_width1 = max_size
                                new_height1 = int((height1 / width1) * max_size)
                            else:
                                new_height1 = max_size
                                new_width1 = int((width1 / height1) * max_size)
                            thumbnail1 = img1.resize((new_width1, new_height1), Image.Resampling.LANCZOS).convert("RGB")
                            qt_img1 = QImage(thumbnail1.tobytes(), thumbnail1.width, thumbnail1.height, thumbnail1.width * 3, QImage.Format.Format_RGB888)
                            self.thumbnails[filepath1] = QPixmap.fromImage(qt_img1)
                except Exception as e:
                    print(f"Error processing {filepath1}: {e}")
                    size_kb1, width1, height1, created1, modified1 = None, 0, 0, "Unknown", "Unknown"
                    self.thumbnails[filepath1] = None
                left_frame = QFrame()
                left_layout = QVBoxLayout(left_frame)
                rel_path1 = os.path.relpath(filepath1, folder_path)
                if size_kb1 is not None:
                    thumbnail_label1 = ClickableLabel(filepath1)
                    if self.thumbnails[filepath1]:
                        thumbnail_label1.setPixmap(self.thumbnails[filepath1])
                    else:
                        thumbnail_label1.setText("[Thumbnail Error]")
                    left_layout.addWidget(thumbnail_label1)
                    info_text1 = f"{rel_path1}\nSize: {size_kb1:.2f} KB\nRes: {width1}x{height1}\nCreated: {created1}\nModified: {modified1}"
                    info_label1 = QLabel(info_text1)
                    info_label1.setToolTip(filepath1)
                    left_layout.addWidget(info_label1)
                else:
                    error_label1 = QLabel(f"{rel_path1}\n[Error retrieving info]")
                    left_layout.addWidget(error_label1)
                pair_layout.addWidget(left_frame)
                choice_frame = QFrame()
                choice_layout = QVBoxLayout(choice_frame)
                choice_label = QLabel("Delete which image?")
                choice_layout.addWidget(choice_label)
                button_group = QtWidgets.QButtonGroup()
                left_radio = QtWidgets.QRadioButton("Left")
                right_radio = QtWidgets.QRadioButton("Right")
                neither_radio = QtWidgets.QRadioButton("Neither")
                button_group.addButton(left_radio, 0)
                button_group.addButton(right_radio, 1)
                button_group.addButton(neither_radio, 2)
                neither_radio.setChecked(True)
                choice_layout.addWidget(left_radio)
                choice_layout.addWidget(right_radio)
                choice_layout.addWidget(neither_radio)
                pair_layout.addWidget(choice_frame)
                try:
                    stat2 = os.stat(filepath2)
                    size_kb2 = stat2.st_size / 1024
                    created2 = datetime.fromtimestamp(stat2.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    modified2 = datetime.fromtimestamp(stat2.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    with Image.open(filepath2) as img2:
                        width2, height2 = img2.size
                        if filepath2 not in self.thumbnails:
                            max_size = 150
                            if width2 > height2:
                                new_width2 = max_size
                                new_height2 = int((height2 / width2) * max_size)
                            else:
                                new_height2 = max_size
                                new_width2 = int((width2 / height2) * max_size)
                            thumbnail2 = img2.resize((new_width2, new_height2), Image.Resampling.LANCZOS).convert("RGB")
                            qt_img2 = QImage(thumbnail2.tobytes(), thumbnail2.width, thumbnail2.height, thumbnail2.width * 3, QImage.Format.Format_RGB888)
                            self.thumbnails[filepath2] = QPixmap.fromImage(qt_img2)
                except Exception as e:
                    print(f"Error processing {filepath2}: {e}")
                    size_kb2, width2, height2, created2, modified2 = None, 0, 0, "Unknown", "Unknown"
                    self.thumbnails[filepath2] = None
                right_frame = QFrame()
                right_layout = QVBoxLayout(right_frame)
                rel_path2 = os.path.relpath(filepath2, folder_path)
                if size_kb2 is not None:
                    thumbnail_label2 = ClickableLabel(filepath2)
                    if self.thumbnails[filepath2]:
                        thumbnail_label2.setPixmap(self.thumbnails[filepath2])
                    else:
                        thumbnail_label2.setText("[Thumbnail Error]")
                    right_layout.addWidget(thumbnail_label2)
                    info_text2 = f"{rel_path2}\nSize: {size_kb2:.2f} KB\nRes: {width2}x{height2}\nCreated: {created2}\nModified: {modified2}"
                    info_label2 = QLabel(info_text2)
                    info_label2.setToolTip(filepath2)
                    right_layout.addWidget(info_label2)
                else:
                    error_label2 = QLabel(f"{rel_path2}\n[Error retrieving info]")
                    right_layout.addWidget(error_label2)
                pair_layout.addWidget(right_frame)
                self.inner_layout.addLayout(pair_layout)
                self.pairs.append({"file1": filepath1, "file2": filepath2, "button_group": button_group})
                button_group.buttonClicked.connect(self.update_button_states)
        self.update_button_states()

    def update_button_states(self):
        any_selected = any(pair["button_group"].checkedId() in [0, 1] for pair in self.pairs)
        self.delete_button.setEnabled(any_selected)

    def delete_selected(self):
        to_delete = set()
        for pair in self.pairs:
            checked_id = pair["button_group"].checkedId()
            if checked_id == 0:
                to_delete.add(pair["file1"])
            elif checked_id == 1:
                to_delete.add(pair["file2"])
        if not to_delete:
            QMessageBox.information(self, "Info", "No images selected for deletion.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete {len(to_delete)} image(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            for file in to_delete:
                try:
                    os.remove(file)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete {file}: {e}")
            QMessageBox.information(self, "Info", "Selected images deleted.")

# Run the application
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    apply_dark_theme(app)
    window = MainWindow()
    window.show()
    app.exec()
    
    
 