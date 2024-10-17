import cv2
import os
import time
import numpy as np
from skimage.metrics import structural_similarity as ssim
from extract import *

def load_images_from_directory(directory):
    images = {}
    for filename in os.listdir(directory):
        if filename.endswith(".png") or filename.endswith(".jpg"): 
            img_path = os.path.join(directory, filename)
            images[filename.split('.')[0]] = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    return images

def slice_image(image, num_slices):
    height, width = image.shape
    slice_width = width // num_slices
    slices = []
    for i in range(num_slices):
        if i == 4:
            digit_slice = image[:, i * slice_width + 1:(i + 2) * slice_width + 1]
        else:
            digit_slice = image[:, i * slice_width:(i + 1) * slice_width]
        slices.append(digit_slice)
    return slices

def recognize_digit_ssim(digit_slice, predefined_digits_directory, similarity_threshold=0.8):
    predefined_images = load_images_from_directory(predefined_digits_directory)
    
    best_match = None
    highest_similarity = -1
    
    for digit, predefined_image in predefined_images.items():
        predefined_resized = cv2.resize(predefined_image, (digit_slice.shape[1], digit_slice.shape[0]))

        similarity = ssim(digit_slice, predefined_resized)

        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = digit
    print(f"ssim score: {highest_similarity}")
    # Check if the highest similarity is below the threshold
    if highest_similarity < similarity_threshold:
        print(f"No match found for slice (SSIM: {highest_similarity}).")
        return None  # Indicating no match found

    return int(best_match)

def mse(imageA, imageB):
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    return err

def recognize_digit_mse(digit_slice, predefined_digits_directory):
    predefined_images = load_images_from_directory(predefined_digits_directory)
    
    best_match = None
    lowest_error = float("inf")
    
    for digit, predefined_image in predefined_images.items():
        predefined_resized = cv2.resize(predefined_image, (digit_slice.shape[1], digit_slice.shape[0]))

        error = mse(digit_slice, predefined_resized)

        if error < lowest_error:
            lowest_error = error
            best_match = digit

    return int(best_match)

def process_image(input_image_path, predefined_digits_directory, use_ssim=True):
    input_image = cv2.imread(input_image_path, cv2.IMREAD_GRAYSCALE)
    
    num_slices = 5  
    digit_slices = slice_image(input_image, num_slices)

    detected_number = []
    for digit_slice in digit_slices:
        if use_ssim:
            recognized_digit = recognize_digit_ssim(digit_slice, predefined_digits_directory)
        else:
            recognized_digit = recognize_digit_mse(digit_slice, predefined_digits_directory)
        
        if recognized_digit is None:  # If no match found
            print("Number not found")
            return None  # Break out and return if any digit is not recognized
        
        detected_number.append(recognized_digit)

    final_number = ''.join(map(str, detected_number))
    return final_number

def process_all_images_in_directory(directory, predefined_digits_dir, use_ssim=True,check_valid_digits_in_frame=False):
    final_outputs = {}
    missing_frames = []


    if check_valid_digits_in_frame:

        for filename in os.listdir(directory):
            if filename.endswith('.png') or filename.endswith('.jpg'):
                image_path = os.path.join(directory, filename)
                final_number = process_image(image_path, predefined_digits_dir, use_ssim)
                if final_number is None:
                    print(f"Number not found in image: {filename}")
                    return False
                else:
                    return True
    else:
        # Process all images in directory
        for filename in os.listdir(directory):
            if filename.endswith('.png') or filename.endswith('.jpg'):
                image_path = os.path.join(directory, filename)
                final_number = process_image(image_path, predefined_digits_dir, use_ssim)
                
                if final_number is None:
                    print(f"Number not found in image: {filename}")
                    continue  # Skip this image if number not found

                final_outputs[filename] = final_number

        # Detect missing frames
        frames_found = [int(detected_number) for detected_number in final_outputs.values()]
        frames_found.sort()

        val = frames_found[0]
        for i in frames_found[1:]:
            if i - val > 1:
                for j in range(1, i - val):
                    missing_frames.append(val + j)
            val = i
        print(missing_frames)
        return missing_frames


if __name__ == "__main__":
    s = time.time()
    
    extracted_images_dir = 'extracted_frames'  
    predefined_digits_dir = 'predefined_digits'
    video_link = 'assets/video2.mp4'

    extract_frames(video_link)
    
    process_all_images_in_directory(extracted_images_dir, predefined_digits_dir, use_ssim=True, check_valid_digits_in_frame=False)  
    
    print(f"Total processing time: {time.time() - s:.2f} seconds")
    cv2.destroyAllWindows()
