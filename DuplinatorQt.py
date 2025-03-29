import os
import imagehash
from PIL import Image
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider, QCheckBox, QScrollArea, QProgressDialog, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont, QImage, QPixmap
from datetime import datetime

# Function to get file information
def get_file_info(filepath):
    try:
        stat = os.stat(filepath)
        size_kb = stat.st_size / 1024
        with Image.open(filepath) as img:
            resolution = img.size
        created = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        return size_kb, resolution, created, modified
    except Exception:
        return None, (0, 0), "Unknown", "Unknown"

# Function to find duplicate images
def find_duplicate_images(folder_path, hash_size, threshold, include_subfolders=False):
    image_hashes = {}
    duplicates = []
    if include_subfolders:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
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
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
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

# Thread class for scanning
class ScanThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, folder_path, hash_size, threshold, include_subfolders):
        super().__init__()
        self.folder_path = folder_path
        self.hash_size = hash_size
        self.threshold = threshold
        self.include_subfolders = include_subfolders

    def run(self):
        try:
            duplicates = find_duplicate_images(self.folder_path, self.hash_size, self.threshold, self.include_subfolders)
            self.finished.emit(duplicates)
        except Exception as e:
            self.finished.emit(e)

# Main application window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Duplinator")
        self.thumbnails = {}  # Store thumbnails to reuse
        self.pairs = []  # Store duplicate pairs and their button groups
        self.setup_ui()

    def setup_ui(self):
        # Central widget and main layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Folder selection frame
        folder_frame = QFrame()
        folder_layout = QHBoxLayout(folder_frame)
        folder_label = QLabel("Folder:")
        self.folder_entry = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_entry)
        folder_layout.addWidget(browse_button)
        main_layout.addWidget(folder_frame)

        # Parameters frame with sliders and checkbox
        params_frame = QFrame()
        params_layout = QVBoxLayout(params_frame)

        # Hash Size slider
        hash_size_layout = QHBoxLayout()
        hash_size_label = QLabel("Hash Size:")
        self.hash_size_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.hash_size_slider.setRange(4, 32)
        self.hash_size_slider.setValue(8)
        self.hash_size_value_label = QLabel("8")
        hash_size_layout.addWidget(hash_size_label)
        hash_size_layout.addWidget(self.hash_size_slider)
        hash_size_layout.addWidget(self.hash_size_value_label)
        params_layout.addLayout(hash_size_layout)

        # Threshold slider
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Threshold:")
        self.threshold_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 20)
        self.threshold_slider.setValue(5)
        self.threshold_value_label = QLabel("5")
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_value_label)
        params_layout.addLayout(threshold_layout)

        # Include subfolders checkbox
        self.include_subfolders_checkbox = QCheckBox("Include subfolders")
        params_layout.addWidget(self.include_subfolders_checkbox)

        main_layout.addWidget(params_frame)

        # Connect sliders to update value labels
        self.hash_size_slider.valueChanged.connect(lambda: self.hash_size_value_label.setText(str(self.hash_size_slider.value())))
        self.threshold_slider.valueChanged.connect(lambda: self.threshold_value_label.setText(str(self.threshold_slider.value())))

        # Start Scan button with larger font
        self.start_button = QPushButton("Start Scan")
        self.start_button.setFont(QFont("Arial", 14))
        self.start_button.clicked.connect(self.run_scan)
        main_layout.addWidget(self.start_button)

        # Scroll area for results
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.inner_widget = QtWidgets.QWidget()
        self.inner_layout = QVBoxLayout(self.inner_widget)
        self.scroll_area.setWidget(self.inner_widget)
        main_layout.addWidget(self.scroll_area)

        # Delete buttons frame
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_selected)
        self.delete_button.setEnabled(False)
        self.delete_rescan_button = QPushButton("Delete and Rescan")
        self.delete_rescan_button.clicked.connect(self.delete_and_rescan)
        self.delete_rescan_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.delete_rescan_button)
        main_layout.addWidget(button_frame)

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

        # Clear previous data
        self.thumbnails.clear()
        for widget in self.inner_widget.findChildren(QtWidgets.QWidget):
            widget.deleteLater()
        self.pairs = []
        self.start_button.setEnabled(False)
        self.status_bar.showMessage("Scanning...")

        # Show progress dialog
        self.progress_dialog = QProgressDialog("Scanning for duplicates...", None, 0, 0, self)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()

        # Start scanning thread
        hash_size = self.hash_size_slider.value()
        threshold = self.threshold_slider.value()
        include_subfolders = self.include_subfolders_checkbox.isChecked()
        self.scan_thread = ScanThread(folder_path, hash_size, threshold, include_subfolders)
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

                # Left image
                left_frame = QFrame()
                left_layout = QVBoxLayout(left_frame)
                size1, (width1, height1), created1, modified1 = get_file_info(filepath1)
                rel_path1 = os.path.relpath(filepath1, folder_path)
                if size1 is not None:
                    if filepath1 not in self.thumbnails:
                        try:
                            pil_img = Image.open(filepath1).resize((100, 100), Image.Resampling.LANCZOS).convert("RGB")
                            qt_img = QImage(pil_img.tobytes(), pil_img.width, pil_img.height, pil_img.width * 3, QImage.Format.Format_RGB888)
                            self.thumbnails[filepath1] = QPixmap.fromImage(qt_img)
                        except Exception as e:
                            print(f"Error loading thumbnail for {filepath1}: {e}")
                            self.thumbnails[filepath1] = None
                    thumbnail_label = QLabel()
                    if self.thumbnails[filepath1]:
                        thumbnail_label.setPixmap(self.thumbnails[filepath1])
                    else:
                        thumbnail_label.setText("[Thumbnail Error]")
                    left_layout.addWidget(thumbnail_label)
                    info_text1 = f"{rel_path1}\nSize: {size1:.2f} KB\nRes: {width1}x{height1}\nCreated: {created1}\nModified: {modified1}"
                    info_label1 = QLabel(info_text1)
                    left_layout.addWidget(info_label1)
                else:
                    error_label = QLabel(f"{rel_path1}\n[Error retrieving info]")
                    left_layout.addWidget(error_label)
                pair_layout.addWidget(left_frame)

                # Choice frame
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

                # Right image
                right_frame = QFrame()
                right_layout = QVBoxLayout(right_frame)
                size2, (width2, height2), created2, modified2 = get_file_info(filepath2)
                rel_path2 = os.path.relpath(filepath2, folder_path)
                if size2 is not None:
                    if filepath2 not in self.thumbnails:
                        try:
                            pil_img = Image.open(filepath2).resize((100, 100), Image.Resampling.LANCZOS).convert("RGB")
                            qt_img = QImage(pil_img.tobytes(), pil_img.width, pil_img.height, pil_img.width * 3, QImage.Format.Format_RGB888)
                            self.thumbnails[filepath2] = QPixmap.fromImage(qt_img)
                        except Exception as e:
                            print(f"Error loading thumbnail for {filepath2}: {e}")
                            self.thumbnails[filepath2] = None
                    thumbnail_label = QLabel()
                    if self.thumbnails[filepath2]:
                        thumbnail_label.setPixmap(self.thumbnails[filepath2])
                    else:
                        thumbnail_label.setText("[Thumbnail Error]")
                    right_layout.addWidget(thumbnail_label)
                    info_text2 = f"{rel_path2}\nSize: {size2:.2f} KB\nRes: {width2}x{height2}\nCreated: {created2}\nModified: {modified2}"
                    info_label2 = QLabel(info_text2)
                    right_layout.addWidget(info_label2)
                else:
                    error_label = QLabel(f"{rel_path2}\n[Error retrieving info]")
                    right_layout.addWidget(error_label)
                pair_layout.addWidget(right_frame)

                self.inner_layout.addLayout(pair_layout)
                self.pairs.append({"file1": filepath1, "file2": filepath2, "button_group": button_group})
                button_group.buttonClicked.connect(self.update_button_states)

        self.update_button_states()

    def update_button_states(self):
        any_selected = any(pair["button_group"].checkedId() in [0, 1] for pair in self.pairs)
        self.delete_button.setEnabled(any_selected)
        self.delete_rescan_button.setEnabled(any_selected)

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
            f"Are you sure you want to delete {len(to_delete)} images?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            for file in to_delete:
                try:
                    os.remove(file)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete {file}: {e}")
            QMessageBox.information(self, "Info", "Selected images deleted.")

    def delete_and_rescan(self):
        self.delete_selected()
        self.run_scan()

# Run the application
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()