from tkinter.ttk import Style

import pyautogui
import cv2
from enum import Enum
from tkinter import *
from PIL import Image, ImageTk
from tkintermapview import TkinterMapView

class ConnectionStatus(Enum):
    DISCONNECTED = 0
    CONNECTED = 1

class MapTileServer(Enum):
    GOOGLE_SATELLITE = 'https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga'
    GOOGLE_NORMAL = 'http://a.tile.stamen.com/toner/{z}/{x}/{y}.png'

class GUIManager:
    WIDTH = 10000
    HEIGHT = 10000
    CONN_STAT_IMG_SIZE = 50
    SATELLITE_SWITCH_WIDTH = 110
    SATELLITE_SWITCH_HEIGHT = 60
    WINDOW_TITLE = "SpyBot Control UI"

    DETECTION_THRESHOLD = 0.6  # Threshold to detect object
    CONFIG_PATH = 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt'
    WEIGHTS_PATH = 'frozen_inference_graph.pb'
    classNames = []
    CLASS_FILE = 'coco.names'
    net = cv2.dnn_DetectionModel(WEIGHTS_PATH, CONFIG_PATH)
    net.setInputSize(320, 320)
    net.setInputScale(1.0 / 127.5)
    net.setInputMean((127.5, 127.5, 127.5))
    net.setInputSwapRB(True)

    # droneCoordinate = (40.39467249640738, 49.84948729079778)
    window = Tk()
    st = Style()
    connectionStatus = ConnectionStatus.CONNECTED

    is_satellite_enabled = False

    def __init__(self):

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.HEIGHT)

        with open(self.CLASS_FILE, 'rt') as f:
            self.classNames = f.read().rstrip('\n').split('\n')

        self.window.bind('<Escape>', lambda e: self.window.quit())
        self.window.bind("<c>", self.__key_pressed)
        self.window.title(self.WINDOW_TITLE)
        self.window.columnconfigure(0, minsize=400, weight=1)

        self.camera_label = Label(self.window)

        self.leftSideFrame = Frame(master=self.window, width=500, height=700)

        # status indicator
        self.status_img = self._generateStatusImage(self.connectionStatus)

        # status label
        self.status_label = Label(text=" Status: CONNECTED", master=self.leftSideFrame)
        self.status_label["compound"] = LEFT
        self.status_label["image"] = self.status_img

        # map widget
        self.map_widget = TkinterMapView(self.leftSideFrame, width=1000, height=1000, corner_radius=10)
        self.map_widget.set_tile_server(MapTileServer.GOOGLE_NORMAL.value, max_zoom=22)

        # screenshot button
        self.ss_button = Button(text="📷 Take Screenshot", command=self.take_ss, height=3, width=25, bg='#000', fg='#FFFFFF')
        self.satellite_switch = Label(text=" Satellite Mode", master=self.leftSideFrame)
        self.satellite_switch["compound"] = LEFT
        self.satellite_status_img = self.generate_satellite_switch_image()
        self.satellite_switch["image"] = self.satellite_status_img
        self.satellite_switch.bind("<Button-1>", self.satellite_mode_switch)

        # adding stuff to the screen
        self.leftSideFrame.grid(row=1, column=0)
        self.status_label.pack(pady=10)
        self.satellite_switch.pack(pady=10)
        self.map_widget.pack(padx=100)
        self.camera_label.grid(row=1, column=1)
        self.ss_button.grid(row=2, column=1)

    def start(self):
        """Starts showing the GUI elements. Contains a blocking call"""
        self.__show_frame(self.cap, self.camera_label)
        self.window.after(800, self._updateConnectionStatusLabel)
        self.window.mainloop()

    def __key_pressed(self, event):
        print("Key Pressed: " + event.char)

    # def setDroneCoordinates(self, lat_long_tuple):
    #     self.droneCoordinate = lat_long_tuple
    #     self._updateCurrentCoordinate()

    # def _updateCurrentCoordinate(self):
    #     """Tells the map widget to center and put a marker on the current drone coordinates.
    #     Also updates the coordinate label accordingly."""
    #     self.map_widget.set_position(self.droneCoordinate[0], self.droneCoordinate[1], marker=True)
    #     self.coord_label.configure(text=" Lat: {}\nLong: {}".format(self.droneCoordinate[0], self.droneCoordinate[1]))
    #     self.map_widget.canvas_marker_list.pop(0)  # removing the previous marker

    def _updateConnectionStatusLabel(self):
        """Updates the status label to show the corresponding text and image for the current connection status"""
        self.status_img = self._generateStatusImage(self.connectionStatus)

        if self.connectionStatus == ConnectionStatus.CONNECTED:
            self.status_label.config(text=" Status: CONNECTED", image=self.status_img)
        else:
            self.status_label.config(text=" Status: DISCONNECTED", image=self.status_img)

    def __show_frame(self, videoCap, mainLabel):
        """Reads and shows one frame from the video feed"""
        _, frame = videoCap.read()
        frame = cv2.flip(frame, 1)

        classIds, confs, bbox = self.net.detect(frame, confThreshold=self.DETECTION_THRESHOLD)

        if len(classIds) != 0:
            for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
                cv2.rectangle(frame, box, color=(0, 255, 0), thickness=2),
                cv2.putText(frame, self.classNames[classId - 1].upper(), (box[0] + 10, box[1] + 30),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        mainLabel.imgtk = imgtk
        mainLabel.configure(image=imgtk)
        mainLabel.after(10, self.__show_frame, videoCap, mainLabel)

    def _generateStatusImage(self, conn_status):
        """Generates an image corresponding to the given connection status"""
        image = None

        if self.connectionStatus == ConnectionStatus.CONNECTED:
            image = Image.open('img/greencircle.png')
        else:
            image = Image.open('img/redcircle.png')

        image = image.resize((self.CONN_STAT_IMG_SIZE, self.CONN_STAT_IMG_SIZE), Image.ANTIALIAS)

        return ImageTk.PhotoImage(image=image)

    def take_ss(self):
        screen_shot = pyautogui.screenshot()
        screen_shot.save(r'image.png')

    def generate_satellite_switch_image(self):
        """Generates an image corresponding to the current switch state"""
        image = None

        if self.is_satellite_enabled:
            image = Image.open('img/enabled.png')
        else:
            image = Image.open('img/disabled.png')

        image = image.resize((self.SATELLITE_SWITCH_WIDTH, self.SATELLITE_SWITCH_HEIGHT), Image.ANTIALIAS)

        return ImageTk.PhotoImage(image=image)

    def satellite_mode_switch(self, _):
        print("Satellite mode changed")

        self._reinit_map()

        if self.is_satellite_enabled:
            self.map_widget.set_tile_server(MapTileServer.GOOGLE_NORMAL.value, max_zoom=22)
        else:
            self.map_widget.set_tile_server(MapTileServer.GOOGLE_SATELLITE.value, max_zoom=22)

        self.map_widget.pack()
        self.is_satellite_enabled = not self.is_satellite_enabled
        self.satellite_status_img = self.generate_satellite_switch_image()
        self.satellite_switch.config(image=self.satellite_status_img)

    def _reinit_map(self):
        """Re-initializes the map widget"""
        self.map_widget.destroy()
        self.map_widget = TkinterMapView(self.leftSideFrame, width=1000, height=1000, corner_radius=10, padx=100)
        # self.map_widget.set_position(self.droneCoordinate[0], self.droneCoordinate[1], marker=True)

