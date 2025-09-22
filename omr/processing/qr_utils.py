import cv2
import ast


def extract_qr_data(image):
    data, _, _ = cv2.QRCodeDetector().detectAndDecode(image)
    if data:
        return ast.literal_eval(data)
    print("Error : Qr-Code didn't detected")
    return {'name': 'Unknown', 'roll': 'Unknown'}
