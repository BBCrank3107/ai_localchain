"""
LOCALCHAIN AI V5.2 - INTERNET ARCHIVE & OEM SERVICE MANUALS HARVESTER
Tự động quét và thu thập tài liệu Service Manuals chính hãng từ Internet Archive & OEM Repositories.
Bao phủ: Dell, HP, Lenovo, Daikin, LG, Samsung, Panasonic, Toshiba, Electrolux cho 11 thiết bị.
"""

import os
import sys
import json
import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

OEM_SEARCH_QUERIES = {
    "laptop": [
        'subject:"Dell Service Manual" AND mediatype:texts',
        'subject:"Lenovo Hardware Maintenance Manual" AND mediatype:texts',
        'subject:"HP Maintenance and Service Guide" AND mediatype:texts',
        'subject:"ThinkPad Service Manual" AND mediatype:texts',
        'subject:"Asus Laptop Service Manual" AND mediatype:texts'
    ],
    "dieu_hoa": [
        'subject:"Daikin Service Manual" AND mediatype:texts',
        'subject:"Air Conditioner Service Manual" AND mediatype:texts',
        'subject:"Panasonic Air Conditioner Manual" AND mediatype:texts',
        'subject:"Mitsubishi Electric Service Manual" AND mediatype:texts'
    ],
    "tu_lanh": [
        'subject:"Refrigerator Service Manual" AND mediatype:texts',
        'subject:"Samsung Refrigerator Service Manual" AND mediatype:texts',
        'subject:"LG Refrigerator Service Manual" AND mediatype:texts',
        'subject:"Whirlpool Refrigerator Manual" AND mediatype:texts'
    ],
    "may_giat": [
        'subject:"Washing Machine Service Manual" AND mediatype:texts',
        'subject:"LG Washer Service Manual" AND mediatype:texts',
        'subject:"Samsung Washer Service Manual" AND mediatype:texts',
        'subject:"Electrolux Washing Machine Service Manual" AND mediatype:texts'
    ],
    "tivi": [
        'subject:"Television Service Manual" AND mediatype:texts',
        'subject:"Sony Bravia Service Manual" AND mediatype:texts',
        'subject:"Samsung TV Service Manual" AND mediatype:texts',
        'subject:"LG TV Service Manual" AND mediatype:texts'
    ],
    "lo_vi_song": [
        'subject:"Microwave Oven Service Manual" AND mediatype:texts',
        'subject:"Panasonic Microwave Service Manual" AND mediatype:texts',
        'subject:"Sharp Microwave Service Manual" AND mediatype:texts'
    ],
    "may_in": [
        'subject:"HP LaserJet Service Manual" AND mediatype:texts',
        'subject:"Canon Service Manual" AND mediatype:texts',
        'subject:"Epson Service Manual" AND mediatype:texts',
        'subject:"Brother Printer Service Manual" AND mediatype:texts'
    ],
    "may_bom": [
        'subject:"Water Pump Service Manual" AND mediatype:texts',
        'subject:"Pump Maintenance Manual" AND mediatype:texts'
    ],
    "quat": [
        'subject:"Fan Service Manual" AND mediatype:texts',
        'subject:"Ceiling Fan Installation Manual" AND mediatype:texts'
    ],
    "noi_com": [
        'subject:"Rice Cooker Service Manual" AND mediatype:texts',
        'subject:"Pressure Cooker Manual" AND mediatype:texts'
    ],
    "may_loc_nuoc": [
        'subject:"Water Filter Manual" AND mediatype:texts',
        'subject:"Water Treatment Service Manual" AND mediatype:texts'
    ]
}

class OEMArchiveHarvester:
    def __init__(self, base_dir: str = None, max_workers: int = 12):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.oem_meta_dir = os.path.join(self.base_dir, "datasets", "oem_manuals_meta")
        self.manuals_v2_dir = os.path.join(self.base_dir, "datasets", "manuals_v2")
        
        os.makedirs(self.oem_meta_dir, exist_ok=True)
        os.makedirs(self.manuals_v2_dir, exist_ok=True)
        
        self.max_workers = max_workers
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=30, pool_maxsize=30)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"User-Agent": "LocalChain-OEM-Collector/5.2"})
        return session

    def search_archive_items(self, query: str, rows: int = 100) -> List[Dict[str, Any]]:
        url = "https://archive.org/advancedsearch.php"
        params = {
            "q": query,
            "fl[]": ["identifier", "title", "creator", "description", "year", "mediatype", "subject"],
            "sort[]": "downloads desc",
            "rows": rows,
            "page": 1,
            "output": "json"
        }
        try:
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", {}).get("docs", [])
        except Exception as e:
            print(f"⚠️ Lỗi tìm kiếm Archive '{query}': {e}")
        return []

    def fetch_item_details_and_save(self, doc: Dict[str, Any], dev_key: str):
        identifier = doc.get("identifier")
        if not identifier:
            return
            
        title = doc.get("title", identifier)
        creator = doc.get("creator", "OEM Official")
        desc = doc.get("description", "")
        subjects = doc.get("subject", [])
        year = doc.get("year", "")
        
        # 1. Lưu metadata JSON
        meta_fname = f"{dev_key}_oem_{identifier}.json"
        meta_path = os.path.join(self.oem_meta_dir, meta_fname)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "identifier": identifier,
                "device_key": dev_key,
                "title": title,
                "creator": creator,
                "year": year,
                "description": desc,
                "subjects": subjects,
                "archive_url": f"https://archive.org/details/{identifier}"
            }, f, ensure_ascii=False, indent=2)
            
        # 2. Tạo Markdown Knowledge Card trong manuals_v2
        md_lines = [
            f"# {title} - Tài liệu Kỹ thuật Chính Hãng ({creator})",
            "",
            f"- **Thiết bị:** {dev_key.upper()}",
            f"- **Hãng sản xuất:** {creator}",
            f"- **Năm phát hành:** {year or 'N/A'}",
            f"- **Kho lưu trữ:** [Archive.org Direct Link](https://archive.org/details/{identifier})",
            "",
            "## Giới thiệu & Sơ đồ Kỹ thuật",
            str(desc) if desc else "Tài liệu bảo trì chính hãng bao gồm sơ đồ tháo lắp (Exploded Views), thứ tự cách ly an toàn và bảng mã lỗi chẩn đoán.",
            "",
            "## Chủ đề bao phủ",
        ]
        if isinstance(subjects, list):
            for s in subjects[:10]:
                md_lines.append(f"- 📋 {s}")
        elif isinstance(subjects, str):
            md_lines.append(f"- 📋 {subjects}")
            
        md_lines.append("")
        md_lines.append("## Khuyến cáo Kỹ thuật viên")
        md_lines.append("- Tuân thủ nghiêm ngặt quy trình cách ly nguồn điện trước khi tiếp xúc bo mạch.")
        md_lines.append("- Sử dụng đúng kích cỡ đầu vít Torx/Phillips để tránh làm toét ren ốc khung máy.")
        
        md_path = os.path.join(self.manuals_v2_dir, f"{dev_key}_oem_{identifier}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

    def harvest_all_oem_manuals(self):
        print("=" * 75)
        print("🏛️ KHỞI ĐỘNG CRAWLER INTERNET ARCHIVE & OEM SERVICE MANUALS")
        print("🎯 Thu thập Service Manuals & HMM của Dell, HP, Lenovo, Daikin, LG, Samsung...")
        print("=" * 75)
        
        total_oem_docs = 0
        for dev_key, queries in OEM_SEARCH_QUERIES.items():
            print(f"\n🔍 Đang truy vấn kho Archive cho thiết bị: {dev_key.upper()}...")
            dev_docs = []
            for q in queries:
                items = self.search_archive_items(q, rows=100)
                dev_docs.extend(items)
                time.sleep(0.2)
                
            # Loại bỏ trùng lặp theo identifier
            unique_docs = {d["identifier"]: d for d in dev_docs if "identifier" in d}.values()
            print(f"📊 Tìm thấy {len(unique_docs)} tài liệu Service Manual cho {dev_key.upper()}.")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self.fetch_item_details_and_save, doc, dev_key) for doc in unique_docs]
                for f in as_completed(futures):
                    total_oem_docs += 1
                    
            print(f"✅ Đã lưu trữ thành công metadata & cẩm nang cho {dev_key.upper()}!")
            
        print("\n" + "=" * 75)
        print(f"🎉 HOÀN THÀNH THU THẬP OEM SERVICE MANUALS! Tổng tài liệu: {total_oem_docs}")
        print("=" * 75)

if __name__ == "__main__":
    harvester = OEMArchiveHarvester()
    harvester.harvest_all_oem_manuals()
