"""
LOCALCHAIN AI V5.2 - GENERIC WORKFLOW RENDERER
Bộ chuyển đổi dữ liệu hiển thị trung lập (Device-Agnostic Renderer).
Render RepairWorkflowDSL thành Interactive State Machine JSON và Báo cáo kỹ thuật tiếng Việt.
"""

from typing import Dict, Any
from ..dsl.state_machine_dsl import RepairWorkflowDSL
from ..validator.risk_scorer import risk_scorer

class GenericWorkflowRenderer:
    def __init__(self):
        self.version = "1.0"

    def render_interactive_json(self, workflow: RepairWorkflowDSL) -> Dict[str, Any]:
        """Xuất đối tượng JSON có cấu trúc đầy đủ cho giao diện Web/Mobile"""
        wf_dict = workflow.model_dump()
        risk_meta = risk_scorer.calculate_risk_score(workflow)
        wf_dict["risk_analysis"] = risk_meta
        return wf_dict

    def render_vietnamese_markdown(self, workflow: RepairWorkflowDSL) -> str:
        """Xuất báo cáo kỹ thuật định dạng Markdown chuẩn cho thợ và kỹ thuật viên"""
        meta = workflow.workflow_metadata
        risk_meta = risk_scorer.calculate_risk_score(workflow)
        
        from ..knowledge_graph.device_knowledge_graph import TOPOLOGY_KNOWLEDGE_SSOT
        from ..knowledge_graph.localization_dict import LOCALIZATION_MAP
        
        ui_map = LOCALIZATION_MAP.copy()
        
        for d in TOPOLOGY_KNOWLEDGE_SSOT.values():
            for s in d.get("subsystems", {}).values():
                for a in s.get("assemblies", {}).values():
                    for cid, cdata in a.get("components", {}).items():
                        ui_map[cid] = cdata["name_vn"]
                        
        def get_vn(k): return ui_map.get(k, k) if k else k

        import re
        def translate_text(text):
            if not text: return text
            keys = sorted(ui_map.keys(), key=len, reverse=True)
            res = text
            for k in keys:
                res = re.sub(rf'\b{k}\b', ui_map[k], res)
            return res
        
        md = []
        md.append(f"# 🛠️ QUY TRÌNH KỸ THUẬT SỬA CHỮA CHUẨN HOÁ (V5.2)")
        md.append(f"> **Mã Workflow:** `{meta.workflow_id}` | **Phiên bản DSL:** `v{meta.dsl_version}` | **Graph:** `v{meta.knowledge_graph_version}`")
        md.append("")
        
        # Risk Badge
        status_icon = "🟢" if workflow.validation_status == "PASS" else "🟡" if workflow.validation_status == "WARNING" else "🔴"
        md.append(f"### 🛡️ Đánh Giá An Toàn & Rủi Ro Kỹ Thuật:")
        md.append(f"- **Trạng thái kiểm toán:** {status_icon} **{workflow.validation_status}**")
        md.append(f"- **Chỉ số rủi ro:** **{workflow.risk_score}/100** ({risk_meta['risk_rating']})")
        md.append(f"- **Khuyến cáo người dùng:** {risk_meta['user_guidance']}")
        md.append(f"- **Chiến lược áp dụng:** `{get_vn(meta.strategy_applied)}`")
        md.append(f"- **Thời gian ước tính:** ~{meta.estimated_duration_minutes} phút | **Trình độ yêu cầu:** `{get_vn(meta.required_skill_level)}`")
        md.append("")

        # Safety Prerequisites
        if workflow.safety_prerequisites:
            md.append("### ⚠️ Tiên Quyết An Toàn Bắt Buộc:")
            for p in workflow.safety_prerequisites:
                md.append(f"- 🔴 **[{get_vn(p.rule_code)}]** {p.audit_checkpoint} (Thao tác: `{get_vn(p.operation)}`)")
            md.append("")

        # State Machine DAG Execution Sequence
        md.append("### 📋 Các Bước Thực Thi Theo Đồ Thị Trạng Thái (DAG):")
        
        for i, s in enumerate(workflow.states, 1):
            md.append(f"#### Bước {i}: [{get_vn(s.phase)}] `{get_vn(s.state_id)}`")
            md.append(f"- **Thao tác:** `{get_vn(s.action)}` | **Đối tượng:** `{get_vn(s.target)}` ({s.assembly})")
            if s.tools:
                mapped_tools = [get_vn(t) for t in s.tools]
                md.append(f"- 🔧 **Dụng cụ:** {', '.join(mapped_tools)}")
            if s.voltage_checkpoint:
                md.append(f"- ⚡ **Mức áp đo kiểm:** `{s.voltage_checkpoint}`")
            md.append(f"- 📝 **Chỉ dẫn kỹ thuật:** {translate_text(s.instruction_vn)}")
            
            if s.transitions:
                md.append("- 🔀 **Điều kiện rẽ nhánh:**")
                for t in s.transitions:
                    if t.condition:
                        md.append(f"  * Nếu `{get_vn(t.condition)}` ({t.condition_description_vn}) 👉 Chuyển sang `{get_vn(t.next_state)}`")
                    elif t.event:
                        md.append(f"  * Khi sự kiện `{get_vn(t.event)}` hoàn tất 👉 Chuyển sang `{get_vn(t.next_state)}`")
            md.append("")

        # Audit Log
        if workflow.audit_log:
            md.append("### 🔍 Nhật Ký Kiểm Toán An Toàn (Audit Trail):")
            for log in workflow.audit_log:
                md.append(f"- `{log}`")
                
        return "\n".join(md)

workflow_renderer = GenericWorkflowRenderer()
