import numpy as np
import cv2
import os
from pdf2image import convert_from_path
from PIL import Image
from .qr_utils import extract_qr_data



def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def pdf_to_images(pdf_path, dpi=None, poppler_path=None, save_path=None):
    """
    Convert a PDF containing OMR sheets into image files and extract student data.
    Saves each page as a PNG file, named with the student's roll number in save_path.
    Returns:
        list[dict]: A list of student metadata dictionaries, one per PDF page.
                    Example: [{'roll': '12345', 'name': 'Alice'}, ...]
    """
    images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
    ensure_dir(save_path)
    students_data = []
    for img in images:
        img_arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        student_data = extract_qr_data(img_arr)
        students_data.append(student_data)

        #! TODO: Remove the saving and return the image
        img.save(f'{save_path}{student_data.get('roll')}.png', 'PNG')
    return students_data




def convert_images_to_pdf(image_paths, output_path):
    images = [Image.open(img).convert("RGB") for img in image_paths]
    images[0].save(output_path, save_all=True, append_images=images[1:]) # Save the first image and append the rest

