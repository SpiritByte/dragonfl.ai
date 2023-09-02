import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# A script created to load the database with some initial data instead of using a manual procedure.
# Not used in app but rather to fill empty db created

print("started db script")

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "gcp database url",
})

ref = db.reference("Users")

print("started db reference")

data = {
    "211211": {"name": "Bhavya Patel", "phone_number": 6475398191, "birth_date": "2007", "email": "bhavyap@gmail.com", "relation": "brother", "last_seen": "2023-08-30 00:54:34", "times_seen": 1},
    "411411": {"name": "Sajan Paventhan", "phone_number": 4356475453, "birth_date": "2007", "email": "sajbeast@gmail.com", "relation": "friend", "last_seen": "2023-08-30 00:54:34", "times_seen": 2},
    "844887": {"name": "Anirudh Vangara", "phone_number": 1234566556, "birth_date": "2007", "email": "anirudhvan@gmail.com", "relation": "cousin", "last_seen": "2023-08-30 00:54:34", "times_seen": 3}

}

# Pushing items above to db

for key, value in data.items():
    ref.child(key).set(value)
    print("pushed user with key:", key)
