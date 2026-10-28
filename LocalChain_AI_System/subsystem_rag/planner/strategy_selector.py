"""
LOCALCHAIN AI V5.2 - STRATEGY SELECTOR
Bộ não hoạch định chiến lược can thiệp kỹ thuật (Repair Strategy Decider).
Phân tích triệu chứng, nguyên nhân gốc rễ (Root Cause) và ngữ cảnh người dùng để chọn chiến lược tối ưu.
"""

from typing import Dict, Any

REPAIR_STRATEGIES = {
    "STRUCTURAL_INTEGRITY_FIRST": {
        "name_vn": "Chiến lược Kiểm định Kết cấu & Bản lề cơ khí trước tiên",
        "description": "Áp dụng cho máy rơi vỡ, nứt vỡ ngoại quan. Kiểm tra gãy ngàm, chèn ép cáp và chân ốc trước khi thay linh kiện mới."
    },
    "CHEMICAL_ISOLATION_FIRST": {
        "name_vn": "Chiến lược Cách ly Hóa học & Khử oxy hóa nguồn điện",
        "description": "Áp dụng cho máy ngấm nước, ẩm mốc. Tuyệt đối cấm cắm sạc, ngắt pin ngay, sấy cồn Isopropyl trước khi đo điện."
    },
    "POWER_RAIL_ISOLATION": {
        "name_vn": "Chiến lược Cô lập Đường nguồn & Trở kháng cuộn cảm",
        "description": "Áp dụng cho sự cố chập cháy, mất nguồn, sập nguồn. Đo trở kháng các đường nguồn trước khi kích nguồn."
    },
    "DIRECT_REPLACEMENT_FLOW": {
        "name_vn": "Chiến lược Thay thế Linh kiện Chuẩn hóa theo cụm",
        "description": "Áp dụng cho hao mòn tự nhiên, linh kiện già cỗi hoặc linh kiện dạng module độc lập."
    },
    "FIRMWARE_RECOVERY_FLOW": {
        "name_vn": "Chiến lược Phục hồi Firmware & Cân chỉnh Tín hiệu",
        "description": "Áp dụng cho lỗi xung đột phần mềm điều khiển, lỗi nạp BIOS hoặc tràn bộ nhớ đệm."
    }
}

class StrategySelector:
    def __init__(self):
        self.version = "1.0"

    def select_strategy(self, complaint: str, fault_code: str, primary_component: str) -> str:
        text_lower = (complaint + " " + fault_code).lower()
        
        # 1. Phát hiện Rơi vỡ / Va chạm cơ học
        if any(w in text_lower for w in ["rơi", "vỡ", "bể", "rớt", "va chạm", "gãy", "móp", "cấn", "drop", "cracked"]):
            return "STRUCTURAL_INTEGRITY_FIRST"
            
        # 2. Phát hiện Vào nước / Ẩm ướt bo mạch
        if any(w in text_lower for w in ["vào nước", "ngập nước", "đổ nước", "ngấm nước", "ướt bo", "nước vào", "bị ẩm", "ẩm mốc", "water damage", "liquid spill", "water ingress"]):
            return "CHEMICAL_ISOLATION_FIRST"

            
        # 3. Phát hiện Chập cháy / Mất nguồn / Mùi khét
        if any(w in text_lower for w in ["khét", "chập", "cháy", "mất nguồn", "không lên", "không nguồn", "nổ", "short", "power"]):
            return "POWER_RAIL_ISOLATION"
            
        # 4. Phát hiện Lỗi Firmware / Treo Logo / BIOS
        if any(w in text_lower for w in ["treo logo", "bios", "firmware", "nhấp nháy", "dump"]):
            return "FIRMWARE_RECOVERY_FLOW"
            
        # 5. Mặc định là Thay thế theo quy chuẩn
        return "DIRECT_REPLACEMENT_FLOW"

strategy_selector = StrategySelector()
