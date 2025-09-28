import numpy as np
import cv2
import os
from pdf2image import convert_from_bytes
from PIL import Image
from .qr_utils import extract_qr_data



def ensure_dir(path):
    os.makedirs(path, exist_ok=True)



def pdf_to_images(pdf_file, dpi=None, poppler_path=None, save_path=None):
    """
    Convert an uploaded PDF (in-memory) into image files and extract student data.
    Saves each page as a PNG file, named with the student's roll number in save_path.

    Args:
        pdf_file (InMemoryUploadedFile): Uploaded PDF file object.
        dpi (int, optional): Resolution for conversion.
        poppler_path (str, optional): Path to poppler binaries (Windows).
        save_path (str, optional): Directory to save images.

    Returns:
        list[dict]: A list of student metadata dictionaries, one per PDF page.
                    Example: [{'roll': '12345', 'name': 'Alice'}, ...]
    """
    # Read PDF bytes directly from uploaded file
    pdf_bytes = pdf_file.read()
    images = convert_from_bytes(pdf_bytes, dpi=dpi, poppler_path=poppler_path)

    if save_path:
        os.makedirs(save_path, exist_ok=True)

    students_data = []
    for img in images:
        img_arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        student_data = extract_qr_data(img_arr)
        students_data.append(student_data)

        if save_path:
            filename = f"{student_data.get('roll', 'unknown')}.png"
            img.save(os.path.join(save_path, filename), "PNG")

    return students_data



def convert_images_to_pdf(image_paths, output_path):
    images = [Image.open(img).convert("RGB") for img in image_paths]
    images[0].save(output_path, save_all=True, append_images=images[1:]) # Save the first image and append the rest

