#!/usr/bin/env python3
# test_firebase_connection.py
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

load_dotenv()

def test_firebase_connection():
    print(" Testing Firebase Connection...")
    
    try:
        # Test 1: Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
            firebase_admin.initialize_app(cred)
        
        print("Firebase Admin SDK initialized")
        
        # Test 2: Test Firestore connection
        db = firestore.client()
        print("Firestore client connected")
        
        # Test 3: Test basic Firestore operations
        test_collection = db.collection('test_connection')
        
        # Write test data
        test_doc_ref = test_collection.document('connection_test')
        test_doc_ref.set({
            'test_message': 'Hello from WellnessGPT',
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        print("Test data written to Firestore")
        
        # Read test data
        doc = test_doc_ref.get()
        if doc.exists:
            print("Test data read from Firestore")
            print(f"   📝 Data: {doc.to_dict()}")
        else:
            print("Could not read test data")
        
        # Clean up test data
        test_doc_ref.delete()
        print(" Test data cleaned up")
        
        print("\n🎉 Firebase connection test PASSED!")
        
    except Exception as e:
        print(f" Firebase connection test FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_firebase_connection()