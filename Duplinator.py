import os
import imagehash
from PIL import Image
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import queue

def find_duplicate_images_with_grouping(folder_path, hash_size=8, threshold=5):
    """
    Finds potential duplicate images and groups them together.

    Args:
        folder_path: The path to the folder.
        hash_size: The hash size.
        threshold: The difference threshold.

    Returns:
        A list of lists. Each inner list contains filenames that are considered duplicates of each other.
    """
    image_hashes = {}
    duplicates = defaultdict(list)

    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
            continue

        filepath = os.path.join(folder_path, filename)

        try:
            with Image.open(filepath) as img:
                image_hash = imagehash.phash(img, hash_size=hash_size)

                found_group = False
                for existing_hash, file_list in duplicates.items():
                    if (image_hash - existing_hash) <= threshold:
                        duplicates[existing_hash].append(filename)
                        image_hashes[filename] = image_hash
                        found_group = True
                        break

                if not found_group:
                    duplicates[image_hash].append(filename)
                    image_hashes[filename] = image_hash

        except (OSError, ValueError) as e:
            print(f"Error processing {filename}: {e}")
            continue

    result = [file_list for file_list in duplicates.values() if len(file_list) > 1]
    return result

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

# Find Duplicates Button
find_button = tk.Button(root, text="Find Duplicates", command=lambda: run_duplicate_finder())
find_button.pack(pady=10)

# Results Display
results_text = scrolledtext.ScrolledText(root, width=80, height=20)
results_text.pack(pady=10)

# Status Bar
status_var = tk.StringVar(value="Ready")
status_label = tk.Label(root, textvariable=status_var)
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# Functions for GUI Logic
def run_duplicate_finder():
    folder_path = folder_path_var.get()
    if not folder_path or not os.path.isdir(folder_path):
        messagebox.showerror("Error", "Please select a valid folder.")
        return

    hash_size = hash_size_var.get()
    threshold = threshold_var.get()

    # Prepare the results area
    results_text.config(state=tk.NORMAL)
    results_text.delete(1.0, tk.END)
    status_var.set("Processing...")
    find_button.config(state=tk.DISABLED)

    # Create the queue for thread communication
    result_queue = queue.Queue()

    def worker():
        try:
            duplicates = find_duplicate_images_with_grouping(folder_path, hash_size, threshold)
            result_queue.put(duplicates)
        except Exception as e:
            result_queue.put(e)

    # Start the worker thread
    thread = threading.Thread(target=worker)
    thread.start()
    # Pass result_queue to check_queue
    check_queue(result_queue)

def check_queue(result_queue):
    try:
        result = result_queue.get_nowait()
        if isinstance(result, Exception):
            messagebox.showerror("Error", str(result))
        else:
            display_results(result)
        status_var.set("Done.")
        find_button.config(state=tk.NORMAL)
    except queue.Empty:
        # Reschedule check_queue with result_queue after 100ms
        root.after(100, check_queue, result_queue)

def display_results(duplicate_groups):
    if not duplicate_groups:
        results_text.insert(tk.END, "No duplicate images found.\n")
    else:
        for i, group in enumerate(duplicate_groups, 1):
            results_text.insert(tk.END, f"Group {i}:\n")
            for filename in group:
                results_text.insert(tk.END, f"  - {filename}\n")
            results_text.insert(tk.END, "\n")
    results_text.config(state=tk.DISABLED)

# Start the GUI
root.mainloop()