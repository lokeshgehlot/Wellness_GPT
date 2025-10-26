from firebase_admin import firestore, auth

# Only reference existing Firebase app
db = firestore.client()
users_collection = db.collection('users')
conversations_collection = db.collection('conversations')

def verify_firebase_token(token):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None