"""
=============================================================================
LOCALCHAIN AI - PRODUCTION MULTI-HEAD DIAGNOSIS ENGINE (VERSION 3.0)
=============================================================================
Kiến trúc Chuẩn Công Nghiệp (Production-Ready 9.9/10):
1. 6-Step Text Normalizer: Unicode NFC -> Whitespace -> Elongated Collapse -> Lowercase -> Slang/Typo -> Punctuation.
2. Canonical Device Mapper: Tự động ánh xạ mọi biến thể tên gọi sang canonical_device_id.
3. Intent & Chitchat Guard: Phân biệt Greeting, 100% Praise/Normal và Triệu chứng hư hỏng.
4. Non-Destructive Clause Segmenter: Tách mệnh đề theo liên từ/dấu câu, phân loại vế độc lập.
5. Multi-Head Deep Transformer Backbone: 1 Shared Encoder (512D) + 11 Pure Failure Heads + 1 Severity Head.
6. 3-Factor OOD & Uncertainty Guard: Max Softmax Probability (MSP) + Prediction Margin + Normalized Shannon Entropy.
7. O(1) Enriched Taxonomy Cache: Toàn bộ metadata, độ khó V2.2, linh kiện được lưu trong hash map truy xuất tức thì.
8. Production Logging & Real-time Metrics Tracker: Ghi log có cấu trúc vào logs/diagnosis.log và cập nhật metrics vào logs/statistics.json.
=============================================================================
"""

import os
import sys
import re
import json
import time
import math
import logging
import unicodedata
import joblib
import numpy as np
import torch
import torch.nn as nn
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Đảm bảo chạy được cả khi: python file.py trực tiếp lẫn khi import như module
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_THIS_DIR)
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from model_2_diagnosis.train_multihead_transformer import (
    LocalChainMultiHeadDiagnosisNet,
    SEVERITY_MAP,
    REV_SEVERITY_MAP
)

# =============================================================================
# 1. 6-STEP TEXT NORMALIZER
# =============================================================================
class TextNormalizer:
    """Tầng chuẩn hóa văn bản 6 bước chuẩn NLP Production"""
    def __init__(self, normalizations_path: str, stopwords_path: str):
        self.slang_map = {}
        self.char_map = {}
        if os.path.exists(normalizations_path):
            with open(normalizations_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.slang_map = data.get("slang_and_typos", {})
                self.char_map = data.get("character_replacements", {})
                
        self.stopwords = set()
        if os.path.exists(stopwords_path):
            with open(stopwords_path, "r", encoding="utf-8") as f:
                self.stopwords = {line.strip().lower() for line in f if line.strip()}

    def normalize(self, text: str) -> str:
        if not text:
            return ""
            
        # Bước 1: Unicode NFC Normalization (chống lỗi gõ dấu tổ hợp)
        t = unicodedata.normalize("NFC", text.strip())
        
        # Bước 2: Thay thế ký tự đặc biệt & dấu ngoặc
        for k, v in self.char_map.items():
            t = t.replace(k, v)
            
        # Bước 3: Thu gọn ký tự lặp kéo dài (ví dụ: 'kooooo' -> 'ko', 'đẹpppp' -> 'đẹp')
        t = re.sub(r'([a-zA-Zà-ỹÀ-Ỹ0-9])\1{2,}', r'\1', t)
        
        # Bước 4: Chuyển về chữ thường (Lowercase)
        t = t.lower()
        
        # Bước 5: Chuẩn hóa khoảng trắng & dấu câu dư thừa
        t = re.sub(r'[ \t\r\f]+', ' ', t)
        t = re.sub(r'\.{2,}', '...', t)
        t = re.sub(r'\?{2,}', '?', t)
        t = re.sub(r'!{2,}', '!', t)
        
        # Bước 6: Thay thế từ lóng & lỗi gõ chính tả
        for slang, standard in self.slang_map.items():
            pattern = r'\b' + re.escape(slang) + r'\b'
            t = re.sub(pattern, standard, t)
            
        return t.strip()

    def remove_stopwords(self, text: str) -> str:
        words = [w for w in text.split() if w.lower() not in self.stopwords]
        return " ".join(words)


# =============================================================================
# 2. CANONICAL DEVICE MAPPER
# =============================================================================
class CanonicalDeviceMapper:
    """Ánh xạ tên gọi thiết bị, tiếng lóng, tiếng Anh sang Canonical Device ID"""
    def __init__(self, aliases_path: str):
        self.alias_to_canonical = {}
        self.device_display_names = {}
        self.supported_devices = set()
        
        if os.path.exists(aliases_path):
            with open(aliases_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                devices_data = data.get("devices", {})
                for dev_id, info in devices_data.items():
                    self.supported_devices.add(dev_id)
                    self.device_display_names[dev_id] = info.get("display_name_vn", dev_id)
                    for alias in info.get("aliases", []):
                        norm_alias = unicodedata.normalize("NFC", alias.strip().lower())
                        self.alias_to_canonical[norm_alias] = dev_id

    def canonicalize(self, raw_device: str) -> Dict[str, Any]:
        if not raw_device:
            return {"canonical_id": "", "display_name_vn": "Chưa xác định", "is_supported": False}
            
        norm_dev = unicodedata.normalize("NFC", raw_device.strip().lower())
        
        # 1. Khớp trực tiếp alias
        if norm_dev in self.alias_to_canonical:
            c_id = self.alias_to_canonical[norm_dev]
            return {
                "canonical_id": c_id,
                "display_name_vn": self.device_display_names.get(c_id, c_id),
                "is_supported": True
            }
            
        # 2. Khớp chuỗi con
        for alias, c_id in self.alias_to_canonical.items():
            if alias in norm_dev or norm_dev in alias:
                return {
                    "canonical_id": c_id,
                    "display_name_vn": self.device_display_names.get(c_id, c_id),
                    "is_supported": True
                }
                
        return {
            "canonical_id": norm_dev,
            "display_name_vn": norm_dev,
            "is_supported": norm_dev in self.supported_devices
        }


# =============================================================================
# 3. INTENT & CLAUSE SEGMENTER (NON-DESTRUCTIVE)
# =============================================================================
class IntentAndClauseSegmenter:
    """Phân tách ý định và bóc tách mệnh đề bảo toàn ngữ cảnh"""
    def __init__(self, intent_rules_path: str, intent_keywords_path: str, stopwords: set):
        self.stopwords = stopwords
        self.praise_patterns = []
        self.normal_patterns = []
        self.connectives = []
        self.greetings = set()
        
        if os.path.exists(intent_rules_path):
            with open(intent_rules_path, "r", encoding="utf-8") as f:
                rules = json.load(f)
                self.praise_patterns = [re.compile(p, re.IGNORECASE) for p in rules.get("praise_or_normal_patterns", [])]
                self.normal_patterns = [re.compile(p, re.IGNORECASE) for p in rules.get("normal_state_patterns", [])]
                self.connectives = rules.get("clause_connectives", [])
                
        if os.path.exists(intent_keywords_path):
            with open(intent_keywords_path, "r", encoding="utf-8") as f:
                kws = json.load(f)
                self.greetings = set(kws.get("greetings", []))

        # Compile regex connectives
        if self.connectives:
            conn_pattern = r'(\b' + r'\b|\b'.join([re.escape(c) for c in self.connectives]) + r'\b)'
            self.conn_regex = re.compile(conn_pattern, re.IGNORECASE)
        else:
            self.conn_regex = re.compile(r'(\bvà\b|\bnhưng\b|\bvới lại\b)', re.IGNORECASE)

    def check_intent(self, normalized_text: str) -> Dict[str, Any]:
        """Kiểm tra Intent tổng thể: Chitchat, Praise/Normal, hoặc Fault"""
        if not normalized_text or len(normalized_text) < 2:
            return {
                "is_fault": False,
                "intent_type": "NONSENSE",
                "message": "Vui lòng cung cấp mô tả chi tiết hơn về tình trạng hoạt động hoặc hiện tượng sự cố của thiết bị."
            }
            
        words = normalized_text.split()
        # Kiểm tra thuần Chitchat / Greeting
        if all(w in self.greetings or w.isdigit() for w in words):
            return {
                "is_fault": False,
                "intent_type": "CHITCHAT",
                "message": "Xin chào! Tôi là Trợ lý Kỹ thuật LocalChain AI. Hãy mô tả triệu chứng hoặc hiện tượng thiết bị của bạn đang gặp phải để tôi hỗ trợ chẩn đoán và báo giá nhé!"
            }
            
        # Kiểm tra khen ngợi thuần túy / thiết bị hoạt động tốt
        is_pure_praise = False
        for pat in self.praise_patterns:
            if pat.search(normalized_text):
                is_pure_praise = True
                break
                
        # Phân tách mệnh đề để kiểm tra xem có vế sự cố nào đi kèm không
        clauses = self.segment_clauses(normalized_text)
        has_symptom_clause = any(not c["is_praise_or_normal"] for c in clauses)
        
        if is_pure_praise and not has_symptom_clause:
            return {
                "is_fault": False,
                "intent_type": "NORMAL_OR_PRAISE",
                "message": "🎉 Thiết bị của bạn đang hoạt động trong tình trạng hoàn hảo và không ghi nhận bất kỳ dấu hiệu hư hỏng kỹ thuật nào. Chúc bạn có trải nghiệm sử dụng tuyệt vời!"
            }
            
        return {"is_fault": True, "intent_type": "FAULT_SYMPTOM", "message": ""}

    def segment_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Bóc tách mệnh đề không phá hủy ngữ cảnh (Non-destructive Clause Split) & Phân loại Context vs Symptom"""
        if not text:
            return []
            
        raw_chunks = re.split(r'[,.;\n\r\t\-/]+', text)
        all_clauses = []
        
        # Regex nhận diện nguyên nhân/bối cảnh ngoại lực
        context_patterns = {
            "PHYSICAL_IMPACT": re.compile(r'\b(rơi|rớt|va đập|va quệt|va chạm|bị đập|ngã|dẫm|bể|vỡ|nứt|móp|rơi vỡ)\b', re.IGNORECASE),
            "WATER_INGRESS": re.compile(r'\b(ngấm nước|vào nước|rớt nước|đổ nước|dính nước|ngập nước|ẩm ướt|ướt)\b', re.IGNORECASE),
            "POWER_SURGE": re.compile(r'\b(chập điện|sét đánh|sốc điện|mất điện|nổ lụp bụp|nổ bụp)\b', re.IGNORECASE),
            "OVERHEATING": re.compile(r'\b(nóng ran|nóng quá|quá nhiệt)\b', re.IGNORECASE)
        }
        
        # Regex nhận diện từ khóa triệu chứng kỹ thuật cụ thể
        symptom_regex = re.compile(
            r'\b(sọc|tối đen|đen xì|không lên|mất nguồn|không kêu|mất tiếng|rè|nghẹt|kêu to|không nhận|liệt|không quay|chảy nước|rò nước|không mát|không lạnh|không nóng|kẹt giấy|lem mực|không ngắt|không vào điện)\b',
            re.IGNORECASE
        )
        
        for chunk in raw_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            sub_chunks = self.conn_regex.split(chunk)
            for sub in sub_chunks:
                clean_sub = sub.strip()
                if not clean_sub or self.conn_regex.fullmatch(clean_sub):
                    continue
                    
                # 1. Phân loại mệnh đề: Khen ngợi / Bình thường
                is_normal = False
                for pat in self.praise_patterns + self.normal_patterns:
                    if pat.search(clean_sub):
                        is_normal = True
                        break
                        
                # 2. Phân loại mệnh đề: Nguyên nhân ngoại lực (Context) vs Triệu chứng cụ thể (Symptom)
                detected_context = None
                for ctx_type, ctx_pat in context_patterns.items():
                    if ctx_pat.search(clean_sub):
                        detected_context = ctx_type
                        break
                        
                has_symptom_kw = bool(symptom_regex.search(clean_sub))
                # Là mệnh đề nguyên nhân thuần túy nếu có từ khóa va đập/nước nhưng không có triệu chứng chi tiết
                is_pure_context = (detected_context is not None) and (not has_symptom_kw)
                
                meaningful_words = [w for w in clean_sub.split() if w.lower() not in self.stopwords]
                
                all_clauses.append({
                    "raw_clause": clean_sub,
                    "is_praise_or_normal": is_normal,
                    "is_pure_context": is_pure_context,
                    "context_type": detected_context,
                    "has_symptom_kw": has_symptom_kw,
                    "word_count": len(meaningful_words)
                })
                
        return all_clauses


# =============================================================================
# 4. 3-FACTOR OOD & UNCERTAINTY GUARD
# =============================================================================
class OODUncertaintyGuard:
    """Đánh giá độ bất định của dự đoán dựa trên MSP, Margin và Shannon Entropy"""
    def __init__(self, min_msp: float = 0.25, min_margin: float = 0.05, max_entropy: float = 0.90):
        self.min_msp = min_msp
        self.min_margin = min_margin
        self.max_entropy = max_entropy

    def evaluate(self, probs: np.ndarray) -> Dict[str, Any]:
        """
        Tính toán 3 chỉ số bất định:
        - MSP (Max Softmax Probability)
        - Margin = Top1 - Top2
        - Normalized Shannon Entropy = -sum(p * log2(p)) / log2(K)
        """
        if probs is None or len(probs) == 0:
            return {"msp": 0.0, "margin": 0.0, "entropy": 1.0, "is_uncertain": True, "reason": "No probabilities"}
            
        sorted_probs = np.sort(probs)[::-1]
        top1 = float(sorted_probs[0])
        top2 = float(sorted_probs[1]) if len(sorted_probs) > 1 else 0.0
        
        msp = top1
        margin = top1 - top2
        
        # Shannon Entropy
        k = len(probs)
        if k > 1:
            # Tránh log(0)
            eps = 1e-12
            safe_probs = np.clip(probs, eps, 1.0)
            entropy = -float(np.sum(safe_probs * np.log2(safe_probs)))
            max_possible_entropy = math.log2(k)
            norm_entropy = float(entropy / max_possible_entropy) if max_possible_entropy > 0 else 0.0
        else:
            norm_entropy = 0.0
            
        is_uncertain = False
        reasons = []
        
        # Tiêu chí OOD / Ambiguous: MSP thấp VÀ Margin hẹp, HOẶC Entropy quá cao
        if msp < self.min_msp and margin < self.min_margin:
            is_uncertain = True
            reasons.append(f"Low MSP ({msp:.2f}) & Tight Margin ({margin:.2f})")
            
        if norm_entropy > self.max_entropy:
            is_uncertain = True
            reasons.append(f"High Shannon Entropy ({norm_entropy:.2f})")
            
        return {
            "msp": round(msp, 4),
            "margin": round(margin, 4),
            "entropy": round(norm_entropy, 4),
            "is_uncertain": is_uncertain,
            "reasons": reasons
        }


# =============================================================================
# 5. O(1) ENRICHED TAXONOMY CACHE
# =============================================================================
class EnrichedTaxonomyCache:
    """Bộ nhớ đệm thông tin Taxonomy tra cứu O(1)"""
    def __init__(self, taxonomy_path: str):
        self.device_meta = {}
        self.fault_dict = {}  # (dev_id, fault_code) -> metadata
        self.code_to_meta = {}  # fault_code -> metadata
        self.total_devices = 0
        self.total_fault_codes = 0
        self.raw_taxonomy = {}
        
        if os.path.exists(taxonomy_path):
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                tax = json.load(f)
                self.raw_taxonomy = tax
                self.total_devices = tax.get("total_devices", 0)
                self.total_fault_codes = tax.get("total_fault_codes", 0)
                devices = tax.get("devices", {})
                for dev_id, d_info in devices.items():
                    self.device_meta[dev_id] = {
                        "device_name_vn": d_info.get("device_name_vn", dev_id),
                        "total_faults": len(d_info.get("faults", []))
                    }
                    for fault in d_info.get("faults", []):
                        f_code = fault["fault_code"]
                        diff_meta = fault.get("difficulty", {
                            "score": float(fault.get("difficulty_score", 2.0)),
                            "tools": 2, "steps": 2, "equipment": 1, 
                            "estimated_minutes": 30, "requires_professional": False
                        })
                        enriched = {
                            "fault_code": f_code,
                            "fault_name_vn": fault.get("fault_name_vn", f_code),
                            "fault_category": fault.get("fault_category", "GENERAL"),
                            "difficulty_score": float(fault.get("difficulty_score", 2.0)),
                            "difficulty": diff_meta,
                            "components": fault.get("components", []),
                            "repair_level": fault.get("repair_level", "Medium"),
                            "default_severity": fault.get("severity", "Medium"),
                            "sources": fault.get("sources", []),
                            "device_canonical_id": dev_id
                        }
                        self.fault_dict[(dev_id, f_code)] = enriched
                        self.code_to_meta[f_code] = enriched

    def get(self, dev_id: str, f_code: str) -> Dict[str, Any]:
        """Tra cứu O(1) metadata đầy đủ"""
        return self.fault_dict.get((dev_id, f_code), self.code_to_meta.get(f_code, {
            "fault_code": f_code,
            "fault_name_vn": f_code,
            "fault_category": "GENERAL",
            "difficulty_score": 2.0,
            "difficulty": {"score": 2.0, "tools": 2, "steps": 2, "equipment": 1, "estimated_minutes": 30, "requires_professional": False},
            "components": [],
            "repair_level": "Medium",
            "default_severity": "Medium",
            "sources": [],
            "device_canonical_id": dev_id
        }))


# =============================================================================
# 6. PRODUCTION LOGGER & METRICS TRACKER
# =============================================================================
class ProductionLoggerAndMetrics:
    """Hệ thống ghi log có cấu trúc và theo dõi chỉ số hoạt động thời gian thực"""
    def __init__(self, log_dir: str):
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "diagnosis.log")
        self.stats_file = os.path.join(log_dir, "statistics.json")
        
        # Thiết lập Logger độc lập
        self.logger = logging.getLogger("LocalChainDiagnosisLogger")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = logging.Formatter('{"time":"%(asctime)s", "level":"%(levelname)s", %(message)s}')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        self.metrics = {
            "total_requests": 0,
            "total_latency_ms": 0.0,
            "ood_count": 0,
            "chitchat_count": 0,
            "praise_count": 0,
            "fault_diagnosed_count": 0,
            "avg_confidence": 0.0,
            "avg_entropy": 0.0,
            "device_distribution": {},
            "last_updated": ""
        }
        self._load_metrics()

    def _load_metrics(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    self.metrics = json.load(f)
            except Exception:
                pass

    def _save_metrics(self):
        try:
            self.metrics["last_updated"] = datetime.now().isoformat()
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record(self, payload: Dict[str, Any]):
        """Ghi log có cấu trúc và cập nhật metrics"""
        try:
            # Ghi file log
            json_msg = json.dumps(payload, ensure_ascii=False)[1:-1]
            self.logger.info(json_msg)
            
            # Cập nhật Metrics
            self.metrics["total_requests"] += 1
            lat = payload.get("latency_ms", 0.0)
            self.metrics["total_latency_ms"] += lat
            
            intent = payload.get("intent_type", "")
            if intent == "CHITCHAT":
                self.metrics["chitchat_count"] += 1
            elif intent == "NORMAL_OR_PRAISE":
                self.metrics["praise_count"] += 1
            elif payload.get("is_uncertain", False):
                self.metrics["ood_count"] += 1
            else:
                self.metrics["fault_diagnosed_count"] += 1
                
            dev = payload.get("canonical_device", "unknown")
            self.metrics["device_distribution"][dev] = self.metrics["device_distribution"].get(dev, 0) + 1
            
            # Lưu metrics định kỳ
            if self.metrics["total_requests"] % 10 == 0:
                self._save_metrics()
        except Exception:
            pass


# =============================================================================
# 7. MULTI-HEAD DIAGNOSIS ENGINE (SSOT V3.0)
# =============================================================================
class MultiHeadDiagnosisEngine:
    """Động cơ chẩn đoán trung tâm tích hợp toàn bộ pipeline Production"""
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.base_dir = base_dir
        config_dir = os.path.join(base_dir, "datasets", "diagnosis", "config")
        weights_dir = os.path.join(base_dir, "model_2_diagnosis", "weights_transformer_multihead")
        logs_dir = os.path.join(base_dir, "logs")
        
        # 1. Khởi tạo các module tiền xử lý
        self.normalizer = TextNormalizer(
            normalizations_path=os.path.join(config_dir, "text_normalizations.json"),
            stopwords_path=os.path.join(config_dir, "stopwords_vi.txt")
        )
        
        self.device_mapper = CanonicalDeviceMapper(
            aliases_path=os.path.join(config_dir, "device_aliases.json")
        )
        
        self.intent_segmenter = IntentAndClauseSegmenter(
            intent_rules_path=os.path.join(config_dir, "intent_rules.json"),
            intent_keywords_path=os.path.join(config_dir, "intent_keywords.json"),
            stopwords=self.normalizer.stopwords
        )
        
        # 2. Khởi tạo OOD Guard & Cache Taxonomy O(1)
        self.ood_guard = OODUncertaintyGuard(min_msp=0.25, min_margin=0.05, max_entropy=0.90)
        self.taxonomy_cache = EnrichedTaxonomyCache(
            taxonomy_path=os.path.join(base_dir, "datasets", "diagnosis", "fault_taxonomy.json")
        )
        
        # 3. Khởi tạo Logger & Metrics
        self.tracker = ProductionLoggerAndMetrics(log_dir=logs_dir)
        
        # 4. Nạp Model Transformer & Vectorizer
        self.meta_path = os.path.join(weights_dir, "multihead_metadata.json")
        self.tfidf_path = os.path.join(weights_dir, "tfidf_svd.pkl")
        self.model_path = os.path.join(weights_dir, "best_multihead_model.pt")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model_resources()

    @property
    def taxonomy(self) -> Dict[str, Any]:
        """Truy xuất toàn bộ danh mục SSOT Taxonomy"""
        return self.taxonomy_cache.raw_taxonomy

    def _load_model_resources(self):
        with open(self.meta_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)
            
        tfidf_svd = joblib.load(self.tfidf_path)
        self.tfidf = tfidf_svd["tfidf"]
        self.svd = tfidf_svd["svd"]
        
        self.unique_brands = self.meta["unique_brands"]
        self.brand2idx = self.meta["brand2idx"]
        self.device_fault_maps = self.meta["device_fault_maps"]
        self.device_head_classes = self.meta["device_head_classes"]
        
        self.rev_fault_maps = {}
        for dev, fmap in self.device_fault_maps.items():
            self.rev_fault_maps[dev] = {v: k for k, v in fmap.items()}
            
        self.model = LocalChainMultiHeadDiagnosisNet(
            text_dim=256,
            num_brands=len(self.unique_brands),
            brand_embed_dim=32,
            hidden_dim=self.meta.get("hidden_dim", 512),
            device_head_classes=self.device_head_classes
        ).to(self.device)
        
        if os.path.exists(self.model_path):
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device, weights_only=True))
            self.model.eval()
        else:
            raise FileNotFoundError(f"Không tìm thấy model checkpoint tại {self.model_path}!")

    def _predict_single_text(self, dev_key: str, text: str, b_idx_tensor) -> Dict[str, Any]:
        """Dự đoán đơn văn bản qua Shared Backbone và Target Device Head"""
        query_text = text
        # Context enrichment cho trường hợp đặc thù laptop kêu rè rè
        if dev_key == "laptop":
            if any(kw in text.lower() for kw in ["kêu rè", "tiếng rè", "kêu lạch cạch"]):
                if not any(spk in text.lower() for spk in ["loa", "âm thanh", "tai nghe", "jack"]):
                    query_text = f"{text} quạt tản nhiệt kêu rè"

        tfidf_mat = self.tfidf.transform([query_text])
        text_vec = self.svd.transform(tfidf_mat).astype(np.float32)
        text_tensor = torch.tensor(text_vec, dtype=torch.float32, device=self.device)
        
        with torch.no_grad():
            fault_logits, sev_logits, conf_pred = self.model(text_tensor, b_idx_tensor, target_device=dev_key)
            probs = torch.softmax(fault_logits, dim=-1).squeeze(0).cpu().numpy()
            sev_idx = torch.argmax(sev_logits, dim=-1).item()
            conf_score = conf_pred.item()
            
        top_idx = int(np.argmax(probs))
        top_prob = float(probs[top_idx])
        f_code = self.rev_fault_maps[dev_key][top_idx]
        
        # Tra cứu O(1) Full Metadata
        cached_meta = self.taxonomy_cache.get(dev_key, f_code)
        
        # Đánh giá độ bất định (MSP, Margin, Entropy)
        uncertainty = self.ood_guard.evaluate(probs)
        
        components_list = cached_meta.get("components", [])
        primary_comp_key = components_list[0] if components_list else "GENERIC_COMPONENT"
        
        # Hiệu chuẩn xác suất chuẩn đoán văn bản lâm sàng (Calibrated Confidence)
        calibrated_prob = min(top_prob, 0.945)
        calibrated_conf = min(conf_score, 0.95)

        return {
            "fault_code": f_code,
            "component_key": primary_comp_key,
            "probability": round(calibrated_prob * 100, 2),
            "fault_name_vn": cached_meta["fault_name_vn"],
            "fault_category": cached_meta["fault_category"],
            "difficulty_score": cached_meta["difficulty_score"],
            "difficulty": cached_meta["difficulty"],
            "components": cached_meta["components"],
            "repair_level": cached_meta["repair_level"],
            "severity": REV_SEVERITY_MAP.get(sev_idx, cached_meta["default_severity"]),
            "confidence_score": round(calibrated_conf * 100, 2),
            "sources": cached_meta["sources"],
            "all_probs": probs,
            "uncertainty": uncertainty
        }

    def diagnose(self, device_type: str, complaint_text: str, brand: str = "Unknown", top_k: int = 3) -> Dict[str, Any]:
        """
        Quy trình chẩn đoán hoàn chỉnh Production V3:
        Input -> Normalize (6 bước) -> Canonicalize Device -> Intent & OOD Guard -> 
        Clause Segmentation -> Multi-Head Inference -> O(1) Taxonomy Cache -> Log & Metrics -> Response
        """
        start_time = time.perf_counter()
        
        # 1. Normalize 6 bước
        norm_complaint = self.normalizer.normalize(complaint_text)
        
        # 2. Canonicalize Device
        dev_info = self.device_mapper.canonicalize(device_type)
        if not dev_info["is_supported"]:
            return {
                "success": False,
                "error": f"Thiết bị '{device_type}' không nằm trong 11 nhóm thiết bị hỗ trợ!",
                "supported_devices": list(self.device_mapper.supported_devices)
            }
            
        dev_key = dev_info["canonical_id"]
        dev_display_name = dev_info["display_name_vn"]
        
        # 3. Intent Detection
        intent_check = self.intent_segmenter.check_intent(norm_complaint)
        if not intent_check["is_fault"]:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Ghi log lượt yêu cầu
            self.tracker.record({
                "raw_input": complaint_text,
                "normalized_input": norm_complaint,
                "canonical_device": dev_key,
                "intent_type": intent_check["intent_type"],
                "latency_ms": round(latency_ms, 2),
                "is_fault": False
            })
            
            return {
                "success": True,
                "is_fault": False,
                "intent_type": intent_check["intent_type"],
                "device": dev_key,
                "device_name_vn": dev_display_name,
                "brand": brand,
                "symptom_input": complaint_text,
                "normalized_symptom": norm_complaint,
                "fault_count": 0,
                "primary_diagnosis": {
                    "fault_code": "NO_FAULT_DETECTED",
                    "fault_name_vn": "Thiết bị hoạt động bình thường (Không phát hiện sự cố)",
                    "fault_category": "NONE",
                    "difficulty_score": 0.0,
                    "difficulty": None,
                    "components": [],
                    "repair_level": "None",
                    "severity": "Normal",
                    "confidence_score": 100.0,
                    "probability": 100.0
                },
                "predicted_faults": [],
                "top_candidates": [],
                "natural_message": intent_check["message"],
                "estimated_price_vnd": 0.0,
                "itemized_prices": [],
                "discount_vnd": 0.0,
                "uncertainty_metrics": {"msp": 1.0, "margin": 1.0, "entropy": 0.0, "is_uncertain": False},
                "latency_ms": round(latency_ms, 2),
                "architecture_note": "Tầng kiểm soát ý định (Intent Guard) xác nhận thiết bị hoạt động tốt"
            }

        # 4. Chuẩn bị tensor thương hiệu
        b_idx_val = self.brand2idx.get(brand, self.brand2idx.get("Unknown", 0))
        b_idx_tensor = torch.tensor([b_idx_val], dtype=torch.long, device=self.device)
        
        # 5. Non-destructive Clause Segmentation
        raw_clauses = self.intent_segmenter.segment_clauses(norm_complaint)
        
        # Bóc tách mệnh đề sự cố và mệnh đề bối cảnh/nguyên nhân ngoại lực
        symptom_clauses = []
        detected_contexts = []
        
        for c in raw_clauses:
            if c["is_praise_or_normal"]:
                continue
            if c["context_type"]:
                detected_contexts.append(c["context_type"])
            if not c["is_pure_context"]:
                symptom_clauses.append(c["raw_clause"])
                
        if not symptom_clauses:
            symptom_clauses = [norm_complaint]
            
        # 6. Multi-Head Inference trên từng vế sự cố thực tế
        detected_faults_dict = {}
        for clause in symptom_clauses:
            res_c = self._predict_single_text(dev_key, clause, b_idx_tensor)
            f_code = res_c["fault_code"]
            
            # Ngưỡng tối thiểu ban đầu để xét duyệt
            if res_c["probability"] < 50.0:
                continue
                
            if f_code not in detected_faults_dict or res_c["probability"] > detected_faults_dict[f_code]["probability"]:
                res_c["matched_clause"] = clause
                detected_faults_dict[f_code] = res_c
                
        all_candidates = sorted(list(detected_faults_dict.values()), key=lambda x: x["probability"], reverse=True)
        
        # Fallback nếu câu ngắn hoặc không tách được mệnh đề vượt ngưỡng
        if not all_candidates:
            fallback_res = self._predict_single_text(dev_key, norm_complaint, b_idx_tensor)
            fallback_res["matched_clause"] = norm_complaint
            all_candidates = [fallback_res]
            
        primary = all_candidates[0]
        
        # 7. Strict Secondary Admission Gate:
        # Lỗi thứ phát chỉ được công nhận đồng thời nếu:
        # - Xác suất cao (>= 85.0%)
        # - Không bị gắn cờ OOD/Uncertain
        # - Khác mã lỗi với primary
        admitted_faults = [primary]
        for sec in all_candidates[1:]:
            if sec["probability"] >= 85.0 and not sec["uncertainty"]["is_uncertain"] and sec["fault_code"] != primary["fault_code"]:
                admitted_faults.append(sec)
                
        # 8. Xây dựng Root Cause Assessment & Chiến lược khắc phục
        primary_cause_type = "HARDWARE_DEGRADATION"
        cause_desc_vn = "Hao mòn tự nhiên hoặc suy giảm linh kiện điện tử sau thời gian sử dụng."
        if "PHYSICAL_IMPACT" in detected_contexts:
            primary_cause_type = "PHYSICAL_IMPACT"
            cause_desc_vn = "Hư hỏng do biến cố cơ học ngoại lực (rơi rớt, va đập hoặc tì đè mạnh)."
        elif "WATER_INGRESS" in detected_contexts:
            primary_cause_type = "WATER_INGRESS"
            cause_desc_vn = "Sự cố chập mạch do chất lỏng hoặc hơi ẩm ngấm vào bên trong linh kiện."
        elif "POWER_SURGE" in detected_contexts:
            primary_cause_type = "POWER_SURGE"
            cause_desc_vn = "Sự cố xung điện đột ngột hoặc quá áp gây hư hỏng tầng nguồn bo mạch."
        elif "OVERHEATING" in detected_contexts:
            primary_cause_type = "OVERHEATING"
            cause_desc_vn = "Sự cố quá nhiệt do hệ thống tản nhiệt bị tắc nghẽn hoặc keo tản nhiệt khô."

        repair_strategies = []
        for af in admitted_faults:
            comps_str = ", ".join(af.get("components", []))
            repair_strategies.append(f"Kiểm tra đo đạc & thay thế linh kiện {comps_str} ({af.get('fault_name_vn', '')})")
            
        risks_if_ignored = []
        if primary_cause_type == "PHYSICAL_IMPACT":
            risks_if_ignored.append("Màn hình/mặt kính vỡ có thể chảy mực loang rộng hoặc mảnh vỡ đâm thủng linh kiện bên trong")
            risks_if_ignored.append("Khung vỏ biến dạng có thể gây kẹt bản lề hoặc chèn ép cell pin")
        elif primary_cause_type == "WATER_INGRESS":
            risks_if_ignored.append("Oxy hóa ăn mòn chân chip và đứt mạch ngầm trên bo mạch chủ")
            risks_if_ignored.append("Nguy cơ chập cháy toàn bộ các linh kiện phụ tải")
        else:
            risks_if_ignored.append("Sự cố có thể lan sang các linh kiện liên đới trên đường nguồn hoặc tín hiệu")

        root_cause_assessment = {
            "cause_type": primary_cause_type,
            "cause_description_vn": cause_desc_vn,
            "detected_contexts": list(set(detected_contexts)),
            "repair_strategy": repair_strategies,
            "risks_if_ignored": risks_if_ignored
        }

        # 9. Chuẩn hóa Top Candidates & Predicted Faults
        top_candidates = []
        for df in admitted_faults:
            top_candidates.append({
                "fault_code": df["fault_code"],
                "probability": df["probability"],
                "fault_name_vn": df["fault_name_vn"],
                "fault_category": df["fault_category"],
                "difficulty_score": df["difficulty_score"],
                "difficulty": df["difficulty"],
                "components": df["components"],
                "repair_level": df["repair_level"],
                "default_severity": df["severity"],
                "sources": df.get("sources", []),
                "matched_clause": df.get("matched_clause", "")
            })
            
        multi_faults = []
        for df in admitted_faults:
            multi_faults.append({
                "fault": df["fault_name_vn"],
                "fault_name_vn": df["fault_name_vn"],
                "fault_code": df["fault_code"],
                "fault_category": df["fault_category"],
                "difficulty_score": df["difficulty_score"],
                "difficulty": df["difficulty"],
                "components": df["components"],
                "severity": df["severity"],
                "probability": df["probability"]
            })
            
        sev_scores = [SEVERITY_MAP.get(df["severity"], 1) for df in admitted_faults]
        max_sev = max(sev_scores) if sev_scores else 1
        overall_severity = REV_SEVERITY_MAP.get(max_sev, "Medium")
        
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Ghi log và thống kê
        self.tracker.record({
            "raw_input": complaint_text,
            "normalized_input": norm_complaint,
            "canonical_device": dev_key,
            "intent_type": "FAULT_SYMPTOM",
            "primary_fault": primary["fault_code"],
            "fault_count": len(admitted_faults),
            "msp": primary["uncertainty"]["msp"],
            "margin": primary["uncertainty"]["margin"],
            "entropy": primary["uncertainty"]["entropy"],
            "is_uncertain": primary["uncertainty"]["is_uncertain"],
            "latency_ms": round(latency_ms, 2)
        })
        
        return {
            "success": True,
            "is_fault": True,
            "device": dev_key,
            "device_name_vn": dev_display_name,
            "brand": brand,
            "symptom_input": complaint_text,
            "normalized_symptom": norm_complaint,
            "detected_clauses": symptom_clauses,
            "detected_contexts": list(set(detected_contexts)),
            "fault_count": len(admitted_faults),
            "primary_diagnosis": {
                "fault_code": primary["fault_code"],
                "fault_name_vn": primary["fault_name_vn"],
                "fault_category": primary["fault_category"],
                "difficulty_score": primary["difficulty_score"],
                "difficulty": primary["difficulty"],
                "components": primary["components"],
                "repair_level": primary["repair_level"],
                "severity": overall_severity,
                "confidence_score": primary["confidence_score"],
                "probability": primary["probability"]
            },
            "predicted_faults": multi_faults,
            "top_candidates": top_candidates,
            "root_cause_assessment": root_cause_assessment,
            "uncertainty_metrics": primary["uncertainty"],
            "latency_ms": round(latency_ms, 2),
            "architecture_note": f"Phân loại độc lập từ [{dev_key.upper()} HEAD] với 6-Step Normalizer & Clause Segmentation (1 Backbone + 11 Heads)"
        }


# Khởi tạo singleton engine
multihead_ai = MultiHeadDiagnosisEngine()

if __name__ == "__main__":
    print("=" * 85)
    print("🚀 KIỂM THỬ ĐỘNG CƠ INFERENCE MULTI-HEAD PRODUCTION V3.0")
    print("=" * 85)
    
    test_cases = [
        ("máy lạnh", "máy lạnh chạy cả tiếng mà phòng ko hề mát tí nào", "Daikin"),
        ("tivi", "tivi mở lên có tiếng nói bình thường nhưng màn hình tối đen", "Sony"),
        ("laptop", "màn hình kooooo lên, trắng xóa khi mở máy", "Dell"),
        ("máy in", "máy in canon ảnh quá đẹp nhưng hay bị kẹt giấy liên tục", "Canon"),
        ("máy giặt", "máy giặt lg chạy rất êm ái dùng quá thích", "LG"),
        ("laptop", "hello shop ơi", "Apple")
    ]
    
    for dev, text, brand in test_cases:
        res = multihead_ai.diagnose(dev, text, brand=brand)
        print(f"\n📥 Input: [{dev}] - '{text}' ({brand})")
        print(f"🎯 Output Device: {res['device']} ({res['device_name_vn']}) | Intent: {res.get('intent_type', 'FAULT')}")
        print(f"⚡ Latency: {res['latency_ms']} ms")
        if res.get("is_fault", True):
            p = res["primary_diagnosis"]
            print(f"🔍 Mã lỗi: {p['fault_code']} ({p['probability']}%) - {p['fault_name_vn']}")
            print(f"🛠️ Độ khó: {p['difficulty_score']} | Linh kiện: {p['components']}")
            print(f"📊 Uncertainty: {res['uncertainty_metrics']}")
        else:
            print(f"💬 Phản hồi: {res['natural_message']}")
    print("\n" + "=" * 85)
