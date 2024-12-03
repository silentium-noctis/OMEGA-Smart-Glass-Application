1. Download these files and put them in a folder together
2. These are the libraries you will need to install in order to use the features the program offers. Simply copy and paste this line in the terminal of your text editor:

/*
pip install ultralytics opencv-python requests SpeechRecognition pyttsx3 pywhatkit wikipedia-api pyjokes smtplib 
*/

3. Click on OMEGA_handsFree.py and press the RUN button to get started on the program. Go to step _ to see how to get the API key and password for the google maps and sending emails.
   
4. You will notice there are two options "handsFree" and "webAppControlled". The "handsFree" requires no extra work and has a built-in voice assistance which is used to control the application. Open the "handsFree" and Run the file.
   
5. For the "webAppControlled" option, you will need to do some tweaking with the IP address your device is currently in.
6. Open Command Prompt in your computer and write ipconfig. This will bring you the IP address configurations, where you will be able to find out the one your device is connected to. You are looking for the IPv4 Address which will be printed out.
7. In like 97 of OMEGA_webAppControlled, replace “0.0.0.0” with your IPv4 Address.
8. Run the program and use the link which is printed out in your terminal to access the website from any device connected to the same local network
