import sys
import os

# ============================================================
# CRITICAL PATCH: PIL.Image.ANTIALIAS bị xóa trong Pillow>=10
# Vá NGAY TẠI ĐÂY trước khi bất kỳ module nào import PIL
# ============================================================
from PIL import Image as _PILImage
if not hasattr(_PILImage, 'ANTIALIAS'):
    _PILImage.ANTIALIAS = _PILImage.LANCZOS

import gradio as gr

# Import Core Engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.app import EkycIntegrationEngine

# Khởi tạo Engine
engine = EkycIntegrationEngine()

def process_ekyc(id_card_img, selfie_img):
    if id_card_img is None or selfie_img is None:
        return "Vui lòng upload đầy đủ 2 ảnh!", "", ""
        
    # Gọi Engine xử lý
    result = engine.process_verification(id_card_img, selfie_img)
    
    decision = result.get("decision", "FAIL")
    reason = result.get("reason", "Lỗi không xác định")
    
    extracted = result.get("data_extracted", {})
    info_text = f"Họ Tên: {extracted.get('full_name', 'N/A')}\n"
    info_text += f"Số CCCD: {extracted.get('id_number', 'N/A')}\n"
    info_text += f"Ngày Sinh: {extracted.get('dob', 'N/A')}\n"
    info_text += f"Giới Tính: {extracted.get('gender', 'N/A')}\n"
    info_text += f"Quốc Tịch: {extracted.get('nationality', 'N/A')}\n"
    info_text += f"Quê Quán / Nơi ĐKKH: {extracted.get('origin', 'N/A')}\n"
    info_text += f"Nơi Cư Trú: {extracted.get('residence', 'N/A')}\n"
    info_text += f"Ngày Hết Hạn: {extracted.get('expiry_date', 'N/A')}"
    
    scores = result.get("scores", {})
    liveness_sc = scores.get("liveness_score", 0.0)
    face_dist = scores.get("face_distance", 1.0)
    metrics = f"Liveness Score: {liveness_sc:.2f}\n"
    metrics += f"Face Distance (Càng thấp càng giống): {face_dist:.2f}"
    
    return decision, reason, info_text, metrics

# Dựng giao diện Web Gradio
with gr.Blocks(title="LocalChain eKYC Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🛡️ Hệ Thống eKYC - Kiến Trúc Tích Hợp (SOTA Models)")
    gr.Markdown("Tích hợp công nghệ YOLOv8 (Detection), VietOCR (Text), MiniFASNet (Liveness), và DeepFace ArcFace (Matching).")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 1. Tải lên CCCD")
            id_input = gr.Image(type="filepath", label="Ảnh mặt trước CCCD")
        
        with gr.Column():
            gr.Markdown("### 2. Chụp Selfie / Upload Ảnh Mặt")
            selfie_input = gr.Image(type="filepath", label="Ảnh khuôn mặt thật")
            
    verify_btn = gr.Button("Xác thực Danh tính (Verify)", variant="primary", size="lg")
    
    gr.Markdown("---")
    gr.Markdown("### KẾT QUẢ XÁC THỰC (PIPELINE DECISION)")
    
    with gr.Row():
        decision_out = gr.Textbox(label="Quyết Định (PASS/REVIEW/FAIL)")
        reason_out = gr.Textbox(label="Lý do chi tiết")
        
    with gr.Row():
        info_out = gr.Textbox(label="Thông tin đọc được (OCR)", lines=3)
        metrics_out = gr.Textbox(label="Chỉ số AI (Metrics)", lines=2)
        
    verify_btn.click(
        fn=process_ekyc,
        inputs=[id_input, selfie_input],
        outputs=[decision_out, reason_out, info_out, metrics_out]
    )

if __name__ == "__main__":
    print("[*] Đang khởi chạy Giao diện Web Gradio (Localhost)...")
    demo.launch(share=False)
