# EZ-Scanner

This is a web application for extracting data from a driver's license using your device's webcam.
The app is available at https://64.23.194.199 both on mobile and PC browsers. 
It is also available for download and use as a locally hosted application.

Please note: the application currently only supports California driver's licenses.

## About

At its core, this app is powered by Flask web framework, and Google's Tesseract Optical Character Recognition (OCR) 
library. It also makes use of other powerful libraries such as OpenCV2, Python Image Library (PIL), and numpy, among 
others.

The user interacts with the app through buttons in their browser. The user is asked for input to take a photo of their 
ID using their device's webcam, and to confirm that the image is of reasonable quality before the app attempts to 
extract Name, Address, Issue Date, and Expiration Date from the image. 

Accessing data from the user's webcam while the app is running on a remote server was one of the major roadblocks I 
faced while building this application. It is achieved different depending on if the user is accessing the app from a 
mobile or desktop browser. On mobile, I used an HTML input tag with type="file" and accept="image/*" to gain access to
the user's device camera. On desktop, I made use of mediaDevices.getUserMedia() to gain access to the device's camera. 
One important note on this method is that it cannot be used with an http connection, only https, which explains the need 
for SSL certificates in the app. After gaining access to the camera, the user captures an image, and submits it with
a button on the page. That button uses Javascript to trigger a POST request to the backend containing the image data, 
and a redirect to a page where the user can review and approve their capture.

Upon approval of the capture, the app then needs to perform some preprocessing of the image to prepare it for use with Tesseract, using a 
variety of OpenCV processing methods. First, if the image is larger than 0.8 megapixels, it is scaled down to 
approximately that size. This is because the preprocessing methods need to be tuned differently for different amounts of 
image data. To reduce development time, I created only two preprocessing pathways: one for input images smaller than 
0.8 megapixels, and one for input images scaled down to 0.8 megapixels. Next, the image goes through the preprocessing 
pathway, which consists of grayscaling, blurring, thresholding, and morphing. I attempted to implement other 
preprocessing methods, which you can see in process.py. After much trial and error, I settled on the aforementioned 
methods, as they consistently returned the best results. 

After the image is preprocessed, it is ready for text recognition with Tesseract-OCR. I found the performance of 
Tesseract 5 to be far superior to Tesseract 4 when used on the same image. I also found Tesseract's default Page 
Segmentation Mode (PSM) to be superior to other PSM config options. Once the text is extracted, it is grouped by line, 
and the desired fields are extracted using a brute force method which involves finding the location of the first line
containing a date (the expiration date), and using that as a reference to find the lines containing the other desired 
fields. If the data extraction was deemed to be successful, the app returns the fields as key-values pairs. If not, it
returns the text that it extracted so that the user can see and then retry.

The most critical part of the backend of this application is undoubtedly the image processing. If the image is not processed well, the 
results of using Tesseract can vary dramatically. Issues with the image processing originate from low-quality captures
of the ID. Some examples include glare on the original image, insufficient illumination of the original image, low-pixel
count, and skewing of the image.

### Assumptions

When testing and tuning this application, I used a California State driver's license, and a webcam with a maximum 
resolution of 640x480 pixels.

## Installation

To run this application locally, you will need to install the EZ-Scanner app and Tesseract-OCR. It is very important 
that the Tesseract data is in the correct directory. Please see below for more details.

### EZ-Scanner Install

```commandline
git clone https://github.com/alexgarnett/ez-scanner
pip install -r requirements.txt
```

### Tesseract Install

#### Ubuntu

In order to install Tesseract 5, we will need to add a PPA repository. Using a Tesseract version older than 5 may result
in significant degradation in performance. 
```commandline
sudo add-apt-repository ppa:alex-p/tesseract-ocr5
sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev
```

The app sets the environment variable _TESSDATA_PREFIX_ to "Tesseract-OCR/tessdata". Use the following commands to 
create the appropriate directory and move the Tesseract data there. 
```commandline
mkdir root/ez-scanner/Tesseract-OCR
cp -r usr/share/tesseract-ocr/5.00/tessdata/ root/ez-scanner/Tesseract-OCR/tessdata/
```

OpenCV depends on libGL, which can be missing from some distributions. Run the following command to make sure that you
have the latest version.
```commandline
sudo apt install libgl1-mesa-glx
```

#### Windows and MacOS

Please follow the installation instructions in the README at https://github.com/tesseract-ocr/tessdoc. Please be sure to 
install Tesseract 5. Using an older version of Tesseract may result in significant degradation in performance.

The app sets the environment variable _TESSDATA_PREFIX_ to "Tesseract-OCR/tessdata". Upon successful installation of 
Tesseract, please locate the Tesseract trained data folder called "tessdata" and place it in a directory named 
"Tesseract-OCR" in the root directory of this project. Refer to the tessdoc README for details regarding where to 
locate the "tessdata" folder.

**ADDITIONAL STEP FOR WINDOWS USERS:** The EZ-Scanner app looks for the executable file "tesseract.exe" in the 
"Tesseract-OCR" directory. For this reason, it is recommended to specify the EZ-Scanner project directory as the 
install location during installation, or simply move the entire Tesseract folder into the project directory after 
installing.


## Usage

To run the app locally, execute the following command from the root of the EZ-Scanner directory.
```commandline
python3 app.py
```

The app runs on https://127.0.0.1:443, or whichever IP your localhost resolves to.

Follow the prompts in the app to use it.

**PLEASE NOTE:** Because the app currently uses adhoc SSL context, you may get a warning screen on your browser saying 
that your connection is not private. You must proceed past this warning in order to use the app.

## Future Work

#### Support for Additional State's Licenses

In its current state this application supports data extraction from only California Drivers Licenses. This is the only 
ID I had access to while creating the app. Additionally, the app uses a brute force method of extracting the desired 
fields from the parsed text, which would need to be changed if other IDs were to be used.

#### Structural Pattern Matching for Data Extraction

Pattern matching could provide an improvement over the current implementation for extracting the desired fields from 
parsed text. This would likely make data extraction from the currently supported IDs more robust, while potentially 
adding the ability to extract data fields from other ID templates at the cost of extra computational resources.

#### Machine Learning Model for Data Extraction

Implementing a machine learning model would likely be the most robust solution for extracting desired data from any ID 
template. This would be a much higher increase in required computational resources, but would likely result in the best 
performance of the application, assuming the model is accurate and the image is of high quality.

#### Implement Proper SSL Certificates

In its current state, the app utilizes adhoc SSL certificates. Some form of SSL certificate was required in order to 
use getUserMedia(), which is crucial to accessing the user device's webcam on desktop browsers. However, using adhoc 
certs results in a big scary window displaying a warning about the website's security before the user accesses the 
site. An improvement would be to use "real" certificates from a well-known Certificate Authority such as Let's Encrypt, 
so that users did not have to navigate through the warning window.

#### Add DNS Routing

The web app is currently accessible remotely only by using the IP of the server in your URL. A future improvement would 
be to purchase a domain name for the site and register it with a DNS so that it is accessible by a name. Something like 
ez-scanner.com would be appropriate.

#### Improved Image Preprocessing

The most crucial element of this app to achieve good data extraction results, following a quality input image, is 
undoubtedly the image preprocessing. Prior to this project I did not have any experience with image processing for OCR. 
I learned alot building this application, and was able to successfully implement some preprocessing methods to achieve 
good results. Additional preprocessing steps or improved tuning of the 
current steps could yield even better data extraction results.

#### Preprocessing Pathways for Higher Quality Images

In order to cut down on development time, I scaled any large images down to 0.8 megapixels before preprocessing, so that I did not have to 
tune the preprocessing steps for lots of different sizes of image data. Considering that new iPhone cameras capture 
10 megapixel images, this app may trim lots of data that could be used to improve the results of the text 
extraction. As a future improvement, additional preprocessing pathways could be built that are tuned to handle much 
larger images.