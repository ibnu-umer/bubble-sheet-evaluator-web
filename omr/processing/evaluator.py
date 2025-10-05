import os
import cv2
import numpy as np
from .pdf_utils import ensure_dir
import csv, json
from io import StringIO, BytesIO
import base64
from PIL import Image



def load_answers(file):
    if not file:
        return None

    content = file.read().decode("utf-8")

    if file.name.endswith(".json"):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON answer key file")

    elif file.name.endswith(".csv"):
        reader = csv.reader(StringIO(content))
        data = {row[0]: row[1] for row in reader}
        return data

    else:
        raise ValueError("Unsupported file format (only .csv and .json allowed)")



def detect_corner_markers(gray_image):
    def angle(pt1, pt2, pt3):
        '''To find angle of the L corners'''
        v1, v2 = pt1 - pt2, pt3 - pt2
        return np.degrees(np.arccos(
            np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0)
        ))

    edges = cv2.Canny(gray_image, 50, 150)
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = gray_image.shape
    corners = []

    for cnt in contours:
        x, y, w_box, h_box = cv2.boundingRect(cnt)
        if not (100 < w_box < 130 and 110 < h_box < 140):
            continue

        if (x < w * 0.2 and y < h * 0.2) or (x + w_box > w * 0.8 and y < h * 0.2) or \
           (x < w * 0.2 and y + h_box > h * 0.8) or (x + w_box > w * 0.8 and y + h_box > h * 0.8):

            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) >= 3:
                if x < w * 0.2 and y < h * 0.2:
                    ref = min(approx, key=lambda pt: pt[0][0] + pt[0][1])
                elif x + w_box > w * 0.8 and y < h * 0.2:
                    ref = min(approx, key=lambda pt: -pt[0][0] + pt[0][1])
                elif x < w * 0.2 and y + h_box > h * 0.8:
                    ref = min(approx, key=lambda pt: pt[0][0] - pt[0][1])
                else:
                    ref = max(approx, key=lambda pt: pt[0][0] + pt[0][1])

                for i in range(len(approx)):
                    ang = angle(approx[i - 1][0], approx[i][0], approx[(i + 1) % len(approx)][0])
                    if 80 <= ang <= 100:
                        corners.append(tuple(ref[0]))
                        break

    corners = list(set(corners))
    if len(corners) == 4:
        sorted_y = sorted(corners, key=lambda pt: pt[1])
        top = sorted(sorted_y[:2], key=lambda pt: pt[0])
        bottom = sorted(sorted_y[2:], key=lambda pt: pt[0])
        src_pts = np.array([top[0], top[1], bottom[1], bottom[0]], dtype="float32")
        dst_pts = np.array([[0, 0], [2480, 0], [2480, 3508], [0, 3508]], dtype="float32")
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        return cv2.warpPerspective(gray_image, M, (2480, 3508)), src_pts

    print(f"Only {len(corners)} corner(s) detected. Cannot perform crop.")
    return None, None



def warp_back(original_img, processed_img, corners):
    dst_pts = np.array([[0, 0], [2480, 0], [2480, 3508], [0, 3508]], dtype="float32")
    src_pts = np.array(corners, dtype="float32")

    # Compute inverse transform (rect → original quadrilateral)
    M = cv2.getPerspectiveTransform(dst_pts, src_pts)
    warped_back = cv2.warpPerspective(processed_img, M, (original_img.shape[1], original_img.shape[0]))
    mask = np.zeros_like(original_img, dtype=np.uint8)
    cv2.fillConvexPoly(mask, np.int32(src_pts), (255, 255, 255))

    # Combine original + new patch
    masked_original = cv2.bitwise_and(original_img, cv2.bitwise_not(mask))
    result = cv2.add(masked_original, warped_back)

    return result



def detect_bubbles(cropped_image):
    img_mid = cropped_image.shape[1] // 2
    halves = [cropped_image[:, :img_mid], cropped_image[:, img_mid:]]
    all_circles = []

    for half in halves:
        blur = cv2.GaussianBlur(half, (5, 5), 0)
        circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                                   param1=50, param2=20, minRadius=35, maxRadius=40
                                )
        all_circles.append(np.round(circles[0, :]).astype("int") if circles is not None else [])

    return all_circles, cv2.hconcat(halves)


def group_and_evaluate(circles, gray_image, mean_intensity_threshold, options):
    result, qn, offset = {}, 1, 0

    for group in circles:
        rows = []
        for c in sorted(group, key=lambda x: x[1]):
            added = False
            for row in rows:
                if abs(row[0][1] - c[1]) < 15:
                    row.append(c)
                    added = True
                    break
            if not added:
                rows.append([c])

        for row in rows:
            row.sort(key=lambda x: x[0])
            for j, (x, y, r) in enumerate(row):
                mask = np.zeros_like(gray_image)
                cv2.circle(mask, (x + offset, y), r, 255, -1)
                mean_val = cv2.mean(gray_image, mask=mask)[0]
                color = (0, 255, 0) if mean_val < mean_intensity_threshold else (0, 0, 255)
                if mean_val < mean_intensity_threshold:
                    result[qn] = options[j]
                cv2.circle(gray_image, (x + offset, y), r, color, 4)
                cv2.putText(gray_image, f'{options[j]} {round(mean_val, 2)}', ((x - 100) + offset, y - 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)
            qn += 1
        offset = gray_image.shape[1] // 2

    return result, gray_image


def evaluate_sheet(responses, answer_keys):
    score = sum(1 for q, a in responses.items() if answer_keys.get(str(q)) == a)
    return {"answers": answer_keys, "score": score}


import random
def process_sheet(
        image, answer_keys, thresh=None, options=None
    ):

    try:
        cropped, corners = detect_corner_markers(image)
        if cropped is None:
            return image, None

        #! Detect roll no
        roll_no = random.randint(1000, 2000)
        bubbles, detected_image = detect_bubbles(cropped)
        answers, marked_image = group_and_evaluate(
            bubbles, detected_image, thresh, options
        )
        result = evaluate_sheet(answers, answer_keys)
        result_img = warp_back(image, marked_image, corners)
        return result_img, result, roll_no

    except Exception as error:
        print(f"error while processing: {error}")
        return image, None, None



def save_results_to_csv(results, result_path):
    if not results:
        print("No results to save.")
        return

    sorted_results = sorted(results, key=lambda x:x['score'], reverse=True)

    keys = ['roll', 'name', 'score']
    with open(result_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(sorted_results)
    return result_path


def cv2_to_base64(gray_img):
    img_array = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2RGB)
    pil_img = Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))

    buffer = BytesIO()
    pil_img.save(buffer, format="PNG")
    base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{base64_str}"
