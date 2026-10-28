# -*- coding: utf-8 -*-
"""
BỘ KIỂM THỬ MÔ PHỎNG 100% CẤU TRÚC FORM NHẬP LIỆU CỦA APP_LOCALCHAIN
(create_job.tsx, CategoryFormRepair, CategoryFormCleaning, CategoryFormMoving, CategoryFormTutoring, CategoryFormBeauty)

Các cấp độ kiểm thử từ Dễ -> Trung Bình -> Khó -> Cực khó / Biên:
1. Dễ: Form Sửa chữa chuẩn + Form Vệ sinh & Vận chuyển tiêu chuẩn
2. Trung bình: Thiết bị gia dụng mới + Chế độ Cần ngay (Instant) + Phụ phí thú cưng / Thang bộ
3. Khó: Form mô tả đa lỗi đồng thời (Multi-fault) + Gia sư IELTS + Trang điểm nhiều người
4. Cực khó / Biên: Form thiếu mô tả (chỉ có ảnh), Lệch thiết bị giữa ảnh và form chọn, Chồng nhiều phụ phí
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

def get_image_path_for_device(dev_key):
    val_dir = os.path.join(BASE_DIR, "datasets", "yolo_vision", "val", dev_key)
    if os.path.exists(val_dir):
        files = [f for f in os.listdir(val_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        if files:
            return os.path.join(val_dir, files[0])
    return None

def run_app_form_benchmark():
    print("=" * 105)
    print("📱 CHẠY BỘ KIỂM THỬ MÔ PHỎNG DỮ LIỆU TỪ FORM TẠO YÊU CẦU CỦA APP_LOCALCHAIN")
    print("=" * 105)
    
    diag_engine = MultiHeadDiagnosisEngine()
    pricing_engine = get_pricing_engine()
    
    report_summary = {
        "level_1_easy": [],
        "level_2_medium": [],
        "level_3_hard": [],
        "level_4_extreme": []
    }

    # =========================================================================
    # CẤP ĐỘ 1: DỄ - FORM NHẬP CHUẨN CƠ BẢN
    # =========================================================================
    print("\n" + "─" * 105)
    print("📋 [CẤP ĐỘ 1: DỄ] - Form chuẩn, thiết bị rõ ràng, dịch vụ tiêu chuẩn")
    print("─" * 105)
    
    level_1_forms = [
        {
            "form_type": "REPAIR",
            "title": "Sửa laptop Dell bị hỏng màn hình",
            "form_fields": {
                "device": "Laptop",
                "brand": "Dell",
                "description": "Màn hình laptop bị sọc ngang giật chớp tối đen",
                "priority": "Scheduled",
                "region": "Metro"
            },
            "canonical_device": "laptop",
            "expected_fault": "LAPTOP_DISPLAY_SYSTEM_FAILURE",
            "price_range": (1000000, 3500000)
        },
        {
            "form_type": "REPAIR",
            "title": "Sửa máy giặt LG không khóa được cửa",
            "form_fields": {
                "device": "Máy giặt",
                "brand": "LG",
                "description": "Máy giặt báo lỗi dE kẹt công tắc cửa không mở được nắp",
                "priority": "Scheduled",
                "region": "Metro"
            },
            "canonical_device": "may_giat",
            "expected_fault": "WASHER_DOOR_LOCK_FAILURE",
            "price_range": (200000, 750000)
        },
        {
            "form_type": "CLEANING",
            "title": "Dọn dẹp chung cư 2 phòng ngủ tiêu chuẩn",
            "form_fields": {
                "propertyType": "APARTMENT",
                "areaSqMeters": 65,
                "bedrooms": 2,
                "bathrooms": 2,
                "cleaningPackage": "STANDARD",
                "estimatedHours": 3,
                "bringSupplies": True,
                "hasPets": False
            },
            "expected_formula_note": "3.0 giờ x 80,000 đ/giờ (Gói tiêu chuẩn)",
            "expected_price": 311000 # 3h x 80k = 240k + 71k supplies = 311k
        },
        {
            "form_type": "MOVING",
            "title": "Chuyển trọ gần bằng xe ba gác",
            "form_fields": {
                "vehicleType": "TRICYCLE",
                "packageWeight": "15 - 50kg",
                "distanceKm": 5.0,
                "needPorter": False,
                "pickupFloor": "Tầng trệt",
                "dropoffFloor": "Tầng trệt",
                "hasElevator": True
            },
            "expected_price": 75000 # Cửa 30k + 4km x 11.2k ~ 75k
        }
    ]
    
    for case in level_1_forms:
        f_type = case["form_type"]
        title = case["title"]
        fields = case["form_fields"]
        
        if f_type == "REPAIR":
            dev_key = case["canonical_device"]
            img_path = get_image_path_for_device(dev_key)
            
            # Model 1
            m1_pred, m1_conf = ("N/A", 0.0)
            if img_path:
                m1_pred, m1_conf = vision_ai.predict(img_path)
            
            # Model 2
            diag_res = diag_engine.diagnose(fields["device"], fields["description"], brand=fields["brand"])
            f_code = diag_res.get("primary_diagnosis", {}).get("fault_code")
            f_conf = diag_res.get("primary_diagnosis", {}).get("confidence_score", 0.0)
            
            # Model 3
            p_res = pricing_engine.estimate_price_by_fault_code(
                fault_code=f_code or case["expected_fault"],
                brand=fields["brand"],
                part_type="OEM",
                region=fields["region"]
            )
            total_vnd = p_res.get("total_price_vnd", 0)
            
            p_min, p_max = case["price_range"]
            passed = (f_code == case["expected_fault"]) and (p_min <= total_vnd <= p_max)
            status = "✅ PASS" if passed else "⚠️ LỆCH"
            
            print(f"[{status}] Form Sửa chữa: {title}")
            print(f"   • Input Form   : Thiết bị='{fields['device']}', Hãng='{fields['brand']}', Mô tả=\"{fields['description']}\"")
            print(f"   • Model 1 Image: Nhận diện '{m1_pred}' ({m1_conf*100:.1f}%)")
            print(f"   • Model 2 Fault: '{f_code}' ({f_conf:.1f}%)")
            print(f"   • Model 3 Price: {total_vnd:,} đ (Linh kiện: {p_res['component']['predicted_price_vnd']:,} đ | Công: {p_res['labor']['predicted_price_vnd']:,} đ)")
            report_summary["level_1_easy"].append({"name": title, "pass": passed})
            
        elif f_type == "CLEANING":
            p_res = pricing_engine.estimate_service_price("CLEANING", fields)
            total_vnd = p_res.get("total_price_vnd", 0)
            passed = abs(total_vnd - case["expected_price"]) <= 20000
            status = "✅ PASS" if passed else "⚠️ LỆCH"
            print(f"[{status}] Form Vệ sinh: {title}")
            print(f"   • Options Form : {fields['areaSqMeters']}m², {fields['cleaningPackage']}, {fields['estimatedHours']}h, Mang dụng cụ={fields['bringSupplies']}")
            print(f"   • Định giá AI  : {total_vnd:,} đ (Ghi chú: {p_res.get('calculation_note')})")
            report_summary["level_1_easy"].append({"name": title, "pass": passed})
            
        elif f_type == "MOVING":
            p_res = pricing_engine.estimate_service_price("MOVING", fields)
            total_vnd = p_res.get("total_price_vnd", 0)
            passed = (total_vnd > 0)
            status = "✅ PASS" if passed else "⚠️ LỆCH"
            print(f"[{status}] Form Vận chuyển: {title}")
            print(f"   • Options Form : Xe={fields['vehicleType']}, {fields['distanceKm']} km, Bốc xếp={fields['needPorter']}")
            print(f"   • Định giá AI  : {total_vnd:,} đ (Ghi chú: {p_res.get('calculation_note')})")
            report_summary["level_1_easy"].append({"name": title, "pass": passed})

    # =========================================================================
    # CẤP ĐỘ 2: TRUNG BÌNH - THIẾT BỊ MỚI, YÊU CẦU CẦN NGAY (INSTANT), PHỤ PHÍ
    # =========================================================================
    print("\n" + "─" * 105)
    print("📋 [CẤP ĐỘ 2: TRUNG BÌNH] - Thiết bị mới, Chế độ Cần ngay (Instant), Phụ phí thú cưng/Thang bộ")
    print("─" * 105)
    
    level_2_forms = [
        {
            "form_type": "REPAIR",
            "title": "Bếp từ Midea báo lỗi E0 (Ưu tiên Cần Ngay - Instant)",
            "form_fields": {
                "device": "Bếp từ",
                "brand": "Midea",
                "description": "bep tu keu tit tit bao loi e0 dat noi len k nhan",
                "priority": "Instant", # Cần ngay -> Phụ phí khẩn cấp
                "distance_km": 8.0,    # > 5km -> Phụ phí di chuyển
                "region": "Metro"
            },
            "canonical_device": "bep_tu",
            "expected_fault": "INDUCTION_STOVE_PAN_DETECTION_FAILURE"
        },
        {
            "form_type": "REPAIR",
            "title": "Quạt điện Senko bó bạc k quay (Ngoại thành 15km)",
            "form_fields": {
                "device": "Quạt điện",
                "brand": "Senko",
                "description": "quat bi bo bac truc quay lo do lay tay quay moi thi moi chay",
                "priority": "Scheduled",
                "distance_km": 15.0, # Cách 15km -> 10km phụ phí
                "region": "Rural"
            },
            "canonical_device": "quat",
            "expected_fault": "FAN_MOTOR_BEARING_FAILURE"
        },
        {
            "form_type": "CLEANING",
            "title": "Tổng vệ sinh biệt thự chuyên sâu + Có thú cưng",
            "form_fields": {
                "propertyType": "VILLA",
                "areaSqMeters": 180,
                "bedrooms": 4,
                "bathrooms": 4,
                "cleaningPackage": "DEEP_CLEAN",
                "estimatedHours": 6,
                "bringSupplies": True,
                "hasPets": True # Phụ phí thú cưng 30k
            }
        },
        {
            "form_type": "MOVING",
            "title": "Xe tải 1 tấn chuyển nhà 12km có thang bộ tầng 3 + thợ vác",
            "form_fields": {
                "vehicleType": "TRUCK_1000KG",
                "packageWeight": "50 - 150kg",
                "distanceKm": 12.0,
                "needPorter": True,
                "floorCount": 3,
                "hasElevator": False # Phụ phí thang bộ
            }
        }
    ]
    
    for case in level_2_forms:
        f_type = case["form_type"]
        title = case["title"]
        fields = case["form_fields"]
        
        if f_type == "REPAIR":
            dev_key = case["canonical_device"]
            is_instant = (fields["priority"] == "Instant")
            dist = fields.get("distance_km", 0.0)
            
            diag_res = diag_engine.diagnose(fields["device"], fields["description"], brand=fields["brand"])
            f_code = diag_res.get("primary_diagnosis", {}).get("fault_code")
            
            p_res = pricing_engine.estimate_price_by_fault_code(
                fault_code=f_code or case["expected_fault"],
                brand=fields["brand"],
                part_type="OEM",
                region=fields.get("region", "Metro"),
                distance_km=dist,
                is_emergency=is_instant
            )
            total_vnd = p_res.get("total_price_vnd", 0)
            surcharge = p_res.get("surcharge_vnd", 0)
            
            passed = (f_code == case["expected_fault"]) and (surcharge > 0 if (is_instant or dist > 5.0) else True)
            status = "✅ PASS" if passed else "⚠️ LỆCH"
            
            print(f"[{status}] Form Sửa chữa: {title}")
            print(f"   • Input Form   : Priority='{fields['priority']}', Dist={dist}km, Mô tả=\"{fields['description']}\"")
            print(f"   • Model 2 Fault: '{f_code}'")
            print(f"   • Model 3 Price: {total_vnd:,} đ (Đã gồm phụ phí khẩn cấp/khoảng cách: +{surcharge:,} đ)")
            report_summary["level_2_medium"].append({"name": title, "pass": passed})
            
        elif f_type == "CLEANING":
            p_res = pricing_engine.estimate_service_price("CLEANING", fields)
            total_vnd = p_res.get("total_price_vnd", 0)
            has_pet_surcharge = (p_res.get("surcharge_breakdown", {}).get("pet_fee_vnd", 0) > 0)
            passed = has_pet_surcharge and (total_vnd > 0)
            status = "✅ PASS" if passed else "⚠️ LỆCH"
            print(f"[{status}] Form Vệ sinh: {title}")
            print(f"   • Options Form : {fields['areaSqMeters']}m², {fields['cleaningPackage']}, hasPets={fields['hasPets']}")
            print(f"   • Định giá AI  : {total_vnd:,} đ (Gồm phụ phí thú cưng: +{p_res['surcharge_breakdown']['pet_fee_vnd']:,} đ)")
            report_summary["level_2_medium"].append({"name": title, "pass": passed})
            
        elif f_type == "MOVING":
            p_res = pricing_engine.estimate_service_price("MOVING", fields)
            total_vnd = p_res.get("total_price_vnd", 0)
            has_stairs = (p_res.get("stairs_carry_fee_vnd", 0) > 0)
            passed = has_stairs and (total_vnd > 0)
            status = "✅ PASS" if passed else "⚠️ LỆCH"
            print(f"[{status}] Form Vận chuyển: {title}")
            print(f"   • Options Form : Xe={fields['vehicleType']}, {fields['distanceKm']}km, Tầng={fields['floorCount']}, Thang máy={fields['hasElevator']}")
            print(f"   • Định giá AI  : {total_vnd:,} đ (Cước xe: {p_res['truck_transport_fee_vnd']:,} đ + Bốc xếp: {p_res['porter_labor_fee_vnd']:,} đ + Thang bộ: {p_res['stairs_carry_fee_vnd']:,} đ)")
            report_summary["level_2_medium"].append({"name": title, "pass": passed})

    # =========================================================================
    # CẤP ĐỘ 3: KHÓ - ĐA MỆNH ĐỀ MULTI-FAULT, GIA SƯ & LÀM ĐẸP
    # =========================================================================
    print("\n" + "─" * 105)
    print("📋 [CẤP ĐỘ 3: KHÓ] - Khách mô tả đa lỗi trong Form, Gia sư IELTS, Makeup cô dâu")
    print("─" * 105)
    
    # 3.1 Form Repair với mô tả 2 lỗi cùng lúc
    multi_repair_form = {
        "title": "Form sửa điện thoại Samsung: Vỡ nắp lưng kính + Chai phồng pin",
        "device": "Điện thoại",
        "brand": "Samsung",
        "description": "Điện thoại rơi nứt vỡ mặt kính màn hình sọc nháy, đồng thời pin bị chai sạc nhanh hết máy rất nóng",
        "region": "Metro"
    }
    diag_multi = diag_engine.diagnose(multi_repair_form["device"], multi_repair_form["description"], brand=multi_repair_form["brand"])
    fault_list = [f.get("fault_code") for f in diag_multi.get("predicted_faults", [])]
    
    p_combo = pricing_engine.estimate_multiple_faults(fault_codes=fault_list, brand=multi_repair_form["brand"])
    discount_applied = (p_combo.get("combo_discount_vnd", 0) > 0)
    passed_multi = (len(fault_list) >= 2) and discount_applied
    status = "✅ PASS" if passed_multi else "⚠️ LỆCH"
    
    print(f"[{status}] Form Sửa chữa đa lỗi: {multi_repair_form['title']}")
    print(f"   • Phân tích mệnh đề : {diag_multi.get('detected_clauses')}")
    print(f"   • Bắt 2 mã lỗi SSOT : {fault_list}")
    print(f"   • Áp dụng chiết khấu: Tiền linh kiện: {p_combo['sum_component_vnd']:,} đ | Giảm tiền công combo: -{p_combo['combo_discount_vnd']:,} đ | Trọn gói: {p_combo['total_price_vnd']:,} đ")
    report_summary["level_3_hard"].append({"name": multi_repair_form["title"], "pass": passed_multi})
    
    # 3.2 Form Tutoring
    tutoring_form = {
        "title": "Tìm gia sư Giáo viên luyện thi IELTS 3 buổi/tuần tại nhà",
        "serviceType": "TUTORING",
        "subject": "Tiếng Anh",
        "gradeLevel": "Đại học / Đi làm",
        "learningFormat": "HOME",
        "sessionsPerWeek": 3,
        "sessionDurationHours": 1.5,
        "targetGoal": "Luyện thi IELTS/TOEIC",
        "tutorRequirement": "Giáo viên trường"
    }
    p_tutor = pricing_engine.estimate_service_price("TUTORING", tutoring_form)
    tutor_total = p_tutor.get("total_price_vnd", 0)
    passed_tutor = (tutor_total > 1500000)
    status = "✅ PASS" if passed_tutor else "⚠️ LỆCH"
    print(f"[{status}] Form Gia sư: {tutoring_form['title']}")
    print(f"   • Thông tin Form : {tutoring_form['subject']} ({tutoring_form['targetGoal']}), {tutoring_form['sessionsPerWeek']} buổi/tuần, {tutoring_form['tutorRequirement']}")
    print(f"   • Dự toán học phí: {tutor_total:,} đ/tháng ({p_tutor.get('calculation_note')})")
    report_summary["level_3_hard"].append({"name": tutoring_form["title"], "pass": passed_tutor})
    
    # 3.3 Form Beauty
    beauty_form = {
        "title": "Trang điểm tiệc & cô dâu cho 3 người",
        "serviceType": "BEAUTY_CARE",
        "beautyService": "MAKEUP_PARTY",
        "beautyServiceLabel": "Trang điểm tiệc & cô dâu",
        "personCount": 3
    }
    p_beauty = pricing_engine.estimate_service_price("BEAUTY_CARE", beauty_form)
    beauty_total = p_beauty.get("total_price_vnd", 0)
    passed_beauty = (beauty_total > 500000)
    status = "✅ PASS" if passed_beauty else "⚠️ LỆCH"
    print(f"[{status}] Form Làm đẹp: {beauty_form['title']}")
    print(f"   • Thông tin Form : Gói={beauty_form['beautyService']}, Số người={beauty_form['personCount']}")
    print(f"   • Dự toán chi phí: {beauty_total:,} đ ({p_beauty.get('calculation_note')})")
    report_summary["level_3_hard"].append({"name": beauty_form["title"], "pass": passed_beauty})

    # =========================================================================
    # CẤP ĐỘ 4: CỰC KHÓ / TRƯỜNG HỢP BIÊN (EDGE CASES TRÊN FORM)
    # =========================================================================
    print("\n" + "─" * 105)
    print("📋 [CẤP ĐỘ 4: CỰC KHÓ / BIÊN FORM] - Thiếu mô tả sự cố (chỉ có ảnh), Chồng nhiều phụ phí tối đa")
    print("─" * 105)
    
    # 4.1 Khách chỉ tải ảnh máy giặt, ô mô tả chỉ gõ vỏn vẹn "hỏng"
    img_washer = get_image_path_for_device("may_giat")
    m1_pred_w, m1_conf_w = vision_ai.predict(img_washer)
    # Model 1 nhận diện là 'may_giat' -> Chuyển vào Model 2 với triệu chứng chung
    diag_brief = diag_engine.diagnose(m1_pred_w, "hỏng")
    pri_brief = diag_brief.get("primary_diagnosis", {})
    passed_brief = (m1_pred_w == "may_giat") and bool(pri_brief.get("fault_code"))
    status = "✅ PASS" if passed_brief else "⚠️ CẢNH BÁO"
    print(f"[{status}] Biên 1: Khách chỉ chụp ảnh, ô mô tả chỉ gõ 'hỏng'")
    print(f"   • Model 1 Image  : Nhận diện thành công '{m1_pred_w}' ({m1_conf_w*100:.1f}%)")
    print(f"   • Model 2 Phán đoán: Mã lỗi mặc định/phổ biến nhất '{pri_brief.get('fault_code')}' (Tin cậy: {pri_brief.get('confidence_score')}%)")
    report_summary["level_4_extreme"].append({"name": "Khách chỉ chụp ảnh, mô tả tối giản", "pass": passed_brief})
    
    # 4.2 Form Repair với tất cả các phụ phí cực đại: Ban đêm/Khẩn cấp + Cuối tuần + Cách 30km + Có VAT
    p_extreme = pricing_engine.estimate_price_by_fault_code(
        fault_code="AIRCON_COMPRESSOR_FAILURE",
        brand="Daikin",
        action_type="replace",
        part_type="Genuine",
        distance_km=30.0,      # Phụ phí di chuyển 25km x 5k = 125k
        is_emergency=True,     # Phụ phí khẩn cấp +20% công thợ
        is_weekend=True,       # Phụ phí cuối tuần +10% công thợ
        include_vat=True       # Thuế GTGT VAT 10%
    )
    surcharges_vnd = p_extreme.get("surcharge_vnd", 0)
    passed_extreme = (surcharges_vnd > 0)
    status = "✅ PASS" if passed_extreme else "⚠️ CẢNH BÁO"
    print(f"[{status}] Biên 2: Form sửa chữa khẩn cấp ban đêm + Cuối tuần + 30km + Xuất VAT")
    print(f"   • Linh kiện gốc  : {p_extreme['component']['predicted_price_vnd']:,} đ")
    print(f"   • Tiền công thợ  : {p_extreme['labor']['predicted_price_vnd']:,} đ")
    print(f"   • Tổng phụ phí   : +{surcharges_vnd:,} đ (Cấp tốc + Cuối tuần + Di chuyển xa)")
    print(f"   • Tổng trọn gói  : {p_extreme['total_price_vnd']:,} đ")
    report_summary["level_4_extreme"].append({"name": "Chồng nhiều phụ phí tối đa an toàn", "pass": passed_extreme})

    # =========================================================================
    # TỔNG KẾT BẢNG ĐIỂM
    # =========================================================================
    print("\n" + "=" * 105)
    print("📊 TỔNG KẾT BẢNG ĐIỂM KIỂM THỬ THEO CHUẨN FORM APP_LOCALCHAIN")
    print("=" * 105)
    total_all = 0
    pass_all = 0
    for lvl, items in report_summary.items():
        lvl_pass = sum(1 for x in items if x["pass"])
        lvl_tot = len(items)
        total_all += lvl_tot
        pass_all += lvl_pass
        print(f"• {lvl.upper():<20}: {lvl_pass}/{lvl_tot} Đạt ({(lvl_pass/lvl_tot*100):.1f}%)")
        
    print("-" * 105)
    print(f"🏆 TỔNG ĐIỂM HOÀN TẤT: {pass_all}/{total_all} Form Test Cases ({pass_all/total_all*100:.1f}%)")
    print("=" * 105)

if __name__ == "__main__":
    run_app_form_benchmark()
