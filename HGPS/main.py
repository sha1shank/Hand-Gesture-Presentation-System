import tkinter as tk
from tkinter import messagebox
import csv
from datetime import datetime
from cvzone.HandTrackingModule import HandDetector
import cv2
import os
import numpy as np

# Initialize registered_users dictionary
registered_users = {}

# Initialize gestures dictionary
gestures = []

# Parameters
width, height = 1280, 720
gestureThreshold = 300
folderPath = "Presentation"

# Camera Setup
cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

# Hand Detector
detectorHand = HandDetector(detectionCon=0.8, maxHands=1)

# Variables
imgList = []
delay = 30
buttonPressed = False
counter = 0
drawMode = False
imgNumber = 0
delayCounter = 0
annotations = [[]]
annotationNumber = -1
annotationStart = False
hs, ws = int(120 * 1), int(213 * 1)  # width and height of the small image

# Get list of presentation images
pathImages = sorted(os.listdir(folderPath), key=len)
print(pathImages)

# Create the main window
root = tk.Tk()
root.title("Login and Presentation")
root.geometry("800x600")



bg2 = tk.PhotoImage(file="C:/Users/user/PycharmProjects/GUI/bg2.png")
background_label = tk.Label(root, image=bg2)
background_label.place(relwidth=1, relheight=1)

heading_label = tk.Label(root, text="Hand Gesture System Login", font=("Comic Sans MS", 20, "bold"), fg='white', bg='#223053')
heading_label.pack(pady=50)

def check_credentials_and_run_presentation():
    username = entry_username.get()
    password = entry_password.get()

    # Read login credentials from the login_log.csv file
    with open("login_log.csv", mode="r") as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == username and row[1] == password:
                log_login(username, password)  # Log the login to the login_log.csv file
                messagebox.showinfo("Login Successful", "Welcome, {}".format(username))
                root.destroy()
                run_presentation(username)
                return  # Exit the function if login is successful

    messagebox.showerror("Login Failed", "Invalid username or password")

# Function to run after successful login
def run_presentation(username):
    global cap, detectorHand, width, height, gestureThreshold, folderPath, cap, imgList, delay, \
        buttonPressed, counter, drawMode, imgNumber, delayCounter, annotations, \
        annotationNumber, annotationStart, hs, ws, pathImages

    while True:
        # Get image frame
        success, img = cap.read()
        img = cv2.flip(img, 1)
        pathFullImage = os.path.join(folderPath, pathImages[imgNumber])
        imgCurrent = cv2.imread(pathFullImage)

        # Find the hand and its landmarks
        hands, img = detectorHand.findHands(img)  # with draw
        # Draw Gesture Threshold line
        cv2.line(img, (0, gestureThreshold), (width, gestureThreshold), (0, 255, 0), 10)

        if hands and buttonPressed is False:  # If hand is detected

            hand = hands[0]
            cx, cy = hand["center"]
            lmList = hand["lmList"]  # List of 21 Landmark points
            fingers = detectorHand.fingersUp(hand)  # List of which fingers are up

            # Constrain values for easier drawing
            xVal = int(np.interp(lmList[8][0], [width // 2, width], [0, width]))
            yVal = int(np.interp(lmList[8][1], [150, height - 150], [0, height]))
            indexFinger = xVal, yVal

            if cy <= gestureThreshold:
                if fingers == [1, 0, 0, 0, 0]:
                    timestamp = datetime.now()
                    gesture_name = "Left"
                    gestures.append((gesture_name, timestamp))
                    log_gestures(username, gesture_name, timestamp)
                    buttonPressed = True
                    if imgNumber > 0:
                        imgNumber -= 1
                        annotations = [[]]
                        annotationNumber = -1
                        annotationStart = False

                if fingers == [0, 0, 0, 0, 1]:
                    timestamp = datetime.now()
                    gesture_name = "Right"
                    gestures.append((gesture_name, timestamp))
                    log_gestures(username, gesture_name, timestamp)
                    buttonPressed = True
                    if imgNumber < len(pathImages) - 1:
                        imgNumber += 1
                        annotations = [[]]
                        annotationNumber = -1
                        annotationStart = False

            if fingers == [0, 1, 1, 0, 0]:
                cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)
                timestamp = datetime.now()
                gesture_name = "Annotation Pointer"
                gestures.append((gesture_name, timestamp))
                log_gestures(username, gesture_name, timestamp)

            if fingers == [0, 1, 0, 0, 0]:
                if annotationStart is False:
                    annotationStart = True
                    annotationNumber += 1
                    annotations.append([])
                annotations[annotationNumber].append(indexFinger)
                cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)
                timestamp = datetime.now()
                gesture_name = "Annotation Painter"
                gestures.append((gesture_name, timestamp))
                log_gestures(username, gesture_name, timestamp)

            else:
                annotationStart = False

            if fingers == [0, 1, 1, 1, 0]:
                if annotations:
                    annotations.pop(-1)
                    annotationNumber -= 1
                    buttonPressed = True
                timestamp = datetime.now()
                gesture_name = "Annotation Eraser"
                gestures.append((gesture_name, timestamp))
                log_gestures(username, gesture_name, timestamp)

        else:
            annotationStart = False

        if buttonPressed:
            counter += 1
            if counter > delay:
                counter = 0
                buttonPressed = False

        for i, annotation in enumerate(annotations):
            for j in range(len(annotation)):
                if j != 0:
                    cv2.line(imgCurrent, annotation[j - 1], annotation[j], (0, 0, 200), 12)

        imgSmall = cv2.resize(img, (ws, hs))
        h, w, _ = imgCurrent.shape
        imgCurrent[0:hs, w - ws: w] = imgSmall

        cv2.imshow("Slides", imgCurrent)
        cv2.imshow("Image", img)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

# Function to check credentials and run the presentation

def log_gestures(username, gesture_name, timestamp):
    gestures_filename = f"{username}_gestures_log.csv"

    file_is_empty = not os.path.isfile(f"{username}_gestures_log.csv") or os.stat(f"{username}_gestures_log.csv").st_size == 0
    with open(gestures_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if file_is_empty:
            writer.writerow(["Gesture name", "Timestamp"])
        writer.writerow([gesture_name, timestamp])

def register_user():
    username = entry_username.get()
    password = entry_password.get()

    if username and password:
        registered_users[username] = password
        log_login(username, password)
        messagebox.showinfo("Registration Successful", "User {} registered successfully".format(username))
    else:
        messagebox.showerror("Registration Failed", "Username and password are required")

def log_login(username, password):
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d %H:%M:%S")

    file_is_empty = not os.path.isfile("login_log.csv") or os.stat("login_log.csv").st_size == 0

    with open("login_log.csv", mode="a", newline="") as file:
        writer = csv.writer(file)

        if file_is_empty:
            writer.writerow(["Username", "Password", "Timestamp"])

        writer.writerow([username, password, date_time])

# Create and place username label and entry
label_username = tk.Label(root, text="Username:", font=("Comic Sans MS", 12), fg='yellow', bg='#223053')
label_username.pack(pady=10)
entry_username = tk.Entry(root, font=("Helvetica", 14))
entry_username.pack(pady=5)

# Create and place password label and entry
label_password = tk.Label(root, text="Password:", font=("Comic Sans MS", 12), fg='yellow', bg='#223053')
label_password.pack(pady=10)
entry_password = tk.Entry(root, show="*", font=("Comic Sans MS", 12))
entry_password.pack(pady=5)

# Create and place login button
login_button = tk.Button(root, text="Login", command=check_credentials_and_run_presentation, font=("Comic Sans MS", 12))
login_button.pack(pady=10)

# Create and place register button
register_button = tk.Button(root, text="Register", command=register_user, font=("Comic Sans MS", 12))
register_button.pack(pady=20)

# Start the main loop
root.mainloop()

# Release the camera when the application is closed
cap.release()
cv2.destroyAllWindows()