"""
LOCALCHAIN AI V5.2 - KNOWLEDGE GRAPH EXPANDER
Tự động mở rộng cụm linh kiện liên đới (Cluster Topology Expansion) từ chẩn đoán Model 2
trước khi chuyển sang bộ tìm kiếm tài liệu (Retriever) và bộ lập kế hoạch (Planner).
"""

from typing import Dict, List, Any, Optional
from ..knowledge_graph.device_knowledge_graph import device_kg

class GraphExpander:
    def __init__(self):
        self.kg = device_kg

    def expand_diagnosis_context(self, device_id: str, primary_component: str, fault_code: str = "") -> Dict[str, Any]:
        """
        Mở rộng ngữ cảnh kỹ thuật:
        - Primary component -> Sibling components trong cùng cụm Assembly
        - Tổng hợp danh mục công cụ, đường điện áp, đường tín hiệu và cảnh báo nguy hiểm
        """
        cluster_components = self.kg.expand_component_cluster(device_id, primary_component)
        top = self.kg.get_topology(device_id)
        
        all_tools = set()
        all_voltages = set()
        all_signals = set()
        all_risks = set()
        assembly_name = "Cụm tiêu chuẩn"
        skill_level = "BASIC_TECH"
        
        if top:
            parent_asm = self.kg.find_parent_assembly(device_id, primary_component)
            if parent_asm:
                assembly_name = parent_asm.name_vn
                all_tools.update(parent_asm.required_tools)
                
            for c_id in cluster_components:
                comp = top.components.get(c_id)
                if comp:
                    all_tools.update(comp.required_tools)
                    all_voltages.update(comp.voltage_rails)
                    all_signals.update(comp.signal_lines)
                    all_risks.update(comp.risks)
                    if comp.skill_required.value == "LICENSED_HVAC_TECH" or comp.skill_required.value == "ADVANCED_SMD_TECH":
                        skill_level = comp.skill_required.value
                        
        return {
            "device_id": device_id,
            "primary_component": primary_component,
            "fault_code": fault_code,
            "assembly_name": assembly_name,
            "expanded_cluster": cluster_components,
            "aggregated_tools": sorted(list(all_tools)),
            "aggregated_voltages": sorted(list(all_voltages)),
            "aggregated_signals": sorted(list(all_signals)),
            "aggregated_risks": sorted(list(all_risks)),
            "skill_level_required": skill_level
        }

graph_expander = GraphExpander()
