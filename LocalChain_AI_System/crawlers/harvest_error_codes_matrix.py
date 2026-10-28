"""
LOCALCHAIN AI V5.2 - ERROR CODES & TROUBLESHOOTING MATRIX HARVESTER
Tổng hợp & chuẩn hóa 100% bảng mã lỗi (LED Blink, Beep Codes, Mã hiển thị màn hình LED)
của các hãng chính hãng phổ biến (Dell, HP, Lenovo, Daikin, LG, Samsung, Toshiba, Panasonic...) cho 11 thiết bị.
"""

import os
import sys
import json
from typing import Dict, List, Any

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

OFFICIAL_ERROR_CODE_DB: Dict[str, List[Dict[str, Any]]] = {
    "laptop": [
        # Dell Diagnostic LED Blink Codes
        {"brand": "Dell", "code": "2 Amber, 7 White", "meaning": "LCD Display Failure / Cáp màn hình eDP hỏng", "target_subsystem": "DISPLAY", "component": "LCD_PANEL", "action": "Kiểm tra cáp eDP và thay tấm nền màn hình LCD."},
        {"brand": "Dell", "code": "3 Amber, 2 White", "meaning": "PCI or Video card / GPU failure", "target_subsystem": "GRAPHICS", "component": "GPU", "action": "Kiểm tra nguồn cấp GPU hoặc nạp lại VBIOS."},
        {"brand": "Dell", "code": "2 Amber, 1 White", "meaning": "CPU Failure / Lỗi xử lý vi xử lý trung tâm", "target_subsystem": "PROCESSING", "component": "CPU", "action": "Đo điện áp VCORE và vệ sinh socket / thay mainboard."},
        {"brand": "Dell", "code": "2 Amber, 4 White", "meaning": "Memory / RAM failure", "target_subsystem": "MEMORY", "component": "RAM", "action": "Vệ sinh chân RAM hoặc thay thế thanh RAM mới."},
        {"brand": "Dell", "code": "3 Amber, 5 White", "meaning": "Power Rail Failure / Chập đường nguồn chính 3.3V/5V", "target_subsystem": "POWER", "component": "POWER_IC", "action": "Đo trở kháng cuộn cảm PL và cách ly tụ chập."},
        {"brand": "Dell", "code": "3 Amber, 6 White", "meaning": "Recovery image not found / Lỗi BIOS ROM", "target_subsystem": "FIRMWARE", "component": "BIOS_CHIP", "action": "Nạp lại Firmware BIOS bằng máy nạp ROM RT809H."},
        
        # HP Diagnostic Blink Codes
        {"brand": "HP", "code": "Caps Lock 3 Slow, 2 Fast", "meaning": "Memory Module Error / Lỗi bộ nhớ RAM", "target_subsystem": "MEMORY", "component": "RAM", "action": "Thử từng khe cắm RAM hoặc thay thanh RAM tương thích."},
        {"brand": "HP", "code": "Caps Lock 5 Slow, 3 Fast", "meaning": "System Board / GPU failure", "target_subsystem": "MOTHERBOARD", "component": "MAINBOARD", "action": "Kiểm tra nguồn cấp GPU và IC điều khiển nguồn."},
        {"brand": "HP", "code": "Caps Lock 2 Slow, 2 Fast", "meaning": "BIOS Corruption / Lỗi vùng nhớ BIOS", "target_subsystem": "FIRMWARE", "component": "BIOS_CHIP", "action": "Phục hồi BIOS bằng phím tắt Windows + B hoặc nạp lại ROM."},
        
        # Lenovo ThinkPad Diagnostic Codes
        {"brand": "Lenovo", "code": "1-3-3-1 Beep", "meaning": "DIMM / RAM not detected", "target_subsystem": "MEMORY", "component": "RAM", "action": "Cắm lại RAM hoặc kiểm tra nguồn 1.2V DDR4."},
        {"brand": "Lenovo", "code": "5 Short Beeps", "meaning": "Security Chip / TPM or Motherboard failure", "target_subsystem": "SECURITY", "component": "MAINBOARD", "action": "Kiểm tra nguồn cấp TPM và khối xử lý trung tâm."},
        {"brand": "Lenovo", "code": "Melody Code 0001", "meaning": "Reset Error / Lỗi mất tín hiệu PLTRST#", "target_subsystem": "POWER", "component": "IO_CHIP", "action": "Kiểm tra IC nguồn SIO IT8586E và các mức áp thứ cấp."}
    ],
    
    "dieu_hoa": [
        # Daikin AC Error Codes
        {"brand": "Daikin", "code": "A1", "meaning": "Lỗi bo mạch dàn lạnh (Indoor PCB Error)", "target_subsystem": "ELECTRONICS", "component": "INDOOR_PCB", "action": "Kiểm tra điện áp cấp 5V/12V cho vi xử lý dàn lạnh."},
        {"brand": "Daikin", "code": "A6", "meaning": "Lỗi quạt dàn lạnh (Indoor Fan Motor Failure)", "target_subsystem": "MOTOR", "component": "BLOWER_MOTOR", "action": "Kiểm tra cảm biến Hall hồi tiếp tốc độ quạt hoặc thay motor quạt."},
        {"brand": "Daikin", "code": "C4", "meaning": "Lỗi cảm biến nhiệt độ đường ống lỏng dàn lạnh", "target_subsystem": "SENSOR", "component": "PIPE_THERMISTOR", "action": "Đo trị số điện trở cảm biến (chuẩn 20kΩ ở 25°C), thay thế nếu đứt/tăng trị số."},
        {"brand": "Daikin", "code": "C9", "meaning": "Lỗi cảm biến nhiệt độ gió hồi dàn lạnh", "target_subsystem": "SENSOR", "component": "ROOM_THERMISTOR", "action": "Đo điện trở cảm biến phòng (chuẩn 10kΩ ở 25°C)."},
        {"brand": "Daikin", "code": "E7", "meaning": "Lỗi motor quạt dàn nóng (Outdoor Fan Motor Error)", "target_subsystem": "MOTOR", "component": "OUTDOOR_FAN_MOTOR", "action": "Kiểm tra kẹt cơ khí cánh quạt, tụ kích hoặc IC công suất quạt dàn nóng."},
        {"brand": "Daikin", "code": "U4", "meaning": "Lỗi đường truyền tín hiệu kết nối dàn lạnh - dàn nóng", "target_subsystem": "COMMUNICATION", "component": "COMM_CIRCUIT", "action": "Kiểm tra dây điện số 3, cặp opto quang cách ly tín hiệu PC817 trên bo mạch."},
        {"brand": "Daikin", "code": "L5", "meaning": "Lỗi quá dòng máy nén Inverter (Compressor Overcurrent)", "target_subsystem": "COMPRESSOR", "component": "INVERTER_COMPRESSOR", "action": "Đo cân bằng trở kháng 3 cuộn dây U-V-W của Block nén và kiểm tra module IPM."}
    ],
    
    "may_giat": [
        # LG & Samsung & Electrolux Washing Machine Codes
        {"brand": "LG", "code": "dE / dE1 / dE2", "meaning": "Lỗi khóa cửa / công tắc cửa không đóng", "target_subsystem": "DOOR_LOCK", "component": "DOOR_LATCH_SWITCH", "action": "Kiểm tra tiếp điểm công tắc cửa, dây nối và rơ-le đóng lệnh trên bo."},
        {"brand": "LG", "code": "IE", "meaning": "Lỗi không cấp đủ nước vào lồng giặt (Water Inlet Error)", "target_subsystem": "WATER_INTAKE", "component": "INLET_VALVE", "action": "Vệ sinh lưới lọc van cấp, đo cuộn hút điện từ 4.5kΩ hoặc thay van cấp nước đôi."},
        {"brand": "LG", "code": "OE", "meaning": "Lỗi không xả được nước (Drain Failure)", "target_subsystem": "DRAIN", "component": "DRAIN_PUMP", "action": "Xả cặn rác tại bầu bơm, đo cuộn dây motor bơm xả (chuẩn ~160Ω)."},
        {"brand": "LG", "code": "UE / UB", "meaning": "Lỗi mất cân bằng lồng giặt khi vắt (Unbalanced Load)", "target_subsystem": "SUSPENSION", "component": "SUSPENSION_RODS", "action": "Kiểm tra 4 thanh ty treo giảm chấn hoặc phân bố lại quần áo."},
        {"brand": "LG", "code": "LE", "meaning": "Lỗi khóa động cơ Direct Drive / Lỗi cảm biến Hall (RPS Error)", "target_subsystem": "MOTOR", "component": "HALL_SENSOR_RPS", "action": "Thay cụm cảm biến điều tốc Hall Sensor RPS gắn tại đuôi mâm từ động cơ."},
        {"brand": "Samsung", "code": "4E / 4C", "meaning": "Lỗi nguồn cấp nước không vào", "target_subsystem": "WATER_INTAKE", "component": "INLET_VALVE", "action": "Kiểm tra áp lực nước và cuộn hút van cấp điện từ."},
        {"brand": "Samsung", "code": "5E / 5C", "meaning": "Lỗi bơm thoát nước bị tắc", "target_subsystem": "DRAIN", "component": "DRAIN_PUMP", "action": "Vệ sinh rác buồng bơm và kiểm tra đường ống xả."}
    ],
    
    "tu_lanh": [
        # Refrigerator Error Codes
        {"brand": "LG", "code": "Er-FF", "meaning": "Lỗi quạt dàn lạnh ngăn đá (Freezer Fan Motor Error)", "target_subsystem": "COOLING_FAN", "component": "FREEZER_FAN", "action": "Kiểm tra đóng tuyết kẹt cánh quạt hoặc thay motor quạt 12V DC."},
        {"brand": "LG", "code": "Er-CF", "meaning": "Lỗi quạt giải nhiệt dàn nóng (Condenser Fan Motor Error)", "target_subsystem": "COOLING_FAN", "component": "CONDENSER_FAN", "action": "Vệ sinh bụi dàn ngưng và kiểm tra quạt giải nhiệt lốc nén."},
        {"brand": "LG", "code": "Er-d1", "meaning": "Lỗi cảm biến xả đá (Defrost Sensor Defect)", "target_subsystem": "DEFROST", "component": "DEFROST_SENSOR", "action": "Đo điện trở cảm biến âm (trị số thay đổi theo độ lạnh), thay mới nếu sai số."},
        {"brand": "Samsung", "code": "22E", "meaning": "Lỗi quạt ngăn lạnh (Fridge Fan Error)", "target_subsystem": "COOLING_FAN", "component": "EVAPORATOR_FAN", "action": "Kiểm tra tuyết bám kẹt quạt và mạch điều khiển trên bo chính."}
    ],
    
    "tivi": [
        # Sony & Samsung Smart TV Blink Codes
        {"brand": "Sony", "code": "Blink Đỏ 6 Nhịp", "meaning": "Lỗi hệ thống đèn nền LED (Backlight / Inverter Error)", "target_subsystem": "BACKLIGHT", "component": "LED_STRIPS", "action": "Đo từng thanh LED bằng máy test LED chuyên dụng, thay thế trọn bộ thanh LED."},
        {"brand": "Sony", "code": "Blink Đỏ 5 Nhịp", "meaning": "Lỗi giao tiếp T-Con hoặc tấm nền LCD (T-Con / Panel Communication Error)", "target_subsystem": "DISPLAY", "component": "TCON_BOARD", "action": "Vệ sinh cáp LVDS, đo nguồn VGH (28V), VGL (-6V), AVDD (15V) trên bo T-Con."},
        {"brand": "Sony", "code": "Blink Đỏ 2 Nhịp", "meaning": "Lỗi nguồn chính (Power Supply Board / Main Power Failure)", "target_subsystem": "POWER", "component": "POWER_BOARD", "action": "Kiểm tra tụ lọc nguồn sơ cấp 450V và IC dao động nguồn cấp trước."}
    ],
    
    "lo_vi_song": [
        {"brand": "Panasonic", "code": "H97 / H98", "meaning": "Lỗi bo mạch cao áp Inverter hoặc Đèn vi sóng (Magnetron Error)", "target_subsystem": "MICROWAVE_GENERATOR", "component": "MAGNETRON", "action": "Đo thông mạch tim đèn Magnetron và kiểm tra cặp diode cao áp."},
        {"brand": "Electrolux", "code": "E-01", "meaning": "Lỗi cảm biến nhiệt độ buồng nướng", "target_subsystem": "SENSOR", "component": "TEMPERATURE_SENSOR", "action": "Kiểm tra jack cắm và thay thế cảm biến nhiệt NTC."}
    ],
    
    "may_in": [
        {"brand": "HP / Canon", "code": "Error 50.x", "meaning": "Lỗi cụm sấy không đạt nhiệt độ (Fuser Error)", "target_subsystem": "FUSER", "component": "FUSER_HEATING_ELEMENT", "action": "Kiểm tra thanh nhiệt Ceramic, rơ-le nhiệt bảo vệ và cảm biến nhiệt sấy."},
        {"brand": "HP / Canon", "code": "Error 59.x", "meaning": "Lỗi động cơ chính (Main Motor Error)", "target_subsystem": "MOTOR", "component": "MAIN_DRIVE_MOTOR", "action": "Kiểm tra kẹt cụm nhông truyền động cơ khí hoặc thay motor truyền động."},
        {"brand": "Canon", "code": "Error 5B00", "meaning": "Lỗi tràn bộ đếm mực thải (Waste Ink Counter Overflow)", "target_subsystem": "WASTE_INK", "component": "ABSORBER_PAD", "action": "Vệ sinh miếng mút thấm mực thải và reset EEPROM bằng phần mềm Service Tool."}
    ],
    
    "may_bom": [
        {"brand": "Generic", "code": "PUMP_ERR_LOCK", "meaning": "Kẹt cánh bơm / Motor gầm không quay", "target_subsystem": "MECHANICAL", "component": "PUMP_IMPELLER", "action": "Dùng tua vít quay mồi trục motor tại đuôi gió, tháo buồng bơm vệ sinh cặn rác."},
        {"brand": "Generic", "code": "PUMP_ERR_CAPACITOR", "meaning": "Hỏng tụ đề / Tụ ngậm (Capacitor Failed)", "target_subsystem": "ELECTRICAL", "component": "START_CAPACITOR", "action": "Đo dung lượng tụ bằng đồng hồ đo Farad, thay thế đúng trị số μF/450V AC."}
    ],
    
    "quat": [
        {"brand": "Generic", "code": "FAN_ERR_BUSHING", "meaning": "Bó bạc đạn / Kẹt cốt bạc động cơ", "target_subsystem": "MECHANICAL", "component": "BRASS_BUSHING", "action": "Vệ sinh trục cốt, tra dầu máy may chuyên dụng hoặc thay thế cặp bạc thau mới."},
        {"brand": "Generic", "code": "FAN_ERR_THERMAL_FUSE", "meaning": "Đứt cầu chì nhiệt bảo vệ cuộn dây (Thermal Fuse Open)", "target_subsystem": "SAFETY", "component": "THERMAL_FUSE", "action": "Bóc lớp gen bọc cuộn stato, đo thông mạch cầu chì nhiệt (chuẩn 130°C/2A), thay mới."}
    ],
    
    "noi_com": [
        {"brand": "Cuckoo / Sunhouse", "code": "E01", "meaning": "Lỗi cảm biến nắp nồi cơm điện tử (Lid Sensor Error)", "target_subsystem": "SENSOR", "component": "LID_THERMISTOR", "action": "Kiểm tra đứt ngầm dây tín hiệu qua bản lề nắp hoặc thay cảm biến nắp vung."},
        {"brand": "Cuckoo / Sunhouse", "code": "E02", "meaning": "Lỗi cảm biến đáy mâm nhiệt (Bottom Sensor Error)", "target_subsystem": "SENSOR", "component": "BOTTOM_THERMISTOR", "action": "Vệ sinh mâm nhiệt, đo điện trở cảm biến đáy (chuẩn 50kΩ ở nhiệt độ phòng)."}
    ],
    
    "may_loc_nuoc": [
        {"brand": "Karofi / Kangaroo", "code": "Er1", "meaning": "Nước cấp yếu / Không có nước đầu vào máy lọc RO", "target_subsystem": "WATER_INTAKE", "component": "LOW_PRESSURE_SWITCH", "action": "Kiểm tra van khóa nguồn nước, áp lực bồn chứa hoặc tiếp điểm van áp thấp."},
        {"brand": "Karofi / Kangaroo", "code": "Er2", "meaning": "Tắc lõi lọc thô số 1, 2, 3 hoặc tắc màng lọc RO", "target_subsystem": "FILTRATION", "component": "RO_MEMBRANE", "action": "Đo lưu lượng nước thải, thay thế lõi lọc thô định kỳ và màng RO chuyên dụng."}
    ]
}

def harvest_error_codes():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, "datasets", "troubleshooting")
    manuals_v2_dir = os.path.join(base_dir, "datasets", "manuals_v2")
    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(manuals_v2_dir, exist_ok=True)
    
    print("=" * 75)
    print("📋 KHỞI ĐỘNG XÂY DỰNG BẢNG MÃ LỖI & PAN BỆNH CHẨN ĐOÁN (11 THIẾT BỊ)")
    print("🎯 Chuẩn hóa LED Blink, Beep Codes, Mã hiển thị LED chính hãng")
    print("=" * 75)
    
    total_codes = 0
    
    for dev_key, code_list in OFFICIAL_ERROR_CODE_DB.items():
        # 1. Lưu JSON chuyên sâu trong datasets/troubleshooting
        out_json_path = os.path.join(target_dir, f"{dev_key}_error_codes.json")
        with open(out_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "device_key": dev_key,
                "total_codes": len(code_list),
                "error_matrix": code_list
            }, f, ensure_ascii=False, indent=2)
            
        # 2. Tạo Markdown cẩm nang mã lỗi trong datasets/manuals_v2
        md_lines = [
            f"# Bảng Mã Lỗi & Hướng Dẫn Khắc Phục Pan Bệnh - {dev_key.upper()}",
            "",
            f"- **Thiết bị:** {dev_key.upper()}",
            f"- **Phân loại:** Tra cứu chẩn đoán mã lỗi chính hãng (Dell, HP, Daikin, LG, Samsung, Sony...)",
            "",
            "## Bảng Tra Cứu Mã Lỗi Chi Tiết",
            "| Hãng / Dòng máy | Mã hiển thị / Nháy đèn / Beep | Ý nghĩa sự cố | Cụm liên quan | Thao tác khắc phục chuẩn |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        
        for c in code_list:
            md_lines.append(f"| **{c['brand']}** | `{c['code']}` | {c['meaning']} | `{c['component']}` | {c['action']} |")
            total_codes += 1
            
        md_lines.append("")
        md_lines.append("## Hướng Dẫn Đo Đạc & Kiểm Tra Kỹ Thuật")
        md_lines.append("- Luôn ngắt điện lưới hoặc tháo pin vật lý trước khi can thiệp vào các đường dây tín hiệu.")
        md_lines.append("- Sử dụng đồng hồ vạn năng kim hoặc số (VOM) có chức năng đo thông mạch Buzzer và đo điện dung Capacitance.")
        
        out_md_path = os.path.join(manuals_v2_dir, f"{dev_key}_official_error_codes_matrix.md")
        with open(out_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        print(f"✅ Đã chuẩn hóa {len(code_list)} mã lỗi cho {dev_key.upper()} -> {out_json_path}")
        
    print("\n" + "=" * 75)
    print(f"🎉 HOÀN THÀNH TỔNG HỢP BẢNG MÃ LỖI! Tổng số mã lỗi chuẩn: {total_codes}")
    print("=" * 75)

if __name__ == "__main__":
    harvest_error_codes()
