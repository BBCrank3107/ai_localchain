"""
LOCALCHAIN AI V5.2 - KNOWLEDGE & PROCEDURE ENGINE MASTER FACADE
Giao diện trung tâm kết nối toàn bộ hệ sinh thái V5.2:
Graph Expander -> Hybrid Retriever -> Strategy Selector -> Workflow Generator -> Safety Validator -> Risk Scorer -> Renderer.
Cung cấp API tra cứu đồng nhất, tương thích ngược 100% với server_api và nlg_engine.
"""

from typing import Dict, List, Any, Optional
from .expansion.graph_expander import graph_expander
from .retrieval.hybrid_retriever import hybrid_retriever
from .planner.strategy_selector import strategy_selector
from .planner.workflow_generator import workflow_generator
from .renderer.workflow_renderer import workflow_renderer


class LocalChainKnowledgeEngineFacade:
    def __init__(self):
        self.version = "5.2"

    def plan_and_retrieve_repair_workflow(
        self,
        device: str,
        fault_code: str = "",
        primary_component: str = "",
        components: List[str] = None,
        complaint: str = ""
    ) -> Dict[str, Any]:
        """
        Hàm chính điều phối toàn bộ chu trình V5.2:
        1. Mở rộng cụm linh kiện qua 5-Layer Knowledge Graph
        2. Truy xuất tài liệu chứng cứ qua Hybrid Retriever
        3. Hoạch định chiến lược can thiệp qua Strategy Selector
        4. Tổng hợp State Machine DAG Workflow qua Workflow Generator
        5. Kiểm toán qua Pure Audit Safety Validator & Risk Scorer
        6. Render sang Interactive JSON & Vietnamese Markdown
        """
        dev_clean = device.lower().strip()
        comp_primary = primary_component or (components[0] if components else "GENERIC_COMPONENT")
        
        # 1. Knowledge Graph Expansion
        expanded_ctx = graph_expander.expand_diagnosis_context(
            device_id=dev_clean,
            primary_component=comp_primary,
            fault_code=fault_code
        )

        # 2. Hybrid Evidence Retrieval
        evidence_chunks = hybrid_retriever.retrieve_cluster_evidence(
            device_id=dev_clean,
            expanded_cluster=expanded_ctx["expanded_cluster"],
            complaint=complaint,
            top_k=5
        )

        # 3. Strategy Selection
        strategy = strategy_selector.select_strategy(
            complaint=complaint,
            fault_code=fault_code,
            primary_component=comp_primary
        )

        # 4. Workflow DAG Synthesis + Validation + Risk Scoring
        workflow_dsl = workflow_generator.generate_workflow(
            expanded_ctx=expanded_ctx,
            strategy=strategy,
            evidence_chunks=evidence_chunks
        )

        # 5. Rendering Output
        interactive_json = workflow_renderer.render_interactive_json(workflow_dsl)
        vietnamese_report = workflow_renderer.render_vietnamese_markdown(workflow_dsl)

        return {
            "status": "success",
            "engine_version": "5.2",
            "repair_workflow": interactive_json,
            "repair_guide": vietnamese_report,
            "evidence_chunks": evidence_chunks,
            "expanded_context": expanded_ctx,
            "validation_status": workflow_dsl.validation_status,
            "risk_score": workflow_dsl.risk_score
        }

class RAGEngine:
    def __init__(self):
        self.facade = LocalChainKnowledgeEngineFacade()

    def query(self, device_key: str, complaint_text: str, primary_comp: str = "LCD_PANEL") -> str:
        """Trả về cẩm nang kỹ thuật định dạng Markdown chuẩn"""
        res = self.facade.plan_and_retrieve_repair_workflow(
            device=device_key,
            complaint=complaint_text,
            primary_component=primary_comp
        )
        return res.get("repair_guide", "")

    def plan_workflow(self, device: str, fault_code: str = "", primary_component: str = "", components: List[str] = None, complaint: str = "") -> Dict[str, Any]:
        """Trả về toàn bộ object V5.2 Workflow JSON & Report"""
        return self.facade.plan_and_retrieve_repair_workflow(
            device=device,
            fault_code=fault_code,
            primary_component=primary_component,
            components=components,
            complaint=complaint
        )

# Singleton instance
engine_facade = LocalChainKnowledgeEngineFacade()
rag_ai = RAGEngine()

def query_repair_guide(query_text: str, top_k: int = 3) -> Dict[str, Any]:
    """Hàm wrapper tương thích ngược với code cũ"""
    result = engine_facade.plan_and_retrieve_repair_workflow(
        device="laptop",
        complaint=query_text,
        primary_component="LCD_PANEL"
    )
    return {
        "repair_guide": result["repair_guide"],
        "repair_workflow": result["repair_workflow"],
        "source": "LocalChain V5.2 Knowledge & Procedure Engine",
        "matches": result["evidence_chunks"]
    }

