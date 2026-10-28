"""
LOCALCHAIN AI V5.2 - 5-LAYER KNOWLEDGE & CAPABILITY GRAPH SCHEMA
Định nghĩa cấu trúc phân tầng 5 lớp:
Layer 1: Device -> Layer 2: Subsystem -> Layer 3: Assembly -> Layer 4: Component -> Layer 5: Capability / Operation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from enum import Enum

class SkillLevel(str, Enum):
    USER_SELF_REPAIR = "USER_SELF_REPAIR"      # Người dùng có thể tự thực hiện
    BASIC_TECH = "BASIC_TECH"                  # Thợ sơ cấp, kỹ thuật viên phổ thông
    ADVANCED_SMD_TECH = "ADVANCED_SMD_TECH"    # Kỹ thuật viên vi mạch chuyên sâu
    LICENSED_HVAC_TECH = "LICENSED_HVAC_TECH"  # Kỹ thuật viên có chứng chỉ an toàn (Gas R32/Cao áp)

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME_DANGER = "EXTREME_DANGER"

@dataclass
class OperationNode:
    """Layer 5: Thao tác kỹ thuật cụ thể gán vào linh kiện"""
    operation_id: str                          # Ví dụ: MEASURE_VOLTAGE, SWAP_COMPONENT
    name_vn: str                               # Tên tiếng Việt: Đo điện áp nguồn
    action_type: str                           # INSPECTION, REMOVE, INSTALL, CALIBRATE, TEST
    required_tools: List[str] = field(default_factory=list)
    voltage_checkpoint: Optional[str] = None   # Ví dụ: 19V DC, 3.3V, 220V AC
    expected_impedance: Optional[str] = None   # Ví dụ: > 10kΩ, 20kΩ ở 25°C
    safety_rule_code: Optional[str] = None     # Ví dụ: REQ_BATTERY_ISOLATION
    description_vn: str = ""

@dataclass
class ComponentNode:
    """Layer 4: Linh kiện phần cứng"""
    component_id: str                          # Ví dụ: LCD_PANEL, EDP_CABLE, MAGNETRON
    name_vn: str                               # Tấm nền LCD, Cáp tín hiệu eDP
    assembly_id: str                           # Thuộc cụm Assembly nào
    voltage_rails: List[str] = field(default_factory=list)     # 19V_VBL, 3.3V_LCDVDD
    signal_lines: List[str] = field(default_factory=list)      # eDP_LANE0..3, AUX_CH
    allowed_operations: List[str] = field(default_factory=list) # Danh sách OperationNode IDs hợp lệ
    blocked_operations: List[str] = field(default_factory=list) # Các thao tác cấm (Anti-pattern)
    required_tools: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)             # ESD_SENSITIVE, HIGH_VOLTAGE
    skill_required: SkillLevel = SkillLevel.BASIC_TECH

@dataclass
class AssemblyNode:
    """Layer 3: Cụm lắp ráp kỹ thuật"""
    assembly_id: str                           # Ví dụ: DISPLAY_PANEL_ASSEMBLY, HINGE_ASSEMBLY
    name_vn: str                               # Cụm màn hình và bản lề
    subsystem_id: str                          # Thuộc phân hệ nào
    components: List[str] = field(default_factory=list)        # Danh sách Component IDs trong cụm
    disassembly_sequence: List[str] = field(default_factory=list) # Thứ tự tháo rời tiêu chuẩn
    required_tools: List[str] = field(default_factory=list)

@dataclass
class SubsystemNode:
    """Layer 2: Phân hệ chức năng của thiết bị"""
    subsystem_id: str                          # Ví dụ: DISPLAY_SUBSYSTEM, POWER_SUBSYSTEM
    name_vn: str                               # Phân hệ hiển thị, Phân hệ nguồn
    device_id: str                             # Thuộc thiết bị nào (laptop, tivi...)
    assemblies: List[str] = field(default_factory=list)        # Danh sách Assembly IDs

@dataclass
class DeviceTopology:
    """Layer 1: Toàn bộ cấu trúc topo của 1 thiết bị"""
    device_id: str                             # laptop, dieu_hoa, may_giat...
    device_name_vn: str
    subsystems: Dict[str, SubsystemNode] = field(default_factory=dict)
    assemblies: Dict[str, AssemblyNode] = field(default_factory=dict)
    components: Dict[str, ComponentNode] = field(default_factory=dict)
    operations: Dict[str, OperationNode] = field(default_factory=dict)
