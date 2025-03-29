import os
import imagehash
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
from datetime import datetime

# Global variables
pairs = []  # List to store duplicate pairs and user choices
thumbnails = {}  # Dictionary to persist thumbnails

# Function to update the state of delete buttons
def update_button_states():
    """Enable or disable delete buttons based on whether any image is selected."""
    any_selected = any(pair["choice"].get() in ["left", "right"] for pair in pairs)
    state = tk.NORMAL if any_selected else tk.DISABLED
    delete_button.config(state=state)
    delete_rescan_button.config(state=state)

# Function to find duplicate images
def find_duplicate_images(folder_path, hash_size=8, threshold=5):
    """Find duplicate images in the specified folder using perceptual hashing."""
    image_hashes = {}
    duplicates = []

    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
            continue

        filepath = os.path.join(folder_path, filename)

        try:
            with Image.open(filepath) as img:
                image_hash = imagehash.phash(img, hash_size=hash_size)

                for other_filename, other_hash in image_hashes.items():
                    if (image_hash - other_hash) <= threshold:
                        duplicates.append((filename, other_filename))

                image_hashes[filename] = image_hash

        except (OSError, ValueError) as e:
            print(f"Error processing {filename}: {e}")
            continue

    return duplicates

# GUI Setup
root = tk.Tk()
root.title("Duplinator")

# Folder Selection
folder_frame = tk.Frame(root)
folder_frame.pack(pady=10)
tk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT)
folder_path_var = tk.StringVar()
folder_entry = tk.Entry(folder_frame, textvariable=folder_path_var, width=50)
folder_entry.pack(side=tk.LEFT, padx=5)

def select_folder():
    """Open a dialog to select a folder and update the entry field."""
    path = filedialog.askdirectory()
    if path:
        folder_path_var.set(path)

tk.Button(folder_frame, text="Browse", command=select_folder).pack(side=tk.LEFT)

# Parameters
params_frame = tk.Frame(root)
params_frame.pack(pady=10)
tk.Label(params_frame, text="Hash Size:").pack(side=tk.LEFT)
hash_size_var = tk.IntVar(value=8)
tk.Spinbox(params_frame, from_=2, to=32, textvariable=hash_size_var).pack(side=tk.LEFT, padx=5)
tk.Label(params_frame, text="Threshold:").pack(side=tk.LEFT)
threshold_var = tk.IntVar(value=5)
tk.Spinbox(params_frame, from_=0, to=100, textvariable=threshold_var).pack(side=tk.LEFT, padx=5)

# Find Duplicates Button (made more prominent)
find_button = tk.Button(root, text="Start Scan", command=lambda: run_duplicate_finder(), font=("Arial", 14), width=20)
find_button.pack(pady=10)

# Results Display (Scrollable Frame)
results_frame = tk.Frame(root)
results_frame.pack(pady=10, fill=tk.BOTH, expand=True)

canvas = tk.Canvas(results_frame)
scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

inner_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=inner_frame, anchor="nw")

def on_frame_configure(event):
    """Update the scroll region when the inner frame size changes."""
    canvas.configure(scrollregion=canvas.bbox("all"))

inner_frame.bind("<Configure>", on_frame_configure)

# Delete Buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

delete_button = tk.Button(button_frame, text="Delete", command=lambda: delete_selected())
delete_button.pack(side=tk.LEFT, padx=5)

delete_rescan_button = tk.Button(button_frame, text="Delete and Rescan", command=lambda: delete_and_rescan())
delete_rescan_button.pack(side=tk.LEFT, padx=5)

# Initially disable the buttons
delete_button.config(state=tk.DISABLED)
delete_rescan_button.config(state=tk.DISABLED)

# Status Bar
status_var = tk.StringVar(value="Ready")
status_label = tk.Label(root, textvariable=status_var)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# Progress Window
progress_window = None
progress_bar = None

def show_progress_window():
    """Display a progress window during scanning."""
    global progress_window, progress_bar
    progress_window = tk.Toplevel(root)
    progress_window.title("Processing")
    progress_window.geometry("300x100")
    progress_window.transient(root)
    progress_window.grab_set()
    tk.Label(progress_window, text="Scanning for duplicates...").pack(pady=10)
    progress_bar = ttk.Progressbar(progress_window, mode="indeterminate")
    progress_bar.pack(pady=10, fill=tk.X, padx=20)
    progress_bar.start()

    # Center the progress window over the main window
    root.update_idletasks()
    main_x = root.winfo_x()
    main_y = root.winfo_y()
    main_width = root.winfo_width()
    main_height = root.winfo_height()
    progress_width = 300
    progress_height = 100
    x = main_x + (main_width // 2) - (progress_width // 2)
    y = main_y + (main_height // 2) - (progress_height // 2)
    progress_window.geometry(f"{progress_width}x{progress_height}+{x}+{y}")

def hide_progress_window():
    """Close the progress window when scanning is complete."""
    global progress_window
    if progress_window:
        progress_bar.stop()
        progress_window.destroy()
        progress_window = None

# Functions for GUI Logic
def run_duplicate_finder():
    """Start the duplicate image finder process in a separate thread."""
    folder_path = folder_path_var.get()
    if not folder_path or not os.path.isdir(folder_path):
        messagebox.showerror("Error", "Please select a valid folder.")
        return

    hash_size = hash_size_var.get()
    threshold = threshold_var.get()

    for widget in inner_frame.winfo_children():
        widget.destroy()

    show_progress_window()
    find_button.config(state=tk.DISABLED)

    result_queue = queue.Queue()

    def worker():
        try:
            duplicates = find_duplicate_images(folder_path, hash_size, threshold)
            result_queue.put(duplicates)
        except Exception as e:
            result_queue.put(e)

    thread = threading.Thread(target=worker)
    thread.start()
    check_queue(result_queue)

def check_queue(result_queue):
    """Check the result queue for the outcome of the duplicate finder."""
    try:
        result = result_queue.get_nowait()
        if isinstance(result, Exception):
            messagebox.showerror("Error", str(result))
        else:
            display_results(result)
        hide_progress_window()
        status_var.set("Done.")
        find_button.config(state=tk.NORMAL)
    except queue.Empty:
        root.after(100, check_queue, result_queue)

def get_file_info(filepath):
    """Retrieve file size, resolution, and timestamps."""
    try:
        stat = os.stat(filepath)
        size = stat.st_size / 1024  # Size in KB
        with Image.open(filepath) as img:
            width, height = img.size
        created = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        return size, (width, height), created, modified
    except Exception as e:
        print(f"Error retrieving info for {filepath}: {e}")
        return None, (0, 0), "Unknown", "Unknown"

def display_results(duplicate_pairs):
    """Display the duplicate pairs with radio buttons for selection."""
    global pairs
    for widget in inner_frame.winfo_children():
        widget.destroy()
    pairs = []
    if not duplicate_pairs:
        tk.Label(inner_frame, text="No duplicate images found.").pack()
    else:
        folder_path = folder_path_var.get()
        for i, (filename1, filename2) in enumerate(duplicate_pairs):
            if i > 0:
                ttk.Separator(inner_frame, orient="horizontal").pack(fill=tk.X, pady=5)
            subframe = tk.Frame(inner_frame)
            subframe.pack(fill=tk.X, pady=5)

            # Left image frame
            left_frame = tk.Frame(subframe)
            left_frame.pack(side=tk.LEFT, padx=10)
            filepath1 = os.path.join(folder_path, filename1)
            size1, (width1, height1), created1, modified1 = get_file_info(filepath1)
            if size1 is not None:
                try:
                    img = Image.open(filepath1)
                    img = img.resize((100, 100), Image.Resampling.LANCZOS)
                    thumbnails[filename1] = ImageTk.PhotoImage(img)
                    tk.Label(left_frame, image=thumbnails[filename1]).pack()
                except Exception as e:
                    print(f"Error loading thumbnail for {filename1}: {e}")
                    tk.Label(left_frame, text="[Thumbnail Error]").pack()
                tk.Label(left_frame, text=f"{filename1}\nSize: {size1:.2f} KB\nRes: {width1}x{height1}\nCreated: {created1}\nModified: {modified1}").pack()
            else:
                tk.Label(left_frame, text=f"{filename1}\n[Error retrieving info]").pack()

            # Delete choice frame with radio buttons
            choice_frame = tk.Frame(subframe)
            choice_frame.pack(side=tk.LEFT, padx=10)
            choice_var = tk.StringVar(value="none")
            tk.Label(choice_frame, text="Delete which image?").pack()
            tk.Radiobutton(choice_frame, text="Left", variable=choice_var, value="left").pack(anchor=tk.W)
            tk.Radiobutton(choice_frame, text="Right", variable=choice_var, value="right").pack(anchor=tk.W)
            tk.Radiobutton(choice_frame, text="Neither", variable=choice_var, value="none").pack(anchor=tk.W)

            # Right image frame
            right_frame = tk.Frame(subframe)
            right_frame.pack(side=tk.LEFT, padx=10)
            filepath2 = os.path.join(folder_path, filename2)
            size2, (width2, height2), created2, modified2 = get_file_info(filepath2)
            if size2 is not None:
                try:
                    img = Image.open(filepath2)
                    img = img.resize((100, 100), Image.Resampling.LANCZOS)
                    thumbnails[filename2] = ImageTk.PhotoImage(img)
                    tk.Label(right_frame, image=thumbnails[filename2]).pack()
                except Exception as e:
                    print(f"Error loading thumbnail for {filename2}: {e}")
                    tk.Label(right_frame, text="[Thumbnail Error]").pack()
                tk.Label(right_frame, text=f"{filename2}\nSize: {size2:.2f} KB\nRes: {width2}x{height2}\nCreated: {created2}\nModified: {modified2}").pack()
            else:
                tk.Label(right_frame, text=f"{filename2}\n[Error retrieving info]").pack()

            # Store pair info and set trace for button updates
            pairs.append({"file1": filename1, "file2": filename2, "choice": choice_var})
            choice_var.trace("w", lambda *args: update_button_states())
    update_button_states()

def delete_selected():
    """Delete the selected images based on user choices."""
    to_delete = set()
    for pair in pairs:
        choice = pair["choice"].get()
        if choice == "left":
            to_delete.add(pair["file1"])
        elif choice == "right":
            to_delete.add(pair["file2"])
    if not to_delete:
        messagebox.showinfo("Info", "No images selected for deletion.")
        return
    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {len(to_delete)} images?")
    if confirm:
        folder_path = folder_path_var.get()
        for file in to_delete:
            filepath = os.path.join(folder_path, file)
            try:
                os.remove(filepath)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {file}: {e}")
        messagebox.showinfo("Info", "Selected images deleted.")

def delete_and_rescan():
    """Delete selected images and rescan the folder."""
    delete_selected()
    run_duplicate_finder()

# Start the GUI
root.mainloop()