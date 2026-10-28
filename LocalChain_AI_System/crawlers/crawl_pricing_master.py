"""
MASTER PRICING CRAWLER - LOCALCHAIN AI
Cào và bóc tách dữ liệu giá sửa chữa, linh kiện, tiền công, bảo hành từ các nguồn web Việt Nam.
"""

import os
import re
import sys
import time
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# DANH SÁCH CÁC NGUỒN CÀO THEO 11 NHÓM THIẾT BỊ
TARGET_SOURCES = [
    # 💻 LAPTOP & THIẾT BỊ ĐIỆN TỬ
    {"url": "https://fptshop.com.vn/tin-tuc/danh-gia/thay-main-laptop-bao-nhieu-tien-2026-205796", "device": "laptop"},
    {"url": "https://fptshop.com.vn/tin-tuc/danh-gia/thay-ban-le-laptop-bao-nhieu-tien-2026-205486", "device": "laptop"},
    {"url": "https://dienthoaivui.com.vn/chinh-sach-bao-hanh", "device": "laptop"},
    
    # ❄️ ĐIỆN LẠNH (ĐIỀU HÒA, MÁY GIẶT, TỦ LẠNH)
    {"url": "https://suachuadienlanhdanang.vn/bang-gia/", "device": "dieu_hoa"},
    {"url": "https://dichvusuadienlanhdanang.com/sua-dieu-hoa-tai-da-nang/", "device": "dieu_hoa"},
    {"url": "https://limosa.vn/bang-gia-bao-tri-may-lanh/", "device": "dieu_hoa"},
    {"url": "https://www.dienmayxanh.com/kinh-nghiem-hay/bang-gia-sua-may-lanh-moi-nhat-chi-tiet-1585356", "device": "dieu_hoa"},
    
    # 📺 TIVI & MÁY IN
    {"url": "https://www.dienmayxanh.com/kinh-nghiem-hay/man-hinh-tivi-bi-soc-nguyen-nhan-va-cach-khac-phuc-652936", "device": "tivi"},
    {"url": "https://thuanbaotin.com/dich-vu/sua-may-in-da-nang.html", "device": "may_in"},
    {"url": "https://truonggiang.vn/sua-may-in.html", "device": "may_in"},
    {"url": "https://mayinphunkholon.com.vn/sua-may-in-kho-lon-tan-noi/sua-may-in-bat-kho-lon-tai-da-nang.html", "device": "may_in"},
    
    # 🍳 GIA DỤNG BẾP (LÒ VI SÓNG, MÁY LỌC NƯỚC, NỒI CƠM)
    {"url": "https://limosa.vn/sua-lo-vi-song/", "device": "lo_vi_song"},
    {"url": "https://suadientulimosa.com/bang-gia-sua-lo-vi-song/", "device": "lo_vi_song"},
    {"url": "https://limosa.vn/bang-gia-sua-may-loc-nuoc/", "device": "may_loc_nuoc"},
    {"url": "https://baohanhkangaroo.com/gia-sua-may-loc-nuoc/", "device": "may_loc_nuoc"},
    {"url": "https://43fix.vn/sua-noi-com-dien-da-nang/", "device": "noi_com"},
    {"url": "https://www.dienlanhanhthang.com/sua-noi-com-dien-tai-da-nang.html", "device": "noi_com"},
    {"url": "https://hoanghamobile.com/tin-tuc/gia-sua-noi-com-dien-bao-nhieu-bang-gia-chi-tiet-tung-loi-2026/", "device": "noi_com"},
    {"url": "https://suathietbichauau.vn/service/sua-noi-com-dien-cao-tan-hawonkoo/", "device": "noi_com"},
    
    # 🌀 ĐIỆN CƠ DÂN DỤNG (QUẠT ĐIỆN, MÁY BƠM NƯỚC)
    {"url": "https://suachuatainha.com.vn/bao-gia-dich-vu-sua-dien/", "device": "may_bom"},
    {"url": "https://thoviet.com.vn/bang-gia-sua-quat-tran.html", "device": "quat"}
]

def parse_vietnamese_currency(text: str) -> Dict[str, float]:
    """Bóc tách khoảng giá min, max từ chuỗi văn bản giá tiền"""
    if not text:
        return {"min_price": 0.0, "max_price": 0.0}
        
    text_clean = text.lower().replace("vnđ", "").replace("vnd", "").replace("đ", "").strip()
    
    # Xử lý dạng: 1.5 - 2.5 triệu
    m_trieu = re.findall(r'(\d+[.,]?\d*)\s*(?:-|đến|–)\s*(\d+[.,]?\d*)\s*triệu', text_clean)
    if m_trieu:
        return {
            "min_price": float(m_trieu[0][0].replace(',', '.')) * 1_000_000,
            "max_price": float(m_trieu[0][1].replace(',', '.')) * 1_000_000
        }
        
    # Xử lý dạng: 150k - 300k
    m_k = re.findall(r'(\d+)\s*k\s*(?:-|đến|–)\s*(\d+)\s*k', text_clean)
    if m_k:
        return {
            "min_price": float(m_k[0][0]) * 1_000,
            "max_price": float(m_k[0][1]) * 1_000
        }

    # Bóc tách các cụm số nguyên lớn (ví dụ: 150.000 - 350.000)
    raw_nums = re.findall(r'\b\d{1,3}(?:[.,]\d{3})+\b|\b\d{4,9}\b', text_clean)
    parsed_nums = []
    for num_str in raw_nums:
        try:
            clean_n = int(re.sub(r'[.,]', '', num_str))
            if 10_000 <= clean_n <= 50_000_000: # Lọc giá hợp lệ từ 10k đến 50M
                parsed_nums.append(clean_n)
        except Exception:
            continue
            
    if len(parsed_nums) >= 2:
        return {"min_price": float(min(parsed_nums)), "max_price": float(max(parsed_nums))}
    elif len(parsed_nums) == 1:
        return {"min_price": float(parsed_nums[0]), "max_price": float(parsed_nums[0])}
        
    return {"min_price": 0.0, "max_price": 0.0}

def parse_warranty_months(text: str) -> int:
    """Trích xuất số tháng bảo hành"""
    m = re.search(r'(\d+)\s*(?:tháng|th|t)\b', text.lower())
    if m:
        return int(m.group(1))
    return 3 # Mặc định 3 tháng theo thị trường

def scrape_single_url(target: Dict[str, str]) -> List[Dict[str, Any]]:
    url = target["url"]
    device = target["device"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    extracted_records = []
    print(f"⏳ Đang cào dữ liệu từ: {url}")
    
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            print(f"  ⚠️ HTTP {resp.status_code} tại {url}")
            return []
            
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # 1. Quét toàn bộ bảng <table>
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = [c.text.strip() for c in row.find_all(["td", "th"])]
                if len(cols) >= 2:
                    service_name = cols[0]
                    # Bỏ qua dòng tiêu đề
                    if any(h_kw in service_name.lower() for h_kw in ["hạng mục", "tên dịch vụ", "linh kiện", "stt", "nội dung", "bảng giá"]):
                        continue
                        
                    price_col_text = " ".join(cols[1:])
                    prices = parse_vietnamese_currency(price_col_text)
                    
                    if prices["min_price"] > 0:
                        warranty = parse_warranty_months(" ".join(cols))
                        extracted_records.append({
                            "device_id": device,
                            "raw_service_name": service_name,
                            "price_min_vnd": prices["min_price"],
                            "price_max_vnd": prices["max_price"],
                            "price_avg_vnd": (prices["min_price"] + prices["max_price"]) / 2.0,
                            "warranty_months": warranty,
                            "source_url": url
                        })
                        
        # 2. Quét danh sách <li> hoặc <p> nếu không có bảng
        if len(extracted_records) == 0:
            for li in soup.find_all(["li", "p", "div"]):
                txt = li.text.strip()
                if len(txt) > 10 and any(kw in txt.lower() for kw in ["giá:", "chi phí:", "thay ", "sửa ", "khoảng ", "từ "]):
                    prices = parse_vietnamese_currency(txt)
                    if prices["min_price"] >= 30_000:
                        extracted_records.append({
                            "device_id": device,
                            "raw_service_name": txt[:140],
                            "price_min_vnd": prices["min_price"],
                            "price_max_vnd": prices["max_price"],
                            "price_avg_vnd": (prices["min_price"] + prices["max_price"]) / 2.0,
                            "warranty_months": parse_warranty_months(txt),
                            "source_url": url
                        })
                        
        print(f"  ✅ Trích xuất thành công {len(extracted_records)} hạng mục giá.")
    except Exception as e:
        print(f"  ❌ Lỗi khi cào {url}: {str(e)[:50]}")
        
    return extracted_records

def run_master_crawler():
    print("=" * 80)
    print("🚀 BẮT ĐẦU CÀO DỮ LIỆU BẢNG GIÁ THỊ TRƯỜNG VIỆT NAM (11 THIẾT BỊ)...")
    print("=" * 80)
    os.makedirs("datasets/pricing", exist_ok=True)
    all_pricing_data = []
    
    for target in TARGET_SOURCES:
        records = scrape_single_url(target)
        all_pricing_data.extend(records)
        time.sleep(1.0) # Nghỉ nhẹ tránh nghẽn
        
    output_json = "datasets/pricing/crawled_market_prices.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_pricing_data, f, ensure_ascii=False, indent=2)
        
    print("=" * 80)
    print(f"🎉 HOÀN TẤT CÀO DỮ LIỆU! Tổng cộng thu được {len(all_pricing_data)} bản ghi giá.")
    print(f"📁 Dữ liệu thô lưu tại: {output_json}")
    print("=" * 80)

if __name__ == "__main__":
    run_master_crawler()
