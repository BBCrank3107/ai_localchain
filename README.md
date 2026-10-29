# LocalChain AI Monorepo (`ai_localchain`)

Kho lưu trữ mã nguồn toàn bộ hệ thống trí tuệ nhân tạo (AI Models, Pipelines, Training & Inference Engines) cho nền tảng **LocalChain**.

---

## 📂 Cấu trúc Repository

```text
ai_localchain/
├── ekyc-ai-engine/             # Hệ thống xác thực danh tính điện tử eKYC
│   ├── api/                    # FastAPI Server phục vụ eKYC verification
│   ├── core/                   # Export ONNX & Core Utilities
│   ├── docs/                   # Dataset cards, Model cards, Threat models
│   ├── pipeline/               # 3 giai đoạn xử lý eKYC:
│   │   ├── stage_1_document/   # OCR CCCD mặt trước (YOLO11 + VietOCR)
│   │   ├── stage_2_liveness/   # Kiểm tra khuôn mặt sống (Anti-spoofing)
│   │   └── stage_3_face_matching/ # So khớp ảnh thẻ & selfie (DeepFace)
│   ├── train_yolo.py           # Script huấn luyện YOLO11 phát hiện trường trên CCCD
│   ├── debug_ocr.py            # Công cụ kiểm thử trực quan OCR CCCD
│   └── requirements.txt        # Thư viện phụ thuộc cho eKYC
│
└── LocalChain_AI_System/       # Hệ thống AI chẩn đoán, thị giác & định giá sửa chữa
    ├── model_1_vision/         # Model 1: Thị giác máy tính YOLO11 (30 loại thiết bị & lỗi)
    │   ├── train_vision.py     # Script huấn luyện YOLO11 Vision
    │   ├── inference_vision.py # Pipeline suy luận thị giác
    │   └── weights/            # Trọng số tốt nhất (best.pt)
    ├── model_2_diagnosis/      # Model 2: Transformer Multi-Head chẩn đoán nguyên nhân
    │   ├── train_multihead_transformer.py
    │   ├── inference_multihead.py
    │   └── weights_transformer_multihead/
    ├── model_3_pricing/        # Model 3: Enterprise Pricing Engine (Linh kiện & Công thợ)
    │   ├── train_pricing_v3.py # Huấn luyện mô hình định giá v3.1
    │   ├── inference_pricing.py# Pipeline tính toán khoảng giá theo thị trường VN
    │   └── weights/            # Trọng số Gradient Boosting / Random Forest
    ├── subsystem_rag/          # Hệ thống RAG & Knowledge Graph quy trình kỹ thuật
    │   ├── database/           # SQLite Knowledge Graph & TF-IDF/SVD Vectors
    │   └── knowledge_graph/    # 30 thiết bị, ma trận năng lực thợ, an toàn điện
    ├── subsystem_nlg/          # Engine sinh giải thích chẩn đoán & tư vấn khách hàng
    ├── crawlers/               # Bộ công cụ thu thập & chuẩn hóa dữ liệu thực tế
    ├── server_api/             # Microservices FastAPI tích hợp với backend LocalChain
    ├── tests/                  # Bộ test hồi quy và kiểm thử tích hợp 3 mô hình
    └── requirements.txt        # Thư viện phụ thuộc cho LocalChain AI System
```

---

## 🚀 Hướng dẫn Cài đặt & Sử dụng

### 1. eKYC AI Engine
```bash
cd ekyc-ai-engine
python -m venv venv
# Kích hoạt venv (Windows: .\venv\Scripts\activate, Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt

# Chạy server FastAPI eKYC
python -m uvicorn api.app:app --host 0.0.0.0 --port 8001 --reload

# Huấn luyện lại mô hình YOLO11 OCR CCCD
python train_yolo.py
```

### 2. LocalChain AI System (Vision, Diagnosis, Pricing, RAG)
```bash
cd LocalChain_AI_System
python -m venv venv
pip install -r requirements.txt

# Chạy server Microservice AI
python -m uvicorn server_api.app:app --host 0.0.0.0 --port 8000 --reload

# Chạy kiểm thử tích hợp toàn bộ pipeline
python tests/comprehensive_test_3models_multilevel.py
```

---

## 🛡️ Bản quyền & Bảo mật dữ liệu
- Các bộ dataset hình ảnh CCCD và dữ liệu thô lớn không lưu trữ trên Git để đảm bảo quyền riêng tư dữ liệu (PII) và tuân thủ chính sách kích thước tệp GitHub.
- Các mô hình đã huấn luyện hoàn chỉnh được lưu trữ sẵn trong thư mục `weights/` để phục vụ chạy trực tiếp.

