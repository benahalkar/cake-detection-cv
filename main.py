#! /usr/bin/python3

# ===================================================================================
# APPLICATION : Generic color detection code (built for cake detection application)
#      AUTHOR : Harsh Benahalkar
#      DEVICE : Raspberry-pi (with HDMI monitor), connected to USB camera
#        DATE : 05th May 2022
# ===================================================================================

from numpy import imag
import cv2 as cv                        # NOTE Open CV             library/ies
import tkinter as tk                    # NOTE Tkinter             library/ies
from PIL import Image, ImageTk          # NOTE Pillow              library/ies
import time, json, random, os           # NOTE Other basic         library/ies
import style                            # NOTE style.py            file
import image_processing as img_proc     # NOTE image_processing.py file
import RPi.GPIO as GPIO

screen_readstatus, screen_width, screen_height = img_proc.get_screensize()
        
class run_device:
    '''
    Definition:
    -----------
    Class is responsible for run-mode.\n
    Class creates a page.\n
    Class provides a video stream on said page.\n
    Class also shows user where which sections of the stream will be processed (ROI/s).\n
    Class calls image-processing function/s to calculate mean-color/s inside said ROIs.\n
    Class notifies user whether said mean-color/s are within user-specified error margin or not.\n 
    
    '''
    # [NOTE EXPLANATION] Initialise run-mode page Class.
    def __init__(self):
        # [NOTE EXPLANATION] Start the run-mode page.
        self.run_page = tk.Toplevel()
        self.run_page.title('Run Device')
        self.run_page.attributes('-fullscreen', True)

        GPIO.add_event_detect(12, GPIO.RISING, callback=self.gpioCallback)

        # [NOTE EXPLANATION] Create a canvas so that the video stream can be shown on it.
        self.video_canvas = tk.Canvas(self.run_page, width=screen_height, height=screen_height)
        self.video_canvas.configure(background=style.COLOR_BLUE)
        self.video_canvas.place(x=0, y=0)

        # [NOTE EXPLANATION] Create another canvas so that the widgets can be placed on it.
        run_canvas_width = screen_width-screen_height
        run_canvas_height = screen_height
        self.run_canvas = tk.Canvas(self.run_page, width=run_canvas_width, height=run_canvas_height)
        self.run_canvas.configure(background=style.PAGE_BACKGROUND)
        self.run_canvas.place(x=screen_height, y=0)

        # [NOTE EXPLANATION] Create page-title and notification label and place on page/canvas.
        self.label1 = tk.Label(self.run_canvas, text="CLICK PICTURE\nTO COMPARE")
        self.label1.configure(  background=style.COLOR_WHITE,
                                foreground=style.COLOR_BLACK,
                                font=(style.FONT,30,"bold"))
        self.label1.place(relx = 0.5, anchor=tk.CENTER,y=1*run_canvas_height//10)

        self.label2 = tk.Label(self.run_canvas)
        self.label2.configure(  background=style.COLOR_WHITE,
                                foreground=style.COLOR_RED,
                                font=(style.FONT,30))
        self.label2.place(relx = 0.5, anchor=tk.CENTER,y=3*run_canvas_height//10)

        # [NOTE EXPLANATION] Create and configure and place buttons on main page/canvas.
        self.button1=tk.Button(self.run_canvas, text="TRIGGER CAMERA", command=self.take_picture_now)
        self.button1.configure( width=30, 
                                height =3,
                                font=(style.FONT, 15), 
                                background=style.COLOR_BLUE, 
                                activebackground=style.COLOR_DARKBLUE,
                                foreground=style.COLOR_WHITE,
                                activeforeground=style.COLOR_WHITE)
        self.button1.place(relx = 0.5, anchor=tk.CENTER, y=4*screen_height//8)

        self.button2=tk.Button(self.run_canvas, text="GO BACK", command=self.go_back)
        self.button2.configure( width=30, 
                                height =3,
                                font=(style.FONT, 15), 
                                background=style.COLOR_RED, 
                                activebackground=style.COLOR_DARKRED,
                                foreground=style.COLOR_WHITE,
                                activeforeground=style.COLOR_WHITE)
        self.button2.place(relx = 0.5, anchor=tk.CENTER, y=6*screen_height//8)

        # NOTE configure gpios here
        with open(style.JSON_FILE, 'r') as file:
            self.config = json.load(file)
            file.close()
            # print(self.config)

        # [NOTE EXPLANATION] Configure camera and stream-variables.
        self.camera = cv.VideoCapture(style.USB_CAMERA)
        self.camera.set(cv.CAP_PROP_FPS, style.VIDEO_STREAM_FPS)
        self.picture_clicked = False
        self.stream_interval = 10 #miliseconds
        self.update_stream()

    def take_picture_now(self):
        '''
        Definition:
        -----------
        Function first clicks a picture when user triggers it.\n
        Picture clicked is cropped to an aspect-ratio of 1:1 (i.e. square).\n
        Picture is stored in the device.\n        
        Stored picture is shown to the user.\n
        User is notified if picture is clicked successfully or not.\n
        Picture is processed to get the dominant-colors of all user-defined ROIs.\n
        Colors obtained are compared against the user-entered error-margin.\n
        User is notfied whether individual ROIs are within or beyond the error-margin.\n
        
        '''
        # [NOTE EXPLANATION] Check if camera is connected to USB-port or not.
        if self.camera.isOpened() == True:
            ret, frame = self.camera.read()
            if ret == True:
                # [NOTE EXPLANATION] Image needs to be cropped to a 1:1 aspect ratio.
                img_width, img_height = int(frame.shape[1]), int(frame.shape[0])
                if img_width > img_height:
                    frame = frame[0:img_height, int((img_width - img_height)/2):int((img_width + img_height)/2)]
                else:
                    frame = frame[int((img_height - img_width)/2):int((img_height + img_width)/2), 0:img_width]
                
                # [NOTE EXPLANATION] resize and store said image.
                dsize = (screen_height, screen_height)
                frame = cv.resize(frame, dsize=dsize)                
                cv.imwrite(style.REALTIME_IMAGE, frame)

                # [NOTE EXPLANATION] Disconnect camera now.
                if self.camera.isOpened() == True:
                    self.camera.release()

                # [NOTE EXPLANATION] Notify user that picture has been taken successfully.
                self.picture_clicked = True
                self.label2.configure(text='PICTURE CLICKED\nSUCCESSFULLY')
                self.label1.configure(text="RESULTS")
                self.button1.configure(state=tk.DISABLED)
                self.button2.configure(command=self.run_again)

                # [NOTE EXPLANATION] Get dominant color in every ROI.
                img_proc.compare_colors(style.REALTIME_IMAGE, style.JSON_FILE, style.OUTPUT_FILE, style.MASK_IMAGE_PATH)
                # [NOTE EXPLANATION] Display picture clicked on the canvas.
                image = cv.imread(style.REALTIME_IMAGE)
                image = cv.cvtColor(image, cv.COLOR_BGR2RGBA)
                pil_frame = Image.fromarray(image)
                pil_frame = pil_frame.resize((screen_height, screen_height))
                pil_pic = ImageTk.PhotoImage(image = pil_frame)
                self.video_canvas.create_image((0, 0), image=pil_pic, anchor=tk.NW)
                self.video_canvas.image = pil_pic

                # [NOTE EXPLANATION] Open config file/s.
                with open(style.OUTPUT_FILE, 'r') as file:
                    color_config = json.load(file)
                    file.close()

                with open(style.APP_CONFIG_JSON, 'r') as file:
                    param_config = json.load(file)
                    file.close()

                # [NOTE EXPLANATION] Highlight ROI on the screen, and in highlight them in GREEN/RED.
                # [NOTE EXPLANATION] GREEN indicates that color has matched.
                # [NOTE EXPLANATION] RED indicates that color has not matched.
                color_dict = {}
                for key in color_config:
                    success = color_config[key]["success_status"]
                    fill_color = style.RESULT_GREEN if success == True else style.RESULT_RED
                    color_dict[key] = fill_color
                    # print(fill_color, success)
                for key in self.config:
                    coordinates = self.config[key]["coordinates"]
                    for i in range(1, len(coordinates)):
                        self.video_canvas.create_line(  coordinates[i-1][0], coordinates[i-1][1],
                                                        coordinates[i][0], coordinates[i][1],
                                                        fill=color_dict[key], 
                                                        width=8)                

                    self.video_canvas.create_line(      coordinates[0][0], coordinates[0][1],
                                                        coordinates[len(coordinates)-1][0], coordinates[len(coordinates)-1][1],
                                                        fill=color_dict[key], 
                                                        width=8)
                    extremes = self.config[key]['extremes_of_ROI']
                    # self.video_canvas

                    # [NOTE EXPLANATION] Display the difference in color in terms of percentage.
                    label = tk.Label(self.video_canvas, text=str(color_config[key]['error']) + ' / ' + str(param_config['error_margin']))
                    label.configure(background=style.COLOR_BLACK,
                                    foreground=style.COLOR_WHITE,
                                    font=(style.FONT,10,"bold"))
                    label.place(x=extremes[0], y=extremes[1] - 30)
            
            else:
                self.label2.configure(text='PLEASE CLICK AGAIN')
        else:
            self.label2.configure(text='ERROR!\nCAMERA NOT OPEN')

        self.update_stream()

    def gpioCallback(self, channel):
        print("Channel Interrupt {}".format(channel))
        if channel == style.GPIO_CAMERA_TRIGGER_PIN:
            print("yes executing")
            self.take_picture_now()

    def run_again(self):
        '''
        Definition:
        -----------
        After one run-mode iteration has been completed, user may want to run the application again.\n
        Function provides the feature of running it again, without the user having to STOP the application or return to main-screen and RUN.\n       
        
        '''
        for widgets in self.video_canvas.winfo_children():
            widgets.destroy()
        self.button1.configure(state=tk.ACTIVE)
        self.button2.configure(command=self.go_back)
        self.label1.configure(text="CLICK PICTURE\nTO COMPARE")
        self.label2.configure(text="")
        self.picture_clicked = False
        self.camera = cv.VideoCapture(style.USB_CAMERA)
        self.camera.set(cv.CAP_PROP_FPS, style.VIDEO_STREAM_FPS)
        self.update_stream()

    def update_stream(self):
        '''
        Definition:
        -----------
        Function creates a constant stream of video.\n
        Function updates the stream feed periodically.\n
        Screenshot is taken at an instant, and the picture is cropped and displayed on the screen.\n
        The user-selected ROIs are also shown on the screen for better accuracy, and the user can align the camera/object accordingly.\n
        The ROIs are also highlighted in their respective colors to show which ROI corresponds to which color.\n
        
        '''
        if self.picture_clicked == False:
            # self.camera = cv.VideoCapture(style.USB_CAMERA)

            # [NOTE EXPLANATION] Check if camera is connected to USB-port or not.
            if self.camera.isOpened() == True:
                ret, frame = self.camera.read()
                if ret == True:
                    # [NOTE EXPLANATION] Image needs to be cropped to a 1:1 aspect ratio.
                    img_width, img_height = int(frame.shape[1]), int(frame.shape[0])
                    if img_width > img_height:
                        frame = frame[0:img_height, int((img_width - img_height)/2):int((img_width + img_height)/2)]
                    else:
                        frame = frame[int((img_height - img_width)/2):int((img_height + img_width)/2), 0:img_width]
                    # img_width, img_height = int(frame.shape[1]), int(frame.shape[0])

                    # [NOTE EXPLANATION] resize and store and show said image on canvas.
                    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                    pil_frame = Image.fromarray(frame)
                    pil_frame = pil_frame.resize((screen_height, screen_height))
                    pil_pic = ImageTk.PhotoImage(image = pil_frame)
                    self.video_canvas.create_image((0, 0), image=pil_pic, anchor=tk.NW)
                    self.video_canvas.image = pil_pic

                    # [NOTE EXPLANATION] Show the ROIs on the stream, with the color in which they were detected while calibrating.
                    for key in self.config:
                        coordinates = self.config[key]["coordinates"]
                        color = img_proc.tkinter_compatible_color(self.config[key]["mean_color"])
                        for i in range(1, len(coordinates)):
                            self.video_canvas.create_line(  coordinates[i-1][0], coordinates[i-1][1],
                                                            coordinates[i][0], coordinates[i][1],
                                                            fill=color, 
                                                            width=8)                

                        self.video_canvas.create_line(      coordinates[0][0], coordinates[0][1],
                                                            coordinates[len(coordinates)-1][0], coordinates[len(coordinates)-1][1],
                                                            fill=color, 
                                                            width=8)
                                                            
                self.label2.configure(text="TAKE A PICTURE\nTO RUN DEVICE")     
            else:
                # [NOTE EXPLANATION] Notify user that camera is not connected.
                time.sleep(0.015)
                # print('camera not connected')
                self.label2.configure(text='ERROR!\nCAMERA NOT CONNECTED')

            self.run_page.after(self.stream_interval, self.update_stream)

    def go_back(self):
        '''
        Definition:
        -----------
        Function returns to main-page.\n
        
        '''
        if self.picture_clicked == False and self.camera.isOpened() == True:
            self.camera.release()
        self.run_page.destroy()
        GPIO.remove_event_detect(12)

class select_ROI:
    '''
    Definition:
    -----------
    Class is responsible for letting user select ROI/s.\n
    Class creates a page.\n
    Class provides user-clicked picture on said page.\n
    User can add/modify/delete points for a ROI.\n
    User can submit multiple ROIs.\n
    User can reset screen to select ROI/s again.\n
    Any region is defined by a minimum of 3 vertex-points.\n
    Class performs exception-handling of allowing an ROI to exist only if 3 points are selected by user.\n
    Class also performs exception-handling of ensuring that atleast one ROI is selected for calibration of device.\n
    Class then calls image-processing functions to compute dominant color of individual ROI/s and storing data in a file.\n
    
    '''
    # [NOTE EXPLANATION] Initialise select-ROI page Class.
    def __init__(self, previous_page):
        self.prev_page = previous_page
        self.all_ROI = {}
        self.ROI_index = 1
        self.temp_ROI = []
        self.tkinter_ROI_points = []
        self.tkinter_ROI_lines = []
        self.first_x, self.first_y = None, None
        self.previous_x, self.previous_y = None, None 
        self.current_x, self.current_x = None, None

        # [NOTE EXPLANATION] Start the select-ROI page.
        self.ROI_page = tk.Toplevel()
        self.ROI_page.title('Select ROI')
        self.ROI_page.attributes('-fullscreen', True)

        # [NOTE EXPLANATION] Create a canvas so that the clicked-picture stream can be shown on it.
        self.image_canvas = tk.Canvas(self.ROI_page, width=screen_height, height=screen_height)
        self.image_canvas.configure(background=style.COLOR_GREY)
        self.image_canvas.place(x=0, y=0)

        # [NOTE EXPLANATION] Show clicked-picture on said canvas.
        image = cv.imread(style.REFERENCE_IMAGE)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGBA)
        pil_frame = Image.fromarray(image)
        pil_frame = pil_frame.resize((screen_height, screen_height))
        pil_pic = ImageTk.PhotoImage(image = pil_frame)
        self.image_canvas.create_image((0, 0), image=pil_pic, anchor=tk.NW)
        self.image_canvas.image = pil_pic

        # [NOTE EXPLANATION] Add mouse-click event on canvas.
        self.image_canvas.bind("<Button-1>", self.add_ROI_point)

        # [NOTE EXPLANATION] Create another canvas so that the widgets can be placed on it.
        button_canvas_width = screen_width-screen_height
        button_canvas_height = screen_height
        self.button_canvas = tk.Canvas(self.ROI_page, width=button_canvas_width, height=button_canvas_height)
        self.button_canvas.configure(background=style.PAGE_BACKGROUND)
        self.button_canvas.place(x=screen_height, y=0)

        # [NOTE EXPLANATION] Create page-title and notification label and place on page/canvas.
        self.label1 = tk.Label(self.button_canvas, text="SELECT\nREGION OF INTEREST")
        self.label1.configure(  background=style.COLOR_WHITE,
                                foreground=style.COLOR_BLACK,
                                font=(style.FONT,30,"bold"))
        self.label1.place(relx = 0.5, anchor=tk.CENTER,y=1*button_canvas_height//10)

        self.label2 = tk.Label(self.button_canvas)
        self.label2.configure(  background=style.COLOR_WHITE,
                                foreground=style.COLOR_RED,
                                font=(style.FONT,30))
        self.label2.place(relx = 0.5, anchor=tk.CENTER,y=2.5*button_canvas_height//10)

        # [NOTE EXPLANATION] Create and configure and place buttons on said page/canvas.
        self.button1=tk.Button(self.button_canvas, text="DELETE RECENT ROI POINT", command=self.remove_last_ROI)
        self.button1.configure( width=30, 
                                height =2,
                                font=(style.FONT, 15), 
                                background=style.COLOR_BLUE, 
                                activebackground=style.COLOR_DARKBLUE,
                                foreground=style.COLOR_WHITE,
                                activeforeground=style.COLOR_WHITE)
        self.button1.place(relx = 0.5, anchor=tk.CENTER, y=4*screen_height//8)

        self.button2=tk.Button(self.button_canvas, text="ADD ANOTHER ROI", command = self.add_another_ROI)
        self.button2.configure( width=30, 
                                height =2,
                                font=(style.FONT, 15), 
                                background=style.COLOR_BLUE, 
                                activebackground=style.COLOR_DARKBLUE,
                                foreground=style.COLOR_WHITE,
                                activeforeground=style.COLOR_WHITE)
        self.button2.place(relx = 0.5, anchor=tk.CENTER, y=5*screen_height//8)

        self.button3=tk.Button(self.button_canvas, text="ALL DONE", command=self.all_done)
        self.button3.configure( width=30, 
                                height =2,
                                font=(style.FONT, 15), 
                                background=style.COLOR_BLUE, 
                                activebackground=style.COLOR_DARKBLUE,
                                foreground=style.COLOR_WHITE,
                                activeforeground=style.COLOR_WHITE)
        self.button3.place(relx = 0.5, anchor=tk.CENTER, y=6*screen_height//8)

        self.button4=tk.Button(self.button_canvas, text="RESET SCREEN", command=self.reset_page)
        self.button4.configure( width=30, 
                                height =2,
                                font=(style.FONT, 15), 
                                background=style.COLOR_RED, 
                                activebackground=style.COLOR_DARKRED,
                                foreground=style.COLOR_WHITE,
                                activeforeground=style.COLOR_WHITE)
        # self.button4.place(x=2*(button_canvas_width)//10, y=7*screen_height//8)
        self.button4.place(relx = 0.5, anchor=tk.CENTER, y=7*screen_height//8)

    def add_ROI_point(self, event):
        '''
        Definition:
        -----------
        Stores the (x, y) coordinates of the point when user clicks via mouse or via touch-screen.\n
        '''
        x, y = event.x, event.y
        self.current_x, self.current_y = x, y
        if len(self.temp_ROI) == 0: 
            self.first_x = x
            self.first_y = y

        if len(self.temp_ROI) !=0: 
            line = self.image_canvas.create_line(  self.previous_x, self.previous_y,
                                            x, y, 
                                            fill=style.SHAPE_OUTLINE, 
                                            width=1)
            self.tkinter_ROI_lines.append(line)

        point = self.image_canvas.create_rectangle( x, y, 
                                                    x + style.SHAPE_PIXEL_SIZE, y + style.SHAPE_PIXEL_SIZE,
                                                    outline=style.SHAPE_FILL,
                                                    fill=style.SHAPE_FILL,
                                                    width=1)
        self.temp_ROI.append([x, y])
        self.previous_x, self.previous_y = x, y
        self.tkinter_ROI_points.append(point)
        self.label2.configure(text='NEW POINT ADDED')
    
    def remove_last_ROI(self):
        '''
        Definition:
        -----------
        Deletes the last entered (x, y) coordinate.\n
        '''
        if len(self.tkinter_ROI_points) != 0: 
            self.image_canvas.delete(self.tkinter_ROI_points.pop())
            self.temp_ROI.pop()
            self.previous_x, self.previous_y = (self.temp_ROI[-1])[0], (self.temp_ROI[-1])[1]
        else: 
            self.label2.configure(text='NO MORE POINTS\nTO DELETE')
            self.previous_y, self.previous_x = None, None
            self.first_x, self.first_y = None, None

        if len(self.tkinter_ROI_lines) != 0: 
            self.image_canvas.delete(self.tkinter_ROI_lines.pop())

    def add_another_ROI(self):
        '''
        Definition:
        -----------
        Allows the user to enter multiple ROIs.\n
        '''
        if len(self.temp_ROI) >= 3:
            self.all_ROI['ROI' + str(self.ROI_index)] = {}
            self.all_ROI['ROI' + str(self.ROI_index)]['coordinates'] = self.temp_ROI
            # self.all_ROI.append(self.temp_ROI)
            line = self.image_canvas.create_line(   self.current_x, self.current_y,
                                                    self.first_x, self.first_y,
                                                    fill=style.SHAPE_OUTLINE, 
                                                    width=1)
            self.previous_y, self.previous_x = None, None
            self.first_x, self.first_y = None, None
            self.temp_ROI = []
            self.tkinter_ROI_points = []
            self.tkinter_ROI_lines = []
            self.ROI_index = self.ROI_index + 1
        else:
            self.label2.configure(text='SELECT ATLEAST\n3 POINTS FIRST')

    def all_done(self):
        '''
        Definition:
        -----------
        Allows the user to go back to main-page after selecting all ROI/s.\n
        '''
        if self.ROI_index != 1:
            with open(style.JSON_FILE, 'w') as file:
                file.write(json.dumps(self.all_ROI))
                file.close()
            img_proc.get_mean_colors(style.REFERENCE_IMAGE, style.JSON_FILE, style.MASK_IMAGE_PATH)
            self.ROI_page.destroy()
            self.prev_page.destroy()
        else:
            self.label2.configure(text='SELECT ATLEAST\n1 ROI')

    def reset_page(self):
        '''
        Definition:
        -----------
        Removes all ROI points selected by the user and refreshes the screen.\n
        '''
        self.all_ROI = {}
        self.ROI_index = 1
        self.temp_ROI = []
        self.tkinter_ROI_points = []
        self.tkinter_ROI_lines = []
        self.first_x, self.first_y = None, None
        self.previous_x, self.previous_y = None, None 
        self.current_x, self.current_x = None, None

        image = cv.imread(style.REFERENCE_IMAGE)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGBA)
        pil_frame = Image.fromarray(image)
        pil_frame = pil_frame.resize((screen_height, screen_height))
        pil_pic = ImageTk.PhotoImage(image = pil_frame)
        self.image_canvas.create_image((0, 0), image=pil_pic, anchor=tk.NW)
        self.image_canvas.image = pil_pic

class take_reference_photo:
    '''
    Definition:
    -----------
    Class is responsible for initiating calibrate-mode.\n
    Class creates a page.\n
    Class provides a video stream on said page.\n
    Class lets user click picture so that user can select section/s of the stream which will be processed (ROI/s) later.\n
    Class calls another class to perform task of selecting ROI/s.\n
    
    '''
    # [NOTE EXPLANATION] Initialise calibrate-mode page Class.
    def __init__(self):    
        # [NOTE EXPLANATION] Start the calibrate-mode page.
        self.calibrate_page = tk.Toplevel()
        self.calibrate_page.title('Calibrate Device')
        self.calibrate_page.attributes('-fullscreen', True)

        # [NOTE EXPLANATION] Create a canvas so that the video stream can be shown on it.
        self.video_canvas = tk.Canvas(self.calibrate_page, width=screen_height, height=screen_height)
        self.video_canvas.configure(background=style.COLOR_BLUE)
        self.video_canvas.place(x=0, y=0)

        # [NOTE EXPLANATION] Create another canvas so that the widgets can be placed on it.
        calib_canvas_width = screen_width-screen_height
        calib_canvas_height = screen_height
        self.calib_canvas = tk.Canvas(self.calibrate_page, width=calib_canvas_width, height=calib_canvas_height)
        self.calib_canvas.configure(background=style.PAGE_BACKGROUND)
        self.calib_canvas.place(x=screen_height, y=0)

        # [NOTE EXPLANATION] Create page-title and notification label and place on page/canvas.
        self.label1 = tk.Label(self.calib_canvas, text="CALIBRATE MODE")
        self.label1.configure(  background=style.COLOR_WHITE,
                                foreground=style.COLOR_BLACK,
                                font=(style.FONT,30,"bold"))
        self.label1.place(relx = 0.5, anchor=tk.CENTER,y=1*calib_canvas_height//10)

        self.label2 = tk.Label(self.calib_canvas)
        self.label2.configure(  background=style.COLOR_WHITE,
                                foreground=style.COLOR_RED,
                                font=(style.FONT,30))
        self.label2.place(relx = 0.5, anchor=tk.CENTER,y=3*calib_canvas_height//10)

        # [NOTE EXPLANATION] Create feature (label + text box + button) to let user select error-margin.
        self.label3 = tk.Label(self.calib_canvas, text='ENTER ERROR MARGIN BELOW')
        self.label3.configure(  background=style.COLOR_WHITE,
                                foreground=style.COLOR_BLACK,
                                font=(style.FONT,20))
        self.label3.place(relx = 0.5, anchor=tk.CENTER,y=4.2*calib_canvas_height//10)

        self.error_margin = tk.StringVar()
        self.entry1 = tk.Entry(self.calib_canvas)
        self.entry1.configure(  bg=style.COLOR_WHITE,
                                fg=style.COLOR_BLACK,
                                width=10,
                                textvariable=self.error_margin,
                                bd=1,
                                font=(style.FONT, 30),
                                justify=tk.CENTER)
        # self.entry1.insert(0, 'ENTER ERROR MARGIN')
        self.entry1.place(relx = 0.5, anchor=tk.CENTER, y=5*calib_canvas_height//10)

        self.button3=tk.Button(self.calib_canvas, text="SUBMIT", command=self.add_error_margin)
        self.button3.configure( width=10, 
                                height =2,
                                font=(style.FONT, 15), 
                                background=style.COLOR_BLUE, 
                                activebackground=style.COLOR_DARKBLUE,
                                foreground=style.COLOR_WHITE,
                                activeforeground=style.COLOR_WHITE)
        self.button3.place(relx = 0.5, anchor=tk.CENTER, y=5*calib_canvas_height//8)

        # [NOTE EXPLANATION] Create and configure and place buttons on main page/canvas.
        self.button1=tk.Button(self.calib_canvas, text="TAKE PICTURE", command=self.take_picture_now)
        self.button1.configure( width=30, 
                                height =2,
                                font=(style.FONT, 15), 
                                background=style.COLOR_BLUE, 
                                activebackground=style.COLOR_DARKBLUE,
                                foreground=style.COLOR_WHITE,
                                activeforeground=style.COLOR_WHITE)
        self.button1.place(relx = 0.5, anchor=tk.CENTER, y=6*screen_height//8)

        self.button2=tk.Button(self.calib_canvas, text="GO BACK", command=self.close_calib_page)
        self.button2.configure( width=30, 
                                height =2,
                                font=(style.FONT, 15), 
                                background=style.COLOR_RED, 
                                activebackground=style.COLOR_DARKRED,
                                foreground=style.COLOR_WHITE,
                                activeforeground=style.COLOR_WHITE)
        self.button2.place(relx = 0.5, anchor=tk.CENTER, y=7*screen_height//8)

        # [NOTE EXPLANATION] Configure camera and stream-variables.
        self.camera = cv.VideoCapture(style.USB_CAMERA)
        self.camera.set(cv.CAP_PROP_FPS, style.VIDEO_STREAM_FPS)
        self.picture_clicked = False
        self.stream_interval = 15 #miliseconds
        self.update_stream()
        # self.calibrate_page.mainloop()

    def add_error_margin(self):
        '''
        Definition:
        -----------
        Function is called when user types and enters an error-margin.\n
        Function also checks whether entered error margin is a valid integer or not.\n
        Function then stores said error-margin in a file.\n

        '''
        json_dict = {}
        try:
            error_margin = int(self.error_margin.get())
            json_dict['error_margin'] = error_margin
            with open(style.APP_CONFIG_JSON, 'w') as file:
                file.write(json.dumps(json_dict))
                file.close()        
            self.label2.configure(text='UPDATED\nERROR MARGIN')
        except Exception as err:
            print('Error received while entering error margin is: {}'.format(err))
            self.label2.configure(text='ENTER ERROR\nMARGIN AGAIN')

    def update_stream(self):
        '''
        Definition:
        -----------
        Function creates a constant stream of video.\n
        Function updates the stream feed periodically.\n
        Screenshot is taken at an instant, and the picture is cropped and displayed on the screen.\n
        
        '''
        if self.picture_clicked == False:
            # self.camera = cv.VideoCapture(style.USB_CAMERA)

            # [NOTE EXPLANATION] Check if camera is connected to USB-port or not.
            if self.camera.isOpened() == True:
                ret, frame = self.camera.read()
                if ret == True:
                    # [NOTE EXPLANATION] Image needs to be cropped to a 1:1 aspect ratio.
                    img_width, img_height = int(frame.shape[1]), int(frame.shape[0])
                    if img_width > img_height:
                        frame = frame[0:img_height, int((img_width - img_height)/2):int((img_width + img_height)/2)]
                    else:
                        frame = frame[int((img_height - img_width)/2):int((img_height + img_width)/2), 0:img_width]
                    # img_width, img_height = int(frame.shape[1]), int(frame.shape[0])

                    # [NOTE EXPLANATION] resize and show said image on canvas.                
                    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                    pil_frame = Image.fromarray(frame)
                    pil_frame = pil_frame.resize((screen_height, screen_height))
                    pil_pic = ImageTk.PhotoImage(image = pil_frame)
                    self.video_canvas.create_image((0, 0), image=pil_pic, anchor=tk.NW)
                    self.video_canvas.image = pil_pic
                self.label2.configure(text="TAKE A PICTURE\nTO SELECT ROI")     
            else:
                # [NOTE EXPLANATION] Notify user that camera is not connected.
                time.sleep(0.015)
                # print('camera not connected')
                self.label2.configure(text='ERROR!\nCAMERA NOT CONNECTED')

            self.calibrate_page.after(self.stream_interval, self.update_stream)

    def take_picture_now(self):
        '''
        Definition:
        -----------
        Function first clicks a picture when user triggers it.\n
        Picture clicked is cropped to an aspect-ratio of 1:1 (i.e. square).\n
        Picture is stored in the device.\n        
        Stored picture is shown to the user.\n
        User is notified if picture is clicked successfully or not.\n
        Function calls another class to let user select ROIs.\n        
        '''
        # [NOTE EXPLANATION] Check if camera is connected to USB-port or not.
        if self.camera.isOpened() == True:
            ret, frame = self.camera.read()

            if ret == True:
                # [NOTE EXPLANATION] Image needs to be cropped to a 1:1 aspect ratio.
                img_width, img_height = int(frame.shape[1]), int(frame.shape[0])
                if img_width > img_height:
                    frame = frame[0:img_height, int((img_width - img_height)/2):int((img_width + img_height)/2)]
                else:
                    frame = frame[int((img_height - img_width)/2):int((img_height + img_width)/2), 0:img_width]
                
                # [NOTE EXPLANATION] resize and store said image.
                dsize = (screen_height, screen_height)
                frame = cv.resize(frame, dsize=dsize)

                cv.imwrite(style.REFERENCE_IMAGE, frame)
                
                if self.camera.isOpened() == True:
                    self.camera.release()
                self.picture_clicked = True
                self.label2.configure(text='PICTURE CLICKED\nSUCCESSFULLY')

                # [NOTE EXPLANATION] Call another class to select ROI/s.
                class_obj = select_ROI
                class_obj(self.calibrate_page)

            else:
                self.label2.configure(text='PLEASE CLICK AGAIN')
        else:
            self.label2.configure(text='ERROR!\nCAMERA NOT OPEN')

        self.update_stream()

    def close_calib_page(self):
        '''
        Definition:
        -----------
        Function returns to main-page.\n
        
        '''
        if self.picture_clicked == False and self.camera.isOpened() == True:
            self.camera.release()
        self.calibrate_page.destroy()

def call_referencephoto_class():
    # [NOTE EXPLANATION] Call calibrate-mode page/class.
    class_obj = take_reference_photo
    class_obj()

def call_runmode_class():
    # [NOTE EXPLANATION] Call Run-mode page/class.
    class_obj = run_device
    class_obj()

def halt_button():
    # [NOTE EXPLANATION] Halt raspberrypi.
    os.system('sudo halt')

def setup_gpio():
    # [NOTE EXPLANATION] GPIO setup to capture image through DI-2 Interupt
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(style.GPIO_CAMERA_TRIGGER_PIN, GPIO.IN)

def main():
    setup_gpio()

    # [NOTE EXPLANATION] Create tkinter object and start the main page.
    main_page = tk.Tk()
    main_page.title('Cake Sorting Application')
    main_page.attributes('-fullscreen', True)

    # [NOTE EXPLANATION] Create mainpage canvas so that widgets can be placed over it.
    main_canvas = tk.Canvas(main_page, width=screen_width, height=screen_height)
    main_canvas.configure(background=style.PAGE_BACKGROUND)

    
    with Image.open(style.COMPANY_LOGO) as image_file:
        image_width = int(1062//1.7)
        image_height = int(295//1.7)
        image = image_file.resize((image_width, image_height), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(image)
        image_file.close()
    
    # [NOTE EXPLANATION] Show logo and title on main page.
    company_image = tk.Label(main_canvas, image = image)
    company_image.configure(borderwidth=0)
    # company_image.place(x=(screen_width - image_width)/2, y=screen_height/20)
    company_image.place(relx = 0.5, anchor=tk.CENTER, y=2.5*screen_height//8)

    company_name = tk.Label(main_canvas, text= "COLOR SOLUTIONS", font=(style.FONT, 30), bg = "#FFFFFF")
    company_name.place(relx = 0.5, anchor=tk.CENTER, y=4*screen_height//8)

    # [NOTE EXPLANATION] Create and configure and place buttons on main page/canvas.
    button1=tk.Button(main_canvas, text="TRAIN MODEL", command=call_referencephoto_class)
    button1.configure(  width=15, 
                        height =4,
                        font=(style.FONT, 20), 
                        background=style.COLOR_BLUE, 
                        activebackground=style.COLOR_DARKBLUE,
                        foreground=style.COLOR_WHITE,
                        activeforeground=style.COLOR_WHITE)
    button1.place(relx=0.25, anchor=tk.CENTER, y=5.5*screen_height//8)

    button2=tk.Button(main_canvas, text="HALT DEVICE",command=halt_button)
    # button2=tk.Button(main_canvas, text="HALT DEVICE",command=main_page.destroy)
    button2.configure(  width=15, 
                        height =4,
                        font=(style.FONT, 20), 
                        background=style.COLOR_RED, 
                        activebackground=style.COLOR_DARKRED,
                        foreground=style.COLOR_WHITE,
                        activeforeground=style.COLOR_WHITE)
    button2.place(relx=0.5, anchor=tk.CENTER, y=5.5*screen_height//8)

    button3=tk.Button(main_canvas, text="RUN MODEL", command=call_runmode_class)
    button3.configure(  width=15, 
                        height =4,
                        font=(style.FONT, 20), 
                        background=style.COLOR_BLUE, 
                        activebackground=style.COLOR_DARKBLUE,
                        foreground=style.COLOR_WHITE,
                        activeforeground=style.COLOR_WHITE)
    button3.place(relx=0.75, anchor=tk.CENTER, y=5.5*screen_height//8)

    # [NOTE EXPLANATION] Start Tkinter loop.
    main_canvas.pack()
    main_page.mainloop()

main()