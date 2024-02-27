from flask import Flask, render_template, Response, request, jsonify, make_response, redirect
from process import *
import cv2
import platform
import pytesseract.pytesseract
import os
import datefinder
import base64
import numpy
from io import BytesIO
from PIL import Image
import user_agents

# Tell Tesseract-OCR where to find its training data
os.environ['TESSDATA_PREFIX'] = 'Tesseract-OCR/tessdata'

# This global will hold the image as it is passed between different view functions
raw_image = None

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/video')
def video():
    # user_agents is used to tell the app whether the user is on mobile or desktop
    ua_string = request.headers.get('User-Agent')
    user_agent = user_agents.parse(ua_string)
    if user_agent.is_mobile or user_agent.is_tablet:
        return render_template('mobile_video.html')
    else:
        return render_template('video.html')


@app.route('/post_image', methods=["GET", "POST"])
def post_image():
    # post_image handles the POST request from the frontend, and opens the
    # image in the raw_image global variable
    global raw_image
    image_url = request.form['data']
    starter = image_url.find(',')
    image_string = image_url[starter + 1:]
    raw_image = Image.open(BytesIO(base64.b64decode(image_string)))
    response = make_response(jsonify({'message': 'got image'}, 200))
    response.headers['Content-type'] = 'application/json'
    return response


@app.route('/display_capture')
def display_capture():
    # This handles returning the capture for use in the review_image endpoint
    global raw_image
    # format raw_image for use with openCV
    raw_image = numpy.array(raw_image)
    raw_image = raw_image[:, :, ::-1].copy()
    # convert to JPEG bytes and return content type for browser
    flag, output_frame = cv2.imencode('.jpg', raw_image)
    image_bytes = (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(output_frame) + b'\r\n')
    return Response(image_bytes, mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route('/review_image')
def review_image():
    return render_template('review_image.html')


def process_capture(image):
    # Preprocessing functions are defined in process.py
    image = resize(image)
    image = gray(image)
    image = blur(image)
    image = thresh(image)
    image = morph(image)
    return image


def extract_lines(image):
    # The path for tesseract executables differs by operating system
    if platform.system() == 'Windows':
        pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
    elif platform.system() == 'Linux':
        pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
    elif platform.system() == 'Darwin':
        pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

    # Call Tesseract to get the text from the image and split it into lines
    text = pytesseract.pytesseract.image_to_string(image)
    _lines = text.split("\n")
    return _lines


def extract_data(image):
    # Initialize the values we are hoping to extract
    expiration = ""
    first_name = ""
    last_name = ""
    issued = ""
    address = ""

    _lines = extract_lines(image)
    print(_lines)

    # Filter out blank lines
    lines = []
    for line in _lines:
        if line != '':
            lines.append(line)

    # Find the first instance of a date, which is expiration, and save the index
    exp_index = 0
    for line in lines:
        matches = list(datefinder.find_dates(line))
        if len(matches) > 0:
            expiration = matches[0]
            break
        else:
            exp_index += 1

    # Use the expiration index as a reference to find the other data
    ln_line = lines[exp_index + 1]
    for char in ln_line:
        if char.isalpha() and char.isupper():
            last_name += char

    fn_line = lines[exp_index + 2]
    for char in fn_line:
        if char.isalpha() and char.isupper():
            first_name += char

    address += lines[exp_index + 3] + " " + lines[exp_index + 4]

    iss_line = lines[-1]
    issued += iss_line.split(' ')[-1]

    # return the extracted data as a dictionary
    results = {
        'name': first_name + " " + last_name,
        'address': address,
        'issuance': issued,
        'expiration': expiration,
    }
    return results, lines


@app.route('/display_results')
def display_results():
    processed_image = process_capture(raw_image)
    # If there is an exception, a different page is returned which shows the text
    # from Tesseract, and prompts the user to try again
    try:
        results, lines = extract_data(processed_image)
        return render_template("results.html", results=results)
    except:
        lines = extract_lines(processed_image)
        return render_template('ocr_failed.html', lines=lines)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=443, debug=True, ssl_context='adhoc')
