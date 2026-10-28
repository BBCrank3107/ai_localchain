import os
import time
import requests
import shutil
from deep_translator import GoogleTranslator

def translate_vi(text):
    if not text or not text.strip():
        return ""
    try:
        return GoogleTranslator(source='auto', target='vi').translate(text)
    except Exception:
        # Nếu Google chặn do request nhiều quá, trả về nguyên bản Tiếng Anh
        return text

def scrape_ifixit_guides():
    queries = {
        "dieu_hoa": "air conditioner",
        "laptop": "laptop",
        "lo_vi_song": "microwave oven",
        "may_bom": "water pump",
        "may_giat": "washing machine",
        "may_in": "printer",
        "may_loc_nuoc": "water purifier",
        "noi_com": "rice cooker",
        "quat": "fan",
        "tivi": "television",
        "tu_lanh": "refrigerator"
    }
    
    manuals_dir = r"D:\Application\local-chain-app\LocalChain_AI_System\documents\manuals"
    
    print("\n📁 Kích hoạt chế độ tải Tích lũy (Resume Mode)... Không xóa file cũ.")
    os.makedirs(manuals_dir, exist_ok=True)
    
    print("🚀 Bắt đầu cào TOÀN BỘ dữ liệu iFixit cho 11 thiết bị...\n")
    
    for device_vi, query_en in queries.items():
        print("="*60)
        print(f"🔍 Đang phân tích kho dữ liệu: {device_vi.upper()} (Từ khóa: {query_en})")
        
        # 1. Lấy tổng số bài viết
        first_url = f"https://www.ifixit.com/api/2.0/search/{requests.utils.quote(query_en)}?filter=guide&limit=1"
        try:
            r = requests.get(first_url)
            total_results = r.json().get("totalResults", 0)
        except:
            total_results = 0
            
        if total_results == 0:
            print(f"⚠️ Không tìm thấy tài liệu nào cho {device_vi}.")
            continue
            
        print(f"📊 Phát hiện tổng cộng {total_results} bài hướng dẫn cho {device_vi.upper()}.")
        
        # Tải danh sách tất cả các Guide ID
        limit = 100
        offset = 0
        all_guide_ids = []
        
        while offset < total_results:
            url = f"https://www.ifixit.com/api/2.0/search/{requests.utils.quote(query_en)}?filter=guide&limit={limit}&offset={offset}"
            res = requests.get(url)
            if res.status_code == 200:
                results = res.json().get("results", [])
                for r in results:
                    if r.get("guideid"):
                        all_guide_ids.append(r.get("guideid"))
            offset += limit
            
        total_guides = len(all_guide_ids)
        print(f"📥 Đã liệt kê {total_guides} bài. Bắt đầu tải và dịch...")
        
        # 2. Tải và dịch từng bài
        for idx, guide_id in enumerate(all_guide_ids, 1):
            percent = (idx / total_guides) * 100
            
            try:
                guide_url = f"https://www.ifixit.com/api/2.0/guides/{guide_id}"
                g_resp = requests.get(guide_url)
                if g_resp.status_code != 200:
                    continue
                    
                guide_data = g_resp.json()
                title_en = guide_data.get("title", "")
                summary_en = guide_data.get("summary", "")
                category_en = guide_data.get("category", "")
                url_goc = guide_data.get("url", guide_url)
                
                # BỘ LỌC LOẠI TRỪ Ô TÔ / XE CỘ
                car_keywords = [
                    "car", "auto", "vehicle", "truck", "chevrolet", "toyota", "ford", 
                    "honda", "nissan", "hyundai", "kia", "bmw", "mercedes", "audi", 
                    "volkswagen", "jeep", "mazda", "subaru", "chrysler", "dodge",
                    "cadillac", "buick", "lincoln", "gmc", "ram", "volvo", "lexus",
                    "infiniti", "acura", "engine", "automotive"
                ]
                
                text_to_check = f"{title_en} {summary_en} {category_en}".lower()
                is_car = any(kw in text_to_check for kw in car_keywords)
                
                if device_vi == "dieu_hoa" and is_car:
                    print(f"[{idx}/{total_guides}] 🚫 Bỏ qua hướng dẫn Điều hòa Ô tô: {title_en[:35]}")
                    continue
                
                # Format chuẩn
                filename = f"{device_vi}_ifixit_{guide_id}.md"
                filepath = os.path.join(manuals_dir, filename)
                
                # CHỨC NĂNG RESUME: Nếu file đã tồn tại thì bỏ qua không tải/dịch lại
                if os.path.exists(filepath):
                    print(f"[{idx}/{total_guides}] ({percent:.1f}%) Đã có sẵn: {filename}. Bỏ qua...")
                    continue

                print(f"[{idx}/{total_guides}] ({percent:.1f}%) Đang xử lý: {title_en[:30]}...")
                
                title_vi = translate_vi(title_en)
                summary_vi = translate_vi(summary_en)
                
                md_content = f"# {title_vi}\n\n"
                md_content += f"- **Thiết bị:** {device_vi}\n"
                md_content += f"- **Nguồn:** [iFixit]({url_goc})\n\n"
                md_content += f"**Tóm tắt:** {summary_vi}\n\n"
                
                steps = guide_data.get("steps", [])
                for step in steps:
                    step_title = step.get("title") or ""
                    if step_title:
                        md_content += f"## {translate_vi(step_title)}\n"
                    else:
                        md_content += f"## Bước {step.get('orderby', 1)}\n"
                        
                    for line in step.get("lines", []):
                        text_en = line.get("text_raw", "")
                        text_vi = translate_vi(text_en)
                        md_content += f"- {text_vi}\n"
                    md_content += "\n"
                    
                # Lưu file với định dạng chuẩn
                filename = f"{device_vi}_ifixit_{guide_id}.md"
                filepath = os.path.join(manuals_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(md_content)
                    
            except Exception as e:
                print(f"❌ Lỗi tải bài {guide_id}: {e}")
                
            time.sleep(0.5) # Nghỉ xíu chống bị iFixit và Google ban IP

if __name__ == "__main__":
    scrape_ifixit_guides()
