from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
from datetime import datetime
import json

# ============================================================================
# IMPORT YOUR DATABASE & MODELS
# ============================================================================

try:
    from database import SessionLocal, engine  # type: ignore
    from models import Farmer, CropReport, Treatment, Base # type: ignore
    from ai_service import analyze_crop_disease, get_treatment_recommendation
    from whatsapp_service import send_whatsapp_message
except ImportError as e:
    print(f"ERROR: Missing file - {e}")
    print("Make sure you have: database.py, models.py, ai_service.py, whatsapp_service.py")

# ============================================================================
# INITIALIZE DATABASE & APP
# ============================================================================

Base.metadata.create_all(bind=engine)
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="AgriVision Pro", description="AI-powered crop disease detection")

# CORS Configuration (Allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def translate_disease(disease_name, language="hi"):
    """Translate disease name to local language"""
    translations = {
        "rice_blast": {
            "hi": "चावल की ब्लास्ट",
            "mr": "तांदूळाचा ब्लास्ट",
            "ta": "அரிசி வெடிப்பு",
            "te": "బియ్య విస్ఫోటనం",
            "kn": "ಅಕ್ಕಿ ಸೋಂಕು"
        },
        "powdery_mildew": {
            "hi": "पाउडरी फफूंदी",
            "mr": "पावडरी मिल्ड्यु",
            "ta": "பொடி இலை நோய்",
            "te": "పౌడరీ మిల్డ్యూ",
            "kn": "ಪೌಡರಿ ಫೋಸಿಂಬೆ"
        }
    }
    
    if disease_name.lower() in translations:
        return translations[disease_name.lower()].get(language, disease_name)
    return disease_name

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to AgriVision Pro",
        "status": "online",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/analyze-crop",
            "farmer_history": "/api/farmer/{phone}",
            "farmers_list": "/api/farmers"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AgriVision Pro",
        "timestamp": datetime.now().isoformat(),
        "ollama": "Check if running on port 11434"
    }

@app.options("/api/analyze-crop")
async def options_analyze():
    """Handle CORS preflight"""
    return {"status": "ok"}

@app.post("/api/analyze-crop")
async def analyze_crop(
    phone: str = Form(...),
    name: str = Form(...),
    crop_name: str = Form(...),
    location: str = Form(...),
    language: str = Form(default="hi"),
    file: UploadFile = File(...)
):
    """
    MAIN ENDPOINT: Farmer uploads crop image, gets AI diagnosis
    
    Parameters:
    - phone: Farmer's phone number
    - name: Farmer's name
    - crop_name: Type of crop (Rice, Wheat, Tomato, etc)
    - location: Location/Village
    - language: Preferred language (hi, mr, ta, te, kn)
    - file: Crop image (JPG, PNG)
    
    Returns: Disease diagnosis, treatment, pesticide info
    """
    
    try:
        print(f"\n=== NEW ANALYSIS REQUEST ===")
        print(f"Farmer: {name} ({phone})")
        print(f"Crop: {crop_name} | Location: {location}")
        
        db = SessionLocal()
        
        # STEP 1: Save uploaded image
        print("STEP 1: Saving image...")
        filename = f"{phone}_{crop_name}_{datetime.now().timestamp()}.jpg"
        image_path = f"uploads/{filename}"
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"✓ Image saved: {image_path}")
        
        # STEP 2: Get or create farmer in database
        print("STEP 2: Checking farmer in database...")
        farmer = db.query(Farmer).filter(Farmer.phone == phone).first()
        
        if not farmer:
            farmer = Farmer(
                phone=phone,
                name=name,
                location=location,
                language=language
            )
            db.add(farmer)
            db.commit()
            db.refresh(farmer)
            print(f"✓ New farmer created: {name}")
        else:
            print(f"✓ Farmer found: {farmer.name}")
        
        # STEP 3: Analyze image using Ollama AI (FREE)
        print("STEP 3: Analyzing with Ollama AI...")
        disease_info = analyze_crop_disease(image_path, crop_name, location)
        print(f"✓ Analysis complete: {disease_info.get('disease_name', 'Unknown')}")
        
        # STEP 4: Get treatment recommendation
        print("STEP 4: Getting treatment recommendation...")
        treatment = get_treatment_recommendation(
            disease_info.get("disease_name", "Unknown"),
            location
        )
        print(f"✓ Treatment: {treatment.get('pesticide', 'N/A')}")
        
        # STEP 5: Save report to database
        print("STEP 5: Saving report to database...")
        report = CropReport(
            farmer_id=farmer.id,
            crop_name=crop_name,
            disease_name=disease_info.get("disease_name", "Unknown"),
            confidence_score=float(disease_info.get("confidence", 0)),
            treatment=json.dumps(disease_info),
            image_url=image_path
        )
        db.add(report)
        db.commit()
        print(f"✓ Report saved to database")
        
        # STEP 6: Send WhatsApp notification
        print("STEP 6: Sending WhatsApp message...")
        
        translated_disease = translate_disease(
            disease_info.get("disease_name", "Unknown"),
            language
        )
        
        whatsapp_msg = f"""🌾 *AgriVision Pro Analysis*

🌱 *फसल / Crop:* {crop_name}
📍 *स्थान / Location:* {location}

🔍 *बीमारी / Disease:* {translated_disease}
📊 *सटीकता / Confidence:* {disease_info.get('confidence', 0)}%

💊 *कीटनाशक / Pesticide:* {treatment.get('pesticide', 'N/A')}
📋 *मात्रा / Dosage:* {treatment.get('dosage', 'N/A')}

🌡️ *लक्षण / Symptoms:* 
{disease_info.get('symptoms', 'Monitor crop regularly')}

✓ AgriVision Pro से आपके लिए विशेष सलाह!
"""
        
        whatsapp_result = send_whatsapp_message(phone, whatsapp_msg)
        print(f"✓ WhatsApp sent: {whatsapp_result.get('status', 'pending')}")
        
        # STEP 7: Return complete response
        print("=== ANALYSIS COMPLETE ===\n")
        
        return {
            "status": "success",
            "message": "Analysis complete",
            "timestamp": datetime.now().isoformat(),
            
            # Analysis Results
            "disease": {
                "name": disease_info.get("disease_name", "Unknown"),
                "confidence": float(disease_info.get("confidence", 0)),
                "symptoms": disease_info.get("symptoms", "Monitor crop"),
                "severity": "Medium" if disease_info.get("confidence", 0) > 70 else "Low"
            },
            
            # Treatment
            "treatment": {
                "pesticide": treatment.get("pesticide", "N/A"),
                "dosage": treatment.get("dosage", "N/A"),
                "cost": treatment.get("cost", 0),
                "application_frequency": treatment.get("application_frequency", "Weekly"),
                "safety_precautions": treatment.get("safety_precautions", "Use protective gear")
            },
            
            # Farmer Info
            "farmer": {
                "id": farmer.id,
                "name": farmer.name,
                "phone": farmer.phone,
                "location": farmer.location
            },
            
            # Notifications
            "notifications": {
                "whatsapp_sent": whatsapp_result.get('status') == 'sent',
                "whatsapp_phone": phone,
                "message": "Check your WhatsApp for detailed advice!"
            },
            
            # Image
            "image": {
                "filename": filename,
                "path": image_path
            }
        }
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/farmer/{phone}")
async def get_farmer_history(phone: str):
    """Get complete history of a farmer"""
    try:
        db = SessionLocal()
        farmer = db.query(Farmer).filter(Farmer.phone == phone).first()
        
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        reports = db.query(CropReport).filter(
            CropReport.farmer_id == farmer.id
        ).order_by(CropReport.created_at.desc()).all()
        
        return {
            "status": "success",
            "farmer": {
                "id": farmer.id,
                "name": farmer.name,
                "phone": farmer.phone,
                "location": farmer.location,
                "language": farmer.language,
                "member_since": farmer.created_at.isoformat()
            },
            "total_reports": len(reports),
            "reports": [
                {
                    "id": r.id,
                    "crop": r.crop_name,
                    "disease": r.disease_name,
                    "confidence": r.confidence_score,
                    "date": r.created_at.isoformat(),
                    "treatment": json.loads(r.treatment) if r.treatment else {}
                }
                for r in reports
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/farmers")
async def get_all_farmers():
    """Get list of all farmers"""
    try:
        db = SessionLocal()
        farmers = db.query(Farmer).all()
        
        return {
            "status": "success",
            "total_farmers": len(farmers),
            "farmers": [
                {
                    "id": f.id,
                    "name": f.name,
                    "phone": f.phone,
                    "location": f.location,
                    "reports": len(f.crop_reports)
                }
                for f in farmers
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        db = SessionLocal()
        
        total_farmers = db.query(Farmer).count()
        total_analyses = db.query(CropReport).count()
        
        return {
            "status": "success",
            "statistics": {
                "total_farmers": total_farmers,
                "total_analyses": total_analyses,
                "average_analyses_per_farmer": round(total_analyses / max(total_farmers, 1), 2),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║         🌾 AgriVision Pro - Starting Server 🌾        ║
    ║                                                        ║
    ║  API running on: http://localhost:8000                 ║
    ║  Frontend: http://localhost:8000/frontend/index.html   ║
    ║  Health: http://localhost:8000/health                  ║
    ║  Docs: http://localhost:8000/docs                      ║
    ║                                                        ║
    ║  Make sure Ollama is running on port 11434!            ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )