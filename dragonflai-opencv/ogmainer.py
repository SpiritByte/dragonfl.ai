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
import numpy as np
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://rythmhacks-4811d-default-rtdb.firebaseio.com/",
    "storageBucket": "rythmhacks-4811d.appspot.com"
})

bucket = storage.bucket()

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

imgBackground = cv2.imread('Resources/background.png')

# Importing the mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))
# print(len(imgModeList))

# Load the encoding file
print("Loading Encode File ...")
file = open('EncodedFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, userIds = encodeListKnownWithIds
# print(studentIds)
print("Encode File Loaded")

modeType = 0
counter = 0
id = -1
imgUser = []

while True:
    success, img = cap.read()

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(
                encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(
                encodeListKnown, encodeFace)
            # print("matches", matches)
            # print("faceDis", faceDis)

            matchIndex = np.argmin(faceDis)
            # print("Match Index", matchIndex)

            # if matches[matchIndex]:
            #     # print("Known Face Detected")
            #     # print(studentIds[matchIndex])
            #     y1, x2, y2, x1 = faceLoc
            #     y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            #     bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
            #     imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
            #     id = userIds[matchIndex]
            #     if counter == 0:
            #         cvzone.putTextRect(imgBackground, "Loading", (275, 400))
            #         cv2.imshow("Face Attendance", imgBackground)
            #         cv2.waitKey(1)
            #         counter = 1
            #         modeType = 1

            if matches[matchIndex]:
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

                id = userIds[matchIndex]
                if counter == 0:
                    cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                    cv2.imshow("Face Attendance", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

                # Draw OpenCV rectangle and name
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7
                font_thickness = 2
                cv2.rectangle(
                    imgBackground, (bbox[0], bbox[1] - 30), (bbox[0] + bbox[2], bbox[1]), (0, 255, 0), -1)
                cv2.putText(imgBackground, str(
                    id), (bbox[0] + 5, bbox[1] - 5), font, font_scale, (0, 0, 0), font_thickness)

        if counter != 0:

            if counter == 1:
                # Get the Data
                userInfo = db.reference(f'Users/{id}').get()

                if userInfo is None:
                    print(f"User information not found for id: {id}")
                    continue  # Skip the rest of the loop iteration

                # Get the Image from the storage

                image_extensions = ['png', 'jpg', 'jpeg']
                blob = None
                for ext in image_extensions:
                    blob = bucket.get_blob(f'Images/{id}.{ext}')
                    if blob:
                        break

                if blob is not None:
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgUser = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                else:
                    print(f"Image for user {id} not found in storage.")

                last_seen = userInfo.get('last_seen')
                if last_seen:
                    datetimeObject = datetime.strptime(
                        last_seen, "%Y-%m-%d %H:%M:%S")
                    secondsElapsed = (
                        datetime.now() - datetimeObject).total_seconds()
                    print(secondsElapsed)
                    if secondsElapsed > 30:
                        ref = db.reference(f'Users/{id}')
                        userInfo['times_seen'] += 1
                        ref.child('times_seen').set(userInfo['times_seen'])
                        ref.child('last_seen').set(
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        # modeType = 3
                        cvzone.putTextRect(
                            imgBackground, "Already Seen. Skipping.", (75, 600), 2, 2, (255, 255, 255), (0, 0, 0))

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

                if 10 < counter < 40:  # Adjusted mode 2 duration
                    modeType = 2

                imgBackground[44:44 + 633, 808:808 +
                              414] = imgModeList[modeType]

                if counter <= 10:
                    cv2.putText(imgBackground, str(userInfo['relation']), (861, 125),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(userInfo['email']), (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(id), (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(userInfo['birth_date']), (910, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv2.putText(imgBackground, str(userInfo['phone_number']), (1025, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    cv2.putText(imgBackground, str(userInfo['times_seen']), (1125, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                    imgUser = cv2.resize(imgUser, (216, 216))
                    imgBackground[175:175 + 216, 909:909 + 216] = imgUser

                counter += 1

                if counter >= 40:  # Adjusted counter value for mode 2 duration
                    counter = 0
                    modeType = 0
                    userInfo = []
                    imgUser = []
                    imgBackground[44:44 + 633, 808:808 +
                                  414] = imgModeList[modeType]
    else:
        modeType = 0
        counter = 0

    cv2.imshow("Face Attendance", imgBackground)
    cv2.waitKey(1)

# Clean up
cap.release()
cv2.destroyAllWindows()
