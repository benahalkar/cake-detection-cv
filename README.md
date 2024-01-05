# cake-detection-cv

# PYTHON3.x BASED APPLICATION BUILT FOR RASPBERRY PI

![image](./images/main.png)

### ABOUT THIS REPOSITORY
This repository contains all codes developed for cake/color detection application.

All code written is for **Python3.x** language.

Although this application was created for differentiating between pieces of cake, **it's deployment is not limited to cakes**, and can be used for any **3-D non-transparent object/**. Examples include, but are not limited to fruits, medicines, packets, boxes, etc.

### HOW TO USE THIS REPOSITORY
- It is highly recommended to go-through the code, before making any modifications to the code.
- Comments are present in all python-codes. These comments explain the working of each line/section of code. Every function is accompanied by a docString to understand the function better.
- The application runs on very specific versions of python libraries namely OpenCv, numpy, sklearn, tkinter. Make sure the libraries in a new device are compatible with the application.


### DOWNLOAD THE REPO

first move to the path on the raspberrypi

```
mv /home/pi/Desktop
```
<br>

clone the repo

```
git clone https://github.com/benahalkar/cake-detection-cv.git cake_detection
```

<br>

you can change the startup logo bmp file kept at the path. Replace it with a bmp file of resolution 1062px x 295px

```
/home/pi/Desktop/cake_detection/data_log/startup_logo.bmp
```
