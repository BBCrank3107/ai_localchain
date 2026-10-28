from fastapi import FastAPI, UploadFile, File
import uvicorn
import shutil
import os
import sys

# Import các Engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline.stage_1_document.ocr_engine import DocumentEngine
from pipeline.stage_2_liveness.liveness_engine import LivenessEngine
from pipeline.stage_3_face_matching.face_engine import FaceMatchingEngine
from api.app import EkycIntegrationEngine

app = FastAPI(title="LocalChain eKYC Core API", version="1.0.0")

# Khởi tạo Engine gốc
ekyc_engine = EkycIntegrationEngine()

os.makedirs("temp", exist_ok=True)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "eKYC API is running"}

@app.post("/ekyc/verify")
async def verify_ekyc(
    id_card: UploadFile = File(..., description="Ảnh mặt trước CCCD"),
    selfie: UploadFile = File(..., description="Ảnh Selfie khuôn mặt")
):
    """
    Endpoint chính nhận 2 ảnh và trả về kết quả eKYC (PASS/REVIEW/FAIL)
    """
    try:
        # 1. Lưu ảnh tạm thời
        id_path = f"temp/{id_card.filename}"
        selfie_path = f"temp/{selfie.filename}"
        
        with open(id_path, "wb") as buffer:
            shutil.copyfileobj(id_card.file, buffer)
        with open(selfie_path, "wb") as buffer:
            shutil.copyfileobj(selfie.file, buffer)
            
        # 2. Xử lý qua Pipeline eKYC (YOLO -> VietOCR -> MiniFASNet -> DeepFace)
        result = ekyc_engine.process_verification(id_path, selfie_path)
        
        # 3. Trả về kết quả JSON
        return result
        
    except Exception as e:
        return {"decision": "ERROR", "reason": str(e)}

if __name__ == "__main__":
    print("[*] Khởi động FastAPI Server trên cổng 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
