# -*- coding: utf-8 -*-
"""
BỘ TEST TOÀN DIỆN ĐA CẤP ĐỘ (DỄ -> TRUNG BÌNH -> KHÓ -> CỰC KHÓ)
KIỂM THỬ ĐỒNG THỜI 3 MÔ HÌNH:
  - Model 1: Thị giác YOLO11 (Vision)
  - Model 2: Chẩn đoán Multi-Head Deep Transformer (Diagnosis)
  - Model 3: Định giá thông minh Dual XGBoost + SSOT (Pricing)
  - End-to-End Pipeline: Vision -> Diagnosis -> Pricing
"""

import os
import sys
import json
import time

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from model_1_vision.inference_vision import vision_ai
from model_2_diagnosis.inference_multihead import MultiHeadDiagnosisEngine
from model_3_pricing.inference_pricing import get_pricing_engine

def find_sample_image(device_key):
    """Tìm 1 file ảnh hợp lệ trong tập val"""
    val_path = os.path.join(BASE_DIR, "datasets", "yolo_vision", "val", device_key)
    if os.path.exists(val_path):
        for f in os.listdir(val_path):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                return os.path.join(val_path, f)
    return None

def run_multilevel_tests():
    print("=" * 100)
    print("🚀 BẮT ĐẦU CHẠY BỘ KIỂM THỬ ĐA CẤP ĐỘ (EASY -> MEDIUM -> HARD -> EXTREME)")
    print("HỆ THỐNG LOCALCHAIN AI MULTI-MODEL: MODEL 1 + MODEL 2 + MODEL 3")
    print("=" * 100)
    
    diag_engine = MultiHeadDiagnosisEngine()
    pricing_engine = get_pricing_engine()
    
    test_results = {
        "level_1_easy": [],
        "level_2_medium": [],
        "level_3_hard": [],
        "level_4_extreme": []
    }
    
    # =========================================================================
    # CẤP ĐỘ 1: DỄ (EASY / CANONICAL BENCHMARK)
    # - Câu từ tiếng Việt chuẩn mực, rõ ràng, thiết bị kinh điển
    # =========================================================================
    print("\n" + "─" * 100)
    print("📌 [CẤP ĐỘ 1: DỄ] - Triệu chứng chuẩn mực, ảnh rõ nét, thiết bị phổ biến")
    print("─" * 100)
    
    easy_cases = [
        {
            "name": "Laptop hỏng màn hình hiển thị",
            "device": "laptop",
            "brand": "Apple",
            "symptom": "Màn hình laptop bị sọc ngang giật chớp tắt tối đen",
            "expected_fault": "LAPTOP_DISPLAY_SYSTEM_FAILURE",
            "expected_min_price": 1000000,
            "expected_max_price": 4000000
        },
        {
            "name": "Tủ lạnh hỏng hệ thống xả đá đông tuyết",
            "device": "tu_lanh",
            "brand": "Panasonic",
            "symptom": "Tủ lạnh ngăn đông đóng tuyết dày ngăn mát không lạnh",
            "expected_fault": "REFRIGERATOR_DEFROST_SYSTEM_FAILURE",
            "expected_min_price": 200000,
            "expected_max_price": 900000
        },
        {
            "name": "Điều hòa rò rỉ thiếu gas",
            "device": "dieu_hoa",
            "brand": "Daikin",
            "symptom": "Máy lạnh không lạnh chỉ thổi gió quạt ống đồng bám tuyết",
            "expected_fault": "AIRCON_GAS_LEAKAGE",
            "expected_min_price": 250000,
            "expected_max_price": 1200000
        },
        {
            "name": "Máy giặt hỏng công tắc khóa cửa",
            "device": "may_giat",
            "brand": "Electrolux",
            "symptom": "Máy giặt báo lỗi kẹt công tắc cửa không mở được nắp",
            "expected_fault": "WASHER_DOOR_LOCK_FAILURE",
            "expected_min_price": 200000,
            "expected_max_price": 800000
        },
        {
            "name": "Ấm siêu tốc hỏng rơ-le nhiệt",
            "device": "am_sieu_toc",
            "brand": "Sunhouse",
            "symptom": "Bình đun siêu tốc nước sôi không tự nhảy nút ngắt điện",
            "expected_fault": "KETTLE_THERMAL_SWITCH_FAILURE",
            "expected_min_price": 50000,
            "expected_max_price": 250000
        }
    ]
    
    for case in easy_cases:
        dev = case["device"]
        sym = case["symptom"]
        img_file = find_sample_image(dev)
        
        # 1. Model 1
        m1_pred, m1_conf = ("N/A", 0.0)
        if img_file:
            m1_pred, m1_conf = vision_ai.predict(img_file)
        
        # 2. Model 2
        diag_res = diag_engine.diagnose(dev, sym, brand=case.get("brand", "Generic"))
        pri = diag_res.get("primary_diagnosis", {})
        m2_fault = pri.get("fault_code")
        m2_conf = pri.get("confidence_score", 0.0)
        sev = pri.get("severity")
        
        # 3. Model 3
        price_res = pricing_engine.estimate_price_by_fault_code(
            fault_code=m2_fault or case["expected_fault"],
            brand=case.get("brand", "Generic"),
            action_type="replace",
            part_type="OEM",
            region="Metro"
        )
        total_p = price_res.get("total_price_vnd", 0)
        
        m1_pass = (m1_pred == dev)
        m2_pass = (m2_fault == case["expected_fault"])
        m3_pass = (case["expected_min_price"] <= total_p <= case["expected_max_price"])
        all_pass = m1_pass and m2_pass and m3_pass
        
        status = "✅ PASS" if all_pass else "⚠️ CẢNH BÁO"
        print(f"[{status}] {case['name']}")
        print(f"   • Model 1 Vision : Dự đoán '{m1_pred}' (Độ tin cậy: {m1_conf*100:.1f}%) -> {'ĐÚNG' if m1_pass else 'SAI'}")
        print(f"   • Model 2 NLP    : Mã lỗi '{m2_fault}' (Tin cậy: {m2_conf:.1f}%, Cấp độ: {sev}) -> {'ĐÚNG' if m2_pass else 'SAI'}")
        print(f"   • Model 3 Pricing: {total_p:,.0f} đ (Linh kiện: {price_res['component']['predicted_price_vnd']:,} đ + Công: {price_res['labor']['predicted_price_vnd']:,} đ) -> {'HỢP LÝ' if m3_pass else 'LỆCH'}")
        
        test_results["level_1_easy"].append({
            "name": case["name"], "all_pass": all_pass, "m1_pass": m1_pass, "m2_pass": m2_pass, "m3_pass": m3_pass
        })

    # =========================================================================
    # CẤP ĐỘ 2: TRUNG BÌNH (MEDIUM / REALISTIC SLANG & TEENCODE)
    # - Teencode, viết tắt, không dấu, thiết bị gia dụng mới mở rộng
    # =========================================================================
    print("\n" + "─" * 100)
    print("📌 [CẤP ĐỘ 2: TRUNG BÌNH] - Teencode, viết tắt, từ lóng, thiết bị gia dụng mới")
    print("─" * 100)
    
    medium_cases = [
        {
            "name": "Bếp từ teencode lỗi E0 k nhận nồi",
            "device": "bep_tu",
            "brand": "Midea",
            "symptom": "bep tu keu tit tit bao loi e0 dat noi len k nhan k nong",
            "expected_fault": "INDUCTION_STOVE_PAN_DETECTION_FAILURE",
            "expected_min_price": 100000,
            "expected_max_price": 500000
        },
        {
            "name": "Máy sấy tóc mùi khét k quay quạt",
            "device": "may_say_toc",
            "brand": "Philips",
            "symptom": "may say bat len nong ruc co mui khet do lo xo quat k quay",
            "expected_fault": "HAIR_DRYER_HEATING_COIL_FAILURE",
            "expected_min_price": 70000,
            "expected_max_price": 300000
        },
        {
            "name": "Quạt điện bó bạc quay lờ đờ phải lấy tay mồi",
            "device": "quat",
            "brand": "Senko",
            "symptom": "quat bat so 3 ma quay lo do lay tay quay moi thi moi chay keu re re",
            "expected_fault": "FAN_BEARING_BUSHING_FAILURE",
            "expected_min_price": 50000,
            "expected_max_price": 200000
        },
        {
            "name": "Điện thoại pin chai phù kênh nắp lưng",
            "device": "dien_thoai",
            "brand": "Apple",
            "symptom": "iphone bi phu pin kenh ca man hinh sac nhanh tut pin ao",
            "expected_fault": "PHONE_BATTERY_SYSTEM_FAILURE",
            "expected_min_price": 200000,
            "expected_max_price": 950000
        },
        {
            "name": "Máy xay sinh tố mòn bánh răng khớp nối",
            "device": "may_xay_sinh_to",
            "brand": "Panasonic",
            "symptom": "coi xay bat motor van quay nhung dao k quay bi mon banh rang nhua",
            "expected_fault": "BLENDER_COUPLER_CLUTCH_FAILURE",
            "expected_min_price": 80000,
            "expected_max_price": 350000
        }
    ]
    
    for case in medium_cases:
        dev = case["device"]
        sym = case["symptom"]
        img_file = find_sample_image(dev)
        
        m1_pred, m1_conf = ("N/A", 0.0)
        if img_file:
            m1_pred, m1_conf = vision_ai.predict(img_file)
            
        diag_res = diag_engine.diagnose(dev, sym, brand=case.get("brand", "Generic"))
        pri = diag_res.get("primary_diagnosis", {})
        m2_fault = pri.get("fault_code")
        m2_conf = pri.get("confidence_score", 0.0)
        sev = pri.get("severity")
        
        price_res = pricing_engine.estimate_price_by_fault_code(
            fault_code=m2_fault or case["expected_fault"],
            brand=case.get("brand", "Generic"),
            action_type="replace",
            part_type="OEM",
            region="Metro"
        )
        total_p = price_res.get("total_price_vnd", 0)
        
        m1_pass = (m1_pred == dev)
        m2_pass = (m2_fault == case["expected_fault"])
        m3_pass = (case["expected_min_price"] <= total_p <= case["expected_max_price"])
        all_pass = m1_pass and m2_pass and m3_pass
        
        status = "✅ PASS" if all_pass else "⚠️ CẢNH BÁO"
        print(f"[{status}] {case['name']}")
        print(f"   • Câu nhập gốc   : \"{sym}\"")
        print(f"   • Model 1 Vision : Dự đoán '{m1_pred}' ({m1_conf*100:.1f}%) -> {'ĐÚNG' if m1_pass else 'SAI'}")
        print(f"   • Model 2 NLP    : Chuẩn hóa -> Mã lỗi '{m2_fault}' (Tin cậy: {m2_conf:.1f}%) -> {'ĐÚNG' if m2_pass else 'SAI'}")
        print(f"   • Model 3 Pricing: {total_p:,.0f} đ (Linh kiện: {price_res['component']['predicted_price_vnd']:,} đ + Công: {price_res['labor']['predicted_price_vnd']:,} đ) -> {'HỢP LÝ' if m3_pass else 'LỆCH'}")
        
        test_results["level_2_medium"].append({
            "name": case["name"], "all_pass": all_pass, "m1_pass": m1_pass, "m2_pass": m2_pass, "m3_pass": m3_pass
        })

    # =========================================================================
    # CẤP ĐỘ 3: KHÓ (HARD / MULTI-FAULT & LIVING SERVICES)
    # - Câu ghép nhiều mệnh đề bệnh lý đồng thời (Clause Segmentation)
    # - Định giá Combo chiết khấu (Bundle Discount)
    # - Định giá 4 dịch vụ đời sống (Cleaning, Moving, Tutoring, Beauty)
    # =========================================================================
    print("\n" + "─" * 100)
    print("📌 [CẤP ĐỘ 3: KHÓ] - Đa mệnh đề / Đa lỗi đồng thời, Chiết khấu Combo & Dịch vụ Đời sống")
    print("─" * 100)
    
    # 3.1 Test Multi-Fault Diagnosis
    multi_fault_case = {
        "device": "dien_thoai",
        "brand": "Samsung",
        "symptom": "Điện thoại bị rơi nứt vỡ mặt kính màn hình sọc nháy, đồng thời pin bị chai sạc rất lâu đầy dùng nhanh hết",
        "expected_fault_count": 2,
        "expected_faults": ["PHONE_DISPLAY_OLED_FAILURE", "PHONE_BATTERY_SYSTEM_FAILURE"]
    }
    
    diag_multi = diag_engine.diagnose(multi_fault_case["device"], multi_fault_case["symptom"], brand=multi_fault_case["brand"])
    detected_clauses = diag_multi.get("detected_clauses", [])
    pred_faults = [f.get("fault_code") for f in diag_multi.get("predicted_faults", [])]
    
    # Định giá Combo
    pricing_combo = pricing_engine.estimate_multiple_faults(
        fault_codes=pred_faults,
        brand="Samsung",
        region="Metro"
    )
    
    multi_m2_pass = (len(pred_faults) >= 2 and any("DISPLAY" in f for f in pred_faults) and any("BATTERY" in f for f in pred_faults))
    combo_discount_pass = (pricing_combo.get("combo_discount_vnd", 0) > 0)
    
    print(f"[COMBO ĐA LỖI] {multi_fault_case['symptom']}")
    print(f"   • Tách mệnh đề   : {detected_clauses}")
    print(f"   • Các lỗi phát hiện: {pred_faults} -> {'ĐẠT CHUẨN ĐA LỖI' if multi_m2_pass else 'THIẾU LỖI'}")
    print(f"   • Tổng tiền linh kiện: {pricing_combo['sum_component_vnd']:,} đ")
    print(f"   • Công thợ gốc   : {pricing_combo['raw_labor_vnd']:,} đ")
    print(f"   • Chiết khấu combo: -{pricing_combo['combo_discount_vnd']:,} đ -> {'ĐÃ GIẢM GIÁ GÓI' if combo_discount_pass else 'CHƯA GIẢM'}")
    print(f"   • Tổng trọn gói  : {pricing_combo['total_price_vnd']:,} đ")
    
    test_results["level_3_hard"].append({
        "name": "Combo đa lỗi điện thoại (Màn hình + Pin)",
        "all_pass": multi_m2_pass and combo_discount_pass
    })
    
    # 3.2 Test 4 Dịch vụ Đời sống
    service_cases = [
        {
            "name": "Vệ sinh sau xây dựng 120m2",
            "type": "CLEANING",
            "params": {"package": "POST_CONSTRUCTION", "area": 120, "bringSupplies": True},
            "min": 800000, "max": 1500000
        },
        {
            "name": "Vận chuyển xe tải 1.5 tấn 20km có thang bộ tầng 4",
            "type": "MOVING",
            "params": {"vehicleType": "TRUCK_1500KG", "distanceKm": 20, "needPorter": True, "floorCount": 4, "hasElevator": False},
            "min": 450000, "max": 900000
        },
        {
            "name": "Gia sư luyện thi IELTS giáo viên 3 buổi/tuần",
            "type": "TUTORING",
            "params": {"level": "IELTS_TOEIC", "tutorType": "TEACHER", "sessionsPerWeek": 3},
            "min": 2500000, "max": 4500000
        },
        {
            "name": "Trang điểm cô dâu ngày cưới",
            "type": "BEAUTY_CARE",
            "params": {"package": "BRIDAL_MAKEUP", "personCount": 1},
            "min": 1000000, "max": 2000000
        }
    ]
    
    for sc in service_cases:
        s_res = pricing_engine.estimate_service_price(sc["type"], sc["params"])
        s_total = s_res.get("total_price_vnd", 0)
        s_pass = (sc["min"] <= s_total <= sc["max"])
        status = "✅ PASS" if s_pass else "⚠️ CẢNH BÁO"
        print(f"[{status}] Dịch vụ {sc['name']}: {s_total:,.0f} đ ({s_res.get('calculation_note')})")
        test_results["level_3_hard"].append({
            "name": sc["name"], "all_pass": s_pass
        })

    # =========================================================================
    # CẤP ĐỘ 4: CỰC KHÓ / BẪY / OOD / RỦI RO CAO (EXTREME & ADVERSARIAL)
    # - Câu chào xã giao / vô nghĩa (Chitchat Guard / OOD)
    # - Câu thiết bị bình thường không có lỗi (Zero-fault)
    # - Lệch pha thiết bị & triệu chứng (Device-Symptom Mismatch)
    # =========================================================================
    print("\n" + "─" * 100)
    print("📌 [CẤP ĐỘ 4: CỰC KHÓ & CẠM BẪY] - Chitchat, Không lỗi, Lệch thiết bị & Bất thường OOD")
    print("─" * 100)
    
    # 4.1 Test Chitchat
    chitchat_sym = "alo shop ơi có ai trực không chào bạn"
    diag_chat = diag_engine.diagnose("laptop", chitchat_sym)
    chat_pass = (not diag_chat.get("is_fault", True) or diag_chat.get("primary_diagnosis", {}).get("fault_code") == "NORMAL_OPERATION_NO_FAULT")
    print(f"[BẪY CHITCHAT] \"{chitchat_sym}\"")
    print(f"   • Phản hồi Model 2: is_fault = {diag_chat.get('is_fault')} | Mã lỗi: {diag_chat.get('primary_diagnosis', {}).get('fault_code')} -> {'CHẶN THÀNH CÔNG' if chat_pass else 'BỊ ĐÁNH LỪA'}")
    test_results["level_4_extreme"].append({"name": "Phát hiện câu chào xã giao Chitchat", "all_pass": chat_pass})
    
    # 4.2 Test Thiết bị hoạt động bình thường (No-Fault)
    normal_sym = "máy chạy êm ru mát rượi dùng rất tốt không vấn đề gì"
    diag_norm = diag_engine.diagnose("laptop", normal_sym)
    norm_pass = (not diag_norm.get("is_fault", True) or diag_norm.get("primary_diagnosis", {}).get("fault_code") == "NORMAL_OPERATION_NO_FAULT")
    print(f"[BẪY KHÔNG LỖI] \"{normal_sym}\"")
    print(f"   • Phản hồi Model 2: is_fault = {diag_norm.get('is_fault')} | Mã lỗi: {diag_norm.get('primary_diagnosis', {}).get('fault_code')} -> {'CHÍNH XÁC (KHÔNG BÁO LỖI ẢO)' if norm_pass else 'BỊ LỖI ẢO'}")
    test_results["level_4_extreme"].append({"name": "Thiết bị hoạt động tốt không báo lỗi ảo", "all_pass": norm_pass})
    
    # 4.3 Test Lệch pha Thiết bị và Triệu chứng (Device-Symptom Mismatch)
    # Người dùng chọn 'tu_lanh' nhưng gõ triệu chứng kẹt giấy của 'may_in'
    mismatch_dev = "tu_lanh"
    mismatch_sym = "máy in kéo giấy bị kẹt giữa chừng rách bao lụa lem mực đen"
    diag_mis = diag_engine.diagnose(mismatch_dev, mismatch_sym)
    mis_pri = diag_mis.get("primary_diagnosis", {})
    # Kiểm tra OOD entropy hoặc confidence score bị hạ thấp
    mis_conf = mis_pri.get("confidence_score", 0.0)
    uncertainty = diag_mis.get("uncertainty_metrics", {})
    mis_pass = (mis_conf < 80.0 or uncertainty.get("is_ood", False) or uncertainty.get("entropy", 0.0) > 1.5)
    print(f"[BẪY LỆCH THIẾT BỊ] Thiết bị: '{mismatch_dev}' nhưng triệu chứng: \"{mismatch_sym}\"")
    print(f"   • Độ tin cậy gán: {mis_conf:.1f}% | OOD Metrics: {uncertainty}")
    print(f"   • Đánh giá rủi ro: {'CẢNH BÁO OOD / HẠ TIN CẬY AN TOÀN' if mis_pass else 'TỰ TIN THÁI QUÁ (NGUY HIỂM)'}")
    test_results["level_4_extreme"].append({"name": "Phát hiện bất thường lệch triệu chứng thiết bị", "all_pass": mis_pass})

    # =========================================================================
    # TỔNG KẾT BÁO CÁO TOÀN DIỆN
    # =========================================================================
    print("\n" + "=" * 100)
    print("📊 TỔNG KẾT BẢNG ĐIỂM KIỂM THỬ ĐA CẤP ĐỘ")
    print("=" * 100)
    
    total_tests = 0
    passed_tests = 0
    
    for level, tests in test_results.items():
        lvl_pass = sum(1 for t in tests if t["all_pass"])
        lvl_total = len(tests)
        total_tests += lvl_total
        passed_tests += lvl_pass
        pct = (lvl_pass / lvl_total * 100) if lvl_total > 0 else 0
        print(f"• {level.upper():<20}: {lvl_pass}/{lvl_total} Passed ({pct:.1f}%)")
        
    overall_pct = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print("-" * 100)
    print(f"🏆 TỔNG ĐIỂM TOÀN DIỆN HỆ THỐNG: {passed_tests}/{total_tests} Test Cases ({overall_pct:.1f}%)")
    print("=" * 100)

if __name__ == "__main__":
    run_multilevel_tests()
