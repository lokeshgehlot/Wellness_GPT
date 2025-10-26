import json
import asyncio
import firebase_admin
from firebase_admin import credentials
import os

# Initialize Firebase once globally
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

#  Global singleton instance
_wellness_manager = None

def get_wellness_manager():
    """Get or create the global WellnessManager instance"""
    global _wellness_manager
    
    if _wellness_manager is None:
        from wellness_manager import WellnessManager
        _wellness_manager = WellnessManager()
        
        # Initialize it synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_wellness_manager.initialize())
        finally:
            loop.close()
    
    return _wellness_manager

def wellness_gpt_agent(request):
    """Cloud Function to handle WellnessGPT requests"""
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
        return ('', 204, headers)
    
    headers = {'Access-Control-Allow-Origin': '*'}
    
    try:
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return (json.dumps({'error': 'No JSON data provided'}), 400, headers)
            
        if 'message' not in request_json:
            return (json.dumps({'error': 'Missing message'}), 400, headers)

        user_input = request_json['message']
        user_id = request_json.get('user_id')
        firebase_token = request_json.get('firebase_token')
        
        if not user_id and not firebase_token:
            user_id = "anonymous-user"

        # Use the singleton instance
        wellness_manager = get_wellness_manager()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(
                wellness_manager.process_message(
                    user_input=user_input,
                    user_id=user_id,
                    firebase_token=firebase_token
                )
            )
            
            pending_tasks = asyncio.all_tasks(loop)
            if pending_tasks:
                loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                
        finally:
            loop.close()

        return (json.dumps({'response': response}), 200, headers)
    
    except Exception as e:
        print(f"Error in cloud function: {str(e)}")
        import traceback
        traceback.print_exc()
        return (json.dumps({'error': 'Internal server error'}), 500, headers)