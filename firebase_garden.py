import

firebaseConfig = {"apiKey": "AIzaSyCdvYLtio80mGb_6eeQyajLMTXOW7fPJdM",
                  "authDomain": "garden-data-827b1.firebaseapp.com",
                  "databaseURL": "https://garden-data-827b1-default-rtdb.firebaseio.com",
                  "projectId": "garden-data-827b1",
                  "storageBucket": "garden-data-827b1.appspot.com",
                  "messagingSenderId": "181091786559",
                  "appId": "1:181091786559:web:2b7ea887e5061824867d8a"}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)

db = firebase.database()
auth = firebase.auth()
# storage = firebase.storage()
# login
email = input("enter your email")
password = input("enter your password")
try:
    auth.sign_in_with_email_and_password(email, password)
    print("sucessfully signed in!")
except:
    print("invalid user ort password. Try again.")

# Storage
filedata = input("enter the data of the file that you want to upload")
cloudfiledata = input("enter the data of the file on the cloud")
storage.child(cloudfiledata).put(filedata)

# Database
data = {}
db.push(data)

# update
# db.child("").child("").update({:})
sensor = db.child("sensor").get()
for instance in sensor.each():
    if instance.val()['data'] == "":
        db.child("sensor").chil
        db(instance.key()).update({"data:"})
