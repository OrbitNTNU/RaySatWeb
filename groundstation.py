import firebase_admin
from firebase_admin import db, credentials
from dotenv import load_dotenv
import os

load_dotenv()

GCP_PROJECT_ID = os.getenv('projectID')
SERIVCE_ACCOUNT_ID = os.getenv('SERVICE_ACCOUNT_FILE')
STORAGE_BUCKET_NAME = os.getenv('storageBucket')
DATABASE_URL = os.getenv('databaseURL')

# default_app = firebase_admin.initialize_app()
cred = credentials.Certificate("credentials.json")
firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

ref = db.reference("/")
print(ref.get())

"""
ref = db.referenece('sensordata/temperature')

# Saving userinfo to database located at an URL server (in JSON)
# Alternative 1, overwrites data located at users_ref
users_ref = ref.child('users')          
users_ref.set({
    'john': {
        'date_of_birth': '14. september 1999'
        'full_name': 'John Paulson'
    },
    'paul': {
        'date_of_birth': '24. april 1970'
        'full_name': 'Paul John'
    }
    'joe': {
        'date_of_birth': '6. september 1879'
        'full_name': 'Joe'
    }
})

# Alternative 2, does not overwrite data but rather just modifies the child node bob
users_ref.child('bob').set({            
    'date_of_birth': '20. oktober 2025'
    'full_name': 'Bob Bobson'
}
)

# Updating saved data, set instead of update would delete the other data already known (date of birth and full name)
hopper_ref = users_ref.child('micho')
hopper_ref.update({
    'nickname': 'Amazing Mike'
})

# Can update multiple users/child-node at once
users_ref.update({
    'ablerto/nickname': 'Brilliant Albert',
    'micho/nickname': 'Amazing Mike'
})

# Overwrites the entire user when updating. Removes fex date of bith and full_name
users_ref.update({
    'ablerto': {
        'nickname': 'Brilliant Albert'
    },
    'micho': {
        'nickname': 'Amazing Mike'
    }
})
"""