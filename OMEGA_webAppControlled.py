from flask import Flask, request, jsonify, send_from_directory
from ultralytics import YOLO
import cv2
import requests
import pyttsx3
import speech_recognition as sr

# Initialize Flask app
app = Flask(__name__)

# Load YOLO model
model = YOLO('yolov8n.pt')  # Ensure the YOLO model file is in the same directory

# Initialize text-to-speech engine
omega = pyttsx3.init()
omega.setProperty('voice', omega.getProperty('voices')[1].id)

# Speech recognizer
listener = sr.Recognizer()

# Serve the HTML frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')  # Serve the HTML file

# Helper function for text-to-speech
def talk(text):
    omega.say(text)
    print(text)
    omega.runAndWait()

# API for voice commands
@app.route('/api/voice-command', methods=['POST'])
def voice_command():
    try:
        with sr.Microphone() as source:
            listener.adjust_for_ambient_noise(source, duration=1)
            talk("Listening for your command...")
            voice = listener.listen(source, timeout=10, phrase_time_limit=5)
            command = listener.recognize_google(voice).lower()
            print(f"Command received: {command}")
            return jsonify({"message": f"Command received: {command}"})
    except sr.WaitTimeoutError:
        return jsonify({"message": "Listening timed out. Please try again."})
    except sr.UnknownValueError:
        return jsonify({"message": "Sorry, I could not understand your voice."})
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"})

# API for camera-based object detection
@app.route('/api/camera', methods=['GET'])
def camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return jsonify({"error": "Could not open camera."})

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        for obj in results[0].boxes:
            x1, y1, x2, y2 = map(int, obj.xyxy[0])
            class_name = model.names[int(obj.cls[0])]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow('Camera Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('c'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return jsonify({"message": "Camera closed."})

# API for checking travel time
@app.route('/api/travel-time', methods=['POST'])
def travel_time():
    data = request.json
    current = data.get('current')
    destination = data.get('destination')

    # API key 
    api_key = str("AIzaSyA_lFtjlkDXbMTKrKGoOryo3z5oT0W6CLM")
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={current}&destinations={destination}&key={api_key}"
    response = requests.get(url)
    json_data = response.json()

    try:
        time_text = json_data["rows"][0]["elements"][0]["duration"]["text"]
        return jsonify({"message": f"The travel time is {time_text}"})
    except Exception as e:
        return jsonify({"message": "Failed to fetch travel time. Check your input or network."})

# Run the Flask app on your IPv4 address and make it accessible to others
if __name__ == '__main__':
    app.run(host='10.192.86.58', port=5000, debug=True)

#10.192.86.58 for eduroam
#192.168.2.50 for home
