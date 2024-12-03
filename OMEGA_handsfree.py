from ultralytics import YOLO
import cv2
import threading
import requests
import smtplib
import datetime
import speech_recognition as sr
import pyttsx3
import pywhatkit
import wikipedia
import pyjokes
import time
import json
import http.client

# Initialize recognizer and text-to-speech engine
listener = sr.Recognizer()
omega = pyttsx3.init()
omega.setProperty('voice', omega.getProperty('voices')[1].id)

# Load YOLOv8 model for object detection
model = YOLO('yolov8n.pt')

# Global variables for YOLO threading
frame = None
results = None
yolo_thread_running = False
shabodi_api_enabled = False  # Initialize Shabodi API flag

# Function to convert text to speech
def talk(text):
    try:
        print(f"Speaking: {text}")
        omega.say(text)
        omega.runAndWait()
    except Exception as e:
        print(f"Error during speech: {e}")

# Introduction
talk("Hi! I am Omega. How may I help you?")

# Function to listen for a voice command
def take_command():
    try:
        with sr.Microphone() as source:
            listener.adjust_for_ambient_noise(source, duration=1)
            print('Listening...')
            voice = listener.listen(source, timeout=10, phrase_time_limit=5)
            command = listener.recognize_google(voice).lower()
            if 'omega' in command:
                command = command.replace('omega', '').strip()
                return command
            else:
                return ""
    except sr.WaitTimeoutError:
        print("Listening timed out while waiting for phrase to start.")
        return ""
    except sr.UnknownValueError:
        print("Could not understand the audio.")
        return ""
    except sr.RequestError:
        print("Could not request results; check your network connection.")
        return ""

# Function to listen for confirmation with multiple attempts
def listen_for_confirmation(attempts=3):
    for _ in range(attempts):
        confirmation = take_command()
        if confirmation:
            confirmation = confirmation.lower()
            if "yes" in confirmation or "yeah" in confirmation or "okay" in confirmation:
                return True
            elif "no" in confirmation:
                return False
        talk("Could not understand. Please say yes or no.")
    return False

# Function for object detection in a separate thread
def yolo_detection_thread():
    global frame, results, yolo_thread_running
    yolo_thread_running = True
    while yolo_thread_running:
        if frame is not None:
            results = model.track(frame, persist=True)  # Perform object detection
        time.sleep(0.03)  # Small delay to reduce CPU usage

# Function to dynamically adjust bandwidth using Shabodi API
def get_access_token():
    try:
        conn = http.client.HTTPConnection("192.168.3.18", 31002)
        payload = json.dumps({
            "client_id": "81895bb9-5576-4eb3-bf0e-c66322b382aa",
            "client_secret": "XDjeZcFU88_gWGfHpk_6Qh1IRLZTKIEKBNTVh8MWstA"
        })
        headers = {'Content-Type': 'application/json'}
        conn.request("POST", "/security/v1/token", payload, headers)
        res = conn.getresponse()
        data = res.read()
        token_data = json.loads(data.decode("utf-8"))
        conn.close()
        return token_data.get("access_token")
    except Exception as e:
        print(f"Error while getting access token: {e}")
        return None

def invocation(access_token):
    try:
        conn = http.client.HTTPConnection("192.168.3.18", 7999)
        payload = json.dumps({
            "device": {"deviceId": 11},
            "maxBitRate": 400,
            "direction": "uplink",
            "duration": 10000
        })
        headers = {
            'Content-type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        conn.request("POST", "/qos/v1/bandwidth", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))
        conn.close()
    except Exception as e:
        print(f"Error while invoking API: {e}")

# Function to open the camera feed and provide proximity-based object detection
def open_camera():
    global frame, results, yolo_thread_running, shabodi_api_enabled

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        talk("Sorry, I couldn't open the camera.")
        return

    talk("Opening the camera.")
    yolo_thread = threading.Thread(target=yolo_detection_thread)
    yolo_thread.start()

    last_direction = None
    last_warning_time = time.time()
    last_object_count = 0  # Store the last object count for comparison
    access_token = get_access_token() if shabodi_api_enabled else None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        object_count = 0  # Initialize object count for the current frame

        # Only process YOLO results if available
        if results is not None:
            for obj in results[0].boxes:
                object_count += 1  # Increment object count for each detection
                x1, y1, x2, y2 = map(int, obj.xyxy[0])
                width = x2 - x1
                height = y2 - y1
                proximity_area = width * height

                if proximity_area > 50000:
                    current_time = time.time()
                    center_x = (x1 + x2) / 2

                    if center_x > frame.shape[1] * 0.4 and center_x < frame.shape[1] * 0.6:
                        if last_direction != 'front' or current_time - last_warning_time > 3:
                            talk("There is an object in front of you.")
                            last_direction = 'front'
                            last_warning_time = current_time

                    elif center_x <= frame.shape[1] * 0.4:
                        if last_direction != 'left' or current_time - last_warning_time > 3:
                            talk("Turn slightly right.")
                            last_direction = 'left'
                            last_warning_time = current_time

                    elif center_x >= frame.shape[1] * 0.6:
                        if last_direction != 'right' or current_time - last_warning_time > 3:
                            talk("Turn slightly left.")
                            last_direction = 'right'
                            last_warning_time = current_time

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                    class_name = model.names[int(obj.cls[0])]
                    cv2.putText(frame, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)

        # Dynamically adjust bandwidth based on object count if Shabodi API is enabled
        if shabodi_api_enabled and object_count != last_object_count:
            print(f"Detected {object_count} objects. Adjusting bandwidth.")
            if access_token:
                adjusted_bandwidth = 400 + (object_count * 50)  # Example adjustment formula
                invocation(access_token)
            last_object_count = object_count

        cv2.imshow('Camera Feed', frame)

        if cv2.waitKey(1) & 0xFF == ord('c'):
            break

    yolo_thread_running = False
    yolo_thread.join()
    cap.release()
    cv2.destroyAllWindows()
    talk("Camera closed.")

# Function to check travel time and send email if needed
def check_travel_time_and_email():
    talk("Where are you right now? Please tell me the city.")
    current = take_command()
    if not current:
        talk("I couldn't hear your location clearly. Please try again.")
        return

    talk("Where do you want to go? Please tell me the city.")
    to = take_command()
    if not to:
        talk("I couldn't hear your destination clearly. Please try again.")
        return

    # API key 
    api_key = str("example") #API Key
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&"
    response = requests.get(url + f"origins={current}&destinations={to}&key={api_key}")
    data = response.json()

    try:
        time_text = data["rows"][0]["elements"][0]["duration"]["text"]
        time_seconds = data["rows"][0]["elements"][0]["duration"]["value"]
    except (KeyError, IndexError):
        talk("I couldn't retrieve the travel time. Please check the locations or your network connection.")
        return

    talk(f"The total travel time is {time_text}")
    if time_seconds > 3600:
        talk("Travel time is over an hour. Would you like me to send an email to the team?")
        if listen_for_confirmation():
            send_email()
        else:
            talk("Okay, I will not send the email.")

# Function to send email
def send_email():
    sender = "example@gmail.com" #Email sender
    recipients = ["example1@gmail.com, example2@gmail.com"] #Email receiver
    subject = "Attendance Update - [Omega]"
    message = "Hi,\nI won't be able make it on time for today's meeting.\n\nRegards,\nOmega."

    email_content = f"Subject: {subject}\n\n{message}"
    app_password = "example" #Your app password

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(sender, app_password)
            for recipient in recipients:
                s.sendmail(sender, recipient, email_content)
            talk("I have successfully sent the email to the team.")
    except Exception as e:
        print(f"Error occurred while sending the email: {e}")
        talk("An error occurred while trying to send the email.")

# Main function to handle commands
def run_omega():
    global shabodi_api_enabled

    command = take_command()
    if command:
        print(f"Command received: {command}")

        if 'time' in command:
            time_now = datetime.datetime.now().strftime('%I:%M %p')
            talk(f'The current time is {time_now}')

        elif 'what can you do' in command:
            talk("I can do many things! I can tell you the time, navigate using the camera, play YouTube videos, search for information, tell jokes, check travel times and even send emails!")

        elif 'play' in command:
            song = command.replace('play', '').strip()
            if song:
                talk(f'Playing {song}')
                pywhatkit.playonyt(song)
            else:
                talk("Please specify a song or video to play.")

        elif 'tell me about' in command:
            topic = command.replace('tell me about', '').strip()
            if topic:
                try:
                    info = wikipedia.summary(topic, sentences=1)
                    talk(info)
                except wikipedia.exceptions.DisambiguationError:
                    talk("The topic is ambiguous. Please be more specific.")
                except wikipedia.exceptions.PageError:
                    talk("Sorry, I couldn't find information on that topic.")
                except Exception as e:
                    talk("An error occurred while searching for the topic.")
            else:
                talk("Please specify a topic to tell you about.")

        elif 'joke' in command:
            talk(pyjokes.get_joke())

        elif 'open camera' in command:
            open_camera()

        elif 'check destination' in command:
            check_travel_time_and_email()

        elif 'turn on shabodi api' in command:
            shabodi_api_enabled = True
            talk("Shabodi API has been activated.")

        elif 'turn off shabodi api' in command:
            shabodi_api_enabled = False
            talk("Shabodi API has been deactivated.")

        elif 'stop' in command:
            talk("Goodbye!")
            return False

        else:
            talk(f'Searching for {command}')
            pywhatkit.search(command)

    return True

# Run the assistant in a loop
while True:
    if not run_omega():
        break
