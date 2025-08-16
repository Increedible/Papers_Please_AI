import sys
import logging

def exception_hook(exctype, value, traceback):
    logging.error("Uncaught exception", exc_info=(exctype, value, traceback))

# Override the excepthook
sys.excepthook = exception_hook

import time
import numpy as np
import pytesseract
import cv2
import pyautogui
import win32api
import win32con
import pyautogui
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush
from PyQt5.QtCore import Qt, QTimer

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.WindowTransparentForInput)
        self.setGeometry(0, 0, 1920, 1080)  # Adjust this based on your screen resolution
        self.squares = []  # List to store squares' coordinates

    def add_square(self, x1, y1, x2, y2, c):
        """Add a square's coordinates to the list and trigger a repaint."""
        self.squares.append((x1, y1, x2, y2, c))
        self.update()  # Trigger a repaint

    def clear_squares(self):
        """Clear all squares and trigger a repaint."""
        self.squares.clear()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        for square in self.squares:
            x1, y1, x2, y2, c = square
            r, g, b, t = c
            painter.setBrush(QColor(r, g, b, t))  # Red color with some transparency
            painter.drawRect(int(x1 * 1.5), int(y1 * 1.5), int((x2 - x1) * 1.5), int((y2 - y1) * 1.5))

app = QApplication(sys.argv)
overlay = Overlay()
overlay.show()

def remove_non_specified_chars(input_string, specified_chars):
    return ''.join(char for char in input_string if char in specified_chars)

def mouse_click(x, y):
    x = int((x / 1280) * 65535)  # desired X coordinate
    y = int((y / 720) * 65535)  # desired Y coordinate
    win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE | win32con.MOUSEEVENTF_MOVE, x, y)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

iss_cities = {
    "Orvech Vonor": "Arstotzka",
    "East Grestin": "Arstotzka",
    "Paradizna": "Arstotzka",
    "Yurko City": "Kolechia",
    "Vedor": "Kolechia",
    "West Grestin": "Kolechia",
    "Skal": "Obristan",
    "Lorndaz": "Obristan",
    "Mergerous": "Obristan",
    "St. Marmero": "Antegria",
    "Glorian": "Antegria",
    "Outer Grouse": "Antegria",
    "True Glorian": "Republia",
    "Lesrenadi": "Republia",
    "Bostan": "Republia",
    "Enkyo": "Impor",
    "Haihan": "Impor",
    "Tsunkeido": "Impor",
    "Great Rapid": "United Fed.",
    "Shingleton": "United Fed.",
    "Korista City": "United Fed.",
}

def check_date(date1, date2):
    date1 = date1.split('.')
    date2 = date2.split('.')
    if len(date1) != 3:
        return False
    if len(date2) != 3:
        return False
    if len(date1[0]) > 2:
        date1[0] = date1[0][-2:]
    if len(date2[0]) > 2:
        date2[0] = date2[0][-2:]
    if date1[0] < date2[0]:
        return False
    elif date1[0] == date2[0]:
        if date1[1] < date2[1]:
            return False
        elif date1[1] == date2[1]:
            if date1[2] <= date2[2]:
                return False
    return True

def find_image(path, x1=0, y1=0, x2=1280, y2=720, treshold=0.6, scale_factor=0.5):
    # Load the template image of the Discord icon (you will need to provide this image)
    template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    # Error checking for template image
    if template is None:
        print(f"Error: Failed to load the template image '{path}'")
        return (-1, -1), (-1, -1)

    # Capture a screenshot of the taskbar and convert it to grayscale
    screenshot = pyautogui.screenshot(region=(x1 * 1.5, y1 * 1.5, (x2 - x1) * 1.5, (y2 - y1) * 1.5))
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    # Error checking for screenshot
    if screenshot is None:
        print("Error: Failed to capture the screenshot")
        return (-1, -1), (-1, -1)

    # Scale down the template and screenshot
    scaled_template = cv2.resize(template, None, fx=scale_factor, fy=scale_factor)

    # Error checking for scaled template
    if scaled_template is None:
        print("Error: Failed to scale the template")
        return (-1, -1), (-1, -1)

    scaled_screenshot = cv2.resize(screenshot, None, fx=scale_factor, fy=scale_factor)

    # Error checking for scaled screenshot
    if scaled_screenshot is None:
        print("Error: Failed to scale the screenshot")
        return (-1, -1), (-1, -1)

    # Perform template matching
    result = cv2.matchTemplate(scaled_screenshot, scaled_template, cv2.TM_CCOEFF_NORMED)

    # Get the coordinates of the matched region
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < treshold:
        return (-1, -1), (-1, -1)
    top_left_scaled = max_loc
    bottom_right_scaled = (top_left_scaled[0] + scaled_template.shape[1], top_left_scaled[1] + scaled_template.shape[0])

    # Convert the scaled coordinates to the original screen scale
    top_left = (int(top_left_scaled[0] / scale_factor) + x1 * 1.5, int(top_left_scaled[1] / scale_factor) + y1 * 1.5)
    bottom_right = (
        int(bottom_right_scaled[0] / scale_factor) + x1 * 1.5, int(bottom_right_scaled[1] / scale_factor) + y1 * 1.5)
    return top_left, bottom_right

def readtext(x1=0, y1=0, x2=1280, y2=720, lang='train', blackandwhite=False, filename='default.png', threshold=50):
    pytesseract.pytesseract.tesseract_cmd = 'C:/Users/mrinc/AppData/Local/Programs/Tesseract-OCR/tesseract.exe'
    # Path of the Tesseract OCR executable
    os.environ["TESSDATA_PREFIX"] = "C:\\Users\\mrinc\\AppData\\Local\\Tesseract-OCR\\tessdata\\"
    # Tesseract configuration options
    custom_config = r'--psm 7'

    # Capture the screen image within the specified coordinates
    cap = pyautogui.screenshot(region=(x1 * 1.5, y1 * 1.5, (x2 - x1) * 1.5, (y2 - y1) * 1.5))

    # Convert the captured image to grayscale for OCR processing
    grayscale_image = cv2.cvtColor(np.array(cap), cv2.COLOR_BGR2GRAY)

    # Apply black and white thresholding if enabled
    if blackandwhite:
        if filename != 'default.png':
            # Write the thresholded image to a file
            cv2.imwrite(filename, grayscale_image)
            print(f"Thresholded image saved as {filename}")
        else:
            _, thresholded_image = cv2.threshold(grayscale_image, threshold, 255, cv2.THRESH_BINARY)
            grayscale_image = thresholded_image
            # this is temporary

    # Obtain the output string by performing OCR on the grayscale image with modified configuration
    return pytesseract.image_to_string(grayscale_image, lang=lang, config=custom_config)

wipe = False
old_weight = ""
space_pressed = False
tab_pressed = False
seen_passport = False
passport_oldpos = ()
passport_judgement_squares = []
latest_passport_inf = (0, 0, 0, 0, 0, 0, 0)
weight = ""
date = ""

def find_information_passport(x1=430, y1=250, x2=1280, y2=720):
    global space_pressed, tab_pressed, seen_passport, old_weight, passport_oldpos, passport_judgement_squares, latest_passport_inf, weight, date
    # Read the weight so that when the person leaves, the 'next' button can be pressed
    weight = readtext(374, 635, 415, 651, 'train2', True).replace('\n', '').replace(' ', '')
    date = readtext(75, 663, 135, 677, 'train2', True).replace('\n', '').replace(' ', '')
    if weight != old_weight:
        old_weight = weight
        if weight == "kg":
            mouse_click(417, 184)
            wipe = True
    # Check if the visa image can be found, thus if there is a passport
    coords = find_image('images//Entry_visa.png', x1, y1, x2, y2, 0.4, 1)
    # We have a narrow window, now for the precise coordinates:
    #coords = find_image('images//Entry_visa.png', int(coords[0][0] / 1.5 - 50), int(coords[0][1] / 1.5 - 50), int(coords[1][0] / 1.5 + 50), int(coords[1][1] / 1.5 + 50), 0.4)

    if coords[0][0] == -1:  # no passport
        seen_passport = False
        passport_judgement_squares = []
        return
    # Grab the coordinates of the passport itself to narrow search
    x1 = int(coords[0][0] / 1.5 - 40)
    y1 = int((coords[0][1] + (coords[1][1] - coords[0][1])) / 1.5 + 20)
    x2 = int((coords[1][0] + 10) / 1.5 + 40)
    y2 = int((coords[1][1] + (coords[1][1] - coords[0][1]) + 10) / 1.5 + 60)
    overlay.add_square(x1, y1 - (y2 - y1), x2, y2, (0, 255, 0, 50))
    mx, my = pyautogui.position()
    if (mx > x1 * 1.5) and (mx < x2 * 1.5) and (my > (y1 - (y2 - y1)) * 1.5) and (my < y2 * 1.5):
        seen_passport = False
    if (passport_oldpos != x1):
        seen_passport = False
    if seen_passport:
        for square in passport_judgement_squares:
            nx1, ny1, nx2, ny2, nc = square
            overlay.add_square(nx1, ny1, nx2, ny2, nc)
        return
    passport_judgement_squares.clear()
    seen_passport = True
    passport_oldpos = x1
    print("Found passport")
    name, birth, sex, city, expire, passportid, country = "0000000"
    # Determine passport type
    coords = find_image('images//Arstotzka.png', int(x1), int(y1), int(x2), int(y2))
    bsquare = ()
    esquare = ()
    csquare = ()
    if coords[0][0] != -1:  # type = Arstotzkan
        country = "Arstotzka"
        print("Type: Arstotzkan")
        name = readtext(x1 + 10, y1 + 10, x2 - 10, y2 - 126, 'train5').replace('\n','')
        birth = readtext(x1 + 125, y1 + 31, x2 - 15, y2 - 106, 'train5').replace('\n','').replace(' ', '')
        bsquare =       (x1 + 125, y1 + 31, x2 - 15, y2 - 106, (255, 0, 0, 120))
        sex = readtext(x1 + 125, y1 + 46, x2 - 55, y2 - 91, 'train5').replace('\n', '').replace(' ', '')
        city = readtext(x1 + 128, y1 + 64, x2 - 10, y2 - 76, 'train5').replace('\n','')
        csquare =      (x1 + 128, y1 + 64, x2 - 10, y2 - 76, (255, 0, 0, 120))
        expire = readtext(x1 + 125, y1 + 79, x2 - 15, y2 - 61, 'train5').replace('\n', '').replace(' ', '')
        esquare =        (x1 + 125, y1 + 79, x2 - 15, y2 - 61, (255, 0, 0, 120))
        passportid = readtext(x1 + 8, y1 + 130, x2 - 120, y2 - 8, 'train5').replace('\n', '').replace(' ', '')
    else:
        coords = find_image('images//Antegria.png', int(x1), int(y1), int(x2), int(y2))
        if coords[0][0] != -1:  # type = Antegrian
            country = "Antegria"
            print("Type: Antegrian")
            name = readtext(x1 + 8, y1 + 113, x2 - 10, y2 - 26, 'train5').replace('\n','')
            birth = readtext(x1 + 40, y1 + 35, x2 - 110, y2 - 103, 'train5').replace('\n','').replace(' ', '')
            bsquare =       (x1 + 40, y1 + 35, x2 - 110, y2 - 103, (255, 0, 0, 120))
            sex = readtext(x1 + 40, y1 + 57, x2 - 180, y2 - 85, 'train5').replace('\n', '').replace(' ', '')
            city = readtext(x1 + 40, y1 + 75, x2 - 100, y2 - 67, 'train5').replace('\n','')
            csquare =      (x1 + 40, y1 + 75, x2 - 100, y2 - 67, (255, 0, 0, 120))
            expire = readtext(x1 + 40, y1 + 93, x2 - 110, y2 - 49, 'train5').replace('\n', '').replace(' ', '')
            esquare =        (x1 + 40, y1 + 93, x2 - 110, y2 - 49, (255, 0, 0, 120))
            passportid = readtext(x1 + 120, y1 + 135, x2 - 8, y2 - 5, 'train5').replace('\n', '').replace(' ', '')
        else:
            coords = find_image('images//Impor.png', int(x1), int(y1), int(x2), int(y2))
            if coords[0][0] != -1:  # type = Imporian
                country = "Impor"
                print("Type: Imporian")
                name = readtext(x1 + 8, y1 + 5, x2 - 10, y2 - 130, 'train5').replace('\n','')
                birth = readtext(x1 + 130, y1 + 31, x2 - 20, y2 - 110, 'train5').replace('\n','').replace(' ', '')
                bsquare =       (x1 + 130, y1 + 31, x2 - 20, y2 - 110, (255, 0, 0, 120))
                sex = readtext(x1 + 130, y1 + 46, x2 - 100, y2 - 95, 'train5').replace('\n', '').replace(' ', '')
                city = readtext(x1 + 130, y1 + 63, x2 - 15, y2 - 77, 'train5').replace('\n','')
                csquare =      (x1 + 130, y1 + 63, x2 - 15, y2 - 77, (255, 0, 0, 120))
                expire = readtext(x1 + 130, y1 + 78, x2 - 20, y2 - 62, 'train5').replace('\n', '').replace(' ', '')
                esquare =        (x1 + 130, y1 + 78, x2 - 20, y2 - 62, (255, 0, 0, 120))
                passportid = readtext(x1 + 120, y1 + 128, x2 - 15, y2 - 10, 'train5').replace('\n', '').replace(' ', '')
            else:
                coords = find_image('images//Kolechia.png', int(x1), int(y1), int(x2), int(y2))
                if coords[0][0] != -1:  # type = Kolechian
                    country = "Kolechia"
                    print("Type: Kolechian")
                    name = readtext(x1 + 8, y1 + 31, x2 - 10, y2 - 106, 'train5').replace('\n','')
                    birth = readtext(x1 + 130, y1 + 51, x2 - 20, y2 - 90, 'train5').replace('\n','').replace(' ', '')
                    bsquare =       (x1 + 130, y1 + 51, x2 - 20, y2 - 90, (255, 0, 0, 120))
                    sex = readtext(x1 + 130, y1 + 66, x2 - 100, y2 - 75, 'train5').replace('\n', '').replace(' ', '')
                    city = readtext(x1 + 130, y1 + 83, x2 - 15, y2 - 57, 'train5').replace('\n','')
                    csquare =      (x1 + 130, y1 + 83, x2 - 15, y2 - 57, (255, 0, 0, 120))
                    expire = readtext(x1 + 130, y1 + 98, x2 - 20, y2 - 42, 'train5').replace('\n', '').replace(' ', '')
                    esquare =        (x1 + 130, y1 + 98, x2 - 20, y2 - 42, (255, 0, 0, 120))
                    passportid = readtext(x1 + 125, y1 + 133, x2 - 15, y2 - 7, 'train5').replace('\n', '').replace(' ', '')
                else:
                    coords = find_image('images//Obristan.png', int(x1), int(y1), int(x2), int(y2))
                    if coords[0][0] != -1:  # type = Obristanian
                        country = "Obristan"
                        print("Type: Obristanian")
                        name = readtext(x1 + 8, y1 + 30, x2 - 10, y2 - 106, 'train5').replace('\n','')
                        birth = readtext(x1 + 45, y1 + 58, x2 - 110, y2 - 82, 'train5').replace('\n','').replace(' ', '')
                        bsquare =       (x1 + 45, y1 + 58, x2 - 110, y2 - 82, (255, 0, 0, 120))
                        sex = readtext(x1 + 45, y1 + 73, x2 - 170, y2 - 65, 'train5').replace('\n', '').replace(' ', '')
                        city = readtext(x1 + 45, y1 + 88, x2 - 90, y2 - 48, 'train5').replace('\n','')
                        csquare =      (x1 + 45, y1 + 88, x2 - 90, y2 - 48, (255, 0, 0, 120))
                        expire = readtext(x1 + 45, y1 + 106, x2 - 110, y2 - 33, 'train5').replace('\n', '').replace(' ', '')
                        esquare =        (x1 + 45, y1 + 106, x2 - 110, y2 - 33, (255, 0, 0, 120))
                        passportid = readtext(x1 + 8, y1 + 130, x2 - 100, y2 - 8, 'train5').replace('\n', '').replace(' ', '')
                    else:
                        coords = find_image('images//Republia.png', int(x1), int(y1), int(x2), int(y2))
                        if coords[0][0] != -1:  # type = Republian
                            country = "Republia"
                            print("Type: Republian")
                            name = readtext(x1 + 8, y1 + 10, x2-5, y2 - 126, 'train5').replace('\n','')
                            birth = readtext(x1 + 45, y1 + 30, x2 - 110, y2 - 106, 'train5').replace('\n','').replace(' ', '')
                            bsquare =       (x1 + 45, y1 + 30, x2 - 110, y2 - 106, (255, 0, 0, 120))
                            sex = readtext(x1 + 45, y1 + 48, x2 - 180, y2 - 91, 'train5').replace('\n', '').replace(' ', '')
                            city = readtext(x1 + 45, y1 + 63, x2 - 90, y2 - 75, 'train5').replace('\n','')
                            csquare =      (x1 + 45, y1 + 63, x2 - 90, y2 - 75, (255, 0, 0, 120))
                            expire = readtext(x1 + 45, y1 + 78, x2 - 110, y2 - 60, 'train5').replace('\n', '').replace(' ', '')
                            esquare =        (x1 + 45, y1 + 78, x2 - 110, y2 - 60, (255, 0, 0, 120))
                            passportid = readtext(x1 + 120, y1 + 130, x2 - 8, y2 - 8, 'train5').replace('\n', '').replace(' ', '')
                        else:
                            coords = find_image('images//United Federation.png', int(x1), int(y1), int(x2), int(y2))
                            if coords[0][0] != -1:  # type = United Federation
                                country = "United Fed."
                                print("Type: United Fed.")
                                name = readtext(x1 + 8, y1 + 31, x2 - 10, y2 - 106, 'train5').replace('\n','')
                                birth = readtext(x1 + 130, y1 + 47, x2 - 20, y2 - 93, 'train5').replace('\n','').replace(' ', '')
                                bsquare =       (x1 + 130, y1 + 47, x2 - 20, y2 - 93, (255, 0, 0, 120))
                                sex = readtext(x1 + 130, y1 + 65, x2 - 100, y2 - 75, 'train5').replace('\n', '').replace(' ', '')
                                city = readtext(x1 + 130, y1 + 80, x2 - 15, y2 - 58, 'train5').replace('\n','')
                                csquare =      (x1 + 130, y1 + 80, x2 - 15, y2 - 58, (255, 0, 0, 120))
                                expire = readtext(x1 + 130, y1 + 97, x2 - 20, y2 - 45, 'train5').replace('\n', '').replace(' ', '')
                                esquare =        (x1 + 130, y1 + 97, x2 - 20, y2 - 45, (255, 0, 0, 120))
                                passportid = readtext(x1 + 128, y1 + 133, x2 - 12, y2 - 7, 'train5').replace('\n', '').replace(' ', '')
                            else:
                                print("Type: Unknown")
                                seen_passport = False
                                return
    # Filter and clean
    name = remove_non_specified_chars(name, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ, ")
    birth = remove_non_specified_chars(birth, ".0123456789")
    sex = remove_non_specified_chars(sex, "MW")
    city = remove_non_specified_chars(city, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ")
    expire = remove_non_specified_chars(expire, ".0123456789")
    passportid = remove_non_specified_chars(passportid, "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-").upper()

    latest_passport_inf = (name, birth, sex, city, expire, passportid, country)

    print("\nJUDGEMENT:")
    if not check_date(date, birth):
        print("BIRTHDAY INVALID.")
        passport_judgement_squares.append(bsquare)
    elif not check_date(expire, date):
        print("EXPIRED.")
        passport_judgement_squares.append(esquare)
    elif city not in iss_cities:
        print(f"INVALID ISS CITY:\n'{city}'")
        passport_judgement_squares.append(csquare)
    elif iss_cities[city] != country:
        print(f"WRONG COUNTRY FOR ISS CITY. EXPECTED:\n'{iss_cities[city]}'\nBUT GOT:\n'{country}'")
        passport_judgement_squares.append(csquare)
    else:
        print("FINE.")
    for square in passport_judgement_squares:
        nx1, ny1, nx2, ny2, nc = square
        overlay.add_square(nx1, ny1, nx2, ny2, nc)
    return

    # if win32api.GetAsyncKeyState(0x20):
    #     if space_pressed == False:
    #         mouse_click(1180, 650)
    #         space_pressed = True
    # else:
    #     space_pressed = False
    # if win32api.GetAsyncKeyState(0x09):
    #     if tab_pressed == False:
    #         mouse_click(1196, 356)
    #         tab_pressed = True
    # else:
    #     tab_pressed = False

entrypermit_oldpos = ()
seen_entrypermit = False
entrypermit_judgement_squares = []
def find_information_entrypermit(x1=430, y1=250, x2=1280, y2=720):
    global entrypermit_oldpos, seen_entrypermit, entrypermit_judgement_squares
    coords = find_image('images//Entry_permit.png', x1, y1, x2, y2, 0.4, 1)

    if coords[0][0] == -1:  # no passport
        seen_entrypermit = False
        entrypermit_judgement_squares = []
        return

    x1 = int(coords[0][0] / 1.5) - 15
    y1 = int((coords[0][1] + (coords[1][1] - coords[0][1])) / 1.5) - 157
    x2 = int((coords[1][0] + 10) / 1.5) + 12
    y2 = int((coords[1][1] + (coords[1][1] - coords[0][1]) + 10) / 1.5) + 150

    print(x1, y1, x2, y2)
    overlay.add_square(x1, y1, x2, y2, (0, 255, 0, 50))
    mx, my = pyautogui.position()
    if (mx > x1 * 1.5) and (mx < x2 * 1.5) and (my > y1 * 1.5) and (my < y2 * 1.5):
        seen_entrypermit = False
    if (entrypermit_oldpos != x1):
        seen_entrypermit = False
    if seen_entrypermit:
        for square in entrypermit_judgement_squares:
            nx1, ny1, nx2, ny2, nc = square
            overlay.add_square(nx1, ny1, nx2, ny2, nc)
        return
    entrypermit_judgement_squares.clear()
    seen_entrypermit = True
    entrypermit_oldpos = x1
    print("Found entry permit")

    name = readtext(x1 + 22, y1 + 163, x2 - 17, y2 - 191, 'train5').replace('\n','')
    birth = readtext(x1 + 125, y1 + 31, x2 - 15, y2 - 106, 'train5').replace('\n','').replace(' ', '')
    bsquare =       (x1 + 125, y1 + 31, x2 - 15, y2 - 106, (255, 0, 0, 120))
    sex = readtext(x1 + 125, y1 + 46, x2 - 55, y2 - 91, 'train5').replace('\n', '').replace(' ', '')
    city = readtext(x1 + 128, y1 + 64, x2 - 10, y2 - 76, 'train5').replace('\n','')
    csquare =      (x1 + 128, y1 + 64, x2 - 10, y2 - 76, (255, 0, 0, 120))
    expire = readtext(x1 + 125, y1 + 79, x2 - 15, y2 - 61, 'train5').replace('\n', '').replace(' ', '')
    esquare =        (x1 + 125, y1 + 79, x2 - 15, y2 - 61, (255, 0, 0, 120))
    passportid = readtext(x1 + 8, y1 + 130, x2 - 120, y2 - 8, 'train5').replace('\n', '').replace(' ', '')

    name = remove_non_specified_chars(name, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ, ")

    print(f"Name: {name}")

    return

accesspermit_oldpos = ()
seen_accesspermit = False
accesspermit_judgement_squares = []
latest_accesspermit_inf = (0, 0, 0, 0, 0, 0)
def find_information_accesspermit(x1=430, y1=250, x2=1280, y2=720):
    global accesspermit_oldpos, seen_accesspermit, accesspermit_judgement_squares, latest_accesspermit_inf
    coords = find_image('images//Access_permit.png', x1, y1, x2, y2, 0.8, 1)

    if coords[0][0] == -1:  # no passport
        seen_accesspermit = False
        accesspermit_judgement_squares = []
        return

    x1 = int(coords[0][0] / 1.5) - 15
    y1 = int((coords[0][1] + (coords[1][1] - coords[0][1])) / 1.5) - 157
    x2 = int((coords[1][0] + 10) / 1.5) + 12
    y2 = int((coords[1][1] + (coords[1][1] - coords[0][1]) + 10) / 1.5) + 150
    print(x1, y1, x2, y2)
    overlay.add_square(x1, y1 + 30, x2, y2 + 60, (0, 255, 0, 50))
    mx, my = pyautogui.position()
    if (mx > x1 * 1.5) and (mx < x2 * 1.5) and (my > (y1 + 30) * 1.5) and (my < (y2 + 60) * 1.5):
        seen_accesspermit = False
    if (accesspermit_oldpos != x1):
        seen_accesspermit = False
    if seen_accesspermit:
        for square in accesspermit_judgement_squares:
            nx1, ny1, nx2, ny2, nc = square
            overlay.add_square(nx1, ny1, nx2, ny2, nc)
        return
    accesspermit_judgement_squares.clear()
    seen_accesspermit = True
    accesspermit_oldpos = x1
    print("Found access permit")

    name = readtext(x1 + 14, y1 + 118, x2 - 23, y2 - 196, 'train652').replace('\n','')
    nationality = readtext(x1 + 19, y1 + 166, x2 - 147, y2 - 153, 'train652').replace('\n','').replace(' ', '')
    ID = readtext(x1 + 145, y1 + 165, x2 - 15, y2 - 152, 'train652').replace('\n', '').replace(' ', '')
    height = readtext(x1 + 18, y1 + 253, x2 - 152, y2 - 62, 'train652').replace('\n','')
    weight = readtext(x1 + 142, y1 + 253, x2 - 25, y2 - 62, 'train652').replace('\n','')
    enterby = readtext(x1 + 147, y1 + 342, x2 - 23, y2 + 25, 'train652').replace('\n','')

    name = remove_non_specified_chars(name.upper(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ, ")
    nationality = remove_non_specified_chars(nationality.upper(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ. ")
    ID = remove_non_specified_chars(ID.upper(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ-1234567890")
    height = remove_non_specified_chars(height, "0123456789cm")
    weight = remove_non_specified_chars(weight, "0123456789kg")
    enterby = remove_non_specified_chars(enterby, "0123456789.")

    latest_accesspermit_inf = (name, nationality, ID, height, weight, enterby)

    print(latest_accesspermit_inf)

    return

poliocert_oldpos = ()
seen_poliocert = False
poliocert_judgement_squares = []
latest_poliocert_inf = []
def find_information_poliocert(x1=430, y1=250, x2=1280, y2=720):
    global poliocert_oldpos, seen_poliocert, poliocert_judgement_squares, latest_poliocert_inf
    coords = find_image('images//Polio_cert.png', x1, y1, x2, y2, 0.4, 1)

    if coords[0][0] == -1:  # no passport
        seen_poliocert = False
        poliocert_judgement_squares = []
        return

    x1 = int(coords[0][0] / 1.5) - 15
    y1 = int((coords[0][1] + (coords[1][1] - coords[0][1])) / 1.5) - 157
    x2 = int((coords[1][0] + 10) / 1.5) + 12
    y2 = int((coords[1][1] + (coords[1][1] - coords[0][1]) + 10) / 1.5) + 150

    overlay.add_square(x1 - 60, y1 + 60, x2 + 60, y2, (0, 255, 0, 50))
    mx, my = pyautogui.position()
    if (mx > (x1 - 60) * 1.5) and (mx < (x2 + 60) * 1.5) and (my > (y1 + 60) * 1.5) and (my < y2 * 1.5):
        seen_poliocert = False
    if (poliocert_oldpos != x1):
        seen_poliocert = False
    if seen_poliocert:
        for square in poliocert_judgement_squares:
            nx1, ny1, nx2, ny2, nc = square
            overlay.add_square(nx1, ny1, nx2, ny2, nc)
        return
    poliocert_judgement_squares.clear()
    seen_poliocert = True
    poliocert_oldpos = x1
    print("Found polio cert")

    name = readtext(x1 - 22, y1 + 165, x2 + 16, y2 - 201, 'train652').replace('\n','')
    ID = readtext(x1 + 2, y1 + 193, x2 + 16, y2 - 174, 'train652').replace('\n','').replace(' ', '')
    v1d = readtext(x1 - 20, y1 + 255 + 24 * 0, x2 - 107, y2 - 111 + 24 * 0, 'train652').replace('\n','')
    v2d = readtext(x1 - 20, y1 + 255 + 24 * 1, x2 - 107, y2 - 111 + 24 * 1, 'train652').replace('\n','')
    v3d = readtext(x1 - 20, y1 + 255 + 24 * 2, x2 - 107, y2 - 111 + 24 * 2, 'train652').replace('\n','')
    v1n = readtext(x1 + 64, y1 + 255 + 24 * 0, x2 + 14, y2 - 111 + 24 * 0, 'train652').replace('\n','')
    v2n = readtext(x1 + 64, y1 + 255 + 24 * 1, x2 + 14, y2 - 111 + 24 * 1, 'train652').replace('\n','')
    v3n = readtext(x1 + 64, y1 + 255 + 24 * 2, x2 + 14, y2 - 111 + 24 * 2, 'train652').replace('\n','')

    name = remove_non_specified_chars(name.upper(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ, ")
    ID = remove_non_specified_chars(ID.upper(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ-1234567890")
    v1d = remove_non_specified_chars(v1d.upper(), "1234567890.")
    v2d = remove_non_specified_chars(v2d.upper(), "1234567890.")
    v3d = remove_non_specified_chars(v3d.upper(), "1234567890.")
    v1n = remove_non_specified_chars(v1n.upper(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ. ")
    v2n = remove_non_specified_chars(v2n.upper(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ. ")
    v3n = remove_non_specified_chars(v3n.upper(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ. ")

    latest_poliocert_inf = [name, ID, v1d, v2d, v3d, v1n, v2n, v3n]

    print(latest_poliocert_inf)

    return

def data_checks():
    global wipe, latest_passport_inf, latest_accesspermit_inf, latest_poliocert_inf
    print("===========================")
    if wipe == True:
        wipe = False
        latest_passport_inf = (0, 0, 0, 0, 0, 0, 0)
        latest_accesspermit_inf = (0, 0, 0, 0, 0, 0)
        latest_poliocert_inf = (0, 0, 0, 0, 0, 0, 0, 0)
        print("NEW CUSTOMER")
        return
    pname, pbirth, psex, pcity, pexpire, pid, pcountry = latest_passport_inf
    if pname != 0:
        if not check_date(date, pbirth):
            print("BIRTHDAY INVALID.")
        elif not check_date(pexpire, date):
            print("EXPIRED.")
        elif pcity not in iss_cities:
            print(f"INVALID ISS CITY:\n'{city}'")
        elif iss_cities[pcity] != pcountry:
            print(f"WRONG COUNTRY FOR ISS CITY. EXPECTED:\n'{iss_cities[pcity]}'\nBUT GOT:\n'{pcountry}'")
    apname, apnationality, apid, apheight, apweight, apenterby = latest_accesspermit_inf
    if apname != 0:
        print("check1")
        if apweight.replace(" ", "") != weight.replace(" ", ""):
            print("WEIGHT MISMATCH.")
        if not check_date(apenterby, date):
            print("ACCESS PERMIT EXPIRED.")
        print("check2")
        if pname != 0:
            if pname.upper() != apname.upper():
                print("NAME MISMATCH.")
            print("check3")
            if apnationality.upper() != pcountry.upper():
                print(f"NATIONALITY MISMATCH. ({apnationality}/{pcountry}")
            if apid != pid:
                print("ID MISMATCH.")


print("start")

def on_timer():
    overlay.clear_squares()
    find_information_passport()
    #find_information_entrypermit()
    find_information_accesspermit()
    find_information_poliocert()

    data_checks()

# Set up a QTimer
timer = QTimer()
timer.timeout.connect(on_timer)  # Connect the timer to the on_timer function
timer.start(1)

sys.exit(app.exec_())
