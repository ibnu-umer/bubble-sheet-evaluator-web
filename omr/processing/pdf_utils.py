import numpy as np
import cv2
import os
from pdf2image import convert_from_path
from omr.constants import PDF_DPI, CONVERTED_IMG_PATH, POPPLER_PATH
from .qr_utils import extract_qr_data



def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def pdf_to_images(pdf_path, dpi=PDF_DPI, save_path=CONVERTED_IMG_PATH):
    images = convert_from_path(pdf_path, dpi=dpi, poppler_path=POPPLER_PATH)
    ensure_dir(save_path)
    students_data = []
    for img in images:
        img_arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        student_data = extract_qr_data(img_arr)
        students_data.append(student_data)
        img.save(f'{save_path}{student_data.get('roll')}.png', 'PNG')
    return students_data


