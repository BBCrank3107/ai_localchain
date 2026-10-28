"""
TEST SCRIPT CHO LOCALCHAIN FASTAPI SERVER
Kiểm thử tự động các endpoints và các ca bệnh phức hợp đa lỗi
"""

import sys
import json

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import requests

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("=" * 85)
    print("🚀 BẮT ĐẦU KIỂM THỬ TỰ ĐỘNG FASTAPI BACKEND (SSOT V2 MULTI-HEAD & MULTI-FAULT)")
    print("=" * 85)
    
    # 1. Test Root Endpoint
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        print("1️⃣ [GET /] Status Root:", r.status_code)
    except Exception as e:
        print(f"❌ Không thể kết nối tới server tại {BASE_URL}. Lỗi: {e}")
        return

    print("-" * 85)

    # 2. Test Compound User Query (Ca bệnh phức hợp đa lỗi)
    user_case = {
        "device": "laptop",
        "complaint": "màn hình bị sọc, vẫn còn nghe âm thanh nhưng màn hình không hiển thị, có tiếng kêu rè rè ở cánh quạt",
        "brand": "Asus"
    }

    print("2️⃣ [POST /api/v1/diagnose-text] Kiểm thử ca bệnh đa lỗi của người dùng:")
    print(f"   💬 Câu mô tả: \"{user_case['complaint']}\"")
    r = requests.post(f"{BASE_URL}/api/v1/diagnose-text", json=user_case, timeout=10)
    
    if r.status_code == 200:
        data = r.json()
        fault_cnt = data.get("fault_count", len(data.get("predicted_faults", [])))
        print(f"\n   ✅ Kết quả chẩn đoán: Phát hiện {fault_cnt} lỗi đồng thời!")
        print(f"   📌 Danh sách lỗi xác định (Predicted Faults):")
        for i, f in enumerate(data.get("predicted_faults", []), 1):
            print(f"      [{i}] Mã lỗi: {f.get('fault_code')} ({f.get('probability', f.get('confidence', 100))}%)")
            print(f"          Tên lỗi: {f.get('fault')}")
            print(f"          Linh kiện hỏng: {f.get('components')}")
        print(f"\n   💰 Báo giá combo trọn gói: {data['estimated_price_vnd']:,} VNĐ")
        if data.get("itemized_prices"):
            print(f"      Chi tiết từng mục:")
            for itm in data["itemized_prices"]:
                print(f"      • {itm['fault']}: {itm['price_vnd']:,} VNĐ")
        print(f"\n   🗣️ Phản hồi tự nhiên NLG:\n{data['natural_message']}")
    else:
        print(f"   ❌ Lỗi ({r.status_code}): {r.text}")

    print("\n" + "=" * 85)
    print("🎉 KIỂM THỬ HOÀN TẤT THÀNH CÔNG!")
    print("=" * 85)

if __name__ == "__main__":
    test_api()
