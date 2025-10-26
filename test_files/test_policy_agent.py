import asyncio
import sys
import os

# CRITICAL: Load .env FIRST, before any other imports
from dotenv import load_dotenv
load_dotenv()

# Verify environment is loaded
print(" Checking environment variables...")
has_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
has_api_key = os.getenv("GOOGLE_API_KEY")

if not has_creds and not has_api_key:
    print(" ERROR: No Google Cloud credentials found!")
    print("Please create a .env file with either:")
    print("  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
    print("  OR")
    print("  GOOGLE_API_KEY=your_api_key")
    sys.exit(1)

if has_creds:
    print(f" Using service account: {has_creds}")
    if not os.path.exists(has_creds):
        print(f" ERROR: Service account file not found at: {has_creds}")
        sys.exit(1)
else:
    print(f"Using API key authentication")

# NOW it's safe to import WellnessManager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from wellness_manager import WellnessManager

# Sample insurance analysis data
SAMPLE_ANALYSIS = {
    "extracted_policy": {
        "policy_details": {
            "insurer": "Tata AIG General Insurance Company Limited",
            "policy_name": "Medicare Premier",
            "sum_insured": "₹5,00,000",
            "policy_term": "1 year",
            "renewal_type": "Lifetime renewable",
            "age_entry": {
                "min_age": "18 years",
                "max_age": "65 years",
                "lifelong_renewal": True
            }
        },
        "coverage": {
            "hospitalization": {
                "room_rent_rule": "Single Private AC Room - actual charges covered",
                "icu_charges": "Actual ICU charges covered",
                "pre_hospitalization_days": "60 days",
                "post_hospitalization_days": "90 days",
                "day_care_procedures": "All covered",
                "domiciliary_treatment": {
                    "covered": True,
                    "exclusions": []
                },
                "ambulance": {
                    "road": "₹3,000 per hospitalization",
                    "air": "unknown"
                }
            },
            "cashless": {
                "available": True,
                "network_hospital_check_url": "https://www.tataaig.com/health-insurance/cashless-hospital-network",
                "hospital_cashless_eligibility": "Yes"
            },
            "special_covers": {
                "maternity": {
                    "covered": True,
                    "waiting_period": "24 months",
                    "normal_delivery_limit": "₹50,000",
                    "c_section_limit": "₹75,000",
                    "newborn_cover": "Covered from birth until policy expiry",
                    "vaccination_cover": "₹5,000"
                },
                "bariatric_surgery": {
                    "covered": False,
                    "waiting_period": "unknown",
                    "limit": "unknown"
                },
                "ayush_treatment": {
                    "covered": True,
                    "limit": "Up to sum insured",
                    "exclusions": []
                }
            }
        },
        "waiting_periods": {
            "initial": "30 days (except accidents)",
            "pre_existing_diseases": "36 months",
            "specific_diseases_wait": {
                "period": "24 months",
                "diseases": ["Cataract", "Hernia", "Piles", "Knee replacement"]
            }
        }
    },
    "plain_summary": "Full policy summary would be here...",
    "confidence_score": 0.85
}

async def test_smart_insurance():
    """Test smart insurance Q&A with policy data"""
    print("\n" + "=" * 70)
    print(" Testing Smart Insurance Q&A")
    print("=" * 70 + "\n")
    
    try:
        wellness_manager = WellnessManager()
        await wellness_manager.initialize()
    except Exception as e:
        print(f" Failed to initialize WellnessManager: {e}")
        return
    
    # Check if agents loaded successfully
    if not wellness_manager.agents:
        print("No agents could be initialized. Please check your credentials.")
        return
    
    print(" Agents initialized successfully\n")
    
    # Test 1: Without policy data
    print("=" * 70)
    print("TEST 1: WITHOUT policy data (should ask for upload)")
    print("=" * 70)
    
    test_queries_no_data = [
        "Is surgery covered in my insurance?",
        "What is my sum insured?",
        "Do I have maternity coverage?"
    ]
    
    for i, query in enumerate(test_queries_no_data, 1):
        print(f"\n[Query {i}] User: {query}")
        try:
            response = await wellness_manager.process_message(query, "test-user")
            print(f"Agent: {response}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 2: Load policy
    print("\n" + "=" * 70)
    print("TEST 2: Loading policy analysis")
    print("=" * 70)
    
    success = wellness_manager.load_insurance_analysis(SAMPLE_ANALYSIS, "test-user")
    if not success:
        print(" Failed to load policy analysis")
        return
    
    print("Policy analysis loaded successfully")
    print(f"   Insurer: {SAMPLE_ANALYSIS['extracted_policy']['policy_details']['insurer']}")
    print(f"   Policy: {SAMPLE_ANALYSIS['extracted_policy']['policy_details']['policy_name']}")
    print(f"   Sum Insured: {SAMPLE_ANALYSIS['extracted_policy']['policy_details']['sum_insured']}")
    
    # Test 3: With policy data
    print("\n" + "=" * 70)
    print("TEST 3: WITH policy data (should answer directly)")
    print("=" * 70)
    
    test_queries_with_data = [
        "Is surgery covered in my insurance?",
        "What is the sum insured?",
        "Is maternity covered?",
        "What is the waiting period for pre-existing diseases?",
        "Do I have cashless hospitalization?",
        "What is covered for ambulance charges?"
    ]
    
    for i, query in enumerate(test_queries_with_data, 1):
        print(f"\n[Query {i}] User: {query}")
        try:
            response = await wellness_manager.process_message(query, "test-user")
            print(f"Agent: {response}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 70)
    print("Smart insurance Q&A test completed!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        asyncio.run(test_smart_insurance())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n Test failed with error: {e}")
        import traceback
        traceback.print_exc()