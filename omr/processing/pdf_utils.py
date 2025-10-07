import numpy as np
import cv2
import os
from pdf2image import convert_from_bytes
from PIL import Image
from .qr_utils import extract_qr_data
from PIL import Image, ImageDraw, ImageFont



def ensure_dir(path):
    os.makedirs(path, exist_ok=True)



def pdf_to_images(pdf_file, dpi=None, poppler_path=None):
    pdf_bytes = pdf_file.read()
    pil_images = convert_from_bytes(pdf_bytes, dpi=dpi, poppler_path=poppler_path)

    # Convert PIL image --> numpy arr --> opencv BGR Image
    cv2_images = []
    for pil_img in pil_images:
        np_img = np.array(pil_img)
        gray_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        cv2_images.append(gray_img)

    return cv2_images



def convert_images_to_pdf(image_paths, output_path):
    images = [Image.open(img).convert("RGB") for img in image_paths]
    images[0].save(output_path, save_all=True, append_images=images[1:]) # Save the first image and append the rest



def create_cover_page(exam_name):
    width, height = 2480, 3508
    cover = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(cover)
    try:
        font = ImageFont.truetype("arial.ttf", 120)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), exam_name, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) / 2
    y = (height - text_height) / 2
    draw.text((x, y), exam_name, fill="black", font=font)
    return cover 
