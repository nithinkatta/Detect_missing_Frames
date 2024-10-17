import cv2
import os
from ssim import process_all_images_in_directory

def crop_frame(frame, region):
    """Crop the frame based on the region (x, y, w, h)."""
    x, y, w, h = region
    return frame[y:y+h, x:x+w]

def clear_directory(directory):
    """Clear all files from the directory."""
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print(f"Directory {directory} does not exist. Creating...")
        os.makedirs(directory, exist_ok=True)

def extract_frames(video_path):
    """Extract frames from the video, rotate and process them."""
    frames_dir = 'uploads/extracted_frames'
    predefined_dir = 'uploads/predefined_digits'

    # Clear the extracted frames directory
    clear_directory(frames_dir)

    # Initialize video capture
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Cannot open video file {video_path}")
        return

    frame_count = 0
    saved_frames = []
    processing_complete = False
    rotate_cnt = 0
    while cap.isOpened():
        ret, org_frame = cap.read()
        if not ret:
            print("End of video or cannot read the frame.")
            break

        initial_frame = org_frame
        if not processing_complete:
            frame_found = False
            
            frame = initial_frame
            for _ in range(4):
                # Rotate frame 90 degrees counterclockwise
                # cv2.imshow("frame",frame)
                # cv2.waitKey(0)
                
                initial_frame = frame
                # cv2.imshow("frame",frame)
                # cv2.waitKey(0)
                # Define region of interest (change this as needed)
                region_of_interest = (200, 200, 250, 50)
                frame = crop_frame(frame, region_of_interest)
                
                # Clear frames directory for new frame comparison
                clear_directory(frames_dir)
                
                # Save the current frame for processing
                frame_filename = os.path.join(frames_dir, f'frame_{frame_count}.png')
                cv2.imwrite(frame_filename, frame)
                saved_frames.append(frame_filename)
                
                # Process frame using SSIM and predefined data
                val = process_all_images_in_directory(frames_dir, predefined_dir, use_ssim=True, check_valid_digits_in_frame=True)
                print(val)
                if val:
                    frame_found = True
                    clear_directory(frames_dir)
                    print(f"Valid frame found at frame {frame_count}")
                    break

                frame = cv2.rotate(initial_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                rotate_cnt += 1


            if not frame_found:
                print("Invalid frame detected. Exiting...")
                return False

            processing_complete = True

        # Crop original frame and save
        for i in range(rotate_cnt):
            frame = cv2.rotate(org_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            org_frame = frame
            # cv2.imshow("frame",frame)
            # cv2.waitKey(0)
            
        
        region_of_interest = (200, 200, 250, 50)
        cropped_frame = crop_frame(org_frame, region_of_interest)
        frame_filename = os.path.join(frames_dir, f'frame_{frame_count}.png')
        cv2.imwrite(frame_filename, cropped_frame)
        saved_frames.append(frame_filename)
        
        frame_count += 1

    # Release video capture
    cap.release()

    # Return frame count and a subset of the saved frames
    return frame_count, saved_frames[:5]

# Example usage
extract_frames(video_path='assets/video.mp4')
