"""
LOCALCHAIN AI V5.2 - AUTOMATED 14-SECTION SEMANTIC CHUNKING & SQLITE KNOWLEDGE BASE BUILDER
Phân rã toàn bộ kho cẩm nang kỹ thuật (manuals + manuals_v2) thành 14 loại Semantic Chunks
kèm siêu dữ liệu chi tiết (Tools, Risk, Voltages, ESD) và nén Embeddings vào SQLite V5.2 Database.
"""

import os
import sys
import re
import json
import sqlite3
import joblib
import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 14 Loại Chunk Nghiệp Vụ Chuẩn
CHUNK_TYPES = [
    "OVERVIEW", "TOOLS", "PARTS", "SAFETY", "PRECHECK", 
    "DISASSEMBLY", "REMOVE_COMPONENT", "INSTALL_COMPONENT", 
    "CALIBRATION", "TESTING", "QUALITY_CHECK", "COMMON_FAILURE", 
    "NOTES", "ERROR_CODE"
]

class SemanticChunkingEngine:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.manuals_dirs = [
            os.path.join(self.base_dir, "datasets", "manuals"),
            os.path.join(self.base_dir, "datasets", "manuals_v2")
        ]
        self.raw_json_dir = os.path.join(self.base_dir, "datasets", "manuals_raw_json")
        self.db_dir = os.path.join(self.base_dir, "subsystem_rag", "database")
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "rag_knowledge_v5.sqlite")
        
    def detect_device_from_filename(self, filename: str, content: str = "") -> str:
        f_lower = filename.lower()
        devices = ["laptop", "dieu_hoa", "may_giat", "tu_lanh", "tivi", "lo_vi_song", "may_in", "may_bom", "quat", "noi_com", "may_loc_nuoc"]
        for d in devices:
            if d in f_lower:
                return d
        c_lower = content[:300].lower()
        for d in devices:
            if d in c_lower:
                return d
        return "laptop"

    def detect_component_ids_from_text(self, text: str) -> List[str]:
        text_upper = text.upper()
        candidates = [
            "LCD_PANEL", "EDP_CABLE", "BACKLIGHT_LED", "METAL_HINGE", "BEZEL", "TOP_CASE", "BOTTOM_CASE",
            "BATTERY_CELL", "DC_JACK", "POWER_IC", "CHARGING_IC", "IO_CHIP", "BIOS_CHIP", "CPU", "GPU", "RAM",
            "FAN", "HEATSINK", "THERMAL_PASTE", "WIFI_CARD", "KEYBOARD", "TOUCHPAD", "SPEAKER",
            "INDOOR_PCB", "OUTDOOR_PCB", "BLOWER_MOTOR", "OUTDOOR_FAN_MOTOR", "INVERTER_COMPRESSOR",
            "PIPE_THERMISTOR", "ROOM_THERMISTOR", "FOUR_WAY_VALVE", "EXPANSION_VALVE", "CAPACITOR",
            "DRAIN_PUMP", "INLET_VALVE", "DOOR_LATCH_SWITCH", "HALL_SENSOR_RPS", "SUSPENSION_RODS", "DRIVE_BELT",
            "FREEZER_FAN", "CONDENSER_FAN", "DEFROST_HEATER", "DEFROST_SENSOR", "BI_METAL", "MAGNETRON",
            "HIGH_VOLTAGE_TRANSFORMER", "HIGH_VOLTAGE_CAPACITOR", "HIGH_VOLTAGE_DIODE", "DOOR_INTERLOCK_SWITCH",
            "FUSER_HEATING_ELEMENT", "PRESSURE_ROLLER", "PICKUP_ROLLER", "ABSORBER_PAD", "MAINBOARD",
            "PUMP_IMPELLER", "START_CAPACITOR", "PRESSURE_SWITCH", "BRASS_BUSHING", "THERMAL_FUSE",
            "LID_THERMISTOR", "BOTTOM_THERMISTOR", "HEATING_PLATE", "RO_MEMBRANE", "SEDIMENT_FILTER", "LOW_PRESSURE_SWITCH"
        ]
        found = []
        for c in candidates:
            # Match component name with words
            clean_c = c.replace("_", " ")
            if c in text_upper or clean_c in text_upper:
                found.append(c)
        return found[:5] if found else ["GENERIC_COMPONENT"]

    def parse_markdown_to_chunks(self, filepath: str) -> List[Dict[str, Any]]:
        filename = os.path.basename(filepath)
        device = self.detect_device_from_filename(filename)
        
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
        except Exception:
            return []
            
        if not raw_text.strip():
            return []
            
        lines = raw_text.split("\n")
        title = lines[0].replace("#", "").strip() if lines else filename
        
        chunks = []
        current_section = "OVERVIEW"
        current_lines = []
        
        # Regex patterns for section headers
        sec_patterns = {
            "SAFETY": re.compile(r"an toàn|khuyến cáo|nguy hiểm|cảnh báo|safety|caution|warning", re.I),
            "TOOLS": re.compile(r"dụng cụ|tools|thiết bị cần", re.I),
            "PARTS": re.compile(r"linh kiện|parts|thay thế", re.I),
            "PRECHECK": re.compile(r"chuẩn bị|yêu cầu tiên quyết|prerequisite|đo đạc", re.I),
            "DISASSEMBLY": re.compile(r"tháo|mở|tách|disassembly|remove|take apart", re.I),
            "INSTALL_COMPONENT": re.compile(r"lắp|gắn|thay mới|install|replace|reassemble", re.I),
            "TESTING": re.compile(r"kiểm tra|test|thử|đo áp|boot|nghiệm thu", re.I),
            "QUALITY_CHECK": re.compile(r"chất lượng|quality|dead pixel|kín khí|tiêu chuẩn", re.I),
            "COMMON_FAILURE": re.compile(r"lỗi thường gặp|sự cố|common failure|troubleshoot", re.I),
            "ERROR_CODE": re.compile(r"mã lỗi|error code|blink|nháy đèn|beep", re.I),
            "NOTES": re.compile(r"lưu ý|notes|bảo dưỡng", re.I)
        }
        
        chunk_idx = 0
        for line in lines:
            if line.startswith("#"):
                # Detect header change
                new_sec = "OVERVIEW"
                for stype, pat in sec_patterns.items():
                    if pat.search(line):
                        new_sec = stype
                        break
                        
                if current_lines:
                    chunk_text = "\n".join(current_lines).strip()
                    if len(chunk_text) > 30:
                        chunks.append({
                            "manual_id": filename,
                            "device": device,
                            "chunk_type": current_section,
                            "chunk_index": chunk_idx,
                            "title": f"{title} - [{current_section}]",
                            "content": chunk_text,
                            "component_ids": self.detect_component_ids_from_text(chunk_text),
                            "risk_level": "HIGH" if current_section == "SAFETY" or "2100V" in chunk_text or "cao áp" in chunk_text else "MEDIUM" if current_section in ["DISASSEMBLY", "INSTALL_COMPONENT"] else "LOW",
                            "need_esd": True if "tĩnh điện" in chunk_text.lower() or "esd" in chunk_text.lower() or device in ["laptop", "tivi"] else False,
                            "need_soldering": True if "hàn" in chunk_text.lower() or "soldering" in chunk_text.lower() else False,
                            "source": "iFixit / OEM Documentation"
                        })
                        chunk_idx += 1
                    current_lines = []
                current_section = new_sec
            current_lines.append(line)
            
        if current_lines:
            chunk_text = "\n".join(current_lines).strip()
            if len(chunk_text) > 30:
                chunks.append({
                    "manual_id": filename,
                    "device": device,
                    "chunk_type": current_section,
                    "chunk_index": chunk_idx,
                    "title": f"{title} - [{current_section}]",
                    "content": chunk_text,
                    "component_ids": self.detect_component_ids_from_text(chunk_text),
                    "risk_level": "MEDIUM",
                    "need_esd": False,
                    "need_soldering": False,
                    "source": "iFixit / OEM Documentation"
                })
                
        return chunks

    def build_and_index(self):
        print("=" * 75)
        print("🧠 BẮT ĐẦU PIPELINE BÓC TÁCH 14-SECTION CHUNKING & NẠP SQLITE V5.2")
        print("=" * 75)
        
        all_chunks = []
        processed_files = set()
        
        for mdir in self.manuals_dirs:
            if not os.path.exists(mdir):
                continue
            print(f"📂 Đang quét thư mục cẩm nang: {mdir}...")
            for root, _, files in os.walk(mdir):
                for f in files:
                    if (f.endswith(".md") or f.endswith(".txt")) and f not in processed_files:
                        fpath = os.path.join(root, f)
                        file_chunks = self.parse_markdown_to_chunks(fpath)
                        all_chunks.extend(file_chunks)
                        processed_files.add(f)
                        
        print(f"\n📊 Tổng hợp: Đã bóc tách thành công {len(all_chunks)} Semantic Chunks từ {len(processed_files)} cẩm nang kỹ thuật!")
        
        if not all_chunks:
            print("⚠️ Không tìm thấy chunks nào để lập chỉ mục.")
            return
            
        # 1. Tạo TF-IDF + SVD Embeddings cho từng chunk
        print("⚡ Đang vector hóa ngữ nghĩa toàn bộ Chunks (TF-IDF + SVD 64D Embeddings)...")
        corpus = [f"{c['device']} {c['chunk_type']} {' '.join(c['component_ids'])} {c['title']} {c['content'][:600]}" for c in all_chunks]
        
        vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2), sublinear_tf=True)
        tfidf_mat = vectorizer.fit_transform(corpus)
        
        svd = TruncatedSVD(n_components=min(64, len(all_chunks) - 1 if len(all_chunks) > 1 else 1), random_state=42)
        dense_vecs = svd.fit_transform(tfidf_mat)
        
        # Chuẩn hóa L2 Norm
        norms = np.linalg.norm(dense_vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = dense_vecs / norms
        
        # 2. Lưu vào SQLite Database V5.2
        print(f"🗄️ Đang ghi {len(all_chunks)} chunks vào SQLite V5.2 Database: {self.db_path}...")
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("DROP TABLE IF EXISTS manual_chunks")
        cur.execute("""
            CREATE TABLE manual_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manual_id TEXT,
                device TEXT,
                chunk_type TEXT,
                chunk_index INTEGER,
                title TEXT,
                content TEXT,
                component_ids TEXT,
                risk_level TEXT,
                need_esd INTEGER,
                need_soldering INTEGER,
                source TEXT,
                embedding BLOB
            )
        """)
        
        for i, c in enumerate(all_chunks):
            emb_bytes = embeddings[i].astype(np.float32).tobytes()
            cur.execute("""
                INSERT INTO manual_chunks (
                    manual_id, device, chunk_type, chunk_index, title, content, 
                    component_ids, risk_level, need_esd, need_soldering, source, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c["manual_id"], c["device"], c["chunk_type"], c["chunk_index"],
                c["title"], c["content"], json.dumps(c["component_ids"], ensure_ascii=False),
                c["risk_level"], 1 if c["need_esd"] else 0, 1 if c["need_soldering"] else 0,
                c["source"], emb_bytes
            ))
            
        conn.commit()
        conn.close()
        
        # 3. Lưu Vectorizer & SVD Models
        joblib.dump(vectorizer, os.path.join(self.db_dir, "rag_v5_vectorizer.pkl"))
        joblib.dump(svd, os.path.join(self.db_dir, "rag_v5_svd.pkl"))
        
        print("\n" + "=" * 75)
        print(f"🎉 HOÀN TẤT XÂY DỰNG KHO TRI THỨC CHUNKS V5.2! ({len(all_chunks)} Chunks trong SQLite)")
        print(f"👉 File Database: {self.db_path}")
        print("=" * 75)

if __name__ == "__main__":
    chunker = SemanticChunkingEngine()
    chunker.build_and_index()
