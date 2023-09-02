
import cv2
import time
import os
from google.cloud import vision
from google.cloud.vision_v1 import types
import requests
import speech_recognition as sr

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp service account token'

# Set up Google Cloud Vision client
client = vision.ImageAnnotatorClient()

# String aggregator
itemsSeen = ""

# Initialize the recognizer
recognizer = sr.Recognizer()

while True:
    try:
        # Listen for the voice command
        print("Listening for voice command...")
        with sr.Microphone() as source:
            # Increased timeout for longer audio sample
            audio = recognizer.listen(source, timeout=5)

        # Recognize the voice command
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

            response_label = client.label_detection(image=image)
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

            api_key = 'token'
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

        else:
            print("Request now being passed to llm.")

        gpt_API_URL = "http://localhost:3000/api/v1/prediction/fcf67374-d710-4adf-8f45-1b070d6bf7e3"

        def query(payload):
            response = requests.post(gpt_API_URL, json=payload)
            return response.json()

        output = query({
            "question": command.lower(),
        })

        print(output)

    except sr.WaitTimeoutError:
        print("No voice input detected. Continuing...")
    except sr.UnknownValueError:
        print("Sorry, could not understand the audio.")
    except sr.RequestError as e:
        print(
            f"Could not request results from Google Speech Recognition service; {e}")
