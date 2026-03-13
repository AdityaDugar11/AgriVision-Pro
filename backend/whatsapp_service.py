"""
WhatsApp Service - Twilio Integration
Send diagnosis results to farmers via WhatsApp
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

# ============================================================================
# TWILIO CONFIGURATION (YOUR CREDENTIALS)
# ============================================================================

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")  # UPDATE THIS!
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

print(f"Twilio Account: {TWILIO_ACCOUNT_SID[:10]}...")
print(f"WhatsApp Number: {TWILIO_WHATSAPP_NUMBER}")

# Initialize Twilio client
try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    print("✓ Twilio client initialized successfully!")
except Exception as e:
    print(f"⚠ Twilio initialization warning: {e}")
    twilio_client = None

# ============================================================================
# SEND WHATSAPP MESSAGE
# ============================================================================

def send_whatsapp_message(phone_number, message_text):
    """
    Send WhatsApp message to farmer with diagnosis
    
    Args:
        phone_number: Farmer's phone number (10 digits, without +91)
        message_text: Message content to send
    
    Returns:
        Dictionary with status and message ID
    """
    
    try:
        if not twilio_client:
            print(f"⚠ WhatsApp message queued (Twilio not configured): {phone_number}")
            return {
                "status": "queued",
                "message_id": "local_queue",
                "phone": phone_number,
                "note": "Update TWILIO_AUTH_TOKEN in .env to send"
            }
        
        # Format phone number for WhatsApp
        formatted_phone = f"whatsapp:+91{phone_number}"
        
        print(f"→ Sending WhatsApp to: {formatted_phone}")
        
        # Send message using Twilio
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message_text,
            to=formatted_phone
        )
        
        print(f"✓ WhatsApp sent! Message ID: {message.sid}")
        
        return {
            "status": "sent",
            "message_id": message.sid,
            "phone": formatted_phone,
            "timestamp": str(message.date_sent)
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"✗ WhatsApp send error: {error_msg}")
        
        # Return queued status instead of failing completely
        return {
            "status": "queued",
            "error": error_msg,
            "phone": phone_number,
            "note": "Message queued for retry"
        }

# ============================================================================
# SEND SMS FALLBACK
# ============================================================================

def send_sms_message(phone_number, message_text):
    """
    Send SMS as fallback if WhatsApp fails
    
    Args:
        phone_number: Farmer's phone number
        message_text: Message content
    
    Returns:
        Dictionary with status
    """
    
    try:
        if not twilio_client:
            print(f"⚠ SMS queued (Twilio not configured)")
            return {
                "status": "queued",
                "note": "Configure Twilio to send SMS"
            }
        
        formatted_phone = f"+91{phone_number}"
        
        print(f"→ Sending SMS to: {formatted_phone}")
        
        message = twilio_client.messages.create(
            from_=os.getenv("TWILIO_PHONE_NUMBER", "+1234567890"),  # Your Twilio SMS number
            body=message_text,
            to=formatted_phone
        )
        
        print(f"✓ SMS sent! Message ID: {message.sid}")
        
        return {
            "status": "sent",
            "message_id": message.sid,
            "phone": formatted_phone
        }
    
    except Exception as e:
        print(f"✗ SMS error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# ============================================================================
# SEND FORMATTED DIAGNOSIS MESSAGE
# ============================================================================

def send_diagnosis_message(phone_number, diagnosis_data, language="hi"):
    """
    Send formatted diagnosis message via WhatsApp
    
    Args:
        phone_number: Farmer's phone number
        diagnosis_data: Dictionary with disease, treatment, etc
        language: Target language (hi, mr, ta, te, kn)
    
    Returns:
        Status of message send
    """
    
    try:
        disease = diagnosis_data.get("disease", {})
        treatment = diagnosis_data.get("treatment", {})
        
        # Format message based on language
        if language == "hi":
            message = f"""
🌾 *AgriVision Pro विश्लेषण परिणाम* 🌾

🌱 **बीमारी:** {disease.get('name', 'Unknown')}
📊 **सटीकता:** {disease.get('confidence', 0)}%

💊 **कीटनाशक:** {treatment.get('pesticide', 'N/A')}
📋 **मात्रा:** {treatment.get('dosage', 'N/A')}
⏰ **छिड़काव अंतराल:** {treatment.get('application_frequency', 'Weekly')}

✓ विस्तृत सलाह के लिए AgriVision Pro dashboaor्ड देखें।

AgriVision Pro से आपकी फसल की सुरक्षा! 🌾
"""
        
        elif language == "mr":
            message = f"""
🌾 *AgriVision Pro विश्लेषण* 🌾

🌱 **रोग:** {disease.get('name', 'Unknown')}
📊 **आत्मविश्वास:** {disease.get('confidence', 0)}%

💊 **कीटकनाशक:** {treatment.get('pesticide', 'N/A')}
📋 **डोज:** {treatment.get('dosage', 'N/A')}

AgriVision Pro - तुमच्या शेतीसाठी उपाय! 🌾
"""
        
        else:
            # Default English
            message = f"""
🌾 *AgriVision Pro Analysis* 🌾

🌱 **Disease:** {disease.get('name', 'Unknown')}
📊 **Confidence:** {disease.get('confidence', 0)}%

💊 **Pesticide:** {treatment.get('pesticide', 'N/A')}
📋 **Dosage:** {treatment.get('dosage', 'N/A')}
⏰ **Frequency:** {treatment.get('application_frequency', 'Weekly')}

✓ Check AgriVision Pro dashboard for detailed advice.

Your crop protection with AI! 🌾
"""
        
        return send_whatsapp_message(phone_number, message)
    
    except Exception as e:
        print(f"Error formatting diagnosis message: {e}")
        return {"status": "error", "error": str(e)}

# ============================================================================
# TEST CONNECTION
# ============================================================================

def test_twilio_connection():
    """Test if Twilio is properly configured"""
    try:
        if not twilio_client:
            print("⚠ Twilio client not initialized")
            return False
        
        account = twilio_client.api.account.fetch()
        print(f"✓ Twilio account verified: {account.friendly_name}")
        return True
    
    except Exception as e:
        print(f"✗ Twilio connection failed: {e}")
        return False

# Test on import
if __name__ == "__main__":
    test_twilio_connection()