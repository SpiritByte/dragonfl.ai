# We combined everything into 1 file- this is how the program should ideally run.
# However, we have a hardware limitation on our laptops as the program demands more computing power.
# We use AMD Radeon Graphics which is not supported by CUDA- so we just split the program. Both features were displayed in the demo.

# At line 262, the "identify" search functionality code explanation is described.

import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime
from gtts import gTTS
import pyttsx3
import time

# Importing gcp firebase db and cloud vision api & google's text-to-speech service
from google.cloud import vision
from google.cloud.vision_v1 import types
import requests
import speech_recognition as sr

# CV2 helper methods for cpu acceleration
cv2.setUseOptimized(True)
cv2.setNumThreads(0)
cv2.ocl.setUseOpenCL(True)

# Create instance and auth use
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://dragonflai-b298c-default-rtdb.firebaseio.com/",
    "storageBucket": "https://dragonflai-b298c.appspot.com/"
})


# init'd some commonly used tools
speechVar = ""

engine = pyttsx3.init()

bucket = storage.bucket()

# Started opencv window
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

imgBackground = cv2.imread('Resources/background.png')

folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

print("Loading Encode File ...")
speechVar = "Loading Encode File ..."
engine.say(speechVar)
engine.runAndWait()

encodeListKnownWithIds = pickle.load(open('EncodedFile.p', 'rb'))
encodeListKnown, userIds = encodeListKnownWithIds  # destructuring pickle file
print("Encode File Loaded")
speechVar = "Encode File Loaded"
engine.say(speechVar)
engine.runAndWait()

speechVar = "Welcome to Dragonfly. I'm here to help you see. Just use the keyword called 'identify' to see."
engine.say(speechVar)
engine.runAndWait()

# localize all images from gcp cloud buckets storing user images
user_images = {}
for id in userIds:
    image_extensions = ['png', 'jpg', 'jpeg']
    for ext in image_extensions:
        blob = bucket.get_blob(f'Images/{id}.{ext}')
        if blob:
            array = np.frombuffer(blob.download_as_string(), np.uint8)
            user_images[id] = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
            break

# Variables used for logic and showing graphics on screen
modeType = 0
counter = 0
id = -1
imgUser = None

while True:

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp service account token'

    # Set up Google Cloud Vision client
    client = vision.ImageAnnotatorClient()

    # String aggregator
    itemsSeen = ""

    # Initialize the recognizer
    recognizer = sr.Recognizer()

    success, img = cap.read()

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Tracking locations of potential faces in the current frame
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    if faceCurFrame:
        # extract the current face encodings present in the frame
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(
                encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(
                encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                # designing frame for detected face
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

                id = userIds[matchIndex]
                if counter == 0:
                    # Once a match has been detected, present loader and begin to retrieve data from the db and cloud buckets
                    cvzone.putTextRect(
                        imgBackground, "Loading", 1, 1 (275, 400))
                    cv2.imshow("Face Attendance", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

                # Once imgUser has been reset or is none (from beginning), begin to retrieve it from the cloud bucket
                if imgUser is None:
                    # Get the Image from the storage
                    image_extensions = ['png', 'jpg', 'jpeg']
                    blob = None
                    for ext in image_extensions:
                        # Get the image based on the user id from blob
                        blob = bucket.get_blob(f'Images/{id}.{ext}')
                        if blob:
                            break

                    if blob is not None:
                        # If the decoded image is in the blob and blob exists, get back image as array
                        array = np.frombuffer(
                            blob.download_as_string(), np.uint8)
                        imgUser = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                    else:
                        print(f"Image for user {id} not found in storage.")

        if counter != 0:
            # Program is active and a face is detected

            if counter == 1:
                # First second after a face was detected
                # Get the detected user's face from the firebase nosql db
                userInfo = db.reference(f'Users/{id}').get()

                if userInfo is None:
                    print(f"User information not found for id: {id}")
                    continue  # Skip the rest of the loop iteration and onto next iteration of while true forever loop
                # Get last seen time and convert it into readble format
                last_seen = userInfo.get('last_seen')
                if last_seen:
                    datetimeObject = datetime.strptime(
                        last_seen, "%Y-%m-%d %H:%M:%S")
                    secondsElapsed = (
                        datetime.now() - datetimeObject).total_seconds()
                    print(secondsElapsed)

                    if secondsElapsed > 30:
                        # Register a new moment that the user has seen them again. It's only 30 seconds for the demo. In reality, it would be 5 mins after.
                        ref = db.reference(f'Users/{id}')
                        userInfo['times_seen'] += 1
                        speechVar = f"You are looking at your {userInfo['relation']}, {userInfo['name']}"
                        engine.say(speechVar)
                        engine.runAndWait()
                        # update user's last seen time
                        ref.child('times_seen').set(userInfo['times_seen'])
                        ref.child('last_seen').set(
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        cvzone.putTextRect(
                            imgBackground, "Already Seen. Skipping.", (75, 600), 1, 1, (255, 255, 255), (0, 0, 0))

                        counter = 0
                        imgBackground[44:44 + 633, 808:808 +
                                      414] = imgModeList[modeType]
                else:
                    print(f"Last seen timestamp not found for user id: {id}")
                    modeType = 3
                    counter = 0
                    imgBackground[44:44 + 633, 808:808 +
                                  414] = imgModeList[modeType]

            if modeType != 3:

                # Adjusted mode 2 duration extension (purpose of demo to show renderings of user data)
                if 10 < counter < 40:
                    # modeType = 2, user's info is rendered on right side
                    userInfo = db.reference(f'Users/{id}').get()

                    if userInfo is None:
                        print(f"User information not found for id: {id}")
                        continue  # Skip the rest of the loop iteration and recheck the new frame and back at loop start
                    # User name
                    textNamed = userInfo.get('name')
                    cvzone.putTextRect(
                        imgBackground, f"Updated db after identifying {textNamed}.", (75, 600), 1, 1, (255, 255, 255), (0, 0, 0))

                imgBackground[44:44 + 633, 808:808 +
                              414] = imgModeList[modeType]

                if counter <= 10:
                    # Render other user data
                    cv2.putText(imgBackground, str(userInfo['name']), (870, 125),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    cv2.putText(imgBackground, "User email: "+str(userInfo['email']), (880, 450),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, "User ID: "+str(id), (880, 500),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, "Birth Date: "+str(userInfo['birth_date']), (880, 530),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, "Phone: "+str(userInfo['phone_number']), (880, 560),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, "Times Seen: "+str(userInfo['times_seen']), (880, 590),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    if imgUser is not None:
                        imgUser = cv2.resize(imgUser, (216, 216))
                        imgBackground[175:175 + 216, 909:909 + 216] = imgUser

                counter += 1

                # Adjusted counter value for mode 2 duration (purpose of demo, show user data longer for presentation explanation)
                if counter >= 40:
                    counter = 0
                    modeType = 0
                    userInfo = []
                    imgUser = None  # Reset to None
                    imgBackground[44:44 + 633, 808:808 +
                                  414] = imgModeList[modeType]
    else:
        modeType = 0
        counter = 0

    cv2.imshow("Face Attendance", imgBackground)
    cv2.waitKey(1)

    try:
        # Listen for the voice command
        print("Listening for voice command...")
        with sr.Microphone() as source:
            # Increased timeout for longer audio sample
            audio = recognizer.listen(source, timeout=5)

        # Recognize the voice command using google's speech interface
        command = recognizer.recognize_google(audio)
        confidence = recognizer.recognize_google(audio, show_all=True)[
            'alternative'][0]['confidence']
        print("You said:", command)

        if "identify" in command.lower() and confidence > 0.8:  # Added confidence threshold
            # Open webcam
            cap = cv2.VideoCapture(0)

            # Wait for 3 seconds
            time.sleep(3)

            # Capture an image from the webcam
            ret, frame = cap.read()

            # Save the captured image
            image_path = "captured_image.jpg"
            cv2.imwrite(image_path, frame)

            # Close the webcam
            cap.release()

            # Prepare the image for Google Cloud Vision API
            with open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)

            # Rest of your code for label and text detection
            #### LABEL DETECTION ######
            # (Not used because it gives back results such as "jaw", "eyebrows", etc)

            response_label = client.label_detection(image=image)

            ### OBJECT DETCTION ###
            objects = client.object_localization(
                image=image).localized_object_annotations

            print(f"Number of objects found: {len(objects)}")
            for object_ in objects:
                print(f"\n{object_.name} (confidence: {object_.score})")
                itemsSeen += object_.name + ", "
                print("Normalized bounding polygon vertices: ")

            # print("Labels detected:")
            # for label in response_label.label_annotations:
            #     print({'label': label.description, 'score': label.score})
            #     itemsSeen += label.description + ", "

            #### TEXT DETECTION ######

            response_text = client.text_detection(image=image)

            text_seen = ""

            print("Text detected:")
            for r in response_text.text_annotations:
                d = {
                    'text': r.description
                }
                print(d)
                text_seen += r.description + ", "

            print(itemsSeen)

            # Prepare OpenAI API request
            # We used openai instead of text-bison, flan or any other vertex ai LLM because GPT was trained on more parameters and thus, could provide an answer based on the context of the labels.
            api_key = 'openai token'
            prompt = "Given below are a bunch of objects/text detected. Your job is to interpret what those labels resemble and make up. The labels are: \n " + \
                itemsSeen + ". After, read out what text got detected. Begin by announcing the objects you found with the prompt 'You see' and then announce the objects. If there is any text, then say 'You are also looking at text. The text says' and then the text. After, if you are able to be accurate, try to provide a description/interpretation of what the clues, labels/text make up or a part of.  \n" + text_seen

            data = {
                "prompt": prompt,
                "max_tokens": 200
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            response = requests.post(
                "https://api.openai.com/v1/engines/text-davinci-003/completions",
                json=data,
                headers=headers
            )

            result = response.json()

            generated_text = result['choices'][0]['text']
            print("Generated Text:", generated_text)
            engine.say(generated_text)
            engine.runAndWait()

        else:
            print("Command not recognized.")

    # Error handling based on Google's Speech/Text API interface. Avoids crashing program due to lack of input.
    except sr.WaitTimeoutError:
        print("No voice input detected. Continuing...")
    except sr.UnknownValueError:
        print("Sorry, could not understand the audio.")
    except sr.RequestError as e:
        print(
            f"Could not request results from Google Speech Recognition service; {e}")


# Clean up
cap.release()
cv2.destroyAllWindows()
