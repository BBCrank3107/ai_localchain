"""
HỆ THỐNG PHỤ TRỢ 1: XÂY DỰNG CƠ SỞ TRI THỨC KỸ THUẬT RAG (SQLITE-VEC)
"""

import os
import sqlite3
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

def build_rag():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manuals_dir = os.path.join(base_dir, "datasets", "manuals")
    db_dir = os.path.join(base_dir, "subsystem_rag", "database")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "rag_database.sqlite")
    
    print(f"📖 Đang quét tài liệu cẩm nang từ: {manuals_dir}")
    documents = []
    
    if os.path.exists(manuals_dir):
        for root, _, files in os.walk(manuals_dir):
            for file in files:
                if file.endswith(".md") or file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                    dev = "dieu_hoa"
                    for d in ["tu_lanh", "may_giat", "laptop", "quat", "tivi", "may_loc_nuoc", "may_in", "may_bom", "noi_com"]:
                        if d in file.lower() or d in root.lower():
                            dev = d
                            break
                            
                    documents.append({
                        "device": dev,
                        "title": file.replace(".md", "").replace("_", " "),
                        "content": content
                    })
                    
    print(f"✅ Đã tìm thấy {len(documents)} tài liệu cẩm nang kỹ thuật!")
    if not documents:
        return
        
    # Tạo Vector Embeddings
    vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
    tfidf_mat = vectorizer.fit_transform([d["title"] + " " + d["content"][:500] for d in documents])
    
    svd = TruncatedSVD(n_components=min(64, len(documents)-1 if len(documents) > 1 else 1))
    dense_vecs = svd.fit_transform(tfidf_mat)
    
    # Chuẩn hóa L2
    norms = np.linalg.norm(dense_vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = dense_vecs / norms
    
    # Lưu vào SQLite
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS manuals")
    cur.execute("""
        CREATE TABLE manuals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT,
            title TEXT,
            content TEXT,
            embedding BLOB
        )
    """)
    
    for i, doc in enumerate(documents):
        emb_bytes = embeddings[i].astype(np.float32).tobytes()
        cur.execute(
            "INSERT INTO manuals (device, title, content, embedding) VALUES (?, ?, ?, ?)",
            (doc["device"], doc["title"], doc["content"], emb_bytes)
        )
        
    conn.commit()
    conn.close()
    
    joblib.dump(vectorizer, os.path.join(db_dir, "rag_vectorizer.pkl"))
    joblib.dump(svd, os.path.join(db_dir, "rag_svd.pkl"))
    
    print(f"🎉 Đã xây dựng Cơ sở Tri thức RAG thành công tại:\n👉 {db_path}")

if __name__ == "__main__":
    build_rag()
