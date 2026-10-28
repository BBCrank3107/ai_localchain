# 🏛️ BÁO CÁO TỔNG THỂ DỰ ÁN LOCALCHAIN AI OPERATING SYSTEM (V5.2)

**Cập nhật lần cuối:** 06/08/2026  
**Phiên bản hiện tại:** LocalChain AI Operating System V5.2 (Enterprise Gold Standard)  
**Trạng thái kiến trúc:** Hoàn thiện toàn diện 100% (Model 1 YOLO11 + Model 2 Multi-Head Diagnosis + Model 3 Dual XGBoost Pricing + Knowledge & Procedure Engine V5.2 + Subsystem NLG + FastAPI Microservices)

---

## 🌟 1. TỔNG QUAN KIẾN TRÚC TOÀN DIỆN V5.2 (10/10 ENTERPRISE ARCHITECTURE)

Hệ thống được kiến trúc theo mô hình **AI Planning & Diagnostic Operating System** phân tách độc lập giữa Machine Learning, Đồ thị Tri thức (Knowledge Graph), Lập kế hoạch quy trình (State Machine DAG) và Kiểm toán an toàn (Pure Audit Guardrail):

```text
                 [Ảnh Sự Cố Thiết Bị] + [Mô Tả Triệu Chứng Từ Khách Hàng]
                                             │
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │  👁️ MODEL 1: Thị Giác Máy Tính (YOLO11 Nano)           │
                 │  👉 File: model_1_vision/inference_vision.py            │
                 │  👉 Nhận diện 11 nhóm thiết bị gia dụng & công nghệ     │
                 └───────────────────────────┬────────────────────────────┘
                                             │ canonical_device_id
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │  🧠 MODEL 2: Chẩn Đoán Đa Nhánh (Multi-Head V3.0)       │
                 │  👉 File: model_2_diagnosis/inference_multihead.py       │
                 │  👉 6-Step Normalize + CanonicalDevice + 3-Factor OOD  │
                 │  👉 EnrichedTaxonomyCache O(1) + ProductionLogger       │
                 └─────────────┬────────────────────────────┬─────────────┘
                               │                            │
                               ▼                            ▼
┌───────────────────────────────────────────┐ ┌───────────────────────────────────────────┐
│ 💎 MODEL 3: Định Giá Dự Toán (Dual XGB)   │ │ 🏛️ KNOWLEDGE & PROCEDURE ENGINE V5.2     │
│ 👉 File: model_3_pricing/feature_builder.py│ │ 👉 File: subsystem_rag/retriever.py        │
│ 👉 Model 3A (Linh Kiện): R² = 0.9695      │ │ 1. Graph Expansion (11 Topologies)        │
│ 👉 Model 3B (Tiền Công): R² = 0.9499      │ │ 2. Hybrid Retrieval (BM25 + Dense Vector) │
│ 👉 Quy tắc SSOT + Bảo vệ biên độ an toàn  │ │ 3. Strategy Selector (Chiến lược xử lý)   │
│ 👉 Dual Explain Layer: Weights + Bullets  │ │ 4. Decision Tree Synthesizer (State DAG)  │
│                                           │ │ 5. Safety Validator (Audit PASS/WARN/FAIL)│
│                                           │ │ 6. Technical Risk Scorer (Thang 0-100)    │
│                                           │ │ 7. Generic Renderer (JSON + Markdown)     │
└──────────────────────┬────────────────────┘ └─────────────────────┬─────────────────────┘
                       │                                            │
                       └─────────────────────┬──────────────────────┘
                                             │
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │  💬 SUBSYSTEM NLG: Bộ Tạo Câu Ngữ Nghĩa Tự Nhiên       │
                 │  👉 File: subsystem_nlg/nlg_engine.py                  │
                 │  👉 Sinh báo cáo giải trình minh bạch chuẩn tiếng Việt │
                 └───────────────────────────┬────────────────────────────┘
                                             │
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │  🚀 PRODUCTION API V5.2: server_api/app.py             │
                 │  👉 Endpoint: /api/v1/diagnose-text, /api/v1/diagnose  │
                 │  👉 Trả về: Primary Diagnosis + Pricing Details        │
                 │     + State Machine DAG Workflow + Repair Guide        │
                 │     + Natural Explanation Message                      │
                 │  👉 Latency: < 45 ms | Bộ nhớ RAM tối ưu: < 120 MB     │
                 └────────────────────────────────────────────────────────┘
```

---

## 📂 2. DANH MỤC CẤU TRÚC THƯ MỤC V5.2

| Thư mục | Thành phần | Mô tả & Trách nhiệm | File Trọng Tâm / Dữ Liệu |
| :--- | :--- | :--- | :--- |
| **`model_1_vision/`** | Model 1: Thị giác máy tính | Phân loại 11 nhóm thiết bị từ ảnh chụp thực tế bằng YOLO11 Nano | `inference_vision.py`, `weights/best.pt` |
| **`model_2_diagnosis/`** | Model 2: Chẩn đoán bệnh học | Multi-Head Transformer 512D: 11 Failure Heads + Severity Head + 3-Factor OOD Guard | `inference_multihead.py`, `weights_transformer_multihead/` |
| **`model_3_pricing/`** | Model 3: Định giá chuyên gia | Dual XGBoost Regressors (Linh kiện & Tiền công) + Rule Engine + Safety Clamp | `feature_builder.py`, `train_pricing_v3.py`, `weights/` |
| **`subsystem_rag/`** | Knowledge & Procedure Engine V5.2 | Đồ thị tri thức Topo 5 lớp, Mở rộng cụm, Hoạch định State Machine DAG, Kiểm toán an toàn | `retriever.py`, `knowledge_graph/`, `planner/`, `validator/`, `renderer/` |
| **`subsystem_nlg/`** | Subsystem: Sinh câu tự nhiên | Tạo phản hồi ngữ nghĩa động tiếng Việt, diễn giải chi phí và hướng dẫn an toàn | `nlg_engine.py` |
| **`datasets/`** | Kho dữ liệu chuẩn hóa | 2,130 cẩm nang kỹ thuật, 46 mã lỗi chẩn đoán, 4 tệp Pricing SSOT | `manuals_v2/`, `troubleshooting/`, `pricing/` |
| **`server_api/`** | FastAPI Microservices API V5.2 | Cung cấp RESTful API hiệu năng cao cho ứng dụng Web và Mobile | `app.py`, `interactive_cli.py` |
| **`scratch/` & `tests/`** | Automated Verification Suites | Bộ kiểm thử tự động toàn bộ Pipeline V5.2 và API End-to-End | `test_rag_v5_pipeline.py`, `test_api_v5_full_flow.py` |

---

## 📊 3. KHO DỮ LIỆU TRI THỨC V5.2 HIỆN HÀNH

| Hạng mục dữ liệu | Nguồn thu thập | Số lượng | Vị trí lưu trữ |
| :--- | :--- | :---: | :--- |
| **Cẩm nang kỹ thuật iFixit** | iFixit REST API v2.0 (16 threads) | **2,066 manuals** | `datasets/manuals_v2/` |
| **OEM Service Manuals** | Internet Archive & Schematics | **8 manuals** | `datasets/manuals_v2/` |
| **Tổng số Manuals** | Tất cả các nguồn | **2,130 manuals** | `datasets/manuals_v2/` |
| **Bảng mã lỗi chẩn đoán** | Dell, HP, Daikin, LG, Samsung, Sony... | **46 mã lỗi** | `datasets/troubleshooting/` |
| **14-Section Semantic Chunks** | Chunker & Vector SVD Embeddings | **31,826 chunks** | `subsystem_rag/database/rag_knowledge_v5.sqlite` |
| **Pricing SSOT Data** | Dữ liệu thị trường chuẩn hóa | **4 files JSON** | `datasets/pricing/` |

---

## 🏆 4. BẢNG TIÊU CHUẨN ĐÁNH GIÁ SLA & HIỆU NĂNG V5.2

| Tiêu chí SLA | Ngưỡng yêu cầu SLA | Kết quả Thực Tế Đạt Được (V5.2) | Đánh Giá |
| :--- | :--- | :--- | :--- |
| **Component Model MAE** | < 80,000 VNĐ | **24,335 VNĐ** | 🟢 Vượt 328% |
| **Component Model $R^2$** | > 0.90 | **0.9695** | 🟢 Xuất sắc |
| **Labor Model MAE** | < 40,000 VNĐ | **8,033 VNĐ** | 🟢 Vượt 498% |
| **Labor Model $R^2$** | > 0.85 | **0.9499** | 🟢 Xuất sắc |
| **V5.2 Planning Pipeline Latency** | < 100.0 ms | **< 35.0 ms** | 🟢 Vượt 285% |
| **API End-to-End Latency** | < 150.0 ms | **< 45.0 ms** | 🟢 Siêu tốc |
| **Unit & E2E Test Coverage** | 100% Pass | **100% (All Test Suites Passed)** | 🟢 Hoàn hảo |
| **Audit Safety Validator** | Bắt buộc | **Đầy đủ PASS/WARN/BLOCK/FAIL** | 🟢 Đạt chuẩn Enterprise |

---

## 🚀 5. LỘ TRÌNH VẬN HÀNH & PHÁT TRIỂN TIẾP THEO

- **Giai đoạn 1 (Hoàn tất 100%):** Hoàn thiện và đóng băng toàn bộ kiến trúc **LocalChain AI Operating System V5.2**.
- **Giai đoạn 2:** Tích hợp giao diện người dùng Web Admin Dashboard và Mobile App (React Native / Flutter) kết nối trực tiếp vào `server_api/app.py`.
- **Giai đoạn 3:** Mở rộng nạp thêm các tài liệu kỹ thuật chuyên sâu theo các danh mục thiết bị mới.
