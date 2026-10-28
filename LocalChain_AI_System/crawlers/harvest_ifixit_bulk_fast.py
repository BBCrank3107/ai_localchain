"""
LOCALCHAIN AI V5.2 - MULTI-THREADED BULK IFIXIT CRAWLER
Tự động quét & tải hàng ngàn cẩm nang kỹ thuật iFixit REST API v2.0 cho 11 nhóm thiết bị.
Hỗ trợ: Resume (tải tiếp), Đa luồng (ThreadPool 16 workers), JSON thô + Markdown chuẩn hóa.
"""

import os
import sys
import json
import time
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Set

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 11 Thiết bị mục tiêu & các từ khóa tìm kiếm toàn diện
DEVICE_SEARCH_QUERIES = {
    "laptop": [
        "laptop", "notebook", "MacBook", "ThinkPad", "Dell Inspiron", "Dell XPS", 
        "HP Pavilion", "HP EliteBook", "Asus ZenBook", "Asus ROG", "Acer Aspire", 
        "Lenovo IdeaPad", "Surface Laptop", "Chromebook"
    ],
    "tivi": [
        "television", "smart tv", "samsung tv", "lg tv", "sony tv", "oled tv", 
        "led tv", "qled tv", "panasonic tv", "tcl tv"
    ],
    "dieu_hoa": [
        "air conditioner", "hvac", "daikin ac", "mini split", "portable ac", 
        "window ac", "panasonic air conditioner", "mitsubishi ac"
    ],
    "tu_lanh": [
        "refrigerator", "freezer", "fridge", "ice maker", "samsung refrigerator", 
        "lg refrigerator", "whirlpool refrigerator"
    ],
    "may_giat": [
        "washing machine", "washer", "washer dryer", "front load washer", 
        "top load washer", "dryer", "electrolux washer"
    ],
    "lo_vi_song": [
        "microwave oven", "microwave", "countertop microwave", "over the range microwave"
    ],
    "noi_com": [
        "rice cooker", "pressure cooker", "instant pot", "electric pressure cooker", "slow cooker"
    ],
    "may_in": [
        "printer", "laser printer", "inkjet printer", "3d printer", "hp laserjet", 
        "canon pixma", "epson ecotank", "brother printer"
    ],
    "may_bom": [
        "water pump", "sump pump", "well pump", "submersible pump", "booster pump", "utility pump"
    ],
    "quat": [
        "fan", "ceiling fan", "standing fan", "tower fan", "desk fan", "dyson fan", "exhaust fan"
    ],
    "may_loc_nuoc": [
        "water purifier", "water filter", "reverse osmosis", "ro system", "brita filter", "under sink filter"
    ]
}

class FastIFixitHarvester:
    def __init__(self, base_dir: str = None, max_workers: int = 16):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.raw_json_dir = os.path.join(self.base_dir, "datasets", "manuals_raw_json")
        self.manuals_v2_dir = os.path.join(self.base_dir, "datasets", "manuals_v2")
        self.meta_dir = os.path.join(self.base_dir, "datasets", "metadata")
        
        os.makedirs(self.raw_json_dir, exist_ok=True)
        os.makedirs(self.manuals_v2_dir, exist_ok=True)
        os.makedirs(self.meta_dir, exist_ok=True)
        
        self.max_workers = max_workers
        self.session = self._create_resilient_session()
        self.downloaded_ids = self._load_existing_downloaded_ids()
        
    def _create_resilient_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=50, pool_maxsize=50)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            "User-Agent": "LocalChain-AI-Enterprise-Harvester/5.2 (Educational & Research Tool)"
        })
        return session

    def _load_existing_downloaded_ids(self) -> Set[int]:
        downloaded = set()
        if os.path.exists(self.raw_json_dir):
            for fname in os.listdir(self.raw_json_dir):
                if fname.endswith(".json"):
                    match = re.search(r"_(\d+)\.json$", fname)
                    if match:
                        downloaded.add(int(match.group(1)))
        print(f"📦 Đã tìm thấy {len(downloaded)} cẩm nang sẵn có trong kho lưu trữ local.")
        return downloaded

    def search_guide_ids_for_query(self, query: str, max_limit: int = 500) -> List[int]:
        guide_ids = []
        limit = 100
        offset = 0
        
        while offset < max_limit:
            url = f"https://www.ifixit.com/api/2.0/search/{requests.utils.quote(query)}?filter=guide&limit={limit}&offset={offset}"
            try:
                resp = self.session.get(url, timeout=12)
                if resp.status_code != 200:
                    break
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    break
                    
                for item in results:
                    gid = item.get("guideid")
                    if gid and gid not in guide_ids:
                        guide_ids.append(gid)
                        
                total_results = data.get("totalResults", 0)
                offset += limit
                if offset >= total_results:
                    break
                time.sleep(0.1)
            except Exception as e:
                print(f"⚠️ Lỗi tìm kiếm '{query}' (offset={offset}): {e}")
                break
                
        return guide_ids

    def fetch_single_guide(self, guide_id: int, device_key: str) -> Dict[str, Any]:
        url = f"https://www.ifixit.com/api/2.0/guides/{guide_id}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                data["_device_key"] = device_key
                data["_fetched_at"] = time.time()
                return data
            elif resp.status_code == 404:
                return {"_error": "NOT_FOUND", "guide_id": guide_id}
            else:
                return {"_error": f"HTTP_{resp.status_code}", "guide_id": guide_id}
        except Exception as e:
            return {"_error": str(e), "guide_id": guide_id}

    def convert_guide_to_clean_markdown(self, guide: Dict[str, Any], device_key: str) -> str:
        title = guide.get("title", "Hướng dẫn sửa chữa")
        difficulty = guide.get("difficulty", "Moderate")
        time_required = guide.get("time_required", "30-60 minutes")
        summary = guide.get("summary", "")
        intro = guide.get("introduction_raw", "")
        tools = guide.get("tools", [])
        parts = guide.get("parts", [])
        prerequisites = guide.get("prerequisites", [])
        steps = guide.get("steps", [])
        conclusion = guide.get("conclusion_raw", "")
        url = guide.get("url", "")
        
        md_lines = []
        md_lines.append(f"# {title}")
        md_lines.append("")
        md_lines.append(f"- **Thiết bị:** {device_key.upper()}")
        md_lines.append(f"- **Độ khó:** {difficulty}")
        md_lines.append(f"- **Thời gian ước tính:** {time_required}")
        if url:
            md_lines.append(f"- **Nguồn:** [iFixit Guide {guide.get('guideid')}]({url})")
        md_lines.append("")
        
        if summary:
            md_lines.append(f"**Tóm tắt:** {summary}\n")
            
        if intro:
            md_lines.append("## Giới thiệu & Khuyến cáo an toàn")
            md_lines.append(f"{intro}\n")
            
        if tools:
            md_lines.append("## Dụng cụ cần thiết")
            for t in tools:
                t_name = t.get("text", "")
                if t_name:
                    md_lines.append(f"- 🔧 {t_name}")
            md_lines.append("")
            
        if parts:
            md_lines.append("## Linh kiện thay thế")
            for p in parts:
                p_name = p.get("text", "")
                if p_name:
                    md_lines.append(f"- 🧩 {p_name}")
            md_lines.append("")
            
        if prerequisites:
            md_lines.append("## Yêu cầu tiên quyết (Prerequisites)")
            for pre in prerequisites:
                md_lines.append(f"- ⚠️ Cần thực hiện trước: **{pre.get('title', '')}** (Guide ID: {pre.get('guideid')})")
            md_lines.append("")
            
        if steps:
            md_lines.append("## Các bước thực hiện chi tiết")
            for i, step in enumerate(steps, 1):
                step_title = step.get("title", f"Bước {i}")
                md_lines.append(f"### Bước {i}: {step_title}")
                lines = step.get("lines", [])
                for line in lines:
                    txt = line.get("text_raw", "").strip()
                    bullet = line.get("bullet", "black")
                    icon = "•"
                    if bullet == "red" or "caution" in bullet:
                        icon = "🚨 **CẢNH BÁO:**"
                    elif bullet == "yellow" or "note" in bullet:
                        icon = "💡 **LƯU Ý:**"
                    elif bullet == "green":
                        icon = "✓"
                    if txt:
                        md_lines.append(f"{icon} {txt}")
                md_lines.append("")
                
        if conclusion:
            md_lines.append("## Nghiệm thu & Hoàn tất")
            md_lines.append(f"{conclusion}\n")
            
        return "\n".join(md_lines)

    def harvest_all_devices(self, target_per_device: int = 1000):
        print("=" * 75)
        print("🚀 KHỞI ĐỘNG CRAWLER ĐA LUỒNG TIER S (IFIXIT v2.0 REST API)")
        print(f"🎯 Mục tiêu: Thu thập hàng ngàn cẩm nang kỹ thuật cho 11 nhóm thiết bị")
        print(f"⚡ Số luồng xử lý song song: {self.max_workers}")
        print("=" * 75)
        
        total_downloaded_new = 0
        catalog = {}
        
        for dev_key, queries in DEVICE_SEARCH_QUERIES.items():
            print(f"\n📂 [BƯỚC 1/2] Quét danh mục Guide IDs cho thiết bị: {dev_key.upper()}...")
            device_guide_ids = set()
            
            for q in queries:
                gids = self.search_guide_ids_for_query(q, max_limit=300)
                device_guide_ids.update(gids)
                if len(device_guide_ids) >= target_per_device:
                    break
                    
            print(f"📊 Tìm thấy {len(device_guide_ids)} bài hướng dẫn phù hợp cho {dev_key.upper()}.")
            
            # Lọc các bài chưa tải
            pending_ids = [gid for gid in device_guide_ids if gid not in self.downloaded_ids]
            print(f"📥 Cần tải mới: {len(pending_ids)} bài (Đã có sẵn: {len(device_guide_ids) - len(pending_ids)})")
            
            if not pending_ids:
                catalog[dev_key] = len(device_guide_ids)
                continue
                
            print(f"⚡ [BƯỚC 2/2] Đang tải song song {len(pending_ids)} bài với {self.max_workers} workers...")
            dev_saved_count = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_id = {
                    executor.submit(self.fetch_single_guide, gid, dev_key): gid 
                    for gid in pending_ids
                }
                
                for future in as_completed(future_to_id):
                    gid = future_to_id[future]
                    try:
                        guide_data = future.result()
                        if "_error" not in guide_data:
                            # 1. Lưu Raw JSON
                            json_fname = f"{dev_key}_ifixit_{gid}.json"
                            json_path = os.path.join(self.raw_json_dir, json_fname)
                            with open(json_path, "w", encoding="utf-8") as f:
                                json.dump(guide_data, f, ensure_ascii=False, indent=2)
                                
                            # 2. Lưu Clean Markdown
                            md_content = self.convert_guide_to_clean_markdown(guide_data, dev_key)
                            md_fname = f"{dev_key}_ifixit_{gid}.md"
                            md_path = os.path.join(self.manuals_v2_dir, md_fname)
                            with open(md_path, "w", encoding="utf-8") as f:
                                f.write(md_content)
                                
                            self.downloaded_ids.add(gid)
                            dev_saved_count += 1
                            total_downloaded_new += 1
                    except Exception as e:
                        pass
                        
            catalog[dev_key] = len(device_guide_ids)
            print(f"✅ Đã lưu thành công {dev_saved_count} cẩm nang mới cho {dev_key.upper()}!")
            
        print("\n" + "=" * 75)
        print(f"🎉 HOÀN THÀNH PHA 1 CRAWL IFIXIT! Tổng số cẩm nang mới tải về: {total_downloaded_new}")
        print(f"📁 Tổng số file trong manuals_v2: {len(os.listdir(self.manuals_v2_dir))}")
        print("=" * 75)
        
        # Lưu catalog metadata
        meta_path = os.path.join(self.meta_dir, "harvest_catalog_ifixit.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.time(),
                "total_guides": len(os.listdir(self.manuals_v2_dir)),
                "devices_breakdown": catalog
            }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    harvester = FastIFixitHarvester(max_workers=16)
    harvester.harvest_all_devices(target_per_device=800)
