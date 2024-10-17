import os
import cv2
import threading
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.popup import Popup
from extract import extract_frames  # Import your existing extract_frames function
from ssim import process_all_images_in_directory  # Import the SSIM processing logic

EXTRACTED_FRAMES_DIR = 'uploads/extracted_frames'
os.makedirs(EXTRACTED_FRAMES_DIR, exist_ok=True)

PREDEFINED_DIGITS_DIR = 'uploads/predefined_digits'
os.makedirs(PREDEFINED_DIGITS_DIR, exist_ok=True)

class VideoProcessorApp(App):
    def build(self):
        self.video_path = None
        self.processing_cancelled = False
        self.layout = BoxLayout(orientation='vertical', padding=10)

        # Video name label
        self.video_name_label = Label(text="No video uploaded", size_hint_y=None, height=40)
        self.layout.add_widget(self.video_name_label)

        # Frame count display
        self.frame_count = TextInput(text="Total frames will be displayed here", readonly=True, size_hint_y=None, height=40)
        self.layout.add_widget(self.frame_count)

        # Output area
        self.result_output = TextInput(text="Processing results will appear here", readonly=True, size_hint_y=None, height=150)
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.result_output)
        self.layout.add_widget(scroll)

        # Buttons for uploading and processing
        self.upload_button = Button(text="Upload Video", size_hint_y=None, height=40)
        self.upload_button.bind(on_press=self.upload_video)
        self.layout.add_widget(self.upload_button)

        self.process_button = Button(text="Process Video", size_hint_y=None, height=40, disabled=True)
        self.process_button.bind(on_press=self.start_processing)
        self.layout.add_widget(self.process_button)

        self.cancel_button = Button(text="Cancel", size_hint_y=None, height=40, disabled=True)
        self.cancel_button.bind(on_press=self.cancel_processing)
        self.layout.add_widget(self.cancel_button)

        return self.layout

    def upload_video(self, instance):
        # This function opens a file dialog to select a video file
        from kivy.utils import platform
        if platform == 'android':
            from android.storage import primary_external_storage_path
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

        # Replace with actual file dialog if necessary
        video_path = "uploads/video2.mp4"  # Placeholder, replace with actual dialog
        if video_path:
            self.video_path = video_path
            video_name = os.path.basename(self.video_path)
            self.video_name_label.text = f"Uploaded: {video_name}"
            self.process_button.disabled = False

    def start_processing(self, instance):
        # Enable processing and start a background thread
        self.result_output.text = "Processing..."
        self.frame_count.text = "Extracting frames..."
        self.process_button.disabled = True
        self.cancel_button.disabled = False

        # Run the processing in a separate thread
        threading.Thread(target=self.process_video).start()

    def cancel_processing(self, instance):
        self.processing_cancelled = True
        self.result_output.text = "Processing cancelled."
        self.cancel_button.disabled = True

    def process_video(self):
        try:
            if not self.video_path:
                return

            # Extract frames and validate video
            validate = extract_frames(self.video_path)
            if not validate:
                self.update_result_text("Frame numbers not found\n", "orange")
                return

            if self.processing_cancelled:
                self.update_result_text("Processing cancelled.\n")
                return

            # Process frames to find missing ones
            missing_frames = process_all_images_in_directory(EXTRACTED_FRAMES_DIR, PREDEFINED_DIGITS_DIR, use_ssim=True, check_valid_digits_in_frame=False)

            # Update frame count
            total_frames_text = f"Total Frames: {validate[0]}"
            Clock.schedule_once(lambda dt: self.update_frame_count(total_frames_text))

            if self.processing_cancelled:
                self.update_result_text("Processing cancelled.\n")
                return

            # Display results
            if missing_frames:
                result_text = f"Missing Frames: {missing_frames}\n"
                self.update_result_text(result_text, "red")
            else:
                self.update_result_text("No Missing Frames!\n", "green")

        except Exception as e:
            self.update_result_text(f"Error occurred: {str(e)}", "red")
        # finally:
            # Re-enable buttons and ensure UI remains active
            # Clock.schedule_once(lambda dt: self.process_button.disabled(False))
            # Clock.schedule_once(lambda dt: self.cancel_button.disabled(True))

    def update_result_text(self, text, color="black"):
        Clock.schedule_once(lambda dt: setattr(self.result_output, 'text', text))
        Clock.schedule_once(lambda dt: setattr(self.result_output, 'foreground_color', color))

    def update_frame_count(self, text):
        self.frame_count.text = text

if __name__ == "__main__":
    VideoProcessorApp().run()
