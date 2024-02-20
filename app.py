from flask import Flask, render_template, Response
from process import *
import cv2
import platform
import pytesseract.pytesseract
import os
import datefinder

# Tell Tesseract-OCR where to find its training data
os.environ['TESSDATA_PREFIX'] = 'Tesseract-OCR/tessdata'

# Initialize some globals for use by webcam functions
raw_image = None
cam = None
cam_on = False

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/capture')
def stream_page():
    return render_template('stream.html')


def generate():
    global raw_image
    global cam
    global cam_on
    cam_on = True
    cam = cv2.VideoCapture(0)
    while cam_on:
        # Continuously grab frames, convert to JPEG then bytes
        success, raw_image = cam.read()
        flag, output_frame = cv2.imencode('.jpg', raw_image)
        if not flag:
            continue
        # todo: do edge detection on the ID
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
               bytearray(output_frame) + b'\r\n')


@app.route('/camera_feed')
def camera_feed():
    # Return the image bytes with content type for the browser to read
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route('/display_capture')
def display_capture():
    # Convert last raw_image to JPEG bytes and returns content type for browser
    flag, output_frame = cv2.imencode('.jpg', raw_image)
    image_bytes = (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(output_frame) + b'\r\n')
    return Response(image_bytes, mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route('/review_image')
def review_image():
    return render_template('review_image.html')


def process_capture(image):
    image = resize(image)
    image = gray(image)
    image = blur(image)
    image = thresh(image)
    image = morph(image)
    return image


def extract_data(image):
    # Initialize the values we are hoping to extract
    expiration = ""
    first_name = ""
    last_name = ""
    issued = ""
    address = ""

    # I am developing on a windows laptop, but will deploy to linux server
    if platform.system() == 'Windows':
        pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
    cv2.imwrite("processed_capture.jpg", image)

    # Get the text from the image and split it into lines
    text = pytesseract.pytesseract.image_to_string(image)
    _lines = text.split("\n")
    print(_lines)

    # Filter out blank lines
    lines = []
    for line in _lines:
        if line != '':
            lines.append(line)

    exp_index = 0
    for line in lines:
        matches = list(datefinder.find_dates(line))
        if len(matches) > 0:
            expiration = matches[0]
            break
        else:
            exp_index += 1
    print(exp_index)

    ln_line = lines[exp_index + 1]
    for char in ln_line:
        if char.isalpha() and char.isupper():
            last_name += char

    fn_line = lines[exp_index + 2]
    for char in fn_line:
        if char.isalpha() and char.isupper():
            first_name += char

    address = lines[exp_index + 3] + " " + lines[exp_index + 4]

    iss_line = lines[-1]
    issued = iss_line.split(' ')[-1]
    #     key = line[:3]
    #     if key == "exp":
    #         try:
    #             expiration = dateutil.parser.parse(line)
    #         except:
    #             print("Expiration parsing failed. Input: " + line)
    #     elif key == "ln ":
    #         last_name = line[3:]
    #     elif key == "fn ":
    #         first_name = line[3:]
    #
    # last_line_split = lines[-1].split(' ')
    # issued = last_line_split[-1]

    print(lines)

    results = {
        'name': first_name + " " + last_name,
        'address': address,
        'issuance': issued,
        'expiration': expiration,
    }
    return results, lines


@app.route('/display_results')
def display_results():
    global cam
    global cam_on
    cam_on = False
    cam.release()
    cv2.imwrite('capture.jpg', raw_image)
    processed_image = process_capture(raw_image)
    results, lines = extract_data(processed_image)
    return render_template("results.html", results=results)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)