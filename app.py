import os
import cv2
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import Text
from tkinter.scrolledtext import ScrolledText
from extract import extract_frames  # Import the existing extract_frames function
from ssim import process_all_images_in_directory  # Import the SSIM processing logic
from tkinterdnd2 import TkinterDnD, DND_FILES  # Import drag and drop support

# Define directories (no need to move the video now)
EXTRACTED_FRAMES_DIR = 'uploads/extracted_frames'
os.makedirs(EXTRACTED_FRAMES_DIR, exist_ok=True)

PREDEFINED_DIGITS_DIR = 'uploads/predefined_digits'
os.makedirs(PREDEFINED_DIGITS_DIR, exist_ok=True)

class VideoProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Missing Frames Detection")
        self.root.geometry("600x500")

        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Video Name Label
        self.video_name_label = tk.Label(main_frame, text="No video uploaded", font=("Arial", 14, "bold"))
        self.video_name_label.pack(pady=(10, 20))

        self.drag_name_label = tk.Label(main_frame, text="(Drag and drop video)", font=("Arial", 8, "bold"))
        self.drag_name_label.pack(pady=(5, 10))
        self.drag_name_label.config(fg="blue")

        #Frame count
        self.frame_count = Text(main_frame,wrap=tk.WORD,font=("Arial",12),height=2, width=20)
        self.frame_count.pack(pady=(3,3))
        self.frame_count.config(state=tk.DISABLED)

        # Drag and Drop Area
        self.result_text = ScrolledText(main_frame, wrap=tk.WORD, font=("Arial", 12), height=5, fg="blue", bg="lightgrey", bd=2, relief="groove")
        self.result_text.pack(expand=True, fill=tk.BOTH, pady=10)
        self.result_text.config(state=tk.DISABLED)  # Disable editing initially
        self.result_text.insert(tk.END, "Drag and drop a video here...")
        


        # Create a frame for buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(10, 10))

        # Upload button
        self.upload_button = tk.Button(button_frame, text="Upload Video", command=self.upload_video, width=20, height=2, bg="#4CAF50", fg="white", relief="raised")
        self.upload_button.grid(row=0, column=0, padx=10, pady=5)

        # Process button
        self.process_button = tk.Button(button_frame, text="Process Video", command=self.start_processing, state=tk.DISABLED, width=20, height=2, bg="#007BFF", fg="white", relief="raised")
        self.process_button.grid(row=0, column=1, padx=10, pady=5)

        # Cancel button
        self.cancel_button = tk.Button(button_frame, text="Cancel", command=self.cancel_processing, state=tk.DISABLED, width=20, height=2, bg="#DC3545", fg="white", relief="raised")
        self.cancel_button.grid(row=0, column=2, padx=10, pady=5)

        # Loading label (hidden by default)
        self.loading_label = tk.Label(main_frame, text="Processing...", font=("Arial", 12), fg="blue")
        self.loading_label.pack(pady=20)
        self.loading_label.pack_forget()  # Hide initially

        self.video_path = None
        self.processing_thread = None
        self.processing_cancelled = False

        # Set up drag-and-drop
        self.setup_drag_and_drop(main_frame)

    def setup_drag_and_drop(self, parent_frame):
        parent_frame.drop_target_register(DND_FILES)  # Register as a drop target for files
        parent_frame.dnd_bind('<<Drop>>', self.on_drop)  # Bind the drop event to the handler

    def on_drop(self, event):
        file_path = event.data.strip('{}').strip('"').strip("'")
        if self.is_video_file(file_path):
            self.video_path = file_path
            video_name = os.path.basename(self.video_path)
            self.video_name_label.config(text=f"Uploaded: {video_name}")  # Show the video name
            self.process_button.config(state=tk.NORMAL)  # Enable process button
        else:
            messagebox.showerror("Invalid File", "The file is not a valid video format.")

    def is_video_file(self, file_path):
        if file_path.lower().endswith(".mp4"):
            return True
        return False

    def upload_video(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
        if self.video_path:
            video_name = os.path.basename(self.video_path)
            self.video_name_label.config(text=f"Uploaded: {video_name}")
            self.process_button.config(state=tk.NORMAL)

    def start_processing(self):
        self.loading_label.pack()  # Show the loading label
        self.process_button.config(state=tk.DISABLED)  # Disable process button during processing
        self.cancel_button.config(state=tk.NORMAL)  # Enable cancel button during processing
        self.result_text.config(state=tk.NORMAL)  # Enable editing to update the result
        self.frame_count.config(state=tk.NORMAL)
        self.frame_count.delete('1.0',tk.END)
        self.result_text.delete('1.0', tk.END)  # Clear previous result

        self.processing_cancelled = False
        self.processing_thread = threading.Thread(target=self.process_video)
        self.processing_thread.start()

    def cancel_processing(self):
        self.processing_cancelled = True

    def process_video(self):
        try:

            if self.video_path:
                validate = extract_frames(self.video_path)
                if not validate:
                    self.result_text.insert(tk.END, "Frame numbers not found\n")
                    self.result_text.config(fg="orange")
                    return
                
                
                if self.processing_cancelled:
                    self.result_text.insert(tk.END, "Processing cancelled.\n")
                    return

                missing_frames = process_all_images_in_directory(EXTRACTED_FRAMES_DIR, PREDEFINED_DIGITS_DIR, use_ssim=True, check_valid_digits_in_frame=False)

                self.frame_count.config(state=tk.NORMAL)
                self.frame_count.insert(tk.END,"Total Frames: "+str(validate[0]))   
                self.frame_count.config(state=tk.DISABLED)
     
                if self.processing_cancelled:
                    self.result_text.insert(tk.END, "Processing cancelled.\n")
                    return

                if missing_frames:
                    self.result_text.insert(tk.END, f"Missing Frames: {missing_frames}\n")
                    self.result_text.config(fg="red")
                else:
                    self.result_text.insert(tk.END, "No Missing Frames!\n")
                    self.result_text.config(fg="green")
            else:
                messagebox.showerror("Error", "Please upload a video first!")
        finally:
            self.loading_label.pack_forget()
            self.process_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            self.result_text.config(state=tk.DISABLED)

# Start the Tkinter application
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = VideoProcessorApp(root)
    root.mainloop()
