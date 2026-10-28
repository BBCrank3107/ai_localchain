# -*- coding: utf-8 -*-
"""
FEATURE BUILDER LAYER CHO MODEL 3 (PRICING ENGINE V3.1 - ENTERPRISE SSOT)
Tự động tra cứu O(1) từ 4 tệp SSOT Knowledge Base trong RAM và tạo véc-tơ đặc trưng tách rời (Decoupled)
cho Component Model và Labor Model.
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Phân nhóm Brand Tiers chuẩn A / B / C
BRAND_TIERS_MAP = {
    # Tier A: Premium
    "A": [
        "apple", "macbook", "imac", "iphone", "ipad", "sony", "bravia", "daikin", 
        "bosch", "mitsubishi", "dyson", "hitachi", "dell xps", "alienware",
        "canon", "nikon", "fujifilm", "delonghi", "breville", "brother", "garmin"
    ],
    # Tier B: Standard / Mid-range
    "B": [
        "asus", "dell", "hp", "acer", "lenovo", "thinkpad", "msi", "panasonic", 
        "samsung", "lg", "toshiba", "sharp", "canon", "brother", "epson", "electrolux",
        "aqua", "philips", "kangaroo", "karofi", "sunhouse", "cuckoo",
        "xiaomi", "oppo", "makita", "dewalt", "milwaukee", "jbl", "marshall", 
        "gemilai", "singer", "juki", "benq"
    ],
    # Tier C: Budget / Value
    "C": [
        "midea", "casper", "asanzo", "funiki", "gree", "nagakawa", "senko", 
        "vinawind", "asia", "panworld", "sananky", "sanaky", "generic", "khác"
    ]
}

class PricingFeatureBuilder:
    """
    Trích xuất và xây dựng đặc trưng Decoupled cho Dual-Model Pricing V3.1
    Tải 4 tệp SSOT 1 lần duy nhất vào bộ nhớ RAM (In-Memory Cache) cho tốc độ O(1).
    """
    _instance = None
    _is_loaded = False

    def __init__(self, pricing_dir: Optional[str] = None):
        if pricing_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.pricing_dir = os.path.join(base_dir, "datasets", "pricing")
            self.taxonomy_path = os.path.join(base_dir, "datasets", "diagnosis", "fault_taxonomy.json")
        else:
            self.pricing_dir = pricing_dir
            self.taxonomy_path = os.path.join(os.path.dirname(pricing_dir), "diagnosis", "fault_taxonomy.json")

        self.component_db: Dict[str, Any] = {}
        self.labor_db: Dict[str, Any] = {}
        self.warranty_policy: Dict[str, int] = {}
        self.pricing_stats: Dict[str, Any] = {}
        self.service_db: Dict[str, Any] = {}
        self.fault_to_component_cache: Dict[str, str] = {}
        
        self.load_once()

    def load_once(self):
        """Tải toàn bộ SSOT Knowledge Base vào RAM 1 lần duy nhất"""
        if self._is_loaded and self.component_db:
            return

        comp_path = os.path.join(self.pricing_dir, "component_market_db.json")
        labor_path = os.path.join(self.pricing_dir, "labor_market_db.json")
        warr_path = os.path.join(self.pricing_dir, "warranty_policy.json")
        stats_path = os.path.join(self.pricing_dir, "pricing_statistics.json")
        service_path = os.path.join(self.pricing_dir, "service_market_db.json")

        if os.path.exists(comp_path):
            with open(comp_path, "r", encoding="utf-8") as f:
                self.component_db = json.load(f)

        if os.path.exists(labor_path):
            with open(labor_path, "r", encoding="utf-8") as f:
                self.labor_db = json.load(f)

        if os.path.exists(warr_path):
            with open(warr_path, "r", encoding="utf-8") as f:
                self.warranty_policy = json.load(f)

        if os.path.exists(stats_path):
            with open(stats_path, "r", encoding="utf-8") as f:
                self.pricing_stats = json.load(f)

        if os.path.exists(service_path):
            with open(service_path, "r", encoding="utf-8") as f:
                self.service_db = json.load(f)

        # Mapping fault_code -> primary_component từ taxonomy
        if os.path.exists(self.taxonomy_path):
            with open(self.taxonomy_path, "r", encoding="utf-8") as f:
                tax = json.load(f)
                devices = tax.get("devices", tax)
                for dev_id, d_info in devices.items():
                    if not isinstance(d_info, dict):
                        continue
                    for fault in d_info.get("faults", []):
                        f_code = fault.get("fault_code", "")
                        comps = fault.get("components", [])
                        prim = comps[0] if comps else "GENERIC_MODULE"
                        self.fault_to_component_cache[f_code] = prim

        self._is_loaded = True

    def resolve_brand_tier(self, brand: str) -> str:
        """Phân loại phân khúc thương hiệu (A / B / C)"""
        if not brand or brand.strip().lower() in ["unknown", "string", "none", ""]:
            return "B"
            
        b_clean = brand.strip().lower()
        for p_brand in BRAND_TIERS_MAP["A"]:
            if p_brand in b_clean:
                return "A"
                
        for b_brand in BRAND_TIERS_MAP["C"]:
            if b_brand in b_clean:
                return "C"
                
        return "B"

    def resolve_region_class(self, region: str) -> str:
        """Phân loại vùng miền (Metro / Urban / Province)"""
        if not region:
            return "Metro"
        r_clean = region.strip().lower()
        if any(m in r_clean for m in ["hà nội", "ha noi", "hcm", "hồ chí minh", "ho chi minh", "hn", "metro"]):
            return "Metro"
        if any(u in r_clean for u in ["đà nẵng", "da nang", "hải phòng", "hai phong", "cần thơ", "can tho", "urban"]):
            return "Urban"
        return "Province"

    def build_features(
        self,
        fault_code: str,
        brand: Optional[str] = "Generic",
        action_type: Optional[str] = "replace",
        part_type: Optional[str] = "OEM",
        component_condition: Optional[str] = "NEW",
        region: Optional[str] = "Metro",
        custom_component_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tra cứu O(1) và sinh ra feature dict đầy đủ cho 2 Model Component & Labor
        """
        # 1. Xác định Component ID
        component_id = custom_component_id or self.fault_to_component_cache.get(fault_code, "GENERIC_MODULE")
        if component_id not in self.component_db:
            # Fallback component
            component_id = list(self.component_db.keys())[0] if self.component_db else "LCD_PANEL"

        comp_meta = self.component_db.get(component_id, {})
        comp_name_vn = comp_meta.get("component_name_vn", component_id)
        base_replace = comp_meta.get("baseline_replace_price", 800000.0)
        base_repair = comp_meta.get("baseline_repair_price", 300000.0)
        baseline_comp = base_replace if action_type == "replace" else base_repair
        availability = comp_meta.get("availability", "Normal")
        market_age = comp_meta.get("market_age_days", 180)

        brand_clean = (brand or "Generic").capitalize()
        brand_tier = self.resolve_brand_tier(brand_clean)
        part_type_clean = part_type if part_type in ["Genuine", "OEM", "Aftermarket"] else "OEM"
        condition_clean = component_condition if component_condition in ["NEW", "REFURBISHED", "USED"] else "NEW"
        region_class = self.resolve_region_class(region)

        # 2. Xây dựng Component Features Dict
        comp_feat_dict = {
            "component_id": component_id,
            "brand": brand_clean,
            "brand_tier": brand_tier,
            "part_type": part_type_clean,
            "availability": availability,
            "component_condition": condition_clean,
            "action_type": action_type,
            "baseline_price_vnd": baseline_comp,
            "market_age_days": market_age
        }

        # 3. Xác định Labor Meta từ labor_db
        labor_meta = self.labor_db.get(fault_code, {})
        dev_id = labor_meta.get("device_id", "laptop")
        diff_score = labor_meta.get("difficulty_score", 2.0)
        est_mins = labor_meta.get("estimated_minutes", 30)
        tools = labor_meta.get("tools_count", 2)
        req_pro = 1 if labor_meta.get("requires_professional", False) else 0
        disasm = labor_meta.get("disassembly_level", 2)
        waterproof = labor_meta.get("waterproof_level", 0)
        base_labor = labor_meta.get("base_labor_vnd", 150000.0)

        # 4. Xây dựng Labor Features Dict
        labor_feat_dict = {
            "device_id": dev_id,
            "region_class": region_class,
            "action_type": action_type,
            "base_labor_vnd": base_labor,
            "difficulty_score": diff_score,
            "estimated_minutes": est_mins,
            "tools_count": tools,
            "requires_professional": req_pro,
            "disassembly_level": disasm,
            "waterproof_level": waterproof
        }

        # 5. Tra cứu Warranty Policy
        warr_key = f"{component_id}_{action_type}"
        warranty_months = self.warranty_policy.get(warr_key, 6 if action_type == "replace" else 3)

        # 6. Tra cứu Market Statistics theo f"{component_id}_{brand_tier}_{part_type}"
        stat_key = f"{component_id}_{brand_tier}_{part_type_clean}"
        market_stats = self.pricing_stats.get(stat_key, {
            "min": int(baseline_comp * 0.85),
            "median": int(baseline_comp),
            "max": int(baseline_comp * 1.20),
            "std": int(baseline_comp * 0.1),
            "iqr": int(baseline_comp * 0.15),
            "source_count": 8
        })

        return {
            "component_id": component_id,
            "component_name_vn": comp_name_vn,
            "brand": brand_clean,
            "brand_tier": brand_tier,
            "part_type": part_type_clean,
            "component_condition": condition_clean,
            "region_class": region_class,
            "action_type": action_type,
            "comp_feat_dict": comp_feat_dict,
            "labor_feat_dict": labor_feat_dict,
            "baseline_component_vnd": baseline_comp,
            "base_labor_vnd": base_labor,
            "difficulty_score": diff_score,
            "estimated_minutes": est_mins,
            "warranty_months": warranty_months,
            "market_stats": market_stats
        }
