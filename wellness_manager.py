"""
WellnessGPT Manager - Main orchestrator for multi-agent healthcare system

This module manages the coordination between specialized healthcare agents including:
- Symptom triage and assessment
- Care plan design
- Insurance policy analysis  
- Appointment scheduling
- Lab test booking (NEW)
- Pharmacy services

Author: WellnessGPT Team
Version: 2.0 (with Lab Test Agent integration)
"""

# ==================== IMPORTS ====================
import asyncio
import firebase_admin
from firebase_admin import firestore, credentials, auth
from google.adk import Runner, sessions
from google.genai.types import Content, Part
import json
import re
import random
from datetime import datetime, timedelta


# ==================== MAIN MANAGER CLASS ====================

class WellnessManager:
    """
    Main manager class for WellnessGPT healthcare platform.
    
    Coordinates multiple specialized agents to provide comprehensive healthcare services
    including symptom assessment, scheduling, lab tests, pharmacy, and insurance.
    
    Attributes:
        agents (dict): Dictionary of initialized agent instances
        session_service: ADK session service for conversation management
        db: Firestore database client
        user_contexts (dict): Per-user conversation contexts
    """
    
    def __init__(self):
        """Initialize WellnessManager with Firebase and agent setup"""
        self.setup_firebase()
        self.session_service = sessions.InMemorySessionService()
        
        print("🏥 Initializing WellnessGPT Agents...")
        self.agents = {}
        
        # ==================== MEDICINE IMAGE MAPPING ====================
        # Maps medicine names/categories to appropriate images for pharmacy agent
        self.MEDICINE_IMAGE_MAP = {
            # Pain & Fever
            "paracetamol": "/static/images/medicine/crocin.jpg",
            "dolo": "/static/images/medicine/dolo.jpg",
            "ibuprofen": "/static/images/medicine/volini.jpg",
            "aspirin": "/static/images/medicine/crocin.jpg",
            "calpol": "/static/images/medicine/crocin.jpg",
            "crocin": "/static/images/medicine/crocin.jpg",
            "volini": "/static/images/medicine/volini.jpg",
            
            # Antibiotics
            "amoxicillin": "/static/images/medicine/moxkind.jpg",
            "azithromycin": "/static/images/medicine/azithral.jpg",
            "ciprofloxacin": "/static/images/medicine/cifran.jpg",
            "moxikind": "/static/images/medicine/moxkind.jpg",
            "azithral": "/static/images/medicine/azithral.jpg",
            "cifran": "/static/images/medicine/cifran.jpg",
            
            # Allergy & Asthma
            "montelukast": "/static/images/medicine/montair.jpg",
            "cetirizine": "/static/images/medicine/allegra.jpg",
            "levocetirizine": "/static/images/medicine/allegra.jpg",
            "allegra": "/static/images/medicine/allegra.jpg",
            "montair": "/static/images/medicine/montair.jpg",
            "asthalin": "/static/images/medicine/asthalin.jpg",
            "duolin": "/static/images/medicine/duolin.jpg",
            
            # Chronic Care (Diabetes, BP, Cholesterol)
            "metformin": "/static/images/medicine/glycomet.jpg",
            "atorvastatin": "/static/images/medicine/storvas.jpg",
            "lisinopril": "/static/images/medicine/telma.jpg",
            "amlodipine": "/static/images/medicine/telma.jpg",
            "enalapril": "/static/images/medicine/telma.jpg",
            "ramipril": "/static/images/medicine/telma.jpg",
            "glycomet": "/static/images/medicine/glycomet.jpg",
            "storvas": "/static/images/medicine/storvas.jpg",
            "telma": "/static/images/medicine/telma.jpg",
            "amaryl": "/static/images/medicine/amaryl.jpg",
            
            # Gastrointestinal
            "omeprazole": "/static/images/medicine/pan.jpg",
            "pantoprazole": "/static/images/medicine/pan.jpg",
            "domperidone": "/static/images/medicine/digene.jpg",
            "rabeprazole": "/static/images/medicine/rantac.jpg",
            "pan": "/static/images/medicine/pan.jpg",
            "digene": "/static/images/medicine/digene.jpg",
            "rantac": "/static/images/medicine/rantac.jpg",
            
            # Vitamins & Supplements
            "vitamin c": "/static/images/medicine/becosules.jpg",
            "vitamin d3": "/static/images/medicine/becosules.jpg",
            "calcium": "/static/images/medicine/shelcal.jpg",
            "multivitamin": "/static/images/medicine/revital.jpg",
            "iron": "/static/images/medicine/becosules.jpg",
            "becosules": "/static/images/medicine/becosules.jpg",
            "shelcal": "/static/images/medicine/shelcal.jpg",
            "revital": "/static/images/medicine/revital.jpg",
            "liv": "/static/images/medicine/liv.jpg",
            
            # Cold & Cough
            "sinarest": "/static/images/medicine/sinarest.jpg",
            "combiflam": "/static/images/medicine/combiflam.jpg",
            
            # Default
            "default": "/static/images/medicine/medicine-placeholder.jpg"
        }
        # Insurance Policy Data 
        self.INSURANCE_POLICY_DATA = {
            "policy_details": {
                "insurer": "HealthSure Insurance",
                "policy_name": "HealthSure Comprehensive Care",
                "sum_insured": "₹5,00,000",
                "policy_term": "1 Year",
                "renewal_type": "Lifelong Renewable",
                "age_entry": {"min_age": "18 years", "max_age": "65 years", "lifelong_renewal": True}
            },
            "coverage": {
                "hospitalization": {
                    "room_rent_rule": "Up to ₹5,000 per day (Single Private AC Room)",
                    "icu_charges": "Up to ₹10,000 per day",
                    "pre_hospitalization_days": "30 days",
                    "post_hospitalization_days": "60 days",
                    "day_care_procedures": "Covered (200+ procedures)",
                    "domiciliary_treatment": {"covered": "Yes", "exclusions": ["Chronic conditions requiring long-term home care"]},
                    "ambulance": {"road": "₹2,000 per emergency", "air": "₹50,000 per emergency (subject to approval)"}
                },
                "cashless": {
                    "available": True,
                    "network_hospital_check_url": "https://healthsure.in/network-hospitals",
                    "hospital_cashless_eligibility": "Yes"
                },
                "special_covers": {
                    "maternity": {
                        "covered": True, 
                        "waiting_period": "24 months", 
                        "normal_delivery_limit": "₹50,000", 
                        "c_section_limit": "₹75,000", 
                        "newborn_cover": "Covered for first 90 days", 
                        "vaccination_cover": "₹5,000 per year"
                    },
                    "bariatric_surgery": {"covered": True, "waiting_period": "48 months", "limit": "₹2,00,000"},
                    "ayush_treatment": {"covered": True, "limit": "₹25,000 per year", "exclusions": ["Experimental AYUSH treatments"]},
                    "organ_donor_expenses": "Covered up to ₹1,00,000",
                    "modern_treatments": "Covered (Robotic surgery, Stem cell therapy, Oral chemotherapy)"
                }
            },
            "financial_features": {
                "automatic_sum_restoration": "Yes (once per policy year)",
                "cumulative_bonus": "10% increase in sum insured for each claim-free year (max 50%)",
                "hospital_cash_allowance": "₹2,000 per day (max 15 days)",
                "wellness_rewards": "₹2,000 annual health checkup",
                "health_checkup": "Comprehensive health checkup every 2 years"
            },
            "waiting_periods": {
                "initial": "30 days",
                "pre_existing_diseases": "36 months",
                "specific_diseases_wait": {
                    "period": "24 months",
                    "diseases": ["Hernia", "Cataract", "Joint replacements", "Gall stones"]
                }
            },
            "co_payment": {
                "applicable": True,
                "age_threshold": "61 years and above",
                "percent": "20%"
            },
            "exclusions": {
                "standard_exclusions": [
                    "Cosmetic surgery", 
                    "Infertility treatments", 
                    "Experimental/Unproven treatments", 
                    "War/nuclear events",
                    "Dental treatments (unless requiring hospitalization)",
                    "Hearing aids and spectacles"
                ],
                "policy_specific_exclusions": ["Adventure sports injuries", "Self-inflicted injuries"]
            },
            "surgery_assessment": {
                "procedure_name": "Knee Replacement Surgery",
                "is_covered_now": True,
                "reason": "Covered after 24-month waiting period for specific diseases",
                "out_of_pocket_estimate": "Approximately ₹20,000 (20% co-payment if applicable)",
                "cashless_available": "Yes at network hospitals",
                "red_flags": ["Required 24-month waiting period for joint replacements"]
            }
        }
        
        self.PHARMACY_INVENTORY_DATA = {
            "pharmacy_info": {
                "name": "Wellness Pharmacy",
                "locations": ["Delhi", "Mumbai", "Bangalore", "Chennai"],
                "delivery_available": True,
                "min_delivery_amount": 500,
                "delivery_time": "2-4 hours"
            },
            "inventory": {
                "pain_fever": {
                    "Paracetamol (500mg)": {"available": True, "price": 20, "type": "strip", "generic_available": True},
                    "Ibuprofen (400mg)": {"available": True, "price": 35, "type": "strip", "generic_available": True},
                    "Aspirin (75mg)": {"available": True, "price": 15, "type": "strip", "generic_available": True},
                    "Dolo 650": {"available": False, "price": 25, "type": "strip", "generic_available": True}
                },
                "antibiotics": {
                    "Amoxicillin (500mg)": {"available": False, "price": 150, "type": "strip", "generic_available": True},
                    "Azithromycin (500mg)": {"available": False, "price": 200, "type": "strip", "generic_available": True},
                    "Ciprofloxacin (500mg)": {"available": True, "price": 120, "type": "strip", "generic_available": True}
                },
                "chronic_care": {
                    "Metformin (500mg)": {"available": True, "price": 80, "type": "strip", "generic_available": True},
                    "Atorvastatin (10mg)": {"available": True, "price": 110, "type": "strip", "generic_available": True},
                    "Lisinopril (10mg)": {"available": False, "price": 120, "type": "strip", "generic_available": False},
                    "Amlodipine (5mg)": {"available": True, "price": 95, "type": "strip", "generic_available": True}
                },
                "gastrointestinal": {
                    "Omeprazole (20mg)": {"available": True, "price": 90, "type": "strip", "generic_available": True},
                    "Pantoprazole (40mg)": {"available": True, "price": 110, "type": "strip", "generic_available": True},
                    "Domperidone (10mg)": {"available": True, "price": 45, "type": "strip", "generic_available": True}
                },
                "allergy_cold": {
                    "Cetirizine (10mg)": {"available": True, "price": 25, "type": "strip", "generic_available": True},
                    "Levocetirizine (5mg)": {"available": True, "price": 40, "type": "strip", "generic_available": True},
                    "Montelukast (10mg)": {"available": True, "price": 85, "type": "strip", "generic_available": True}
                },
                "supplements": {
                    "Vitamin C (500mg)": {"available": True, "price": 30, "type": "strip", "generic_available": True},
                    "Vitamin D3 (60K IU)": {"available": True, "price": 50, "type": "bottle", "generic_available": True},
                    "Calcium + Vitamin D3": {"available": True, "price": 60, "type": "bottle", "generic_available": True},
                    "Multivitamin": {"available": True, "price": 75, "type": "bottle", "generic_available": True}
                }
            },
            "ordering_info": {
                "pickup_ready_time": "2-4 hours",
                "order_arrival_time": "1-2 days",
                "delivery_charge": "Free for orders above ₹500, ₹50 otherwise",
                "prescription_required": True,
                "id_required": True
            },
            "alternative_options": {
                "Paracetamol": ["Dolo 650", "Calpol 650"],
                "Amoxicillin": ["Amoxclav", "Moxikind CV"],
                "Azithromycin": ["Azipro", "Zithrox"],
                "Lisinopril": ["Enalapril", "Ramipril"]
            }
        }
        
        # Routing keywords
        self.INSURANCE_KEYWORDS = [
            'insurance', 'policy', 'coverage', 'claim', 'premium',
            'sum insured', 'maternity', 'cashless', 'hospitalization'
        ]
        
        self.SYMPTOM_KEYWORDS = [
            'symptom', 'pain', 'fever', 'headache', 'cough', 'cold',
            'nausea', 'vomit', 'dizzy', 'fatigue', 'tired', 'weak',
            'hurt', 'ache', 'unwell', 'sick', 'ill', 'not feeling well',
            'broken', 'fracture', 'sprain', 'injury'
        ]
        
        self.CARE_PLAN_KEYWORDS = [
            'care plan', 'treatment plan', 'recovery', 'rehab', 'rehabilitation',
            'therapy', 'medication', 'exercise', 'diet', 'physical therapy',
            'surgery', 'surgical', 'post-op', 'post operative', 'recover from',
            'knee surgery', 'hip surgery', 'shoulder surgery', 'operation'
        ]

        self.SCHEDULING_KEYWORDS = [
            'schedule', 'appointment', 'book', 'meet doctor', 'see doctor',
            'visit doctor', 'consult doctor', 'fix appointment', 'set appointment',
            'make appointment', 'arrange appointment', 'book appointment'
        ]

        
        
        self.PHARMACY_KEYWORDS = [
            'pharmacy', 'medicine', 'medication', 'prescription', 'drug',
            'pill', 'tablet', 'capsule', 'injection', 'dose', 'dosage',
            'pharmacist', 'meds', 'prescribed', 'refill', 'order medicine',
            'buy medicine', 'get medicine', 'availability', 'in stock',
            'out of stock', 'delivery', 'pickup', 'pharmaceutical'
        ]
        
        self._initialize_agents()
        self.session_counter = 0
        self.user_contexts = {}
        self.user_sessions = {}
        
        print("✓ All agents initialized successfully!")

    # === CARD GENERATION METHODS ===
    def _generate_hospital_cards(self) -> list:
        """Generate hospital selection cards"""
        return [
            {
                "type": "hospital",
                "title": "Apollo Hospital",
                "description": "Multi-specialty hospital with emergency services, ICU, and all major departments",
                "meta": "📍 Delhi • ⭐ 4.5 • 🚑 24/7 Emergency",
                "selection_text": "Apollo Hospital",
                "hospital_id": "apollo_delhi"
            },
            {
                "type": "hospital", 
                "title": "Max Super Specialty Hospital",
                "description": "Advanced cardiac care, neurosciences, oncology with latest medical technology",
                "meta": "📍 Delhi • ⭐ 4.6 • 💰 Cashless Available",
                "selection_text": "Max Super Specialty Hospital", 
                "hospital_id": "max_delhi"
            },
            {
                "type": "hospital",
                "title": "Fortis Escorts Heart Institute",
                "description": "World-class cardiac care center with renowned cardiologists and cardiac surgeons",
                "meta": "📍 Delhi • ⭐ 4.7 • ❤️ Cardiac Specialist",
                "selection_text": "Fortis Escorts Heart Institute",
                "hospital_id": "fortis_cardiac"
            }
        ]

    def _generate_booking_confirmation_card(self, context: dict) -> dict:
        """Generate comprehensive booking confirmation card with all appointment details"""
        scheduling_info = context['shared_memory'].get('scheduling_info', {})
        
        # Generate appointment details
        appointment_id = f"APPT-{random.randint(1000, 9999)}-{datetime.now().strftime('%m%d')}"
        
        # Determine department based on symptoms
        symptoms = context['shared_memory'].get('symptoms_discussed', [])
        if any(symptom in ['fever', 'cold', 'cough'] for symptom in symptoms):
            department = "General Medicine"
            doctor = "Dr. Sharma"
        elif any(symptom in ['broken', 'fracture', 'pain'] for symptom in symptoms):
            department = "Orthopedics" 
            doctor = "Dr. Kumar"
        else:
            department = "General Medicine"
            doctor = "Dr. Sharma"
        
        # Generate appointment time (next available slot)
        tomorrow = datetime.now() + timedelta(days=1)
        time_slot = "10:00 AM"
        
        return {
            "type": "booking_confirmation",
            "title": "✅ Appointment Confirmed!",
            "appointment_id": appointment_id,
            "details": {
                "Department": department,
                "Hospital": scheduling_info.get('hospital_preference', 'Apollo Hospital'),
                "Doctor": doctor,
                "Date": tomorrow.strftime("%B %d, %Y"),
                "Time": time_slot,
                "Location": scheduling_info.get('location', 'Delhi')
            },
            "instructions": [
                "📍 Arrive 15 minutes early for registration",
                "📄 Bring your ID and insurance card", 
                "💊 Bring current medications list",
                "📱 Keep this appointment ID for reference"
            ],
            "meta": f"Appointment ID: {appointment_id} • ⏰ Duration: 30 mins",
            "full_details": f"""Excellent! I've scheduled your appointment:

    **Department:** {department}
    **Hospital:** {scheduling_info.get('hospital_preference', 'Apollo Hospital')}, {scheduling_info.get('location', 'Delhi')}
    **Doctor:** {doctor}
    **Date:** {tomorrow.strftime("%B %d, %Y")}
    **Time:** {time_slot}
    **Appointment ID:** {appointment_id}

    You'll receive a confirmation message shortly. Please arrive 15 minutes early with your ID and any relevant medical reports."""
        }

    def _generate_medicine_cards(self, medicines_data):
        """Generate medicine availability cards"""
        cards = []
        for medicine in medicines_data:
            card = {
                "type": "medicine",
                "medicine_name": medicine['name'],
                "status": medicine['status'],  # 'available' or 'unavailable'
                "price": medicine['price'],
                "image_url": self._get_medicine_image(medicine['name']),
                "description": medicine.get('description', ''),
                "generic_available": medicine.get('generic_available', False),
                "alternatives": medicine.get('alternatives', []),
                "selection_text": medicine['name']
            }
            cards.append(card)
        return cards

    def _get_medicine_image(self, medicine_name):
        """Map medicine names to appropriate images using exact filenames"""
        name_lower = medicine_name.lower()
        
        # First, check for exact brand name matches
        for medicine_key, image_path in self.MEDICINE_IMAGE_MAP.items():
            if medicine_key in name_lower and medicine_key != "default":
                return image_path
        
        # Then check for generic name mappings
        if any(word in name_lower for word in ['paracetamol', 'crocin', 'dolo', 'pain', 'fever', 'headache']):
            return self.MEDICINE_IMAGE_MAP['crocin']
        elif any(word in name_lower for word in ['antibiotic', 'amoxicillin', 'azithromycin', 'infection']):
            return self.MEDICINE_IMAGE_MAP['moxkind']
        elif any(word in name_lower for word in ['allergy', 'asthma', 'montelukast', 'cetirizine']):
            return self.MEDICINE_IMAGE_MAP['montair']
        elif any(word in name_lower for word in ['diabetes', 'metformin', 'glycomet', 'amaryl']):
            return self.MEDICINE_IMAGE_MAP['glycomet']
        elif any(word in name_lower for word in ['cholesterol', 'atorvastatin', 'storvas']):
            return self.MEDICINE_IMAGE_MAP['storvas']
        elif any(word in name_lower for word in ['blood pressure', 'bp', 'telma', 'amlodipine']):
            return self.MEDICINE_IMAGE_MAP['telma']
        elif any(word in name_lower for word in ['stomach', 'acid', 'digestion', 'pan', 'omeprazole']):
            return self.MEDICINE_IMAGE_MAP['pan']
        elif any(word in name_lower for word in ['vitamin', 'supplement', 'becosules']):
            return self.MEDICINE_IMAGE_MAP['becosules']
        elif any(word in name_lower for word in ['cold', 'cough', 'sinarest']):
            return self.MEDICINE_IMAGE_MAP['sinarest']
        
        # Default fallback
        return self.MEDICINE_IMAGE_MAP['default']
    def _extract_medicines_from_response(self, response):
        """Extract medicine data from pharmacy agent response"""
        medicines = []
        
        # Look for medicine patterns in the response
        medicine_patterns = [
            'Paracetamol', 'Dolo', 'Ibuprofen', 'Aspirin', 'Amoxicillin', 
            'Azithromycin', 'Ciprofloxacin', 'Metformin', 'Atorvastatin', 
            'Lisinopril', 'Amlodipine', 'Omeprazole', 'Pantoprazole', 
            'Domperidone', 'Cetirizine', 'Levocetirizine', 'Montelukast',
            'Vitamin C', 'Vitamin D3', 'Calcium', 'Multivitamin'
        ]
        
        for medicine in medicine_patterns:
            if medicine.lower() in response.lower():
                # Check availability from inventory
                available = self._check_medicine_availability(medicine)
                medicines.append({
                    'name': medicine,
                    'status': 'available' if available else 'unavailable',
                    'price': self._get_medicine_price(medicine),
                    'description': self._get_medicine_description(medicine)
                })
        
        return medicines

    def _check_medicine_availability(self, medicine_name):
        """Check if medicine is available in inventory"""
        for category, medicines in self.PHARMACY_INVENTORY_DATA['inventory'].items():
            for med_name, details in medicines.items():
                if medicine_name.lower() in med_name.lower():
                    return details['available']
        return False

    def _get_medicine_price(self, medicine_name):
        """Get medicine price from inventory"""
        for category, medicines in self.PHARMACY_INVENTORY_DATA['inventory'].items():
            for med_name, details in medicines.items():
                if medicine_name.lower() in med_name.lower():
                    return f"₹{details['price']}/{details['type']}"
        return "Price not available"

    def _get_medicine_description(self, medicine_name):
        """Get medicine description"""
        descriptions = {
            'Paracetamol': 'Pain reliever and fever reducer',
            'Dolo': 'Paracetamol 650mg tablet for pain and fever',
            'Ibuprofen': 'Non-steroidal anti-inflammatory drug',
            'Amoxicillin': 'Broad-spectrum antibiotic',
            'Azithromycin': 'Macrolide antibiotic',
            'Montelukast': 'Asthma and allergy medication',
            'Metformin': 'Diabetes medication',
            'Atorvastatin': 'Cholesterol-lowering medication',
            'Cetirizine': 'Antihistamine for allergies',
            'Vitamin C': 'Immune system support',
            'Vitamin D3': 'Bone health and immunity',
            'Calcium': 'Bone strength supplement',
            'Multivitamin': 'Complete daily nutrition'
        }
        return descriptions.get(medicine_name, 'General medication')

    def _generate_quick_reply_cards(self, options: list) -> list:
        """Generate quick reply action cards"""
        cards = []
        for option in options:
            cards.append({
                "type": "quick_reply",
                "title": option,
                "selection_text": option
            })
        return cards

    def _generate_lab_cards(self, location: str) -> list:
        """Generate lab selection cards based on location"""
        labs_data = {
            "delhi": [
                {
                    "type": "lab",
                    "title": "Dr. Lal PathLabs",
                    "description": "NABL accredited lab with home collection service",
                    "meta": "📍 Delhi • ⭐ 4.5 • 🏠 Home Visit Available",
                    "selection_text": "Dr. Lal PathLabs",
                    "lab_id": "lal_delhi",
                    "tests_available": ["Blood Tests", "Thyroid", "Diabetes", "Liver Function", "Kidney Function"]
                },
                {
                    "type": "lab",
                    "title": "Thyrocare Technologies",
                    "description": "Advanced testing with same-day reports for most tests",
                    "meta": "📍 Delhi • ⭐ 4.4 • ⚡ Same Day Reports",
                    "selection_text": "Thyrocare",
                    "lab_id": "thyrocare_delhi",
                    "tests_available": ["Full Body Checkup", "Hormone Tests", "Vitamin Tests", "Cardiac Tests"]
                },
                {
                    "type": "lab",
                    "title": "SRL Diagnostics",
                    "description": "Comprehensive diagnostic services with digital reports",
                    "meta": "📍 Delhi • ⭐ 4.6 • 📱 Digital Reports",
                    "selection_text": "SRL Diagnostics",
                    "lab_id": "srl_delhi",
                    "tests_available": ["Blood Tests", "Urine Tests", "Pathology", "Radiology"]
                }
            ],
            "mumbai": [
                {
                    "type": "lab",
                    "title": "Suburban Diagnostics",
                    "description": "Leading diagnostic chain with multiple collection centers",
                    "meta": "📍 Mumbai • ⭐ 4.5 • 🏠 Home Visit Available",
                    "selection_text": "Suburban Diagnostics",
                    "lab_id": "suburban_mumbai",
                    "tests_available": ["Blood Tests", "Thyroid", "Diabetes", "Full Body Checkup"]
                },
                {
                    "type": "lab",
                    "title": "Metropolis Healthcare",
                    "description": "Advanced laboratory testing with quality assurance",
                    "meta": "📍 Mumbai • ⭐ 4.6 • 🔬 Advanced Testing",
                    "selection_text": "Metropolis",
                    "lab_id": "metropolis_mumbai",
                    "tests_available": ["Blood Tests", "Genetic Tests", "Oncology Tests", "Infectious Diseases"]
                }
            ],
            "bangalore": [
                {
                    "type": "lab",
                    "title": "Aster Labs",
                    "description": "Comprehensive diagnostic services with quick turnaround",
                    "meta": "📍 Bangalore • ⭐ 4.4 • ⚡ Quick Results",
                    "selection_text": "Aster Labs",
                    "lab_id": "aster_bangalore",
                    "tests_available": ["Blood Tests", "Thyroid", "Diabetes", "Liver Function"]
                },
                {
                    "type": "lab",
                    "title": "Apollo Diagnostics",
                    "description": "Trusted diagnostic services from Apollo healthcare group",
                    "meta": "📍 Bangalore • ⭐ 4.5 • 🏥 Hospital Network",
                    "selection_text": "Apollo Diagnostics",
                    "lab_id": "apollo_diagnostics_bangalore",
                    "tests_available": ["Blood Tests", "Full Body Checkup", "Specialized Tests"]
                }
            ]
        }
        
        # Default labs if location not found
        default_labs = labs_data.get("delhi", [])
        return labs_data.get(location.lower(), default_labs)

    def _generate_visit_type_cards(self) -> list:
        """Generate visit type selection cards (home visit vs lab visit)"""
        return [
            {
                "type": "visit_type",
                "title": "🏠 Home Visit",
                "description": "Get tests done at your home by trained technicians",
                "meta": "Extra ₹200 charge • Same day slots available",
                "selection_text": "Home Visit",
                "visit_type": "home"
            },
            {
                "type": "visit_type",
                "title": "🏥 Lab Visit",
                "description": "Visit the lab for your tests at your convenience",
                "meta": "No extra charge • Flexible timing",
                "selection_text": "Lab Visit", 
                "visit_type": "lab"
            }
        ]
    
    def _generate_test_package_cards(self) -> list:
        """Generate test package selection cards - NEW"""
        return [
            {
                "type": "test_package",
                "title": "Basic Health Checkup",
                "subtitle": "₹999 | 40+ parameters",
                "details": [
                    "Ideal for: Routine annual health monitoring",
                    "Includes:",
                    "• Complete Blood Count (CBC)",
                    "• Blood Sugar (Fasting & PP)",
                    "• Liver Function Test (LFT)",
                    "• Kidney Function Test (KFT)",
                    "• Lipid Profile"
                ],
                "action": {
                    "type": "select_package",
                    "value": "Basic Health Checkup",
                    "price": 999
                }
            },
            {
                "type": "test_package",
                "title": "Full Body Checkup",
                "subtitle": "₹2,499 | 80+ parameters",
                "details": [
                    "Ideal for: Comprehensive health assessment",
                    "Includes:",
                    "• All Basic Health tests",
                    "• Thyroid Profile (T3, T4, TSH)",
                    "• Vitamin D & B12",
                    "• Iron Studies",
                    "• HbA1c (Diabetes marker)",
                    "• Urine Complete Analysis"
                ],
                "action": {
                    "type": "select_package",
                    "value": "Full Body Checkup",
                    "price": 2499
                },
                "recommended": True
            },
            {
                "type": "test_package",
                "title": "Executive Health Checkup",
                "subtitle": "₹4,999 | 120+ parameters",
                "details": [
                    "Ideal for: Complete preventive screening",
                    "Includes:",
                    "• All Full Body tests",
                    "• Cardiac Risk Markers",
                    "• Cancer Markers",
                    "• Complete Hormone Panel",
                    "• Advanced Metabolic Panel"
                ],
                "action": {
                    "type": "select_package",
                    "value": "Executive Health Checkup",
                    "price": 4999
                }
            },
            {
                "type": "test_package",
                "title": "Women's Wellness Package",
                "subtitle": "₹3,499 | 70+ parameters",
                "details": [
                    "Ideal for: Women-specific health monitoring",
                    "Includes:",
                    "• All Basic tests",
                    "• Hormone Panel (FSH, LH, Estrogen)",
                    "• Thyroid Profile Complete",
                    "• Vitamin D, B12, Iron",
                    "• Calcium & Bone Health markers"
                ],
                "action": {
                    "type": "select_package",
                    "value": "Women's Wellness Package",
                    "price": 3499
                }
            },
            {
                "type": "test_package",
                "title": "Senior Citizen Package",
                "subtitle": "₹3,999 | 90+ parameters",
                "details": [
                    "Ideal for: Comprehensive screening for seniors (60+)",
                    "Includes:",
                    "• All Full Body tests",
                    "• Bone Density markers",
                    "• Cardiac Risk Complete Assessment",
                    "• Diabetes Complete Screening",
                    "• Complete Vitamin Profile"
                ],
                "action": {
                    "type": "select_package",
                    "value": "Senior Citizen Package",
                    "price": 3999
                }
            }
        ]
    
    def _generate_lab_booking_confirmation(self, context: dict) -> dict:
        """Generate lab booking confirmation card - NEW"""
        lab_info = context['shared_memory'].get('lab_test_info', {})
        
        # Generate booking ID with LAB- prefix
        booking_id = f"LAB-{random.randint(10000, 99999)}"
        
        lab_name = lab_info.get('preferred_lab', 'Selected Lab')
        test_or_package = lab_info.get('package_selected') or lab_info.get('test_type', 'Diagnostic Test')
        visit_type = lab_info.get('visit_type', 'Lab Visit')
        location = lab_info.get('location', 'Your Location')
        time_slot = lab_info.get('preferred_time', 'Morning (7 AM - 12 PM)')
        
        # Generate next steps
        next_steps = [
            "Technician will call 30 mins before visit (for home visits)",
            "Keep your ID proof ready",
            "Fasting required for some tests (8-12 hours)",
            "Results will be available in 24-48 hours via email/SMS",
            "You can track your booking status anytime"
        ]
        
        return {
            "type": "lab_booking_confirmation",
            "title": "✅ Lab Test Booked Successfully",
            "booking_id": booking_id,
            "details": [
                f"Lab: {lab_name}",
                f"Test/Package: {test_or_package}",
                f"Visit Type: {visit_type.capitalize()} Visit",
                f"Time: {time_slot}",
                f"Location: {location}"
            ],
            "next_steps": next_steps
        }

    def _generate_test_booking_confirmation(self, context: dict) -> dict:
        """Generate test booking confirmation card"""
        test_info = context['shared_memory'].get('test_booking_info', {})
        
        # Generate booking ID
        booking_id = f"TEST-{random.randint(1000, 9999)}-{datetime.now().strftime('%m%d')}"
        
        lab_name = test_info.get('lab_preference', 'Selected Lab')
        test_type = test_info.get('test_type', 'Blood Test')
        visit_type = test_info.get('visit_type', 'Lab Visit')
        location = test_info.get('location', 'Your Location')
        
        # Generate appointment time
        tomorrow = datetime.now() + timedelta(days=1)
        time_slot = "9:00 AM - 12:00 PM" if visit_type == 'home' else "Any time during lab hours"
        
        instructions = []
        if visit_type == 'home':
            instructions = [
                "📍 Stay at your registered address during the time slot",
                "💧 Drink water to stay hydrated before blood test",
                "📱 Keep your ID proof ready",
                "⏰ 4-6 hours fasting required for most blood tests"
            ]
        else:
            instructions = [
                "📍 Visit the lab at your selected time",
                "💧 Fasting required for most blood tests (4-6 hours)",
                "📱 Carry your ID proof and this booking ID",
                "⏰ Lab timings: 7:00 AM - 8:00 PM"
            ]
        
        return {
            "type": "test_booking_confirmation",
            "title": "✅ Test Booking Confirmed!",
            "booking_id": booking_id,
            "details": {
                "Test Type": test_type,
                "Lab": lab_name,
                "Visit Type": visit_type,
                "Location": location,
                "Date": tomorrow.strftime("%B %d, %Y"),
                "Time Slot": time_slot,
                "Booking ID": booking_id
            },
            "instructions": instructions,
            "meta": f"Booking ID: {booking_id} • 📱 You'll receive confirmation SMS",
            "full_details": f"""Excellent! Your test has been booked:

    **Test Type:** {test_type}
    **Lab:** {lab_name}, {location}
    **Visit Type:** {visit_type}
    **Date:** {tomorrow.strftime("%B %d, %Y")}
    **Time:** {time_slot}
    **Booking ID:** {booking_id}

    {'A technician will visit your home at the scheduled time.' if visit_type == 'home' else 'You can visit the lab anytime during operating hours.'}
    You'll receive a confirmation message with detailed instructions."""
        }
    # Add these methods to your WellnessManager class

    def _detect_test_booking_intent(self, user_input: str, context: dict) -> bool:
        """Detect if user wants to book a test - based on their explicit words"""
        user_input_lower = user_input.lower()
        
        # Clear test-specific phrases
        test_specific_phrases = [
            # Basic test terms
            'blood test', 'lab test', 'cbc test', 'diagnostic test',
            'pathology test', 'medical test', 'get tested',
            'book a test', 'schedule a test', 'test booking',
            
            # Specific tests
            'complete blood count', 'cbc', 'blood work', 'lab work',
            'thyroid test', 'diabetes test', 'sugar test', 
            'cholesterol test', 'liver test', 'kidney test',
            'vitamin test', 'hormone test',
            
            # Packages and checkups
            'health checkup', 'full body checkup', 'medical checkup',
            'test package', 'health package', 'diagnostic package',
            'comprehensive test', 'preventive screening',
            
            # Lab terms
            'go to lab', 'visit lab', 'lab visit', 'home collection',
            'sample collection', 'get my tests done'
        ]
          # Doctor appointment phrases (these should NOT trigger test booking)
        doctor_phrases = [
            'see doctor', 'doctor appointment', 'consult doctor',
            'meet doctor', 'visit doctor', 'doctor visit',
            'see a doctor', 'consultation', 'doctor consult'
        ]
        
        # Only mark as test booking if:
        # 1. User uses test-specific terms AND
        # 2. Does NOT use doctor-specific terms
        is_test_booking = (
            any(phrase in user_input_lower for phrase in test_specific_phrases) and
            not any(phrase in user_input_lower for phrase in doctor_phrases)
        )
        
        # Also respect if we're already in a test booking flow
        current_test_booking = context['shared_memory'].get('test_booking_info', {}).get('is_test_booking', False)
        
        result = is_test_booking or current_test_booking
        
        print(f"🔍 User intent analysis:")
        print(f"   - User said: '{user_input}'")
        print(f"   - Test-specific terms: {is_test_booking}")
        print(f"   - Doctor terms found: {any(phrase in user_input_lower for phrase in doctor_phrases)}")
        print(f"   - Already in test flow: {current_test_booking}")
        print(f"   - Final decision: {'TEST BOOKING' if result else 'HOSPITAL APPOINTMENT'}")
        
        return result

    def _initialize_test_booking_context(self, context: dict):
        """Initialize test booking context and clear any hospital scheduling context"""
        shared = context['shared_memory']
        
        # Clear hospital scheduling info when starting test booking
        if 'scheduling_info' in shared:
            shared['scheduling_info'] = {}
        
        # Initialize test booking context
        if 'test_booking_info' not in shared:
            shared['test_booking_info'] = {
                'is_test_booking': True,
                'step': 'initial',  # initial -> location -> lab -> visit_type -> confirmation
                'location': None,
                'lab_preference': None,
                'visit_type': None,
                'test_type': 'Blood Test',  # default
                'confirmation_shown': False
            }
        else:
            shared['test_booking_info']['is_test_booking'] = True

    def _update_test_booking_context(self, user_input: str, agent_response: str, context: dict):
        """Update test booking context based on conversation"""
        user_input_lower = user_input.lower()
        test_booking_info = context['shared_memory'].get('test_booking_info', {})
        
        if not test_booking_info.get('is_test_booking'):
            return
        
        # Track location
        location_indicators = ['delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata', 'hyderabad', 'pune', 'ahmedabad']
        for location in location_indicators:
            if location in user_input_lower:
                test_booking_info['location'] = location.title()
                test_booking_info['step'] = 'lab_selection'
                print(f" Test booking location set: {location.title()}")
                break
        
        # Track lab selection from cards or user input
        lab_mappings = {
            'lal': 'Dr. Lal PathLabs',
            'thyrocare': 'Thyrocare Technologies', 
            'srl': 'SRL Diagnostics',
            'suburban': 'Suburban Diagnostics',
            'metropolis': 'Metropolis Healthcare',
            'aster': 'Aster Labs',
            'apollo': 'Apollo Diagnostics'
        }
        
        for lab_key, lab_name in lab_mappings.items():
            if lab_key in user_input_lower:
                test_booking_info['lab_preference'] = lab_name
                test_booking_info['step'] = 'visit_type_selection'
                print(f" Lab selected: {lab_name}")
                break
        
        # Track visit type
        if any(phrase in user_input_lower for phrase in ['home', 'home visit', 'at home']):
            test_booking_info['visit_type'] = 'Home Visit'
            test_booking_info['step'] = 'confirmation'
            print(" Visit type: Home Visit")
        elif any(phrase in user_input_lower for phrase in ['lab', 'center', 'clinic', 'visit lab']):
            test_booking_info['visit_type'] = 'Lab Visit' 
            test_booking_info['step'] = 'confirmation'
            print(" Visit type: Lab Visit")
        
        # Track specific test types
        test_mappings = {
            'blood': 'Blood Test',
            'thyroid': 'Thyroid Test', 
            'diabetes': 'Diabetes Test',
            'sugar': 'Blood Sugar Test',
            'cholesterol': 'Cholesterol Test',
            'liver': 'Liver Function Test',
            'kidney': 'Kidney Function Test',
            'full body': 'Full Body Checkup',
            'vitamin': 'Vitamin Test',
            'cbc': 'Complete Blood Count'
        }
        
        for test_key, test_name in test_mappings.items():
            if test_key in user_input_lower:
                test_booking_info['test_type'] = test_name
                print(f" Test type: {test_name}")
        
    # === CARD DETECTION LOGIC ===
    def _should_show_lab_cards(self, user_input: str, context: dict) -> bool:
        """Determine if lab selection cards should be shown (step-based)"""
        test_booking_info = context['shared_memory'].get('test_booking_info', {})
        
        # Show lab cards if:
        # 1. User is in test booking flow AND
        # 2. Location is known AND  
        # 3. Lab preference is not known AND
        # 4. User hasn't already selected a lab in this message
        
        is_test_booking = test_booking_info.get('is_test_booking', False)
        has_location = test_booking_info.get('location')
        no_lab_selected = not test_booking_info.get('lab_preference')
        no_lab_mentioned = not any(lab in user_input.lower() for lab in 
                                ['lal', 'thyrocare', 'srl', 'suburban', 'metropolis', 'aster', 'apollo'])
        
        should_show = (is_test_booking and 
                    has_location and 
                    no_lab_selected and
                    no_lab_mentioned)
        
        print(f"   LAB CARD CHECK:")
        print(f"   - Test Booking: {is_test_booking}")
        print(f"   - Location: {has_location} ({test_booking_info.get('location')})")
        print(f"   - No lab selected: {no_lab_selected}")
        print(f"   - No lab mentioned: {no_lab_mentioned}")
        print(f"   - Should show: {should_show}")
        
        return should_show

    def _should_show_visit_type_cards(self, user_input: str, context: dict) -> bool:
        """Determine if visit type cards should be shown (step-based)"""
        test_booking_info = context['shared_memory'].get('test_booking_info', {})
        
        if not test_booking_info.get('is_test_booking'):
            return False
        
        # Show visit type cards when:
        # 1. We have lab selected AND
        # 2. No visit type selected yet AND  
        # 3. The agent is asking about visit type in the response
        
        has_lab = test_booking_info.get('lab_preference')
        no_visit_type = not test_booking_info.get('visit_type')
        
        # Check if agent is asking about visit type in the current response
        current_response = context.get('current_agent_response', '')
        asks_about_visit = any(phrase in current_response.lower() for phrase in [
            'home visit', 'visit the lab', 'technician collects', 'prefer a home',
            'would you prefer', 'home or lab'
        ])
        
        should_show = (has_lab and no_visit_type and asks_about_visit)
        
        print(f"   VISIT TYPE CARD CHECK:")
        print(f"   - Has lab: {has_lab}")
        print(f"   - No visit type: {no_visit_type}")
        print(f"   - Asks about visit: {asks_about_visit}")
        print(f"   - Should show: {should_show}")
        
        return should_show
    
    def _should_show_test_package_cards(self, user_input: str, context: dict) -> bool:
        """Determine if test package cards should be shown - NEW"""
        lab_info = context['shared_memory'].get('lab_test_info', {})
        
        if not lab_info.get('is_lab_booking'):
            return False
        
        # Show package cards when:
        # 1. Lab is selected AND
        # 2. No package selected yet AND
        # 3. User asking about packages or checkups
        
        has_lab = lab_info.get('preferred_lab')
        no_package = not lab_info.get('package_selected')
        
        package_keywords = ['package', 'checkup', 'full body', 'screening', 'health check']
        asking_about_packages = any(kw in user_input.lower() for kw in package_keywords)
        
        should_show = (has_lab and no_package and asking_about_packages)
        
        print(f"   PACKAGE CARD CHECK:")
        print(f"   - Has lab: {has_lab}")
        print(f"   - No package: {no_package}")
        print(f"   - Asking about packages: {asking_about_packages}")
        print(f"   - Should show: {should_show}")
        
        return should_show
    
    def _should_show_lab_booking_confirmation(self, agent_response: str, context: dict) -> bool:
        """Determine if lab booking confirmation card should be shown - NEW"""
        lab_info = context['shared_memory'].get('lab_test_info', {})
        
        if not lab_info.get('is_lab_booking'):
            return False
        
        # Show confirmation when all details are collected and agent confirms
        response_lower = agent_response.lower()
        has_confirmation = any(phrase in response_lower for phrase in [
            'confirmed', 'booked', 'booking id', 'lab-'
        ])
        
        has_all_info = (
            lab_info.get('location') and
            lab_info.get('preferred_lab') and 
            lab_info.get('visit_type')
        )
        
        already_shown = lab_info.get('confirmation_shown', False)
        
        should_show = (has_confirmation and has_all_info and not already_shown)
        
        if should_show:
            lab_info['confirmation_shown'] = True
        
        print(f"   LAB BOOKING CONFIRMATION CHECK:")
        print(f"   - Has confirmation: {has_confirmation}")
        print(f"   - Has all info: {has_all_info}")
        print(f"   - Should show: {should_show}")
        
        return should_show

    def _should_show_test_booking_confirmation(self, agent_response: str, context: dict) -> bool:
        """Determine if test booking confirmation card should be shown"""
        test_booking_info = context['shared_memory'].get('test_booking_info', {})
        
        if not test_booking_info.get('is_test_booking'):
            return False
        
        # Show confirmation when all details are collected and agent confirms
        response_lower = agent_response.lower()
        has_confirmation = any(phrase in response_lower for phrase in [
            'confirmed', 'booked', 'scheduled', 'booking id'
        ])
        
        has_all_info = (
            test_booking_info.get('location') and
            test_booking_info.get('lab_preference') and 
            test_booking_info.get('visit_type')
        )
        
        already_shown = test_booking_info.get('confirmation_shown', False)
        
        should_show = (has_confirmation and has_all_info and not already_shown)
        
        if should_show:
            test_booking_info['confirmation_shown'] = True
            test_booking_info['step'] = 'complete'
        
        return should_show
    def _should_show_hospital_cards(self, user_input: str, agent_response: str, context: dict) -> bool:
        """Determine if hospital selection cards should be shown"""
        user_input_lower = user_input.lower()
        scheduling_info = context['shared_memory'].get('scheduling_info', {})
        test_booking_info = context['shared_memory'].get('test_booking_info', {})
        
        # Show hospital cards ONLY if:
        # 1. User is in scheduling flow AND
        # 2. Location is known AND  
        # 3. Hospital preference is not known AND
        # 4. User hasn't already selected a hospital AND
        # 5. This is NOT a test booking
        
        is_scheduling = context['active_agent'] == 'scheduling'
        has_location = scheduling_info.get('location')
        no_hospital_selected = not scheduling_info.get('hospital_preference')
        no_hospital_mentioned = not any(hospital in user_input_lower for hospital in 
                                        ['apollo', 'max', 'fortis', 'aiims', 'manipal', 'medanta'])
        is_test_booking = test_booking_info.get('is_test_booking', False)
        
        should_show = (is_scheduling and 
                    has_location and 
                    no_hospital_selected and
                    no_hospital_mentioned and
                    not is_test_booking)  # CRITICAL: Don't show hospital cards for test booking
        
        print(f"   HOSPITAL CARD CHECK:")
        print(f"   - Scheduling: {is_scheduling}")
        print(f"   - Location: {has_location} ({scheduling_info.get('location')})")
        print(f"   - No hospital selected: {no_hospital_selected}")
        print(f"   - No hospital mentioned: {no_hospital_mentioned}")
        print(f"   - Is test booking: {is_test_booking}")
        print(f"   - Should show: {should_show}")
        
        return should_show

    def _should_show_booking_confirmation(self, agent_response: str, context: dict) -> bool:
        """Determine if booking confirmation card should be shown"""
        response_lower = agent_response.lower()
        scheduling_info = context['shared_memory'].get('scheduling_info', {})
        
        # ENHANCED: Show booking confirmation when:
        # 1. Appointment is confirmed in response AND
        # 2. We have hospital and location info AND
        # 3. We haven't shown it yet in this session
        
        # Enhanced confirmation phrase detection
        confirmation_phrases = [
            'appointment confirmed', 'appointment id', 'scheduled', 'booked', 'confirmed',
            'apt-', 'appt-', 'booking id', 'reservation confirmed', 'successfully scheduled',
            'i\'ve scheduled', 'your appointment is', 'see you on', 'arrive at'
        ]
        
        has_confirmation = any(phrase in response_lower for phrase in confirmation_phrases)
        
        has_required_info = (
            scheduling_info.get('hospital_preference') and 
            scheduling_info.get('location')
        )
        
        already_shown = scheduling_info.get('confirmation_shown', False)
        
        should_show = (has_confirmation and has_required_info and not already_shown)
        
        # Enhanced debugging
        print(f"🎫 BOOKING CONFIRMATION CHECK:")
        print(f"   Response snippet: {response_lower[:200]}...")
        print(f"   - Has confirmation phrase: {has_confirmation}")
        print(f"   - Hospital: {scheduling_info.get('hospital_preference')}")
        print(f"   - Location: {scheduling_info.get('location')}")
        print(f"   - Has required info: {has_required_info}")
        print(f"   - Already shown: {already_shown}")
        print(f"   - SHOULD SHOW: {should_show}")
        
        if should_show:
            print("✅ Should show booking confirmation card")
            # Mark as shown to prevent duplicates
            scheduling_info['confirmation_shown'] = True
        
        return should_show

    def _should_stop_showing_cards(self, context: dict) -> bool:
        """Determine when to stop showing any cards"""
        scheduling_info = context['shared_memory'].get('scheduling_info', {})
        
        # Stop showing cards when:
        # 1. Appointment is confirmed OR
        # 2. Hospital is selected
        should_stop = ( 
            scheduling_info.get('appointment_confirmed') or
            scheduling_info.get('hospital_preference')
        )
        
        if should_stop:
            print(f" Stopping all cards - confirmed: {scheduling_info.get('appointment_confirmed')}, "
                  f"hospital_selected: {bool(scheduling_info.get('hospital_preference'))}")
        
        return should_stop
    def _should_show_medicine_cards(self, agent_response: str, context: dict) -> bool:
            """Determine if medicine cards should be shown"""
            response_lower = agent_response.lower()
            pharmacy_context = context['shared_memory'].get('pharmacy_info', {})
            
            # Show medicine cards ONLY when:
            # 1. Response lists available medicines OR
            # 2. Response shows search results
            # 3. AND user hasn't selected a medicine yet
            
            shows_availability = any(phrase in response_lower for phrase in [
                'we have', 'available', 'in stock', 'i can check', 
                'here are the', 'these medicines', 'following medicines'
            ])
            
            asks_for_selection = any(phrase in response_lower for phrase in [
                'which one', 'would you like to order', 'which medicine',
                'select', 'choose'
            ])
            
            medicine_already_selected = pharmacy_context.get('medicine_selected')
            
            should_show = (shows_availability or asks_for_selection) and not medicine_already_selected
            
            if should_show:
                print(f" Should show medicine cards - availability: {shows_availability}, "
                    f"asks_selection: {asks_for_selection}, selected: {medicine_already_selected}")
            else:
                print(f" NOT showing medicine cards - selected: {medicine_already_selected}")
            
            return should_show
    
    def _get_user_context(self, user_id: str) -> dict:
        """Get or create shared context for a user across all agents"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {
                'user_id': user_id,  # ADD THIS LINE
                'active_agent': 'orchestrator',
                'shared_memory': {
                    'medical_history': [],
                    'current_condition': None,
                    'recent_doctor_visit': None,
                    'insurance_queries': [],
                    'care_plan_goals': [],
                    'symptoms_discussed': [],
                    'treatments_mentioned': [],
                    'scheduling_info': {}
                },
                'in_symptom_assessment': False,
                'symptom_assessment_complete': False,
                'conversation_history': [],
                'symptom_data': {
                    'symptoms': [],
                    'onset': None,
                    'severity': None,
                    'character': None,
                },
                'questions_asked': []
            }
        return self.user_contexts[user_id]

    async def _generate_ai_suggestions(self, user_input: str, agent_response: str, context: dict, agent_type: str) -> list:
        """Generate AI-powered context-aware suggested replies"""
        
        try:
            # Build conversation context for the AI
            conversation_history = context.get('conversation_history', [])
            recent_conversation = "\n".join(conversation_history[-6:]) if conversation_history else "No previous conversation"
            
            shared_memory = context['shared_memory']
            symptoms = shared_memory.get('symptoms_discussed', [])
            scheduling_info = shared_memory.get('scheduling_info', {})
            pharmacy_info = shared_memory.get('pharmacy_info', {})
            
            # Build AI prompt for suggestion generation
            suggestion_prompt = f"""CONVERSATION CONTEXT:
            {recent_conversation}

            CURRENT AGENT: {agent_type}
            USER'S LAST MESSAGE: "{user_input}"
            ASSISTANT'S RESPONSE: "{agent_response}"

            ADDITIONAL CONTEXT:
            - Symptoms discussed: {symptoms}
            - Scheduling info: {scheduling_info}
            - Pharmacy info: {pharmacy_info}

            TASK: Generate 3-4 natural follow-up questions that a PATIENT/USER would likely ask next based on this medical conversation.
            Think from the user's perspective - what would they naturally want to know next?

            IMPORTANT: These should be questions the USER would ask, NOT questions the doctor/assistant would ask.

            EXAMPLES OF GOOD USER QUESTIONS:
            - "What medicine should I take?"
            - "When should I see a doctor?"
            - "How can I relieve the symptoms at home?"
            - "Is this covered by my insurance?"

            EXAMPLES OF BAD QUESTIONS (what assistant would ask):
            - "Do you have any other symptoms?"
            - "How high is your fever?"
            - "When did the symptoms start?"

            GUIDELINES:
            - Make them concise (6-12 words max)
            - Sound like natural patient questions
            - Be directly relevant to the current medical context
            - Cover different aspects (treatment, urgency, logistics, concerns)
            - Don't repeat what's already been asked

            FORMAT: Return ONLY the user questions as a bulleted list, nothing else."""

            # Use the orchestrator agent to generate intelligent suggestions
            orchestrator_agent = self.agents.get('orchestrator')
            if orchestrator_agent:
                ai_response = await self._call_agent(
                    orchestrator_agent, 
                    suggestion_prompt, 
                    context.get('user_id', 'temp') + '_suggestions', 
                    'suggestions'
                )
                
                # Parse the AI response to extract suggestions
                suggestions = self._parse_ai_suggestions(ai_response)
                
                if suggestions:
                    print(f"🤖 AI generated {len(suggestions)} suggestions: {suggestions}")
                    return suggestions
            
            # Fallback to smart rule-based suggestions if AI fails
            return self._get_fallback_suggestions(agent_type, context)
            
        except Exception as e:
            print(f"AI suggestion error: {e}")
            # Fallback to rule-based suggestions
            return self._get_fallback_suggestions(agent_type, context)

    def _parse_ai_suggestions(self, ai_response: str) -> list:
        """Parse AI response to extract suggested replies"""
        if not ai_response:
            return []
        
        # Extract bullet points or numbered lists
        suggestions = []
        lines = ai_response.split('\n')
        
        for line in lines:
            line = line.strip()
            # Remove bullet points, numbers, etc.
            clean_line = re.sub(r'^[•\-*\d+\.]\s*', '', line)
            clean_line = clean_line.strip()
            
            # Filter valid suggestions
            if (clean_line and 
                len(clean_line) > 5 and 
                len(clean_line) < 60 and  # Reasonable length
                not clean_line.lower().startswith('format:') and
                not clean_line.lower().startswith('guidelines:')):
                suggestions.append(clean_line)
        
        # Return top 3-4 unique suggestions
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
            if len(unique_suggestions) >= 4:
                break
        
        return unique_suggestions[:4]

    def _get_fallback_suggestions(self, agent_type: str, context: dict) -> list:
        """Smart fallback suggestions when AI fails"""
        
        shared_memory = context['shared_memory']
        symptoms = shared_memory.get('symptoms_discussed', [])
        scheduling_info = shared_memory.get('scheduling_info', {})
        pharmacy_info = shared_memory.get('pharmacy_info', {})
        
        # Base templates for each agent
        base_templates = {
            'orchestrator': [
                "I'm feeling sick - can you help?",
                "I need to schedule a doctor's appointment",
                "Can you check my insurance coverage?",
                "I need information about medicines"
            ],
            'symptom': [
                "What could be causing this?",
                "Should I be worried about these symptoms?",
                "What home remedies can I try?",
                "When should I see a doctor?"
            ],
            'scheduling': [
                "What are the available time slots?",
                "Which hospital should I choose?",
                "What should I bring to my appointment?",
                "How do I prepare for the visit?"
            ],
            'pharmacy': [
                "Do you have alternative medicines?",
                "What's the recommended dosage?",
                "Are there any side effects?",
                "When will my order arrive?"
            ],
            'policy_analysis': [
                "What's covered under my policy?",
                "How do I make an insurance claim?",
                "What's not covered by my insurance?",
                "Can I add family members to my policy?"
            ],
            'care_plan': [
                "How long will recovery take?",
                "What exercises should I do?",
                "What foods should I avoid?",
                "When should I follow up?"
            ]
        }
        
        suggestions = base_templates.get(agent_type, base_templates['orchestrator'])
        
        # Context-aware adjustments
        if agent_type == 'symptom' and symptoms:
            if any('fever' in str(s).lower() for s in symptoms):
                suggestions = [
                    "How can I reduce fever quickly?",
                    "When is fever considered dangerous?",
                    "What medicine is best for fever?",
                    "Should I go to emergency for this fever?"
                ]
            elif any('pain' in str(s).lower() for s in symptoms):
                suggestions = [
                    "What's the best pain relief?",
                    "Is this pain something serious?",
                    "When should I go to the ER?",
                    "How can I manage the pain at home?"
                ]
        
        elif agent_type == 'scheduling' and scheduling_info:
            if scheduling_info.get('hospital_preference'):
                suggestions = [
                    "What are the doctor's qualifications?",
                    "How long will the appointment take?",
                    "What tests might be needed?",
                    "Can I get directions to the hospital?"
                ]
            elif scheduling_info.get('location'):
                suggestions = [
                    "Which hospital do you recommend?",
                    "What are the available dates?",
                    "Do you have evening appointments?",
                    "How do I cancel if needed?"
                ]
        
        elif agent_type == 'pharmacy' and pharmacy_info:
            if pharmacy_info.get('medicine_selected'):
                suggestions = [
                    "What's the exact dosage?",
                    "Any food interactions?",
                    "How should I store this medicine?",
                    "Can I get faster delivery?"
                ]
        
        return suggestions[:4]
    
    def _format_agent_response(self, response: str, agent: str, suggested_replies: list = None) -> dict:
        """Format the agent response with metadata and suggested replies"""
        
        # Clean up the response text
        cleaned_response = response.strip()
        
        # Create the base response structure
        formatted_response = {
            "response": cleaned_response,
            "agent": agent,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add suggested replies if provided
        if suggested_replies:
            formatted_response["suggested_replies"] = suggested_replies
        
        # Add agent-specific metadata
        if agent == 'symptom':
            formatted_response["agent_type"] = "Symptom Assessment"
            formatted_response["icon"] = "🩺"
        elif agent == 'scheduling':
            formatted_response["agent_type"] = "Appointment Scheduling"
            formatted_response["icon"] = "📅"
        elif agent == 'pharmacy':
            formatted_response["agent_type"] = "Pharmacy Services"
            formatted_response["icon"] = "💊"
        elif agent == 'policy_analysis':
            formatted_response["agent_type"] = "Insurance Analysis"
            formatted_response["icon"] = "📄"
        elif agent == 'care_plan':
            formatted_response["agent_type"] = "Care Planning"
            formatted_response["icon"] = "❤️"
        else:
            formatted_response["agent_type"] = "Wellness Assistant"
            formatted_response["icon"] = "🤖"
        
        return formatted_response
    def setup_firebase(self):
        """Initialize Firebase services"""
        try:
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.users_collection = self.db.collection('users')
            self.conversations_collection = self.db.collection('conversations')
            
            print("Firebase services initialized")
        except Exception as e:
            print(f"Firebase setup warning: {e}")
    
    def _initialize_agents(self):
        """Initialize all agents"""
        from agents.orchestrator_agent import OrchestratorAgent
        from agents.symptom_triage_agent import SymptomTriageAgent
        from agents.care_plan_agent import CarePlanDesignAgent
        from agents.insurance_policy_agent import InsurancePolicyAnalysisAgent
        from agents.scheduling_agent import SchedulingAgent
        from agents.pharmacy_agent import PharmacyAgent  
        from agents.router_agent import RouterAgent
        from agents.lab_test_agent import LabTestAgent  # NEW: Import lab test agent
        
        agent_configs = {
            'router': ('Intent Router', RouterAgent),
            'orchestrator': ('Orchestrator', OrchestratorAgent),
            'symptom': ('Symptom Triage', SymptomTriageAgent),
            'care_plan': ('Care Plan', CarePlanDesignAgent),
            'policy_analysis': ('Insurance Policy', InsurancePolicyAnalysisAgent),
            'scheduling': ('Scheduling', SchedulingAgent),
            'pharmacy': ('Pharmacy', PharmacyAgent),
            'lab_test': ('Lab Test Specialist', LabTestAgent)  # NEW: Lab test agent
        }
        
        for key, (name, AgentClass) in agent_configs.items():
            try:
                self.agents[key] = AgentClass()
                print(f"  {name} Agent - Initialized")
            except Exception as e:
                print(f"  {name} Agent - Failed: {e}")
    
    async def detect_query_type(self, user_input: str, context: dict) -> str:
        """Detect query type using LLM-based router with keyword fallback"""
        
        # Build context for router
        recent_conv = "\n".join(context['conversation_history'][-4:]) if context['conversation_history'] else "No previous conversation"
        current_agent = context.get('active_agent', 'orchestrator')
        
        router_context = f"""
CONVERSATION CONTEXT:
{recent_conv}

CURRENT ACTIVE AGENT: {current_agent}
USER MESSAGE: "{user_input}"

Which agent should handle this message?
"""
        
        try:
            router_agent = self.agents.get('router')
            if not router_agent:
                print("Router agent not found, falling back to keywords")
                return await self._keyword_fallback(user_input)
            
            # Call router agent
            response = await self._call_agent(
                router_agent, 
                router_context, 
                context.get('user_id', 'temp'), 
                'router'
            )
            
            detected_intent = response.strip().upper()
            
            # Map router response to agent names
            intent_map = {
                'SYMPTOM': 'symptom',
                'SCHEDULING': 'scheduling',
                'PHARMACY': 'pharmacy',
                'INSURANCE': 'policy_analysis',
                'CARE_PLAN': 'care_plan',
                'LAB_TEST': 'lab_test',
                'GENERAL': 'general'
            }
            
            result = intent_map.get(detected_intent, 'general')
            print(f"Router detected: {detected_intent} → {result}")
            return result
            
        except Exception as e:
            print(f" Router error: {e}, falling back to keywords")
            return await self._keyword_fallback(user_input)
    
    async def _keyword_fallback(self, user_input: str) -> str:
        """Fallback to keyword-based routing when LLM fails"""
        user_input_lower = user_input.lower()
        
        # NEW: Check for lab test keywords first
        lab_test_keywords = [
            'test', 'blood test', 'lab', 'diagnostic', 'checkup',
            'health checkup', 'full body checkup', 'pathology',
            'blood work', 'scan', 'x-ray', 'ultrasound', 'mri',
            'ct scan', 'ecg', 'screening', 'thyroid test',
            'diabetes test', 'liver function', 'kidney function'
            # ADD PACKAGE KEYWORDS
            'package', 'packages', 'test package', 'health package', 
            'checkup package', 'diagnostic package', 'medical package',
            'checkup', 'health checkup', 'full body checkup', 
            'comprehensive checkup', 'preventive checkup', 'executive checkup',
            'basic checkup', 'wellness package', 'screening package',
            # ADD SPECIFIC PACKAGE NAMES
            'full body', 'executive health', 'basic health', 'women wellness',
            'senior citizen', 'thyroid package', 'diabetes package'
        ]
        
        # Check if it's a lab test request (not doctor appointment)
        if any(keyword in user_input_lower for keyword in lab_test_keywords):
            appointment_keywords = ['doctor', 'appointment', 'consult', 'see a doctor', 'physician']
            if not any(kw in user_input_lower for kw in appointment_keywords):
                print("🔬 Lab test detected via keyword fallback")
                return 'lab_test'
        
        # Check for common medicine names (strong pharmacy indicator)
        medicine_names = [
            'paracetamol', 'dolo', 'crocin', 'calpol', 'ibuprofen', 'aspirin',
            'amoxicillin', 'azithromycin', 'ciprofloxacin', 'augmentin',
            'cetirizine', 'levocetirizine', 'allegra', 'avil', 'montair',
            'montelukast', 'metformin', 'glucophage', 'glycomet',
            'atorvastatin', 'lipitor', 'rosuvastatin', 'crestor',
            'omeprazole', 'pantoprazole', 'rabeprazole', 'pan',
            'vitamin', 'supplement', 'calcium', 'iron', 'multivitamin',
            'combiflam', 'disprin', 'saridon', 'sinarest'
        ]
        
        # Check if user mentions medicine names directly
        medicine_mentioned = any(med in user_input_lower for med in medicine_names)
        
        # Also check for availability queries with medicine context
        availability_query = any(phrase in user_input_lower for phrase in [
            'is available', 'available?', 'in stock', 'do you have',
            'can i get', 'where can i buy', 'need to buy'
        ])
        
        insurance_score = sum(1 for kw in self.INSURANCE_KEYWORDS if kw in user_input_lower)
        symptom_score = sum(1 for kw in self.SYMPTOM_KEYWORDS if kw in user_input_lower)
        care_plan_score = sum(1 for kw in self.CARE_PLAN_KEYWORDS if kw in user_input_lower)
        scheduling_score = sum(1 for kw in self.SCHEDULING_KEYWORDS if kw in user_input_lower)
        pharmacy_score = sum(1 for kw in self.PHARMACY_KEYWORDS if kw in user_input_lower)
        
        # Boost pharmacy score if medicine mentioned or availability query
        if medicine_mentioned or availability_query:
            pharmacy_score += 2
            print(f"Medicine/availability detected - pharmacy_score boosted to {pharmacy_score}")
        
        print(f"🔍 Keyword fallback scores - symptom:{symptom_score}, scheduling:{scheduling_score}, "
            f"pharmacy:{pharmacy_score}, insurance:{insurance_score}, care:{care_plan_score}")
        
        # Medical workflow priority:
        if symptom_score >= 1 and pharmacy_score < 2:  # Only route to symptom if not clearly pharmacy
            return 'symptom'
        if pharmacy_score >= 1:  # Pharmacy takes priority when medicine mentioned
            return 'pharmacy'
        if scheduling_score >= 1:
            return 'scheduling'
        if insurance_score >= 1:
            return 'policy_analysis'
        if care_plan_score >= 1:
            return 'care_plan'
        
        return 'general'
    
    def _build_agent_context(self, user_input: str, context: dict, target_agent: str) -> str:
        """Build shared context for any agent"""
        shared = context['shared_memory']
        recent_conversation = "\n".join(context['conversation_history'][-6:]) if context['conversation_history'] else "No previous conversation"
        
        base_context = f"""
SHARED CONVERSATION CONTEXT:
{recent_conversation}

KNOWN INFORMATION:
- Current Condition: {shared['current_condition'] or 'Not specified'}
- Symptoms Discussed: {', '.join(shared['symptoms_discussed']) if shared['symptoms_discussed'] else 'None'}
- Scheduling Info: Location: {shared.get('scheduling_info', {}).get('location', 'Not specified')}, Hospital: {shared.get('scheduling_info', {}).get('hospital_preference', 'Not specified')}

CURRENT USER MESSAGE: "{user_input}"

IMPORTANT: 
- Do not ask for information that's already in the context above
- Acknowledge relevant previous conversation when appropriate
"""
        
        if target_agent == 'scheduling':
            test_booking_info = shared.get('test_booking_info', {})
            if test_booking_info.get('is_test_booking'):
                base_context += f"""
        USER'S CHOICE: TEST BOOKING
        The user explicitly wants to book a diagnostic test: {test_booking_info.get('test_type', 'Blood Test')}

        Follow the TEST BOOKING workflow:
        1. Help them choose a lab
        2. Ask about home visit vs lab visit preference  
        3. Confirm test booking details

        Current status:
        - Location: {test_booking_info.get('location', 'Not specified')}
        - Lab: {test_booking_info.get('lab_preference', 'Not selected')}
        - Visit Type: {test_booking_info.get('visit_type', 'Not selected')}

        Use test booking confirmation format with booking ID starting with TEST-
        """
            else:
                base_context += """
        USER'S CHOICE: HOSPITAL APPOINTMENT  
        The user wants to schedule a doctor's appointment.

        Follow the HOSPITAL APPOINTMENT workflow:
        1. Help them choose a hospital
        2. Schedule appointment time
        3. Confirm appointment details

        Use hospital appointment confirmation format with appointment ID starting with APPT-
        """
        
        return base_context.strip()
    
    def _update_shared_context(self, user_input: str, agent_response: str, context: dict, agent_type: str):
        """Update shared context with new information from conversation"""
        
        # Add to conversation history
        context['conversation_history'].extend([
            f"User: {user_input}",
            f"Agent: {agent_response}"
        ])
        
        if len(context['conversation_history']) > 20:
            context['conversation_history'] = context['conversation_history'][-20:]
        
        shared = context['shared_memory']
        user_input_lower = user_input.lower()
        agent_response_lower = agent_response.lower()
        
        if any(symptom in user_input_lower for symptom in ['fever', 'cold', 'cough', 'pain', 'headache', 'broken', 'fracture']):
            if 'broken' in user_input_lower and 'leg' in user_input_lower:
                shared['current_condition'] = "Broken leg"
                if 'broken leg' not in shared['symptoms_discussed']:
                    shared['symptoms_discussed'].append('broken leg')
        # Check if this is test booking intent
        is_test_booking = self._detect_test_booking_intent(user_input, context)
        
        if is_test_booking:
            # Initialize test booking context if needed
            self._initialize_test_booking_context(context)
            # Update test booking context
            self._update_test_booking_context(user_input, agent_response, context)
        else:
            # Track location
            location_indicators = ['delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata', 'hyderabad', 'pune', 'ahmedabad']
            for location in location_indicators:
                if location in user_input_lower:
                    if 'scheduling_info' not in shared:
                        shared['scheduling_info'] = {}
                    shared['scheduling_info']['location'] = location.title()
                    print(f" Location detected: {location.title()}")
                    break
            
            # Track hospital preferences
            hospital_indicators = {
                'apollo': 'Apollo Hospital',
                'max': 'Max Super Specialty Hospital', 
                'fortis': 'Fortis Escorts Heart Institute'
            }
        
            for hospital_key, hospital_name in hospital_indicators.items():
                if hospital_key in user_input_lower:
                    if 'scheduling_info' not in shared:
                        shared['scheduling_info'] = {}
                    shared['scheduling_info']['hospital_preference'] = hospital_name
                    print(f"Hospital selected: {hospital_name}")
                    break

        # Track time preferences
        time_indicators = {
            'morning': 'Morning',
            'afternoon': 'Afternoon', 
            'evening': 'Evening',
            'tomorrow': 'Tomorrow',
            'today': 'Today'
        }
        
        for time_key, time_name in time_indicators.items():
            if time_key in user_input_lower:
                if 'scheduling_info' not in shared:
                    shared['scheduling_info'] = {}
                shared['scheduling_info']['time_preference'] = time_name
                print(f" Time preference: {time_name}")
                break

        # Track appointment confirmation
        if 'appointment id' in agent_response_lower or 'appointment confirmed' in agent_response_lower:
            if 'scheduling_info' not in shared:
                shared['scheduling_info'] = {}
            shared['scheduling_info']['appointment_confirmed'] = True
            print(" Appointment confirmed in shared context")
            # Track medicine selection (for pharmacy agent)
        if agent_type == 'pharmacy':
            # Check if user selected a specific medicine
            medicine_names = ['paracetamol', 'ibuprofen', 'cetirizine', 'levocetirizine', 
                            'montelukast', 'azithromycin', 'amoxicillin', 'omeprazole']
            
            for medicine in medicine_names:
                if medicine in user_input_lower and ('order' in user_input_lower or 
                                                    'want' in user_input_lower or
                                                    'buy' in user_input_lower):
                    if 'pharmacy_info' not in shared:
                        shared['pharmacy_info'] = {}
                    shared['pharmacy_info']['medicine_selected'] = medicine.title()
                    print(f" Medicine selected: {medicine.title()}")
                    break
            
            # Check if asking for quantity (means medicine was selected)
            if any(phrase in agent_response_lower for phrase in 
                ['how many', 'quantity', 'strips', 'number of']):
                if 'pharmacy_info' not in shared:
                    shared['pharmacy_info'] = {}
                shared['pharmacy_info']['medicine_selected'] = True
                print("Medicine selection confirmed (asking for quantity)")

    async def _call_agent(self, agent, message: str, user_id: str, agent_type: str) -> str:
        """Call an agent"""
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        
        if agent_type not in self.user_sessions[user_id]:
            session_id = f"{user_id}-{agent_type}-{self.session_counter}"
            self.session_counter += 1
            self.user_sessions[user_id][agent_type] = session_id
            
            await self.session_service.create_session(
                app_name="wellness-gpt",
                user_id=user_id,
                session_id=session_id,
            )
        
        session_id = self.user_sessions[user_id][agent_type]
        
        runner = Runner(
            app_name="wellness-gpt",
            agent=agent,
            session_service=self.session_service
        )
        
        content = Content(parts=[Part(text=message)])
        
        try:
            response_generator = runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            )
            response_text = ""
            for event in response_generator:
                if hasattr(event, 'content') and event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                    break
            
            return response_text if response_text else "I'm processing..."
            
        except Exception as e:
            print(f" Agent error: {e}")
            return "I'm having trouble responding."
    
    async def process_message(self, user_input: str, user_id: str = None, 
                            firebase_token: str = None) -> dict:
        """Process message with shared context routing"""
        
        if not self.agents:
            return {
                "response": "I'm having some technical issues right now. Please try again.",
                "agent": "orchestrator"
            }
        
        try:
            final_user_id = user_id or "anonymous-user"
            context = self._get_user_context(final_user_id)
            
            # Detect if we need to route to specialist (NOW ASYNC)
            query_type = await self.detect_query_type(user_input, context)
            
            # SYMPTOM ROUTING
            if query_type == 'symptom' and context['active_agent'] != 'symptom' and not context.get('symptom_assessment_complete', False):
                context['active_agent'] = 'symptom'
                context['in_symptom_assessment'] = True
                print(" Switching to symptom agent")
                
                symptom_context = self._build_agent_context(user_input, context, 'symptom')
                symptom_prompt = f"""{symptom_context}

You are the symptom specialist. Start the assessment immediately. Acknowledge their symptoms warmly and ask your first diagnostic question.

Do NOT say you're connecting them to anyone - you ARE the specialist. Start NOW."""

                agent = self.agents.get('symptom')
                response = await self._call_agent(agent, symptom_prompt, final_user_id, 'symptom')
                
                self._update_shared_context(user_input, response, context, 'symptom')
                # Generate AI suggestions
                suggested_replies = await self._generate_ai_suggestions(user_input, response, context, 'symptom')
                return self._format_agent_response(response, "symptom", suggested_replies)
            
            # INSURANCE ROUTING
            elif query_type == 'insurance' and context['active_agent'] != 'policy_analysis':
                context['active_agent'] = 'policy_analysis'
                print(" Switching to insurance agent")
                
                insurance_context = self._build_agent_context(user_input, context, 'policy_analysis')
                
                insurance_prompt = f"""{insurance_context}

YOUR CURRENT INSURANCE POLICY DETAILS:
```json
{json.dumps(self.INSURANCE_POLICY_DATA, indent=2)}
Use this policy data to answer their question."""
                agent = self.agents.get('policy_analysis')
                response = await self._call_agent(agent, insurance_prompt, final_user_id, 'policy_analysis')
                self._update_shared_context(user_input, response, context, 'policy_analysis')

                suggested_replies = await self._generate_ai_suggestions(user_input, response, context, 'policy_analysis')
                return self._format_agent_response(response, "policy_analysis", suggested_replies)
                
            # CARE PLAN ROUTING
            elif query_type == 'care_plan' and context['active_agent'] != 'care_plan':
                context['active_agent'] = 'care_plan'
                print("Switching to care plan agent")
                
                care_context = self._build_agent_context(user_input, context, 'care_plan')
                
                agent = self.agents.get('care_plan')
                response = await self._call_agent(agent, care_context, final_user_id, 'care_plan')
                
                self._update_shared_context(user_input, response, context, 'care_plan')
                
                suggested_replies = await self._generate_ai_suggestions(user_input, response, context, 'care_plan')
                return self._format_agent_response(response, "care_plan", suggested_replies)
                
                # PHARMACY ROUTING
            elif query_type == 'pharmacy' and context['active_agent'] != 'pharmacy':
                context['active_agent'] = 'pharmacy'
                print(" Switching to pharmacy agent")
                
                pharmacy_context = self._build_agent_context(user_input, context, 'pharmacy')
                
                pharmacy_prompt = f"""{pharmacy_context}
YOUR PHARMACY INVENTORY DATA:
```json
{json.dumps(self.PHARMACY_INVENTORY_DATA, indent=2)}
USER IS ASKING ABOUT: "{user_input}"
CRITICAL INSTRUCTIONS:
1. Check medicine availability using the inventory data above
2. When a medicine is selected, automatically process the order and provide order confirmation
3. For pain/fever medicines like Paracetamol, use appropriate dosage: "1 tablet as needed for pain/fever"
4. Provide professional order confirmations with delivery details
5. Ask for prescription if needed, but don't require it for common medicines
EXAMPLE RESPONSES:
GOOD: "Great! I've processed your order for Paracetamol. Standard dosage: 1 tablet as needed for pain or fever. Your order will be delivered in 2-4 hours. Total: ₹20"
BAD: "I'll use the basic_antibiotic prescription template"
Process orders naturally using the pharmacy inventory data."""
                agent = self.agents.get('pharmacy')
                response = await self._call_agent(agent, pharmacy_prompt, final_user_id, 'pharmacy')
                
                self._update_shared_context(user_input, response, context, 'pharmacy')
                
                # Generate AI suggestions
                suggested_replies = await self._generate_ai_suggestions(user_input, response, context, 'pharmacy')
                response_data = self._format_agent_response(response, "pharmacy", suggested_replies)

                # ONLY show cards when appropriate
                if self._should_show_medicine_cards(response, context):
                    medicines_data = self._extract_medicines_from_response(response)
                    if medicines_data:
                        response_data["cards"] = self._generate_medicine_cards(medicines_data)
                        print(" Adding medicine availability cards")
                
                return response_data
            
            # LAB TEST ROUTING - NEW: Dedicated lab test agent
            elif query_type == 'lab_test' and context['active_agent'] != 'lab_test':
                context['active_agent'] = 'lab_test'
                print("🔬 Switching to lab test agent")
                
                # Initialize lab test context
                if 'lab_test_info' not in context['shared_memory']:
                    context['shared_memory']['lab_test_info'] = {
                        'is_lab_booking': True,
                        'location': None,
                        'preferred_lab': None,
                        'test_type': None,
                        'visit_type': None,
                        'preferred_time': None,
                        'package_selected': None
                    }
                
                lab_test_context = self._build_agent_context(user_input, context, 'lab_test')
                
                agent = self.agents.get('lab_test')
                if not agent:
                    print("⚠️ Lab test agent not registered, falling back to scheduling")
                    query_type = 'scheduling'
                else:
                    response = await self._call_agent(agent, lab_test_context, final_user_id, 'lab_test')
                    
                    # Update context
                    self._update_shared_context(user_input, response, context, 'lab_test')
                    
                    # Generate AI suggestions
                    suggested_replies = await self._generate_ai_suggestions(user_input, response, context, 'lab_test')
                    response_data = self._format_agent_response(response, "lab_test", suggested_replies)
                    
                    # Show appropriate lab cards
                    lab_info = context['shared_memory']['lab_test_info']
                    
                    if self._should_show_lab_cards(user_input, context):
                        location = lab_info.get('location', 'delhi')
                        response_data["cards"] = self._generate_lab_cards(location)
                        print("🏥 Adding lab selection cards")
                    
                    elif self._should_show_test_package_cards(user_input, context):
                        response_data["cards"] = self._generate_test_package_cards()
                        print("📦 Adding test package cards")
                    
                    elif self._should_show_visit_type_cards(user_input, context):
                        response_data["cards"] = self._generate_visit_type_cards()
                        print("🏠 Adding visit type cards")
                    
                    # Check for booking confirmation
                    if self._should_show_lab_booking_confirmation(response, context):
                        response_data["cards"] = [self._generate_lab_booking_confirmation(context)]
                        print("✅ Adding lab booking confirmation card")
                    
                    return response_data
            
            # SCHEDULING ROUTING
            elif query_type == 'scheduling' and context['active_agent'] != 'scheduling':
                context['active_agent'] = 'scheduling'
                print(" Switching to scheduling agent")
                
                # Let the user's words determine what they want - no assumptions
                is_test_booking = self._detect_test_booking_intent(user_input, context)
                if is_test_booking:
                    self._initialize_test_booking_context(context)
                    print("🔬 User explicitly asked for test booking")
                
                scheduling_context = self._build_agent_context(user_input, context, 'scheduling')
                
                agent = self.agents.get('scheduling')
                response = await self._call_agent(agent, scheduling_context, final_user_id, 'scheduling')
                
                # UPDATE CONTEXT FIRST (this detects location from user input)
                self._update_shared_context(user_input, response, context, 'scheduling')
                
                # Generate AI suggestions
                suggested_replies = await self._generate_ai_suggestions(user_input, response, context, 'scheduling')
                response_data = self._format_agent_response(response, "scheduling", suggested_replies)

                # SHOW CARDS BASED ON USER'S ACTUAL REQUEST
                test_booking_info = context['shared_memory'].get('test_booking_info', {})
                
                if test_booking_info.get('is_test_booking', False):
                    # User wants tests - show lab cards
                    print("🔬 User wants test booking - checking for lab cards")
                    if self._should_show_lab_cards(user_input, context):
                        location = test_booking_info.get('location', 'delhi')
                        response_data["cards"] = self._generate_lab_cards(location)
                        print("Adding lab selection cards")
                else:
                    # User wants hospital appointment - show hospital cards
                    if self._should_show_hospital_cards(user_input, agent_response=response, context=context):
                        response_data["cards"] = self._generate_hospital_cards()
                        print("Adding hospital selection cards")
                
                return response_data
        
            # CONTINUE WITH CURRENT AGENT
            else:
                target_agent = context['active_agent']
                
                # If orchestrator and symptom assessment just completed, offer next steps
                if target_agent == 'orchestrator' and context.get('symptom_assessment_complete', False):
                    next_steps_response = """I understand. Based on the symptom assessment, here's what you can do next:
            1.Schedule an appointment - Would you like me to help you book an appointment with the General Medicine department?

            2.Check insurance coverage - I can help you understand what your insurance covers for this visit

            3.Get a care plan - After your doctor visit, I can help you with recovery plans

            4.What would you like help with?"""
                    context['symptom_assessment_complete'] = False  # Reset flag
                    
                    return {
                        "response": next_steps_response,
                        "agent": "orchestrator"
                    }
                
                if query_type != 'general' and query_type != target_agent:
                    print(f" User wants {query_type}, switching from {target_agent}")
                    context['active_agent'] = query_type
                    target_agent = query_type    
                
                if target_agent == 'orchestrator':
                    target_agent = query_type if query_type != 'general' else 'orchestrator'
                
                agent = self.agents.get(target_agent, self.agents.get('orchestrator'))
                
                contextual_input = self._build_agent_context(user_input, context, target_agent)
                
                if target_agent == 'policy_analysis':
                    contextual_input = f"""{contextual_input}
            {json.dumps(self.INSURANCE_POLICY_DATA, indent=2)}
            Use this policy data to answer their question."""
                print(f" Processing with {target_agent}")
                
                response = await self._call_agent(agent, contextual_input, final_user_id, target_agent)

                # UPDATE CONTEXT FIRST (this includes location detection)
                self._update_shared_context(user_input, response, context, target_agent)

                # ✅ THEN check for cards (now location is available)
                # Generate AI suggestions
                suggested_replies = await self._generate_ai_suggestions(user_input, response, context, target_agent)
                
                # ✅ DEFINE response_data FIRST
                response_data = self._format_agent_response(response, target_agent, suggested_replies)

                # ✅ ADD CARDS BASED ON CONTEXT - ONLY WHEN NEEDED
                test_booking_info = context['shared_memory'].get('test_booking_info', {})

                # ✅ FIRST: Check for booking confirmation (ALWAYS check this, regardless of stop condition)
                if target_agent == 'scheduling':
                    if test_booking_info.get('is_test_booking', False):
                        # Test booking confirmation
                        if self._should_show_test_booking_confirmation(response, context):
                            response_data["cards"] = [self._generate_test_booking_confirmation(context)]
                            print("Adding test booking confirmation card")
                    else:
                        # Hospital appointment confirmation
                        if self._should_show_booking_confirmation(response, context):
                            response_data["cards"] = [self._generate_booking_confirmation_card(context)]
                            print("✅ Adding booking confirmation card")

                # ✅ THEN: Check for other selection cards (subject to stop check)
                if target_agent == 'scheduling' and not self._should_stop_showing_cards(context):
                    
                    # Store current response for card detection
                    context['current_agent_response'] = response
                    
                    # CHECK WHAT USER ACTUALLY WANTS - USER-DRIVEN LOGIC
                    if test_booking_info.get('is_test_booking', False):
                        print("🔬 User wants test booking - showing test-related cards")
                        
                        if self._should_show_lab_cards(user_input, context):
                            location = test_booking_info.get('location', 'delhi')
                            response_data["cards"] = self._generate_lab_cards(location)
                            print("Adding lab selection cards")
                        
                        elif self._should_show_visit_type_cards(user_input, context):
                            response_data["cards"] = self._generate_visit_type_cards()
                            print("Adding visit type cards")
                    
                    else:
                        # User wants hospital appointment
                        if self._should_show_hospital_cards(user_input, agent_response=response, context=context):
                            response_data["cards"] = self._generate_hospital_cards()
                            print("Adding hospital selection cards")

                # CHECK FOR MEDICINE CARDS (for pharmacy agent)
                if target_agent == 'pharmacy' and self._should_show_medicine_cards(response, context):
                    medicines_data = self._extract_medicines_from_response(response)
                    if medicines_data:
                        response_data["cards"] = self._generate_medicine_cards(medicines_data)
                        print(" Adding medicine availability cards")

                # Check if appointment is being confirmed
                if "appointment id" in response.lower() or "confirmed" in response.lower():
                    if 'scheduling_info' not in context['shared_memory']:
                        context['shared_memory']['scheduling_info'] = {}
                    context['shared_memory']['scheduling_info']['appointment_confirmed'] = True
                    print("Appointment confirmed - stopping cards")

                return response_data
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            
            # Even in error, provide helpful suggestions
            suggested_replies = ["Try again", "Start over", "Help with symptoms", "Medicine inquiry"]
            return self._format_agent_response(
                "I apologize, I'm having trouble right now. Could you try again?",
                "orchestrator",
                suggested_replies
            )

    async def initialize(self):
        print("Wellness Manager Ready!")

    async def close(self):
        pass