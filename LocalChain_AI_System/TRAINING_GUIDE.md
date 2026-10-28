# 📖 HƯỚNG DẪN CHI TIẾT HUẤN LUYỆN & VẬN HÀNH HỆ THỐNG LOCALCHAIN AI (V5.2)

Tài liệu này cung cấp toàn bộ các câu lệnh thực thi độc lập cho từng **Mô hình AI (Model 1, Model 2, Model 3)**, **Hệ thống Tri thức & Lập Kế hoạch Sửa Chữa (Knowledge & Procedure Engine V5.2)**, **Bộ Tạo Câu Tự Nhiên (Subsystem NLG)** và **Cổng API Microservices (FastAPI)**.

---

## 📂 SƠ ĐỒ QUY HOẠCH CẤU TRÚC THƯ MỤC CHUẨN HÓA V5.2

```text
LocalChain_AI_System/
│
├── 📁 model_1_vision/               # [MODEL 1] Thị giác máy tính nhận diện thiết bị (YOLO11 Nano)
│   ├── train_vision.py             # Huấn luyện YOLO11n-cls trên tập ảnh 11 nhóm thiết bị
│   ├── inference_vision.py         # Module suy luận nhận diện thiết bị từ ảnh/video
│   └── weights/                    # Chứa trọng số best.pt tối ưu
│
├── 📁 model_2_diagnosis/            # [MODEL 2] Bộ não chẩn đoán bệnh học sâu đa nhánh (Multi-Head Transformer V3.0)
│   ├── train_multihead_transformer.py # Huấn luyện Shared Backbone + 11 Failure Heads + Severity Head (PyTorch/CUDA)
│   ├── inference_multihead.py      # Production Engine: 6-Step Normalizer, CanonicalDeviceMapper,
│   │                               #   IntentAndClauseSegmenter, OODUncertaintyGuard (MSP+Margin+Entropy),
│   │                               #   EnrichedTaxonomyCache O(1), ProductionLogger
│   └── weights_transformer_multihead/ # Chứa best_multihead_model.pt, tfidf_svd.pkl, multihead_metadata.json
│
├── 📁 model_3_pricing/              # [MODEL 3] Chuyên gia định giá Enterprise V3.1 (Dual XGBoost Regressors)
│   ├── feature_builder.py          # Module Feature Builder nạp 4 SSOT vào RAM, tạo Decoupled Features O(1)
│   ├── train_pricing_v3.py         # Huấn luyện Component Model (Model A) & Labor Model (Model B)
│   ├── inference_pricing.py        # Suy luận tính giá minh bạch: Rule Engine, Safety Clamp, Confidence & Explain
│   └── weights/                    # Chứa component_model_v3.1.pkl, labor_model_v3.1.pkl, pricing_metadata.json
│
├── 📁 subsystem_rag/                # [KNOWLEDGE & PROCEDURE ENGINE V5.2]
│   ├── knowledge_graph/            # Đồ thị tri thức Topo 5 lớp & Ma trận phân quyền phần cứng
│   │   ├── graph_schema.py         # Định nghĩa Schema 5 lớp (Device -> Subsystem -> Assembly -> Component -> Capability)
│   │   ├── capability_matrix.py    # Ma trận phân quyền thao tác phần cứng
│   │   └── device_knowledge_graph.py # Tri thức topo SSOT 11 thiết bị
│   ├── expansion/                  # Module mở rộng cụm linh kiện liên đới (Cluster Expander)
│   │   └── graph_expander.py
│   ├── retrieval/                  # Bộ truy xuất kết hợp (BM25 + Dense Vector Embeddings)
│   │   └── hybrid_retriever.py
│   ├── planner/                    # Bộ não hoạch định chiến lược & sinh quy trình DAG
│   │   ├── strategy_selector.py    # Phân tích Root Cause (Rơi vỡ, ngấm nước, chập nguồn...)
│   │   └── workflow_generator.py   # Sinh State Machine DAG Workflow Pydantic
│   ├── validator/                  # Bộ kiểm toán an toàn thuần túy & tính điểm rủi ro
│   │   ├── safety_validator.py     # Pure Audit Guardrail (PASS / WARNING / BLOCK / FAIL)
│   │   └── risk_scorer.py          # Thang đo chỉ số nguy hiểm 0 - 100
│   ├── renderer/                   # Xuất dữ liệu đa định dạng
│   │   └── workflow_renderer.py    # Render Interactive JSON State Machine & Markdown tiếng Việt
│   ├── retriever.py                # Facade điều phối trung tâm của Engine V5.2
│   └── database/                   # CSDL SQLite V5.2 chứa 31,826 chunks & TF-IDF/SVD models
│
├── 📁 subsystem_nlg/                # [SUBSYSTEM NLG] Bộ tạo câu tiếng Việt tự nhiên
│   └── nlg_engine.py               # Mẫu câu ngữ nghĩa động giải trình chi phí & cảnh báo an toàn
│
├── 📁 datasets/                     # [DATASETS & KNOWLEDGE BASE]
│   ├── manuals_v2/                 # 2,130 cẩm nang kỹ thuật iFixit & OEM Service Manuals
│   ├── troubleshooting/            # 46 mã lỗi chẩn đoán tiêu chuẩn chính hãng
│   └── pricing/                    # 4 tệp JSON SSOT định giá thị trường & CSV huấn luyện
│
├── 📁 crawlers/                     # [CRAWLERS & ETL PIPELINES]
│   ├── harvest_ifixit_bulk_fast.py # Multi-threaded Crawler thu thập iFixit Manuals
│   ├── harvest_oem_service_manuals.py # Harvester thu thập OEM Service Manuals
│   ├── harvest_error_codes_matrix.py  # Harvester chuẩn hóa bảng mã lỗi
│   ├── build_chunked_knowledge_base.py# Pipeline bóc tách 14-Section Chunking & nạp SQLite V5.2
│   └── build_pricing_dataset_v3.py # ETL Pipeline sinh tập dữ liệu huấn luyện Model 3
│
├── 📁 server_api/                   # [API & CLI] Cổng giao tiếp Microservices V5.2
│   ├── app.py                      # FastAPI Production Server V5.2
│   └── interactive_cli.py          # Công cụ Chat tương tác trực tiếp trên Terminal
│
└── 📁 scratch/ & 📁 tests/          # [AUTOMATED VERIFICATION TEST SUITES]
    ├── test_rag_v5_pipeline.py     # Kiểm thử độc lập Pipeline V5.2 (4 ca bệnh thực tế)
    └── test_api_v5_full_flow.py    # Kiểm thử End-to-End toàn bộ API Server
```

---

## 🛠️ CÁC BƯỚC THỰC THI & HUẤN LUYỆN TOÀN BỘ HỆ THỐNG

### 1. Thu Thập Dữ Liệu & Xây Dựng Kho Tri Thức V5.2 (ETL Pipeline)
```powershell
# Bước 1.1: Thu thập cẩm nang iFixit đa luồng
.\localchain_env\Scripts\python.exe crawlers\harvest_ifixit_bulk_fast.py

# Bước 1.2: Thu thập tài liệu OEM Service Manuals
.\localchain_env\Scripts\python.exe crawlers\harvest_oem_service_manuals.py

# Bước 1.3: Chuẩn hóa ma trận mã lỗi chính hãng
.\localchain_env\Scripts\python.exe crawlers\harvest_error_codes_matrix.py

# Bước 1.4: Bóc tách 14-Section Semantic Chunks và nạp CSDL SQLite V5.2
.\localchain_env\Scripts\python.exe crawlers\build_chunked_knowledge_base.py
```
*Kết quả:* Cơ sở dữ liệu `subsystem_rag/database/rag_knowledge_v5.sqlite` chứa 31,826 chunks vector hóa.

---

### 2. Huấn Luyện & Kiểm Thử Model 3 Enterprise Pricing Engine
```powershell
# Bước 2.1: Sinh tập dữ liệu huấn luyện Model 3 từ SSOT
.\localchain_env\Scripts\python.exe crawlers\build_pricing_dataset_v3.py

# Bước 2.2: Huấn luyện Dual XGBoost Regressors
.\localchain_env\Scripts\python.exe model_3_pricing\train_pricing_v3.py
```
*Kết quả:*
- **Component Model:** $R^2 = 0.9695$, $\text{MAE} = 24,335\text{ VNĐ}$ (SLA $< 80,000\text{ VNĐ}$).
- **Labor Model:** $R^2 = 0.9499$, $\text{MAE} = 8,033\text{ VNĐ}$ (SLA $< 40,000\text{ VNĐ}$).

---

### 3. Huấn Luyện Model 1 (Vision) & Model 2 (Multi-Head Diagnosis)
```powershell
# Huấn luyện Model 1: Thị giác YOLO11 Nano (nếu có dữ liệu ảnh mới)
.\localchain_env\Scripts\python.exe model_1_vision\train_vision.py

# Huấn luyện Model 2: Multi-Head Transformer V3.0 (PyTorch CUDA)
.\localchain_env\Scripts\python.exe model_2_diagnosis\train_multihead_transformer.py
```

---

### 4. Kiểm Thử Độc Lập Engine Hoạch Định V5.2 (Pipeline Unit Tests)
```powershell
.\localchain_env\Scripts\python.exe scratch\test_rag_v5_pipeline.py
```
*Kiểm thử tự động 4 kịch bản:*
- **TC1 (Laptop rơi vỡ):** Chiến lược `STRUCTURAL_INTEGRITY_FIRST`, trạng thái `PASS`, rủi ro `10/100 (LOW)`.
- **TC2 (Lò vi sóng cao áp 2100V):** Chiến lược `POWER_RAIL_ISOLATION`, trạng thái `WARNING`, rủi ro `100/100 (EXTREME_DANGER)`.
- **TC3 (Máy giặt LG van cấp nước):** Chiến lược `DIRECT_REPLACEMENT_FLOW`, trạng thái `PASS`, rủi ro `40/100 (MEDIUM)`.
- **TC4 (Điều hòa Daikin Inverter):** Chiến lược `DIRECT_REPLACEMENT_FLOW`, trạng thái `PASS`, rủi ro `75/100 (HIGH)`.

---

### 5. Khởi Chạy Máy Chủ API Microservices (FastAPI Production)
```powershell
.\localchain_env\Scripts\python.exe -m uvicorn server_api.app:app --host 0.0.0.0 --port 8000 --reload
```

---

### 6. Chạy Bộ Kiểm Thử Tích Hợp Toàn Diện (End-to-End System Tests)
```powershell
.\localchain_env\Scripts\python.exe scratch\test_api_v5_full_flow.py
```
*Kết quả:* Xác minh 100% phản hồi từ API Server trả về đầy đủ 5 trụ cột:
1. `primary_diagnosis` (Model 2)
2. `estimated_price_vnd` + `pricing_details` (Model 3)
3. `repair_workflow` (State Machine DAG JSON + Risk Analysis V5.2)
4. `repair_guide` (Technical Markdown Report)
5. `natural_message` (Subsystem NLG)
