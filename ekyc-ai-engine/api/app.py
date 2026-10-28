import sys
import os
from datetime import datetime

# Import các Engine Tích hợp (Wrapper)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline.stage_1_document.ocr_engine import DocumentEngine
from pipeline.stage_2_liveness.liveness_engine import LivenessEngine
from pipeline.stage_3_face_matching.face_engine import FaceMatchingEngine

class EkycIntegrationEngine:
    def __init__(self):
        print("[*] Khởi tạo Hệ thống eKYC (Chế độ Tích hợp Pre-trained Models)...")
        # Khởi tạo 3 khối Engine chính
        self.doc_engine = DocumentEngine()
        self.liveness_engine = LivenessEngine()
        self.face_engine = FaceMatchingEngine()
        
    def process_verification(self, id_card_img_path, selfie_img_path):
        """
        Luồng eKYC hoàn chỉnh:
        1. Gọi DocumentEngine xử lý thẻ, lấy ra Ảnh Mặt trên CCCD.
        2. Gọi LivenessEngine quét ảnh Selfie chống giả mạo.
        3. Gọi FaceMatchingEngine so khớp Ảnh CCCD và Ảnh Selfie.
        """
        print(f"\n[*] Đang xử lý giao dịch: CCCD={id_card_img_path}, Selfie={selfie_img_path}")
        
        # 1. Quét thẻ CCCD (YOLO + VietOCR)
        doc_result = self.doc_engine.process_id_card(id_card_img_path)
        if doc_result["status"] != "SUCCESS":
            return {"decision": "FAIL", "reason": "Không thể đọc CCCD. Vui lòng chụp lại."}
        
        # 2. Quét Liveness Selfie (MiniFASNet)
        liveness_result = self.liveness_engine.check_liveness(selfie_img_path)
        if liveness_result["status"] != "LIVE":
            return {"decision": "FAIL", "reason": "Phát hiện khuôn mặt giả mạo."}
            
        # 3. So khớp khuôn mặt (DeepFace)
        # DeepFace sẽ tự động detect mặt trên cả 2 ảnh nếu chưa được cắt
        face_1_path = doc_result.get("face_crop_path", id_card_img_path)
        match_result = self.face_engine.match_faces(face_1_path, selfie_img_path)
        if not match_result["verified"]:
            return {"decision": "FAIL", "reason": "Khuôn mặt không khớp với CCCD."}
            
        # 4. Trả kết quả thành công
        return {
            "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "decision": "PASS",
            "reason": "Xác thực danh tính thành công.",
            "data_extracted": doc_result["extracted_data"],
            "scores": {
                "liveness_score": liveness_result["score"],
                "face_distance": match_result["distance"]
            }
        }

if __name__ == "__main__":
    print("=" * 60)
    print(" GIAO DIỆN API - KIẾN TRÚC TÍCH HỢP (YOLO/VIETOCR/DEEPFACE)")
    print("=" * 60)
    
    app = EkycIntegrationEngine()
    response = app.process_verification("cccd_khachhang_01.jpg", "selfie_khachhang_01.jpg")
    
    # Hiển thị kết quả ra Terminal
    color_code = '\033[92m' if response['decision'] == 'PASS' else '\033[93m' if response['decision'] == 'REVIEW' else '\033[91m'
    reset_code = '\033[0m'
    
    print("-" * 40)
    print(f"Decision: {color_code}{response['decision']}{reset_code}")
    print(f"Lý do:    {response['reason']}")
    print(f"Thông tin CCCD: {response.get('data_extracted', {})}")
    print(f"Metrics:  {response.get('scores', {})}")
    print("-" * 40)
