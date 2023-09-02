import cv2
import face_recognition
import pickle
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

# This script helps generate encodings of user pictures and then saves the embeddings into a pickle file (EncodedFile.p) to help compare similarity against.
# Once embeddings are created and destructured in properMainer.py or app.py, each frame and location of face is compared against them.
# Similar faces are detected through euclidian distance.

print("started db script")

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "gcp firebase nosql db",
    "storageBucket": "gcp cloud bucket through firebase sdk"
})


folderPath = r"Images"
pathList = os.listdir(folderPath)
print(pathList)

imgList = []
userIds = []

for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    userIds.append(os.path.splitext(path)[0])
    fileName = f'{folderPath}/{path}'
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)


print("Images are", len(imgList))
print(userIds)


def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList


print("Econding started")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, userIds]
print("Encoding completed")

file = open("EncodedFile.p", "wb")
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("Ecoded ids saved in a file.")
