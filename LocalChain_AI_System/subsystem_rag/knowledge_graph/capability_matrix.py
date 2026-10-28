"""
LOCALCHAIN AI V5.2 - CAPABILITY MATRIX
Ma trận xác thực năng lực thao tác phần cứng (Hardware Capability Matrix).
Ngăn chặn các quy trình phi lý (Ví dụ: Cấm thao tác hàn khò BGA lên Pin Lithium, Cấm đo điện dung lên Cáp tín hiệu).
"""

from typing import Dict, List, Set

# Danh mục các năng lực thao tác chuẩn công nghiệp
ALL_CAPABILITIES = {
    "MEASURE_VOLTAGE": "Đo điện áp kiểm tra đường nguồn cấp (V)",
    "MEASURE_CONTINUITY": "Đo thông mạch và kiểm tra đứt ngầm/chập mass (Buzzer/Ω)",
    "MEASURE_IMPEDANCE": "Đo trở kháng cuộn cảm hoặc linh kiện (Ω)",
    "MEASURE_CAPACITANCE": "Đo dung lượng tụ điện (μF/nF)",
    "THERMAL_CAMERA_SCAN": "Soi camera nhiệt tìm linh kiện phát nhiệt bất thường",
    "DISCONNECT_POWER": "Ngắt nguồn điện AC hoặc cách ly pin",
    "REMOVE_SCREWS": "Tháo ốc cố định theo thứ tự đối xứng",
    "REMOVE_BEZEL": "Tách ngàm nẹp viền bảo vệ bằng cây nạy nhựa",
    "SWAP_COMPONENT": "Thay thế linh kiện mới tương thích 100%",
    "REPLACE_FUSE": "Thay thế cầu chì bảo vệ mạch",
    "REBALL_BGA": "Đóng chân chip vi mạch BGA chuyên dụng",
    "CLEAN_ISOPROPYL": "Vệ sinh tẩy rửa cặn bẩn/oxy hóa bằng cồn IPA 99%",
    "APPLY_THERMAL_PASTE": "Tra keo tản nhiệt kim loại lỏng hoặc gốm dẫn nhiệt",
    "FLASH_FIRMWARE": "Nạp lại Firmware/BIOS bằng máy nạp ROM RT809H",
    "CALIBRATE_SENSOR": "Cân chỉnh cảm biến và áp lực cân bằng",
    "VACUUM_EVACUATION": "Hút chân không đường ống môi chất lạnh",
    "GAS_CHARGING": "Nạp gas môi chất lạnh R32/R410A/R134a theo cân nặng gram",
    "TEST_POST_BOOT": "Bật máy kiểm tra tín hiệu khởi động POST",
    "TEST_RGB_FULLSCREEN": "Chạy dải màu đơn sắc kiểm tra điểm chết và hở sáng",
    "PRESSURE_SEAL_TEST": "Kiểm tra kín khí và áp lực nước chống rò rỉ"
}

# Ma trận phân quyền thao tác theo phân loại linh kiện
COMPONENT_CAPABILITY_RULES: Dict[str, Dict[str, List[str]]] = {
    "BATTERY": {
        "ALLOWED": ["DISCONNECT_POWER", "MEASURE_VOLTAGE", "SWAP_COMPONENT", "CLEAN_ISOPROPYL"],
        "BLOCKED": ["REBALL_BGA", "REPLACE_FUSE", "APPLY_THERMAL_PASTE", "FLASH_FIRMWARE"],
        "MANDATORY_SAFETY": ["REQ_NO_PUNCTURE", "REQ_ISOLATE_TERMINALS"]
    },
    "DISPLAY_PANEL": {
        "ALLOWED": ["REMOVE_BEZEL", "REMOVE_SCREWS", "SWAP_COMPONENT", "TEST_POST_BOOT", "TEST_RGB_FULLSCREEN", "MEASURE_VOLTAGE"],
        "BLOCKED": ["REBALL_BGA", "GAS_CHARGING", "VACUUM_EVACUATION", "APPLY_THERMAL_PASTE"],
        "MANDATORY_SAFETY": ["REQ_ESD_WRIST_STRAP", "REQ_GENTLE_PRYING"]
    },
    "CABLE_HARNESS": {
        "ALLOWED": ["MEASURE_CONTINUITY", "MEASURE_IMPEDANCE", "SWAP_COMPONENT", "CLEAN_ISOPROPYL"],
        "BLOCKED": ["REBALL_BGA", "FLASH_FIRMWARE", "GAS_CHARGING", "APPLY_THERMAL_PASTE"],
        "MANDATORY_SAFETY": ["REQ_ZERO_VOLTAGE_PLUGGING"]
    },
    "MAINBOARD_PCB": {
        "ALLOWED": ["MEASURE_VOLTAGE", "MEASURE_IMPEDANCE", "MEASURE_CONTINUITY", "THERMAL_CAMERA_SCAN", "REPLACE_FUSE", "REBALL_BGA", "FLASH_FIRMWARE", "CLEAN_ISOPROPYL", "SWAP_COMPONENT"],
        "BLOCKED": ["GAS_CHARGING", "VACUUM_EVACUATION"],
        "MANDATORY_SAFETY": ["REQ_BATTERY_DISCONNECTED", "REQ_ESD_PROTECTION"]
    },
    "COOLING_FAN": {
        "ALLOWED": ["REMOVE_SCREWS", "CLEAN_ISOPROPYL", "SWAP_COMPONENT", "MEASURE_VOLTAGE", "TEST_POST_BOOT"],
        "BLOCKED": ["REBALL_BGA", "FLASH_FIRMWARE", "GAS_CHARGING"],
        "MANDATORY_SAFETY": ["REQ_DO_NOT_SPIN_WITH_COMPRESSED_AIR"]
    },
    "COMPRESSOR_REFRIGERATION": {
        "ALLOWED": ["MEASURE_IMPEDANCE", "VACUUM_EVACUATION", "GAS_CHARGING", "PRESSURE_SEAL_TEST", "SWAP_COMPONENT"],
        "BLOCKED": ["FLASH_FIRMWARE", "REBALL_BGA", "TEST_RGB_FULLSCREEN"],
        "MANDATORY_SAFETY": ["REQ_DISCHARGE_HIGH_PRESSURE", "REQ_FIRE_EXTINGUISHER_R32"]
    },
    "MICROWAVE_HIGH_VOLTAGE": {
        "ALLOWED": ["DISCONNECT_POWER", "MEASURE_IMPEDANCE", "MEASURE_CONTINUITY", "SWAP_COMPONENT"],
        "BLOCKED": ["FLASH_FIRMWARE", "REBALL_BGA", "GAS_CHARGING"],
        "MANDATORY_SAFETY": ["REQ_DISCHARGE_HV_CAPACITOR_2100V", "REQ_INSULATED_GLOVES"]
    }
}

def validate_operation_against_component_type(component_type: str, operation_id: str) -> bool:
    """Kiểm tra xem operation có hợp lệ cho loại linh kiện này hay không"""
    rules = COMPONENT_CAPABILITY_RULES.get(component_type)
    if not rules:
        return True # Default allow if not restricted
    if operation_id in rules.get("BLOCKED", []):
        return False
    return True
