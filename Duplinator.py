import os
import imagehash
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import queue

# Global dictionary to store checkbox variables
file_vars = {}

def find_duplicate_images(folder_path, hash_size=8, threshold=5):
    """
    Finds pairs of duplicate images within a folder.

    Args:
        folder_path: The path to the folder containing the images.
        hash_size: The size of the image hash (higher values are more precise but slower).
        threshold: The maximum difference between hashes to consider images duplicates (lower is stricter).

    Returns:
        A list of tuples, each containing two filenames that are duplicates.
    """
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
    canvas.configure(scrollregion=canvas.bbox("all"))

inner_frame.bind("<Configure>", on_frame_configure)

# Delete Buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

delete_button = tk.Button(button_frame, text="Delete", command=lambda: delete_selected())
delete_button.pack(side=tk.LEFT, padx=5)

delete_rescan_button = tk.Button(button_frame, text="Delete and Rescan", command=lambda: delete_and_rescan())
delete_rescan_button.pack(side=tk.LEFT, padx=5)

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

    # Clear previous results
    for widget in inner_frame.winfo_children():
        widget.destroy()

    status_var.set("Processing...")
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
    try:
        result = result_queue.get_nowait()
        if isinstance(result, Exception):
            messagebox.showerror("Error", str(result))
        else:
            display_results(result)
        status_var.set("Done.")
        find_button.config(state=tk.NORMAL)
    except queue.Empty:
        root.after(100, check_queue, result_queue)

def display_results(duplicate_pairs):
    global file_vars
    for widget in inner_frame.winfo_children():
        widget.destroy()
    if not duplicate_pairs:
        tk.Label(inner_frame, text="No duplicate images found.").pack()
        file_vars = {}
    else:
        # Collect all unique filenames
        all_files = set()
        for pair in duplicate_pairs:
            all_files.update(pair)
        file_vars = {file: tk.BooleanVar() for file in all_files}
        # Display each pair with checkboxes
        for pair in duplicate_pairs:
            subframe = tk.Frame(inner_frame)
            subframe.pack(fill=tk.X)
            filename1, filename2 = pair
            var1 = file_vars[filename1]
            tk.Checkbutton(subframe, variable=var1).pack(side=tk.LEFT)
            tk.Label(subframe, text=filename1).pack(side=tk.LEFT)
            var2 = file_vars[filename2]
            tk.Checkbutton(subframe, variable=var2).pack(side=tk.LEFT)
            tk.Label(subframe, text=filename2).pack(side=tk.LEFT)

def delete_selected():
    global file_vars
    to_delete = [file for file, var in file_vars.items() if var.get()]
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
    delete_selected()
    run_duplicate_finder()

# Start the GUI
root.mainloop()