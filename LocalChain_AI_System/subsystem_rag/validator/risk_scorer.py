"""
LOCALCHAIN AI V5.2 - INDEPENDENT RISK SCORER
Bộ đo lường chỉ số nguy hiểm kỹ thuật (0 - 100 Risk Score).
Độc lập với Safety Validator để cung cấp khuyến nghị an toàn trực quan cho người dùng và giao diện Frontend.
"""

from typing import Dict, Any
from ..dsl.state_machine_dsl import RepairWorkflowDSL

class TechnicalRiskScorer:
    def __init__(self):
        self.version = "1.0"

    def calculate_risk_score(self, workflow: RepairWorkflowDSL) -> Dict[str, Any]:
        score = 10 # Base score for opening any electronics
        reasons = []
        device = workflow.workflow_metadata.device_id.lower()
        
        # 1. Yếu tố Điện áp cực cao & Nguy hiểm chết người
        if device == "lo_vi_song" or any("MAGNETRON" in (s.target or "") for s in workflow.states):
            score += 75
            reasons.append("⚡ Điện áp biến áp cao tần cực lớn (2100V - 4000V DC) có thể gây giật chết người ngay lập tức.")
        elif device in ["dieu_hoa", "may_giat", "tu_lanh", "may_bom"]:
            score += 30
            reasons.append("⚡ Điện áp nguồn lưới xoay chiều 220V AC công suất lớn.")
        elif device in ["tivi"]:
            score += 25
            reasons.append("⚡ Điện áp nguồn sơ cấp và cao áp LED Driver (100V - 300V DC).")

        # 2. Yếu tố Môi chất hóa học & Gas cháy nổ
        if device in ["dieu_hoa", "tu_lanh"] and any("GAS" in s.action or "COMPRESSOR" in (s.target or "") for s in workflow.states):
            score += 20
            reasons.append("🔥 Môi chất lạnh R32/R600a có tính bắt lửa hoặc áp suất cao (lên tới 450 PSI).")

        # 3. Yếu tố Pin Lithium & Chập cháy
        if any("BATTERY" in (s.target or "") for s in workflow.states):
            score += 15
            reasons.append("🔋 Khối pin Lithium tiềm ẩn nguy cơ quá nhiệt hoặc cháy nổ nếu bị thủng/uốn cong.")

        # 4. Yếu tố Yêu cầu kỹ năng chuyên môn
        skill = workflow.workflow_metadata.required_skill_level
        if skill in ["LICENSED_HVAC_TECH", "ADVANCED_SMD_TECH"]:
            score += 15
            reasons.append("🛠️ Yêu cầu kỹ thuật viên có chứng chỉ chuyên môn hoặc thiết bị đo đạc phòng lab chuyên dụng.")

        # Giới hạn thang điểm 0 - 100
        score = min(100, max(0, score))

        # Phân loại mức độ cảnh báo
        if score >= 80:
            rating = "EXTREME_DANGER"
            user_guidance = "🔴 NGUY HIỂM CAO - KHÔNG TỰ SỬA TẠI NHÀ: Bắt buộc kết nối kỹ thuật viên chuyên nghiệp có chứng chỉ an toàn."
        elif score >= 55:
            rating = "HIGH"
            user_guidance = "🟠 RỦI RO KỸ THUẬT CAO: Chỉ thực hiện nếu bạn có đồ nghề bảo hộ, đồng hồ VOM và am hiểu điện cơ bản."
        elif score >= 30:
            rating = "MEDIUM"
            user_guidance = "🟡 RỦI RO TRUNG BÌNH: Có thể tự thực hiện theo đúng từng bước của cẩm nang, chú ý ngắt nguồn điện."
        else:
            rating = "LOW"
            user_guidance = "🟢 AN TOÀN / MỨC ĐỘ DỄ: Người dùng hoàn toàn có thể tự thao tác tháo lắp tại nhà."

        return {
            "risk_score": score,
            "risk_rating": rating,
            "user_guidance": user_guidance,
            "risk_factors": reasons
        }

risk_scorer = TechnicalRiskScorer()
