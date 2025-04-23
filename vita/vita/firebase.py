import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("vitalis-1-firebase-adminsdk-fbsvc-98e31ef762.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://vitalis-1-default-rtdb.firebaseio.com',
})
