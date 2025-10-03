#!/usr/bin/env python3
# main.py
import asyncio
import os
from dotenv import load_dotenv
from wellness_manager import WellnessManager

load_dotenv()

async def main():
   
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable is required")
        print("Please set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON file path")
        print("Example: export GOOGLE_APPLICATION_CREDENTIALS=\"/path/to/your/service-account-key.json\"")
        return

   
    sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not os.path.exists(sa_path):
        print(f"❌ ERROR: Service account file not found at: {sa_path}")
        print("Please check the file path and try again")
        return

    print("🔐 Using service account authentication")
    
    try:
        manager = WellnessManager()
        
        # Initialize the session before processing messages
        await manager.initialize()
        
        print("🤖 WellnessGPT - Medical Assistant")
        print("Type 'exit' to quit\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                break
                
            if user_input:
                print("💭 Processing...")
                response = await manager.process_message(user_input)
                print(f"🤖 WellnessGPT: {response}\n")
                
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
    except Exception as e:
        print(f"❌ Application error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())