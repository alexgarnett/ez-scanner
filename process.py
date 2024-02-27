"""
The preprocessing functions defined in this file make use of cv2 methods.
For documentation on the cv2 methods, please visit https://docs.opencv.org/4.x/index.html.
"""

import cv2
import pytesseract
import os
import numpy as np
import imutils
import platform

os.environ['TESSDATA_PREFIX'] = r'Tesseract-OCR/tessdata'
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
elif platform.system() == 'Linux':
    pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
elif platform.system() == 'Darwin':
    pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'


def extract_text(image):
    text = pytesseract.pytesseract.image_to_string(image)
    return text


def evaluate(text):
    keys_correct = 0
    keys = ["EXP", "LN", "FN", "DOB"]
    values_correct = 0
    values = ["06/27/2024", "GARNETT", "ALEXANDER LEE", "06/27/1995"]
    lines = text.split('\n')
    print(lines)
    for line in lines:
        for key in keys:
            if key in line:
                keys_correct += 1
        for value in values:
            if value in line:
                values_correct += 1
    return "Keys correct: " + str(keys_correct) + "  Values correct: " + str(values_correct)


def normalize(image):
    norm_img = np.zeros((image.shape[0], image.shape[1]))
    img = cv2.normalize(image, norm_img, 0, 255, cv2.NORM_MINMAX)
    return img


def deskew(image):
    co_ords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(co_ords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
    return rotated


def thresh(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]


def gray(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def blur(image):
    height, width = image.shape[:2]
    if height >= 720 or width >= 720:
        image = cv2.GaussianBlur(image, (1, 1), 0)
        image = cv2.bilateralFilter(image, 11, 41, 21)
    else:
        image = cv2.GaussianBlur(image, (1, 1), 0)
        image = cv2.bilateralFilter(image, 11, 21, 7)
    return image


def distance(image):
    image = cv2.distanceTransform(image, cv2.DIST_L2, 5)
    image = cv2.normalize(image, None, 0, 1.0, cv2.NORM_MINMAX)
    image = (image * 255).astype("uint8")
    return image


def morph(image):
    height, width = image.shape[:2]
    if height >= 720 or width >= 720:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    else:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

    return image


def resize(image):
    height, width = image.shape[:2]
    max_height = 720
    max_width = 1080
    if width > max_width or height > max_height:
        scaling_factor = max_height/float(height)
        if max_width/float(width) < scaling_factor:
            scaling_factor = max_width/float(width)
        image = cv2.resize(image, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
    return image


def contours(image):
    cnts = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    chars = []

    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        chars.append(c)

        # compute the convex hull of the characters
        chars = np.vstack([chars[i] for i in range(0, len(chars))])
        hull = cv2.convexHull(chars)
        # allocate memory for the convex hull mask, draw the convex hull on
        # the image, and then enlarge it via a dilation
        mask = np.zeros(image.shape[:2], dtype="uint8")
        cv2.drawContours(mask, [hull], -1, 255, -1)
        mask = cv2.dilate(mask, None, iterations=2)
        # take the bitwise of the opening image and the mask to reveal *just*
        # the characters in the image
        final = cv2.bitwise_and(image, image, mask=mask)
        return final


