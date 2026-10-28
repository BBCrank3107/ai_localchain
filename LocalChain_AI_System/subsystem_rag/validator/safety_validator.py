"""
LOCALCHAIN AI V5.2 - PURE AUDIT SAFETY VALIDATOR
Bộ kiểm toán an toàn thuần túy (Pure Audit Safety Guardrail).
Tuyệt đối không tự ý sửa đổi code Workflow DSL để giữ trọn vẹn Audit Trail.
Trả về: PASS, WARNING, BLOCK, FAIL kèm mã lỗi vi phạm.
"""

from typing import Dict, List, Any
from ..dsl.state_machine_dsl import RepairWorkflowDSL

class PureAuditSafetyValidator:
    def __init__(self):
        self.version = "1.0"

    def validate_workflow(self, workflow: RepairWorkflowDSL) -> Dict[str, Any]:
        violations = []
        warnings = []
        device = workflow.workflow_metadata.device_id.lower()
        
        # 1. Kiểm toán Tính Toàn Vẹn Của Đồ Thị (DAG Structural Integrity)
        state_ids = {s.state_id for s in workflow.states}
        if workflow.initial_state not in state_ids:
            violations.append({
                "code": "ERR_INVALID_INITIAL_STATE",
                "severity": "FAIL",
                "message": f"Trạng thái khởi đầu '{workflow.initial_state}' không tồn tại trong danh sách states."
            })
            
        for state in workflow.states:
            for trans in state.transitions:
                if trans.next_state and trans.next_state not in state_ids:
                    violations.append({
                        "code": "ERR_BROKEN_TRANSITION",
                        "severity": "FAIL",
                        "message": f"State '{state.state_id}' rẽ nhánh tới next_state không tồn tại: '{trans.next_state}'."
                    })

        # 2. Kiểm toán Quy Tắc Cách Ly Nguồn Điện (Power Isolation Rule)
        has_power_isolation = False
        for pre in workflow.safety_prerequisites:
            if "POWER" in pre.rule_code or "BATTERY" in pre.rule_code or "DISCONNECT" in pre.operation:
                has_power_isolation = True
                break
                
        if not has_power_isolation:
            for state in workflow.states[:2]:
                if "POWER" in state.action or "DISCONNECT" in state.action:
                    has_power_isolation = True
                    break
                    
        if not has_power_isolation:
            violations.append({
                "code": "ERR_MISSING_POWER_ISOLATION",
                "severity": "BLOCK",
                "message": "Vi phạm an toàn nghiêm trọng: Quy trình sửa chữa phần cứng thiếu bước ngắt nguồn/cách ly pin bắt buộc."
            })

        # 3. Kiểm toán Thiết Bị Cao Áp (Lò vi sóng - 2100V-4000V)
        if device == "lo_vi_song":
            has_hv_discharge = False
            for state in workflow.states:
                if "DISCHARGE" in state.action or "HV" in str(state.tools) or "xả tụ" in state.instruction_vn.lower():
                    has_hv_discharge = True
                    break
            if not has_hv_discharge:
                violations.append({
                    "code": "ERR_MISSING_HV_CAPACITOR_DISCHARGE",
                    "severity": "BLOCK",
                    "message": "Nguy hiểm chết người: Sửa chữa lò vi sóng bắt buộc phải có bước xả tụ cao áp 2100V."
                })
            else:
                warnings.append({
                    "code": "WARN_HIGH_VOLTAGE_MICROWAVE",
                    "message": "Thiết bị có điện áp cực cao (2100V-4000V). Yêu cầu kỹ thuật viên có đồ bảo hộ cách điện."
                })

        # 4. Kiểm toán Thiết Bị Môi Chất Lạnh Gas Áp Suất Cao (Điều hòa / Tủ lạnh)
        if device in ["dieu_hoa", "tu_lanh"]:
            has_vacuum_or_pressure = any("PRESSURE" in s.action or "VACUUM" in s.action or "GAS" in s.action for s in workflow.states)
            if has_vacuum_or_pressure:
                warnings.append({
                    "code": "WARN_FLAMMABLE_REFRIGERANT_R32",
                    "message": "Thao tác trên đường ống gas R32/R410A yêu cầu kiểm tra kín khí và không dùng nguồn nhiệt hở."
                })

        # Đánh giá trạng thái cuối cùng
        if any(v["severity"] == "FAIL" for v in violations):
            status = "FAIL"
        elif any(v["severity"] == "BLOCK" for v in violations):
            status = "BLOCK"
        elif warnings:
            status = "WARNING"
        else:
            status = "PASS"

        audit_log = [f"[{v['severity']}] {v['code']}: {v['message']}" for v in violations]
        audit_log.extend([f"[WARNING] {w['code']}: {w['message']}" for w in warnings])
        if not audit_log:
            audit_log.append("[PASS] Quy trình vượt qua 100% tiêu chí an toàn và cấu trúc đồ thị.")

        return {
            "status": status,
            "violations": violations,
            "warnings": warnings,
            "audit_log": audit_log
        }

safety_validator = PureAuditSafetyValidator()
