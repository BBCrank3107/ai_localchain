"""
LOCALCHAIN AI V5.2 - STATE MACHINE DAG REPAIR WORKFLOW DSL
Pydantic Schemas định nghĩa Ngôn ngữ Quy trình Sửa chữa chuẩn Đồ thị Trạng thái (State Machine DAG).
Hỗ trợ đầy đủ Versioning, Transition Conditions, Voltage Checkpoints và Audit Checks.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class WorkflowMetadata(BaseModel):
    workflow_id: str = Field(..., description="ID định danh duy nhất của workflow")
    dsl_version: str = Field(default="2.2", description="Phiên bản ngôn ngữ DSL")
    knowledge_graph_version: str = Field(default="5.2", description="Phiên bản Graph tri thức")
    planner_version: str = Field(default="1.0", description="Phiên bản bộ lập kế hoạch")
    validator_version: str = Field(default="1.0", description="Phiên bản bộ kiểm toán")
    device_id: str = Field(..., description="Thiết bị mục tiêu (laptop, tivi...)")
    fault_code: str = Field(..., description="Mã sự cố chẩn đoán từ Model 2")
    strategy_applied: str = Field(..., description="Chiến lược sửa chữa được áp dụng")
    estimated_duration_minutes: int = Field(default=45, description="Thời gian ước tính (phút)")
    required_skill_level: str = Field(default="BASIC_TECH", description="Cấp độ kỹ thuật viên yêu cầu")

class SafetyPrerequisite(BaseModel):
    rule_code: str = Field(..., description="Mã quy tắc an toàn (REQ_POWER_OFF, REQ_BATTERY_ISOLATION)")
    operation: str = Field(..., description="Thao tác thực thi (DISCONNECT_AC, UNPLUG_BATTERY)")
    mandatory: bool = Field(default=True, description="Bắt buộc phải thực hiện")
    audit_checkpoint: str = Field(..., description="Tiêu chí kiểm toán an toàn")

class StateTransition(BaseModel):
    condition: Optional[str] = Field(None, description="Điều kiện logic (VOLTAGE_NORMAL, CABLE_SEVERED)")
    condition_description_vn: Optional[str] = Field(None, description="Mô tả điều kiện tiếng Việt")
    event: Optional[str] = Field(None, description="Sự kiện kích hoạt chuyển trạng thái")
    next_state: Optional[str] = Field(None, description="ID của State tiếp theo (None nếu là trạng thái kết thúc)")

class DAGStateNode(BaseModel):
    state_id: str = Field(..., description="ID của trạng thái (STATE_INSPECT_CABLE...)")
    phase: str = Field(..., description="Giai đoạn: SAFETY_PREREQUISITE, INSPECTION, REPAIR, VERIFICATION, QUALITY, DELIVERY")
    action: str = Field(..., description="Hành động kỹ thuật (MEASURE_CONTINUITY, SWAP_COMPONENT...)")
    target: Optional[str] = Field(None, description="Linh kiện hoặc đường mạch mục tiêu")
    assembly: Optional[str] = Field(None, description="Cụm lắp ráp liên quan")
    tools: List[str] = Field(default_factory=list, description="Dụng cụ yêu cầu cho trạng thái này")
    voltage_checkpoint: Optional[str] = Field(None, description="Mức điện áp đo kiểm mong đợi")
    instruction_vn: str = Field(..., description="Chỉ dẫn kỹ thuật chi tiết bằng tiếng Việt")
    transitions: List[StateTransition] = Field(default_factory=list, description="Các nhánh rẽ trạng thái")

class RepairWorkflowDSL(BaseModel):
    workflow_metadata: WorkflowMetadata
    safety_prerequisites: List[SafetyPrerequisite] = Field(default_factory=list)
    initial_state: str = Field(..., description="Trạng thái khởi đầu của State Machine")
    states: List[DAGStateNode] = Field(default_factory=list, description="Toàn bộ các nút trạng thái trong DAG")
    validation_status: Optional[str] = Field(default="PENDING", description="Trạng thái kiểm toán: PASS / WARNING / BLOCK / FAIL")
    risk_score: Optional[int] = Field(default=0, description="Chỉ số nguy hiểm kỹ thuật (0 - 100)")
    audit_log: List[str] = Field(default_factory=list, description="Nhật ký kiểm toán an toàn")
