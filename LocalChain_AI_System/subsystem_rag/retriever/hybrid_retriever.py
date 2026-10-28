"""
LOCALCHAIN AI V5.2 - HYBRID CLUSTER RETRIEVER
Bộ truy xuất kết hợp BM25 + Dense Vector Embeddings qua SQLite V5.2 Database.
Hỗ trợ tái xếp hạng (Re-ranking) theo cụm linh kiện mở rộng từ Knowledge Graph.
"""

import os
import sys
import json
import sqlite3
import joblib
import numpy as np
from typing import Dict, List, Any, Optional

class HybridClusterRetriever:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_dir = os.path.join(self.base_dir, "subsystem_rag", "database")
        self.db_path = os.path.join(self.db_dir, "rag_knowledge_v5.sqlite")
        self.vectorizer_path = os.path.join(self.db_dir, "rag_v5_vectorizer.pkl")
        self.svd_path = os.path.join(self.db_dir, "rag_v5_svd.pkl")
        
        self.vectorizer = None
        self.svd = None
        self._load_models()

    def _load_models(self):
        if os.path.exists(self.vectorizer_path) and os.path.exists(self.svd_path):
            try:
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.svd = joblib.load(self.svd_path)
            except Exception as e:
                print(f"⚠️ Lỗi tải Vectorizer/SVD: {e}")

    def retrieve_cluster_evidence(self, device_id: str, expanded_cluster: List[str], complaint: str = "", top_k: int = 5) -> List[Dict[str, Any]]:
        """Truy xuất các chunk tài liệu liên quan nhất cho toàn bộ cụm linh kiện mở rộng"""
        if not os.path.exists(self.db_path):
            return []
            
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # 1. Lọc theo thiết bị
        cur.execute("""
            SELECT id, manual_id, device, chunk_type, title, content, component_ids, risk_level, embedding 
            FROM manual_chunks 
            WHERE device = ? OR device = 'laptop'
        """, (device_id,))
        rows = cur.fetchall()
        conn.close()
        
        if not rows:
            return []

        # 2. Tính Vector Query nếu có model
        query_text = f"{device_id} {' '.join(expanded_cluster)} {complaint}"
        query_vec = None
        if self.vectorizer and self.svd:
            try:
                tfidf = self.vectorizer.transform([query_text])
                dense = self.svd.transform(tfidf)
                norm = np.linalg.norm(dense)
                if norm > 0:
                    query_vec = (dense / norm)[0]
            except Exception:
                pass

        scored_chunks = []
        cluster_set = set([c.upper() for c in expanded_cluster])
        
        for r in rows:
            cid, mid, dev, ctype, title, content, comp_ids_json, risk, emb_bytes = r
            try:
                comp_ids = json.loads(comp_ids_json)
            except Exception:
                comp_ids = []
                
            # Đánh giá điểm tương đồng Cosine
            sim_score = 0.0
            if query_vec is not None and emb_bytes:
                emb = np.frombuffer(emb_bytes, dtype=np.float32)
                if len(emb) == len(query_vec):
                    sim_score = float(np.dot(query_vec, emb))
                    
            # Boosting nếu chunk thuộc cụm linh kiện mở rộng
            overlap = len(set([c.upper() for c in comp_ids]).intersection(cluster_set))
            cluster_boost = overlap * 0.25
            
            # Boosting nếu là chunk loại quan trọng (SAFETY, DISASSEMBLY, TESTING)
            type_boost = 0.15 if ctype in ["SAFETY", "DISASSEMBLY", "INSTALL_COMPONENT"] else 0.0
            
            final_score = sim_score + cluster_boost + type_boost
            
            scored_chunks.append({
                "id": cid,
                "manual_id": mid,
                "device": dev,
                "chunk_type": ctype,
                "title": title,
                "content": content,
                "component_ids": comp_ids,
                "risk_level": risk,
                "relevance_score": round(final_score, 4)
            })

        # Sắp xếp và lấy top K
        scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_chunks[:top_k]

hybrid_retriever = HybridClusterRetriever()
