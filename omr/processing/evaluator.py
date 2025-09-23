import os
import cv2
import json
import csv
import numpy as np
from omr.constants import (
    RESULT_IMG_PATH, MEAN_INTENSITY_THRESHOLD, OPTIONS, RESULT_SHEET_PATH, CONVERTED_IMG_PATH
)



def load_answers(path):
    if path.endswith(".json"):
        # Load answers from JSON file
        with open(path, "r") as file:
            answers = json.load(file)
        return answers

    elif path.endswith(".csv"):
        # Load answers from CSV file
        answers = {}
        with open(path, newline='', encoding="utf-8") as file:
            reader = csv.reader(file)
            # CSV format: question_number, answer
            for row in reader:
                if len(row) >= 2:
                    question, answer = row[0].strip(), row[1].strip()
                    answers[question] = answer
        return answers

    else:
        raise ValueError("Unsupported file format. Please use .json or .csv")



def detect_corner_markers(image_path):
    def angle(pt1, pt2, pt3):
        '''To find angle of the L corners'''
        v1, v2 = pt1 - pt2, pt3 - pt2
        return np.degrees(np.arccos(
            np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0)
        ))

    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = gray.shape
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
        return cv2.warpPerspective(image, M, (2480, 3508))

    print(f"Only {len(corners)} corner(s) detected. Cannot perform crop.")
    return None


def detect_bubbles(image, img_name=None):
    img_mid = image.shape[1] // 2
    halves = [image[:, :img_mid], image[:, img_mid:]]
    all_circles = []

    for half in halves:
        gray = cv2.cvtColor(half, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                                   param1=50, param2=20, minRadius=35, maxRadius=40)
        all_circles.append(np.round(circles[0, :]).astype("int") if circles is not None else [])

    cv2.imwrite(f'{RESULT_IMG_PATH}blobs_detected_{img_name}.png', cv2.hconcat(halves))
    return all_circles


def group_and_evaluate(circles, img_name=None):
    img_path = f'{RESULT_IMG_PATH}blobs_detected_{img_name}.png'
    image = cv2.imread(img_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result = {}
    qn = 1
    offset = 0

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
                mask = np.zeros_like(gray)
                cv2.circle(mask, (x + offset, y), r, 255, -1)
                mean_val = cv2.mean(gray, mask=mask)[0]
                color = (0, 255, 0) if mean_val < MEAN_INTENSITY_THRESHOLD else (0, 0, 255)
                if mean_val < MEAN_INTENSITY_THRESHOLD:
                    result[qn] = OPTIONS[j]
                cv2.circle(image, (x + offset, y), r, color, 4)
                cv2.putText(image, f'{OPTIONS[j]} {round(mean_val, 2)}', ((x - 100) + offset, y - 55),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)
            qn += 1
        offset = image.shape[1] // 2

    if img_name is not None:
        cv2.imwrite(f'{RESULT_IMG_PATH}marked_{img_name}.png', image)
        os.remove(f'{RESULT_IMG_PATH}blobs_detected_{img_name}.png')
    return result


def evaluate_sheet(responses, student_data, answer_keys):
    # answers = load_answers()  # Loading in each coz multithreading didn't share variables
    score = sum(1 for q, a in responses.items() if answer_keys.get(str(q)) == a)
    student_data['score'] = score

    print(f"Student: {student_data.get('name')} {student_data.get('roll')}\nScore: {score}/40\n")
    return student_data

import time
def process_sheet(img_filename, student_data, answer_keys):
    # img_path = f'{CONVERTED_IMG_PATH}/{img_filename}'
    # cropped = detect_corner_markers(img_path)
    # if cropped is not None:
    #     img_name = img_filename.split('.')[0]
    #     bubbles = detect_bubbles(cropped, img_name=img_name)
    #     results = group_and_evaluate(bubbles, img_name=img_name)
    #     # student_info = evaluate_sheet(results, student_data, answer_keys)
    # else:
    #     return f"Failed to process: {img_filename}"

    # os.remove(img_path)
    time.sleep(0.2)
    return True # student_info


def save_results_to_csv(results):
    if not results:
        print("No results to save.")
        return

    sorted_results = sorted(results, key=lambda x:x['score'], reverse=True)

    keys = ['roll', 'name', 'score']
    with open(RESULT_SHEET_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(sorted_results)
    return RESULT_SHEET_PATH
