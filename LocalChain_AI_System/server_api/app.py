# -*- coding: utf-8 -*-
"""
LOCALCHAIN AI - PRODUCTION MICROSERVICE API (FASTAPI)
Tích hợp:
  1. Model 1 (Vision YOLO11)
  2. Model 2 (Multi-Head SSOT V3.0 Diagnosis Network with Clause Segmentation & Multi-Fault)
  3. Model 3 (Enterprise AI Pricing Engine V3.1 - Dual XGBoost + SSOT RAM Cache + Rule Engine + Explain)
  4. Phụ trợ 1 (RAG Cẩm nang Kỹ thuật)
  5. Phụ trợ 2 (NLG Sinh câu tự nhiên)
"""

import os
import sys
import io
import json

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from PIL import Image

# Import các module từ hệ thống
from model_1_vision.inference_vision import vision_ai
from model_2_diagnosis.inference_multihead import MultiHeadDiagnosisEngine
from model_3_pricing.inference_pricing import get_pricing_engine
from subsystem_rag.retriever import rag_ai
from subsystem_nlg.nlg_engine import generate_natural_message

app = FastAPI(
    title="LocalChain AI Multi-Model Diagnostic Engine",
    version="3.1.0",
    description="Hệ sinh thái AI Microservices: Thị giác YOLO11 + Chẩn đoán Multi-Head SSOT V3.0 + Enterprise Pricing Engine V3.1 (Dual XGBoost + Rule Engine + Validator + Explain) + RAG + NLG"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Khởi tạo các singleton AI Engines
multihead_ai = MultiHeadDiagnosisEngine()
pricing_engine = get_pricing_engine()

# =====================================================================
# REQUEST & RESPONSE SCHEMAS
# =====================================================================
class TextDiagnosisRequest(BaseModel):
    device: str
    complaint: str
    brand: Optional[str] = "Unknown"
    region: Optional[str] = "Metro"
    action_type: Optional[str] = "replace"
    part_type: Optional[str] = "OEM"
    explain_pricing: Optional[bool] = False

class EstimatePricingRequest(BaseModel):
    fault_code: Optional[str] = None
    fault_codes: Optional[List[str]] = None
    brand: Optional[str] = "Generic"
    action_type: Optional[str] = "replace"
    part_type: Optional[str] = "OEM"
    component_condition: Optional[str] = "NEW"
    region: Optional[str] = "Metro"
    distance_km: Optional[float] = 0.0
    is_emergency: Optional[bool] = False
    is_weekend: Optional[bool] = False
    include_vat: Optional[bool] = False
    explain: Optional[bool] = True

class ServicePricingRequest(BaseModel):
    service_type: str = Field(..., description="Loại dịch vụ: CLEANING, BEAUTY_CARE, TUTORING, MOVING")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Các thông số chi tiết (package, hours, area, personCount, vehicleType, distanceKm, etc.)")

class TextDiagnosisResponse(BaseModel):
    device: str
    device_name_vn: str
    brand: str
    symptom_input: str
    fault_count: int
    primary_diagnosis: dict
    predicted_faults: List[dict]
    estimated_price_vnd: float
    discount_vnd: Optional[float] = 0.0
    surcharge_vnd: Optional[float] = 0.0
    warranty_months: Optional[int] = 3
    confidence_score: Optional[float] = 0.85
    pricing_details: Optional[Dict[str, Any]] = None
    root_cause_assessment: Optional[Dict[str, Any]] = None
    top_candidates: List[dict]
    natural_message: str
    repair_guide: Optional[str] = None
    repair_workflow: Optional[Dict[str, Any]] = None
    architecture_note: str

class FullDiagnosisResponse(BaseModel):
    device: str
    brand: Optional[str] = "Unknown"
    complaint: str
    fault_count: int
    primary_diagnosis: dict
    predicted_faults: List[dict]
    estimated_price_vnd: float
    discount_vnd: Optional[float] = 0.0
    surcharge_vnd: Optional[float] = 0.0
    warranty_months: Optional[int] = 3
    confidence_score: Optional[float] = 0.85
    pricing_details: Optional[Dict[str, Any]] = None
    root_cause_assessment: Optional[Dict[str, Any]] = None
    natural_message: str
    repair_guide: Optional[str] = None
    repair_workflow: Optional[Dict[str, Any]] = None
    note: str = "Powered by LocalChain AI Operating System V5.2"



# =====================================================================
# API ENDPOINTS
# =====================================================================
@app.on_event("startup")
def startup_event():
    print("=" * 70, flush=True)
    print("Khởi động Hệ Thống LocalChain AI Microservices V3.1...", flush=True)
    print("   • Model 1: YOLO11 Classifier", flush=True)
    print("   • Model 2: Multi-Head Transformer V3.0", flush=True)
    print("   • Model 3: Enterprise AI Pricing Engine V3.1 (Dual XGBoost + SSOT RAM Cache)", flush=True)
    print("   • Subsystem: RAG Knowledge Base + NLG Engine", flush=True)
    print("=" * 70, flush=True)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "LocalChain AI Multi-Model API",
        "version": "3.1.0",
        "models": {
            "model_1_vision": "YOLO11 Classifier",
            "model_2_diagnosis": "Multi-Head Deep Transformer V3.0 (6-Step Normalize + CanonicalDevice + 3-Factor OOD Guard)",
            "model_3_pricing": "Enterprise Dual XGBoost Regressor V3.1 (Decoupled SSOT + Rule Engine + Safety Clamp)",
            "subsystem_rag": "sqlite-vec Knowledge Base",
            "subsystem_nlg": "Dynamic Semantic Generator"
        },
        "supported_devices": list(multihead_ai.device_mapper.supported_devices),
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "localchain-ai-api",
        "version": "3.1.0",
        "models_loaded": True
    }

@app.get("/api/v1/taxonomy")
def get_taxonomy():
    """Lấy danh mục bệnh lý kỹ thuật chuẩn hóa SSOT của 11 thiết bị"""
    return multihead_ai.taxonomy

@app.post("/api/v1/estimate-pricing")
def estimate_pricing_endpoint(req: EstimatePricingRequest):
    """
    Endpoint định giá độc lập (Dành cho Mobile App / Web Portal gọi trực tiếp Model 3)
    Hỗ trợ cả lỗi đơn và combo đa lỗi với đầy đủ chiết khấu, phụ phí, bảo hành và giải trình.
    """
    try:
        # Nếu truyền danh sách nhiều lỗi
        if req.fault_codes and len(req.fault_codes) > 1:
            res = pricing_engine.estimate_multiple_faults(
                fault_codes=req.fault_codes,
                brand=req.brand or "Generic",
                action_type=req.action_type or "replace",
                region=req.region or "Metro",
                distance_km=req.distance_km or 0.0,
                is_emergency=req.is_emergency or False,
                is_weekend=req.is_weekend or False,
                include_vat=req.include_vat or False,
                explain=req.explain or False
            )
            return res

        # Nếu truyền 1 lỗi đơn
        f_code = req.fault_code or (req.fault_codes[0] if req.fault_codes else "LAPTOP_DISPLAY_SYSTEM_FAILURE")
        res = pricing_engine.estimate_price_by_fault_code(
            fault_code=f_code,
            brand=req.brand or "Generic",
            action_type=req.action_type or "replace",
            part_type=req.part_type or "OEM",
            component_condition=req.component_condition or "NEW",
            region=req.region or "Metro",
            explain=req.explain or False,
            distance_km=req.distance_km or 0.0,
            is_emergency=req.is_emergency or False,
            is_weekend=req.is_weekend or False,
            include_vat=req.include_vat or False
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tính toán định giá: {str(e)}")

@app.post("/api/v1/estimate-service-pricing")
def estimate_service_pricing_endpoint(req: ServicePricingRequest):
    """
    Endpoint định giá cho 4 dịch vụ đời sống (Vệ sinh, Làm đẹp, Gia sư, Vận chuyển)
    Tra cứu trực tiếp từ bảng giá SSOT thị trường Việt Nam 2024-2026.
    """
    try:
        res = pricing_engine.estimate_service_price(
            service_type=req.service_type,
            params=req.params or {}
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tính toán định giá dịch vụ: {str(e)}")

@app.post("/api/v1/diagnose-text", response_model=TextDiagnosisResponse)
def diagnose_text_only(req: TextDiagnosisRequest):
    """
    Endpoint chẩn đoán trực tiếp qua Văn bản (Model 2 Multi-Head -> Model 3 Enterprise Pricing)
    """
    try:
        dev_info = multihead_ai.device_mapper.canonicalize(req.device)
        if not dev_info["is_supported"]:
            raise HTTPException(status_code=400, detail=f"Thiết bị '{req.device}' không nằm trong danh sách 30 thiết bị hỗ trợ!")
        dev_key = dev_info["canonical_id"]
        brand_clean = req.brand.strip() if req.brand and req.brand.strip().lower() != "string" else "Unknown"
        
        # 1. Chẩn đoán Multi-Head SSOT
        diag_res = multihead_ai.diagnose(dev_key, req.complaint, brand=brand_clean)
        if not diag_res.get("success", False):
            raise HTTPException(status_code=400, detail=diag_res.get("error", "Lỗi chẩn đoán thiết bị!"))
            
        # Trường hợp thiết bị hoạt động tốt / không có lỗi
        if not diag_res.get("is_fault", True):
            return TextDiagnosisResponse(
                device=dev_key,
                device_name_vn=diag_res["device_name_vn"],
                brand=brand_clean,
                symptom_input=req.complaint,
                fault_count=0,
                primary_diagnosis=diag_res["primary_diagnosis"],
                predicted_faults=[],
                estimated_price_vnd=0.0,
                discount_vnd=0.0,
                surcharge_vnd=0.0,
                warranty_months=0,
                confidence_score=1.0,
                pricing_details=None,
                top_candidates=[],
                natural_message=diag_res["natural_message"],
                repair_guide=None,
                architecture_note=diag_res["architecture_note"]
            )
            
        primary = diag_res["primary_diagnosis"]
        predicted_faults = diag_res.get("predicted_faults", [primary])
        fault_name_vn = primary["fault_name_vn"]
        severity = primary["severity"]
        
        # 2. Định giá qua Enterprise AI Pricing Engine V3.1
        itemized_prices = []
        if len(predicted_faults) > 1:
            fault_codes = [f.get("fault_code", "") for f in predicted_faults]
            pricing_res = pricing_engine.estimate_multiple_faults(
                fault_codes=fault_codes,
                brand=brand_clean,
                action_type=req.action_type or "replace",
                region=req.region or "Metro",
                explain=req.explain_pricing or False
            )
            total_price = pricing_res["total_price_vnd"]
            discount_vnd = pricing_res.get("combo_discount_vnd", 0.0)
            surcharge_vnd = pricing_res.get("total_surcharge_vnd", 0.0)
            warranty_mo = pricing_res.get("warranty_months", 3)
            confidence_score = pricing_res.get("confidence", 0.85)
            for it in pricing_res.get("items", []):
                itemized_prices.append({
                    "fault": it["component"]["component_name_vn"],
                    "price_vnd": it["total_price_vnd"],
                    "labor_fee": it["labor"]["predicted_price_vnd"],
                    "component_price": it["component"]["predicted_price_vnd"],
                    "action": "Thay thế/Xử lý"
                })
        else:
            f_code = primary.get("fault_code", "LAPTOP_DISPLAY_SYSTEM_FAILURE")
            pricing_res = pricing_engine.estimate_price_by_fault_code(
                fault_code=f_code,
                brand=brand_clean,
                action_type=req.action_type or "replace",
                part_type=req.part_type or "OEM",
                region=req.region or "Metro",
                explain=req.explain_pricing or False
            )
            total_price = pricing_res["total_price_vnd"]
            discount_vnd = pricing_res.get("discount_vnd", 0.0)
            surcharge_vnd = pricing_res.get("surcharge_vnd", 0.0)
            warranty_mo = pricing_res.get("warranty_months", 3)
            confidence_score = pricing_res.get("confidence", 0.85)
            itemized_prices.append({
                "fault": pricing_res["component"]["component_name_vn"],
                "price_vnd": total_price,
                "labor_fee": pricing_res["labor"]["predicted_price_vnd"],
                "component_price": pricing_res["component"]["predicted_price_vnd"],
                "action": "Thay thế/Xử lý"
            })

        # 3. Hoạch định quy trình kỹ thuật State Machine DAG qua Engine V5.2
        rag_query_text = f"{brand_clean} {req.complaint}" if brand_clean != "Unknown" else req.complaint
        primary_comp = primary.get("component_key") or (primary.get("components")[0] if primary.get("components") else "GENERIC_COMPONENT")
        workflow_res = rag_ai.plan_workflow(
            device=dev_key,
            fault_code=primary.get("fault_code", ""),
            primary_component=primary_comp,
            components=primary.get("components", [primary_comp]),
            complaint=rag_query_text
        )
        repair_guide = workflow_res.get("repair_guide")
        repair_wf_json = workflow_res.get("repair_workflow")
        has_guide = bool(repair_guide and len(repair_guide) > 30)
        
        # 4. Sinh câu phản hồi tự nhiên NLG
        natural_msg = generate_natural_message(
            device_key=dev_key,
            complaint=req.complaint,
            predicted_fault=fault_name_vn,
            severity=severity,
            estimated_price=total_price,
            brand=brand_clean,
            predicted_faults=predicted_faults,
            itemized_prices=itemized_prices,
            discount_vnd=discount_vnd,
            has_guide=has_guide,
            difficulty_score=primary.get("difficulty_score", 2.0),
            difficulty_obj=primary.get("difficulty"),
            root_cause_assessment=diag_res.get("root_cause_assessment"),
            detected_contexts=diag_res.get("detected_contexts")
        )
        
        return TextDiagnosisResponse(
            device=dev_key,
            device_name_vn=diag_res["device_name_vn"],
            brand=brand_clean,
            symptom_input=req.complaint,
            fault_count=len(predicted_faults),
            primary_diagnosis=primary,
            predicted_faults=predicted_faults,
            estimated_price_vnd=total_price,
            discount_vnd=discount_vnd,
            surcharge_vnd=surcharge_vnd,
            warranty_months=warranty_mo,
            confidence_score=confidence_score,
            pricing_details=pricing_res,
            root_cause_assessment=diag_res.get("root_cause_assessment"),
            top_candidates=diag_res["top_candidates"],
            natural_message=natural_msg,
            repair_guide=repair_guide if has_guide else None,
            repair_workflow=repair_wf_json,
            architecture_note=diag_res["architecture_note"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý chẩn đoán văn bản: {str(e)}")

@app.post("/api/v1/diagnose", response_model=FullDiagnosisResponse)
async def diagnose_multimodal(
    image: UploadFile = File(..., description="Ảnh chụp sự cố thiết bị"),
    complaint: str = Form(..., description="Lời phàn nàn của khách hàng"),
    brand: Optional[str] = Form(None, description="Hãng sản xuất thiết bị (nếu có)"),
    region: Optional[str] = Form("Metro", description="Khu vực (Metro/Urban/Province)")
):
    """
    Endpoint chẩn đoán toàn diện đa phương thức (Ảnh chụp YOLO11 + Mô tả sự cố Multi-Head AI + Enterprise Pricing V3.1)
    """
    try:
        # 1. MODEL 1: Thị giác máy tính nhận diện thiết bị
        image_bytes = await image.read()
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        detected_device, vision_conf = vision_ai.predict(pil_img)
        
        # 2. MODEL 2: Chẩn đoán Multi-Head SSOT
        brand_clean = str(brand).strip() if (brand is not None and isinstance(brand, str) and str(brand).strip().lower() != "string") else "Unknown"
        diag_res = multihead_ai.diagnose(detected_device, complaint, brand=brand_clean)
        
        # Trường hợp thiết bị hoạt động tốt
        if not diag_res.get("is_fault", True):
            return FullDiagnosisResponse(
                device=detected_device,
                brand=brand_clean,
                complaint=complaint,
                fault_count=0,
                primary_diagnosis=diag_res["primary_diagnosis"],
                predicted_faults=[],
                estimated_price_vnd=0.0,
                discount_vnd=0.0,
                surcharge_vnd=0.0,
                warranty_months=0,
                confidence_score=1.0,
                pricing_details=None,
                root_cause_assessment=None,
                natural_message=diag_res["natural_message"],
                repair_guide=None,
                note=diag_res["architecture_note"]
            )
        
        primary = diag_res["primary_diagnosis"]
        predicted_faults = diag_res.get("predicted_faults", [primary])
        fault_name_vn = primary["fault_name_vn"]
        severity = primary["severity"]
        
        # 3. MODEL 3: Định giá thông minh qua Enterprise AI Pricing Engine V3.1
        itemized_prices = []
        if len(predicted_faults) > 1:
            fault_codes = [f.get("fault_code", "") for f in predicted_faults]
            pricing_res = pricing_engine.estimate_multiple_faults(
                fault_codes=fault_codes,
                brand=brand_clean,
                region=region,
                explain=True
            )
            total_price = pricing_res["total_price_vnd"]
            discount_vnd = pricing_res.get("combo_discount_vnd", 0.0)
            surcharge_vnd = pricing_res.get("total_surcharge_vnd", 0.0)
            warranty_mo = pricing_res.get("warranty_months", 3)
            confidence_score = pricing_res.get("confidence", 0.85)
            for it in pricing_res.get("items", []):
                itemized_prices.append({
                    "fault": it["component"]["component_name_vn"],
                    "price_vnd": it["total_price_vnd"],
                    "labor_fee": it["labor"]["predicted_price_vnd"],
                    "component_price": it["component"]["predicted_price_vnd"],
                    "action": "Thay thế/Xử lý"
                })
        else:
            f_code = primary.get("fault_code", "LAPTOP_DISPLAY_SYSTEM_FAILURE")
            pricing_res = pricing_engine.estimate_price_by_fault_code(
                fault_code=f_code,
                brand=brand_clean,
                region=region,
                explain=True
            )
            total_price = pricing_res["total_price_vnd"]
            discount_vnd = pricing_res.get("discount_vnd", 0.0)
            surcharge_vnd = pricing_res.get("surcharge_vnd", 0.0)
            warranty_mo = pricing_res.get("warranty_months", 3)
            confidence_score = pricing_res.get("confidence", 0.85)
            itemized_prices.append({
                "fault": pricing_res["component"]["component_name_vn"],
                "price_vnd": total_price,
                "labor_fee": pricing_res["labor"]["predicted_price_vnd"],
                "component_price": pricing_res["component"]["predicted_price_vnd"],
                "action": "Thay thế/Xử lý"
            })

        # 4. Hoạch định quy trình kỹ thuật State Machine DAG qua Engine V5.2
        rag_query_text = f"{brand_clean} {complaint}" if brand_clean != "Unknown" else complaint
        primary_comp = primary.get("component_key") or (primary.get("components")[0] if primary.get("components") else "GENERIC_COMPONENT")
        workflow_res = rag_ai.plan_workflow(
            device=detected_device,
            fault_code=primary.get("fault_code", ""),
            primary_component=primary_comp,
            components=primary.get("components", [primary_comp]),
            complaint=rag_query_text
        )
        repair_guide = workflow_res.get("repair_guide")
        repair_wf_json = workflow_res.get("repair_workflow")
        has_guide = bool(repair_guide and len(repair_guide) > 30)
        
        # 5. Sinh phản hồi tự nhiên NLG
        natural_msg = generate_natural_message(
            device_key=detected_device,
            complaint=complaint,
            predicted_fault=fault_name_vn,
            severity=severity,
            estimated_price=total_price,
            brand=brand_clean,
            predicted_faults=predicted_faults,
            itemized_prices=itemized_prices,
            discount_vnd=discount_vnd,
            has_guide=has_guide,
            difficulty_score=primary.get("difficulty_score", 2.0),
            difficulty_obj=primary.get("difficulty"),
            root_cause_assessment=diag_res.get("root_cause_assessment"),
            detected_contexts=diag_res.get("detected_contexts")
        )
        
        return FullDiagnosisResponse(
            device=detected_device,
            brand=brand_clean,
            complaint=complaint,
            fault_count=len(predicted_faults),
            primary_diagnosis=primary,
            predicted_faults=predicted_faults,
            estimated_price_vnd=total_price,
            discount_vnd=discount_vnd,
            surcharge_vnd=surcharge_vnd,
            warranty_months=warranty_mo,
            confidence_score=confidence_score,
            pricing_details=pricing_res,
            root_cause_assessment=diag_res.get("root_cause_assessment"),
            natural_message=natural_msg,
            repair_guide=repair_guide if has_guide else None,
            repair_workflow=repair_wf_json
        )

        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý chẩn đoán đa phương thức: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server_api.app:app", host="127.0.0.1", port=8000, reload=True)
