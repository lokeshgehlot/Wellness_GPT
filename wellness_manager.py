# wellness_manager_enhanced.py
import asyncio
from google.adk import Runner, sessions
from google.genai.types import Content, Part
from agents.orchestrator_agent import OrchestratorAgent
from agents.symptom_triage import SymptomTriageAgent
from agents.care_plan import CarePlanDesignAgent

class WellnessManager:
    def __init__(self):
        self.session_service = sessions.InMemorySessionService()
        
        print("🚀 Initializing WellnessGPT Agents...")
        self.agents = {}
        self._initialize_agents()
        
        self.current_agent = 'orchestrator'
        self.session_counter = 0
        
        # Enhanced conversation tracking to prevent loops
        self.conversation_context = {
            'in_symptom_assessment': False,
            'symptoms_mentioned': [],
            'questions_asked': [],
            'questions_answered': [],
            'assessment_stage': 0,  # 0=not started, 1=primary, 2=clarification, 3=complete
            'last_user_input': ''
        }
        
        if not self.agents:
            raise Exception("No agents could be initialized.")
        
        print("✅ All agents initialized successfully!")
    
    async def initialize(self):
        """Initialize the manager"""
        print("✅ Wellness Manager Ready!")
    
    def _initialize_agents(self):
        """Initialize agents with proper error handling"""
        agent_configs = {
            'orchestrator': {
                'class': OrchestratorAgent,
                'name': 'Orchestrator'
            },
            'symptom': {
                'class': SymptomTriageAgent, 
                'name': 'Symptom Triage'
            },
            'care_plan': {
                'class': CarePlanDesignAgent,
                'name': 'Care Plan'
            }
        }
        
        for key, config in agent_configs.items():
            try:
                self.agents[key] = config['class']()
                print(f"   ✅ {config['name']} Agent - Initialized")
            except Exception as e:
                print(f"   ❌ {config['name']} Agent - Failed: {e}")
    
    async def process_message(self, user_input: str) -> str:
        if not self.agents:
            return "I'm having some technical issues right now. Please try again in a moment."
        
        try:
            # Update conversation context BEFORE routing
            self._update_context(user_input)
            
            # Smart routing that prevents loops
            self._smart_route_agent(user_input)
            
            # Get the appropriate agent
            agent = self.agents[self.current_agent]
            
            # Create a new session for each message
            session_id = f"session-{self.session_counter}"
            user_id = "user-001"
            
            await self.session_service.create_session(
                app_name="wellness-gpt",
                user_id=user_id,
                session_id=session_id,
            )
            
            self.session_counter += 1
            
            runner = Runner(
                app_name="wellness-gpt",
                agent=agent,
                session_service=self.session_service
            )

            # Add comprehensive context to prevent repetition
            contextual_input = self._create_contextual_input(user_input)
            content = Content(parts=[Part(text=contextual_input)])
            
            print(f"💭 Processing with {self.current_agent} agent...")
            
            # Process the message
            response_generator = runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            )
            
            # Extract response from generator
            response_text = ""
            for event in response_generator:
                if hasattr(event, 'content') and event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                    break
            
            # Update context after response to track what was asked
            self._update_context_from_response(response_text)
            
            return response_text
            
        except Exception as e:
            return "I apologize, but I'm having trouble processing that right now. Could you try again?"
    
    def _update_context(self, user_input: str):
        """Update conversation context to track what we know"""
        user_input_lower = user_input.lower()
        self.conversation_context['last_user_input'] = user_input
        
        # Reset for new conversations
        if user_input_lower in ['hi', 'hello', 'hey', 'start over']:
            self.conversation_context.update({
                'in_symptom_assessment': False,
                'symptoms_mentioned': [],
                'questions_asked': [],
                'questions_answered': [],
                'assessment_stage': 0
            })
            return
        
        # Track symptom mentions
        symptom_keywords = ['fever', 'headache', 'cough', 'pain', 'hurt', 'symptom', 'nausea', 'dizzy', 'shivering']
        for symptom in symptom_keywords:
            if symptom in user_input_lower and symptom not in self.conversation_context['symptoms_mentioned']:
                self.conversation_context['symptoms_mentioned'].append(symptom)
        
        # Track answered questions
        if any(word in user_input_lower for word in ['day', 'days', 'hour', 'hours', 'week', 'weeks']):
            if 'onset' not in self.conversation_context['questions_answered']:
                self.conversation_context['questions_answered'].append('onset')
        
        if any(word in user_input_lower for word in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'scale']):
            if 'severity' not in self.conversation_context['questions_answered']:
                self.conversation_context['questions_answered'].append('severity')
        
        if any(word in user_input_lower for word in ['sharp', 'dull', 'throbbing', 'burning', 'aching']):
            if 'character' not in self.conversation_context['questions_answered']:
                self.conversation_context['questions_answered'].append('character')
    
    def _smart_route_agent(self, user_input: str):
        """Smart routing that prevents repetitive loops"""
        user_input_lower = user_input.lower()
        
        # If we're in the middle of symptom assessment, STAY with symptom agent
        if self.conversation_context['in_symptom_assessment']:
            self.current_agent = 'symptom'
            print(f"🔍 Continuing symptom assessment with Symptom Triage Agent")
            return
        
        # Only route to symptom agent for NEW symptom conversations
        symptom_keywords = ['fever', 'headache', 'cough', 'pain', 'hurt', 'symptom']
        care_plan_keywords = ['recovery', 'plan', 'treatment', 'exercise', 'rehab']
        
        if any(keyword in user_input_lower for keyword in symptom_keywords):
            self.current_agent = 'symptom'
            self.conversation_context['in_symptom_assessment'] = True
            self.conversation_context['assessment_stage'] = 1
            print(f"🔍 Routed to: Symptom Triage Agent")
        elif any(keyword in user_input_lower for keyword in care_plan_keywords):
            self.current_agent = 'care_plan'
            print(f"📋 Routed to: Care Plan Agent")
        else:
            self.current_agent = 'orchestrator'
            print(f"🌐 Routed to: Main Orchestrator")
    
    def _create_contextual_input(self, user_input: str) -> str:
        """Create comprehensive context to prevent repetitive questions"""
        context_parts = []
        
        # Symptom assessment context
        if self.conversation_context['in_symptom_assessment']:
            context_parts.append("You are in the middle of a symptom assessment. Continue the assessment naturally.")
            
            # Don't ask questions that have already been answered
            if 'onset' in self.conversation_context['questions_answered']:
                context_parts.append("The user has already told you when symptoms started. Do NOT ask about onset again.")
            if 'severity' in self.conversation_context['questions_answered']:
                context_parts.append("The user has already provided severity information. Do NOT ask about severity scale again.")
            if 'character' in self.conversation_context['questions_answered']:
                context_parts.append("The user has already described symptom character. Do NOT ask about pain character again.")
            
            # Progress through assessment stages
            if self.conversation_context['assessment_stage'] == 1:
                context_parts.append("You are in stage 1: Primary complaint. Focus on understanding the main symptoms.")
            elif self.conversation_context['assessment_stage'] == 2:
                context_parts.append("You are in stage 2: Symptom clarification. Ask about specific details.")
            elif self.conversation_context['assessment_stage'] >= 3:
                context_parts.append("You are in final stages. Consider providing department recommendation soon.")
        
        # Mentioned symptoms
        if self.conversation_context['symptoms_mentioned']:
            context_parts.append(f"Mentioned symptoms: {', '.join(self.conversation_context['symptoms_mentioned'])}")
        
        # Critical: Prevent asking same questions
        if self.conversation_context['questions_answered']:
            context_parts.append(f"Already answered: {', '.join(self.conversation_context['questions_answered'])}")
        
        if context_parts:
            context_message = "CONVERSATION CONTEXT:\n" + "\n".join(context_parts)
            context_message += "\n\nIMPORTANT: Continue the conversation naturally. Do NOT repeat questions that have already been answered. Move to the next appropriate question or provide recommendations."
            return f"{context_message}\n\nUser: {user_input}"
        
        return user_input
    
    def _update_context_from_response(self, response_text: str):
        """Update context based on what the agent just asked"""
        response_lower = response_text.lower()
        
        # Track what questions were just asked
        if 'when did' in response_lower or 'when did this start' in response_lower:
            if 'onset' not in self.conversation_context['questions_asked']:
                self.conversation_context['questions_asked'].append('onset')
        elif 'scale of 1' in response_lower or 'how severe' in response_lower:
            if 'severity' not in self.conversation_context['questions_asked']:
                self.conversation_context['questions_asked'].append('severity')
        elif 'what does it feel like' in response_lower or 'describe the' in response_lower:
            if 'character' not in self.conversation_context['questions_asked']:
                self.conversation_context['questions_asked'].append('character')
        
        # Detect assessment completion
        if any(phrase in response_lower for phrase in ['emergency department', 'visit the', 'department', 'schedule', 'recommend']):
            self.conversation_context['in_symptom_assessment'] = False
            self.conversation_context['assessment_stage'] = 0
            print("✅ Symptom assessment completed")
        
        # Progress assessment stage
        if self.conversation_context['in_symptom_assessment']:
            answered_count = len(self.conversation_context['questions_answered'])
            if answered_count >= 2 and self.conversation_context['assessment_stage'] < 3:
                self.conversation_context['assessment_stage'] = 3  # Ready for recommendation
    
    async def close(self):
        pass