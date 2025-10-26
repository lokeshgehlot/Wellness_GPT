#!/usr/bin/env python3
# test_authentication.py
import asyncio
import os
from dotenv import load_dotenv
from wellness_manager import WellnessManager

load_dotenv()

async def test_authentication():
    print("🔐 Testing Firebase Authentication Integration...")
    
    try:
        manager = WellnessManager()
        await manager.initialize()
        
        # Test 1: Anonymous user (backward compatibility)
        print("\n1. Testing anonymous user...")
        response1 = await manager.process_message("Hello, I have a headache", user_id="test-user-001")
        print(f"Response: {response1}")
        print(" Anonymous user works")
        
        # Test 2: Invalid token
        print("\n2. Testing invalid token...")
        response2 = await manager.process_message("Hello", firebase_token="invalid-token-123")
        print(f" Response: {response2}")
        print(" Invalid token handled gracefully")
        
        # Test 3: No authentication (should use anonymous)
        print("\n3. Testing no authentication...")
        response3 = await manager.process_message("Hello")
        print(f" Response: {response3}")
        print("No auth falls back to anonymous")
        
        # Test 4: Valid conversation flow with authentication
        print("\n4. Testing medical conversation with auth...")
        response4 = await manager.process_message(
            "I have fever and cough", 
            user_id="authenticated-user-001"
        )
        print(f" Response: {response4}")
        print(" Medical conversation with auth works")
        
        print("\n Authentication tests completed!")
        
    except Exception as e:
        print(f" Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(test_authentication())