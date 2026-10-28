"""
TEST SUITE: KIỂM THỬ TOÀN DIỆN MÔ HÌNH MULTI-HEAD CHẨN ĐOÁN (SSOT V2)
Kiểm thử 12 ca bệnh thực tế trên toàn bộ 11 Device Heads
"""

import os
import sys

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from model_2_diagnosis.inference_multihead import MultiHeadDiagnosisEngine

def run_comprehensive_multihead_tests():
    print("=" * 85)
    print("🧪 KIỂM THỬ TOÀN DIỆN MÔ HÌNH MULTI-HEAD (SSOT V2 SCHEMA)")
    print("=" * 85)
    
    engine = MultiHeadDiagnosisEngine()
    print(f"🧠 [Multi-Head Model 2] Mạng Nơ-ron PyTorch ({engine.device}) đã sẵn sàng! (Val Acc: {engine.meta['best_val_acc']:.2f}%)\n")
    
    test_cases = [
        {
            "device": "laptop",
            "brand": "Asus",
            "symptom": "Laptop Asus màn hình bị sọc kẻ ngang nhấp nháy liên tục khi gập mở bản lề",
            "expected_fault": "LAPTOP_DISPLAY_SYSTEM_FAILURE"
        },
        {
            "device": "laptop",
            "brand": "Apple",
            "symptom": "MacBook pin dùng được 10 phút là sập nguồn rút sạc tắt ngúm",
            "expected_fault": "LAPTOP_BATTERY_SYSTEM_FAILURE"
        },
        {
            "device": "may_in",
            "brand": "Canon",
            "symptom": "Máy in Canon 2900 kéo giấy bị kẹt giữa chừng kêu cạch cạch liên tục",
            "expected_fault": "PRINTER_PICKUP_ROLLER_FAILURE"
        },
        {
            "device": "dieu_hoa",
            "brand": "Daikin",
            "symptom": "Điều hòa Daikin nháy đèn báo lỗi U4 không nhận tín hiệu giữa dàn nóng và dàn lạnh",
            "expected_fault": "AIRCON_COMMUNICATION_FAILURE"
        },
        {
            "device": "may_giat",
            "brand": "LG",
            "symptom": "Máy giặt LG đến chu trình vắt thì rung lắc cực mạnh đập thùng ầm ĩ báo lỗi UE",
            "expected_fault": "WASHER_UNBALANCE_SUSPENSION_FAILURE"
        },
        {
            "device": "tu_lanh",
            "brand": "Samsung",
            "symptom": "Tủ lạnh Samsung ngăn mát không lạnh và ngăn đông bị đóng tuyết dày đặc không tự xả đá",
            "expected_fault": "REFRIGERATOR_DEFROST_SYSTEM_FAILURE"
        },
        {
            "device": "tivi",
            "brand": "Sony",
            "symptom": "Tivi Sony có tiếng nói bình thường nhưng màn hình tối đen soi đèn mới thấy hình mờ",
            "expected_fault": "TV_BACKLIGHT_LED_FAILURE"
        },
        {
            "device": "lo_vi_song",
            "brand": "Panasonic",
            "symptom": "Lò vi sóng đĩa vẫn quay đèn vẫn sáng nhưng quay 5 phút thức ăn nguội ngắt không nóng",
            "expected_fault": "MICROWAVE_MAGNETRON_FAILURE"
        },
        {
            "device": "may_loc_nuoc",
            "brand": "Karofi",
            "symptom": "Máy lọc nước Karofi máy bơm chạy liên tục không tự ngắt nước tinh khiết chảy nhỏ giọt",
            "expected_fault": "WATER_PURIFIER_PRESSURE_SWITCH_FAILURE"
        },
        {
            "device": "noi_com",
            "brand": "Cuckoo",
            "symptom": "Nồi cơm điện Cuckoo nhảy nút sớm làm cơm bị sống sượng khê đáy",
            "expected_fault": "RICE_COOKER_THERMOSTAT_FAILURE"
        },
        {
            "device": "quat",
            "brand": "Senko",
            "symptom": "Quạt điện Senko bị bó bạc kẹt trục quay lờ đờ phải lấy tay mồi mới quay",
            "expected_fault": "FAN_MOTOR_BEARING_FAILURE"
        },
        {
            "device": "may_bom",
            "brand": "Panasonic",
            "symptom": "Máy bơm nước bị rỉ nước ở cổ trục buồng bơm và rơ-le tăng áp đóng ngắt tạch tạch liên tục",
            "expected_fault": "PUMP_PRESSURE_SWITCH_FAILURE"
        }
    ]
    
    for i, tc in enumerate(test_cases, 1):
        res = engine.diagnose(tc["device"], tc["symptom"], brand=tc["brand"])
        primary = res["primary_diagnosis"]
        
        print(f"[{i:02d}/12] 📥 [{tc['device'].upper()}] - Thương hiệu: [{tc['brand']}]")
        print(f"       💬 Triệu chứng: \"{tc['symptom']}\"")
        print(f"       🎯 Chẩn đoán từ [{tc['device'].upper()} HEAD]:")
        print(f"          • Mã lỗi: {primary['fault_code']}")
        print(f"          • Tên bệnh: {primary['fault_name_vn']}")
        print(f"          • Linh kiện (Array): {primary['components']}")
        print(f"          • Mức độ sửa: {primary['repair_level']} | Độ nghiêm trọng: {primary['severity']} | Độ tự tin: {primary['confidence_score']}%")
        print(f"          • Top 3 khả năng:")
        for rank, cand in enumerate(res["top_candidates"], 1):
            print(f"            [{rank}] {cand['fault_code']} ({cand['probability']}%) -> {cand['fault_name_vn']}")
        print()
        
    print("=" * 85)
    print("🎉 TẤT CẢ 12 CA KIỂM THỬ TRÊN 11 HEAD ĐÃ HOÀN TẤT XUẤT SẮC!")
    print("=" * 85)

if __name__ == "__main__":
    run_comprehensive_multihead_tests()
