#!/usr/bin/env python3
# test_cloud_function_auth.py
import json
import os
import sys

# CRITICAL: Load .env FIRST before any imports
from dotenv import load_dotenv
load_dotenv()

# Verify environment is loaded
print("🔍 Checking environment variables...")
has_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
has_api_key = os.getenv("GOOGLE_API_KEY")

if not has_creds and not has_api_key:
    print("❌ ERROR: No Google Cloud credentials found!")
    print("Please create a .env file with either:")
    print("  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
    print("  OR")
    print("  GOOGLE_API_KEY=your_api_key")
    sys.exit(1)

if has_creds:
    print(f"✅ Using service account: {has_creds}")
    if not os.path.exists(has_creds):
        print(f"❌ ERROR: Service account file not found at: {has_creds}")
        sys.exit(1)
else:
    print(f"✅ Using API key authentication")

# NOW import the cloud function (which imports WellnessManager)
from cloud_functions import wellness_gpt_agent

class MockRequest:
    def __init__(self, json_data, method='POST'):
        self.method = method
        self._json_data = json_data
    
    def get_json(self, silent=False):
        return self._json_data

def test_cloud_function_auth():
    print("\n🌐 Testing Cloud Function with Authentication...")
    print("=" * 70)
    
    # Test 1: Legacy user_id (backward compatibility)
    print("\n[TEST 1] Legacy user_id (backward compatibility)")
    print("-" * 70)
    test_data_legacy = {
        'user_id': 'legacy-user-123',
        'message': 'Hello, I have a headache'
    }
    
    request_legacy = MockRequest(test_data_legacy)
    response, status_code, headers = wellness_gpt_agent(request_legacy)
    
    print(f"📊 Status Code: {status_code}")
    response_data = json.loads(response)
    
    if 'error' in response_data:
        print(f"❌ Error: {response_data['error']}")
    else:
        print(f"✅ Response: {response_data.get('response', 'No response')[:100]}...")
    
    if status_code == 200 and 'response' in response_data:
        print("✅ Legacy user_id authentication works")
    else:
        print("❌ Legacy user_id authentication failed")
    
    # Test 2: Firebase token authentication
    print("\n[TEST 2] Firebase token authentication")
    print("-" * 70)
    test_data_token = {
        'firebase_token': 'test-token-456',  # Will be rejected as invalid
        'message': 'Hello with token auth'
    }
    
    request_token = MockRequest(test_data_token)
    response, status_code, headers = wellness_gpt_agent(request_token)
    
    print(f"📊 Status Code: {status_code}")
    response_data = json.loads(response)
    
    if 'error' in response_data:
        print(f"⚠️  Expected error (invalid token): {response_data['error']}")
    else:
        print(f"✅ Response: {response_data.get('response', 'No response')[:100]}...")
    
    # Invalid token should either return error or fall back to anonymous
    if status_code in [200, 401]:
        print("✅ Firebase token handling works (invalid token properly handled)")
    else:
        print("❌ Firebase token handling unexpected")
    
    # Test 3: Anonymous user (no auth)
    print("\n[TEST 3] Anonymous user (no authentication)")
    print("-" * 70)
    test_data_anon = {
        'message': 'Hello anonymous'
    }
    
    request_anon = MockRequest(test_data_anon)
    response, status_code, headers = wellness_gpt_agent(request_anon)
    
    print(f"📊 Status Code: {status_code}")
    response_data = json.loads(response)
    
    if 'error' in response_data:
        print(f"❌ Error: {response_data['error']}")
    else:
        print(f"✅ Response: {response_data.get('response', 'No response')[:100]}...")
    
    if status_code == 200 and 'response' in response_data:
        print("✅ Anonymous user works")
    else:
        print("❌ Anonymous user failed")
    
    # Test 4: Error handling - missing message
    print("\n[TEST 4] Error handling - missing message")
    print("-" * 70)
    test_data_error = {
        'user_id': 'test-user'
        # Missing 'message' field
    }
    
    request_error = MockRequest(test_data_error)
    response, status_code, headers = wellness_gpt_agent(request_error)
    
    print(f"📊 Status Code: {status_code} (expected: 400)")
    response_data = json.loads(response)
    print(f"❌ Error message: {response_data.get('error', 'No error')}")
    
    if status_code == 400:
        print("✅ Error handling works correctly")
    else:
        print("❌ Error handling failed (wrong status code)")
    
    # Test 5: CORS preflight (OPTIONS request)
    print("\n[TEST 5] CORS preflight (OPTIONS request)")
    print("-" * 70)
    request_options = MockRequest({}, method='OPTIONS')
    response, status_code, headers = wellness_gpt_agent(request_options)
    
    print(f"📊 Status Code: {status_code} (expected: 204)")
    print(f"📋 Headers: {headers}")
    
    if status_code == 204 and 'Access-Control-Allow-Origin' in headers:
        print("✅ CORS preflight works")
    else:
        print("❌ CORS preflight failed")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print("✅ Cloud Function authentication tests completed!")
    print("\nNote: If agents fail to initialize, check that:")
    print("  1. .env file exists in project root")
    print("  2. GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_API_KEY is set")
    print("  3. Service account file exists at the specified path")
    print("  4. Service account has necessary permissions")

if __name__ == "__main__":
    try:
        test_cloud_function_auth()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()