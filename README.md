sudo apt install libgl1-mesa-glx
sudo add-apt-repository ppa:alex-p/tesseract-ocr5
sudo apt update
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev

mkdir root/ez-scanner/Tesseract-OCR
cp -r usr/share/tesseract-ocr/4.00/tessdata/ root/ez-scanner/Tesseract-OCR/tessdata/