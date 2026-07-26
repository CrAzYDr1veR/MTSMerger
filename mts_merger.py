"""
MTS File Merger - simple GUI
Merges MTS video files via binary concatenation (equivalent to:
copy /b file1.mts + file2.mts + ... output.mts)

No re-encoding happens - this just glues the files together the same
way the EEVblog method does, so quality/settings are untouched.
https://youtu.be/JXb5cGFLvLw?si=5ZqjSNVmzKouTwLr
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class MTSMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MTS Merger")
        self.root.geometry("560x420")
        self.root.resizable(False, False)

        self.files = []  # ordered list of full paths

        # --- Top buttons ---
        top_frame = tk.Frame(root, pady=10)
        top_frame.pack(fill="x", padx=10)

        tk.Button(top_frame, text="Add Files...", width=14,
                  command=self.add_files).pack(side="left", padx=5)
        tk.Button(top_frame, text="Remove Selected", width=14,
                  command=self.remove_selected).pack(side="left", padx=5)
        tk.Button(top_frame, text="Clear All", width=14,
                  command=self.clear_all).pack(side="left", padx=5)

        # --- Listbox with files (drag order matters -> merge order) ---
        list_frame = tk.Frame(root)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame, selectmode="extended",
            yscrollcommand=scrollbar.set, font=("Consolas", 10)
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        # --- Reorder buttons ---
        order_frame = tk.Frame(root)
        order_frame.pack(fill="x", padx=10)
        tk.Button(order_frame, text="Move Up", width=14,
                  command=self.move_up).pack(side="left", padx=5, pady=5)
        tk.Button(order_frame, text="Move Down", width=14,
                  command=self.move_down).pack(side="left", padx=5, pady=5)

        tk.Label(root, text="Files merge in the order shown above (top to bottom).",
                 fg="gray").pack(pady=(0, 5))

        # --- Merge button ---
        merge_frame = tk.Frame(root, pady=10)
        merge_frame.pack(fill="x", padx=10)

        self.merge_btn = tk.Button(
            merge_frame, text="Merge Files...", width=20, height=2,
            bg="#2e7d32", fg="white", font=("Segoe UI", 10, "bold"),
            command=self.merge_files
        )
        self.merge_btn.pack()

        # --- Progress + status ---
        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(10, 5))

        self.status_var = tk.StringVar(value="Add 2 or more .MTS files to begin.")
        tk.Label(root, textvariable=self.status_var, fg="gray").pack()

    # ---------- file list management ----------

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select MTS files to merge",
            filetypes=[("MTS video files", "*.mts *.MTS"), ("All files", "*.*")]
        )
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", os.path.basename(p))
        self.update_status()

    def remove_selected(self):
        selected = list(self.listbox.curselection())
        for i in reversed(selected):
            self.listbox.delete(i)
            del self.files[i]
        self.update_status()

    def clear_all(self):
        self.listbox.delete(0, "end")
        self.files.clear()
        self.update_status()

    def move_up(self):
        selected = list(self.listbox.curselection())
        for i in selected:
            if i == 0:
                continue
            self.files[i - 1], self.files[i] = self.files[i], self.files[i - 1]
            text = self.listbox.get(i)
            self.listbox.delete(i)
            self.listbox.insert(i - 1, text)
            self.listbox.selection_set(i - 1)

    def move_down(self):
        selected = list(self.listbox.curselection())
        for i in reversed(selected):
            if i == len(self.files) - 1:
                continue
            self.files[i + 1], self.files[i] = self.files[i], self.files[i + 1]
            text = self.listbox.get(i)
            self.listbox.delete(i)
            self.listbox.insert(i + 1, text)
            self.listbox.selection_set(i + 1)

    def update_status(self):
        n = len(self.files)
        if n == 0:
            self.status_var.set("Add 2 or more .MTS files to begin.")
        elif n == 1:
            self.status_var.set("Add at least one more file to merge.")
        else:
            self.status_var.set(f"{n} files ready to merge.")

    # ---------- merge logic ----------

    def merge_files(self):
        if len(self.files) < 2:
            messagebox.showwarning("Not enough files", "Add at least 2 .MTS files to merge.")
            return

        default_name = "merged.mts"
        first_dir = os.path.dirname(self.files[0])

        out_path = filedialog.asksaveasfilename(
            title="Save merged file as",
            initialdir=first_dir,
            initialfile=default_name,
            defaultextension=".mts",
            filetypes=[("MTS video files", "*.mts")]
        )
        if not out_path:
            return

        # Don't allow merging a file into itself
        if os.path.abspath(out_path) in [os.path.abspath(f) for f in self.files]:
            messagebox.showerror("Invalid output", "Output file can't be one of the input files.")
            return

        try:
            total_size = sum(os.path.getsize(f) for f in self.files)
            written = 0
            self.progress["value"] = 0
            self.merge_btn.config(state="disabled")

            chunk_size = 1024 * 1024 * 4  # 4 MB chunks
            with open(out_path, "wb") as out_f:
                for f in self.files:
                    with open(f, "rb") as in_f:
                        while True:
                            chunk = in_f.read(chunk_size)
                            if not chunk:
                                break
                            out_f.write(chunk)
                            written += len(chunk)
                            pct = (written / total_size) * 100
                            self.progress["value"] = pct
                            self.root.update_idletasks()

            self.status_var.set(f"Done! Saved to {out_path}")
            self.merge_btn.config(state="normal")
            messagebox.showinfo("Merge complete", f"Merged file saved:\n{out_path}")

        except Exception as e:
            self.merge_btn.config(state="normal")
            messagebox.showerror("Error", f"Something went wrong:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MTSMergerApp(root)
    root.mainloop()
