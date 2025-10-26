# agents/adk_base_agent.py
import os
import json
from google.adk.agents import Agent

class ADKAgent(Agent):
    def __init__(self, name: str, description: str, instruction: str, 
                 model: str = "gemini-2.0-flash", tools: list = None):
        
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not os.getenv("GOOGLE_API_KEY"):
            raise ValueError(
                "Either GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_API_KEY "
                "environment variable is required"
            )
        
        # List of confirmed working models from your API
        confirmed_models = [
            "gemini-2.0-flash",          
            "gemini-2.0-flash-001",      
            "gemini-2.5-flash",           
            "gemini-pro-latest",         
            "gemini-2.0-flash-lite",      
        ]
        
        last_error = None
        successful_model = None
        
        # Try the requested model first, then fallbacks
        model_attempts = [model] + [m for m in confirmed_models if m != model]
        
        for model_attempt in model_attempts:
            try:
                print(f" {name}: Trying model '{model_attempt}'")
                super().__init__(
                    name=name,
                    description=description,
                    instruction=instruction,
                    model=model_attempt,
                    tools=tools or []
                )
                successful_model = model_attempt
                print(f" {name}: Success with model '{model_attempt}'")
                break
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                if "404" in error_msg or "not found" in error_msg.lower():
                    print(f" {name}: Model '{model_attempt}' not found")
                elif "PERMISSION_DENIED" in error_msg:
                    print(f" {name}: Permission denied for '{model_attempt}'")
                else:
                    print(f" {name}: Model '{model_attempt}' failed - {error_msg[:100]}...")
                continue
        
        if not successful_model:
            raise Exception(f"All model attempts failed for {name}. Last error: {last_error}")