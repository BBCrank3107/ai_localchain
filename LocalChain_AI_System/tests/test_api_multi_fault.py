"""
INTEGRATION TEST: KIỂM THỬ TOÀN DIỆN SERVER API VỚI TESTCLIENT (FASTAPI)
"""

import os
import sys
import io
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from server_api.app import app

client = TestClient(app)

def run_api_tests():
    print("=" * 70)
    print("🌐 KIỂM THỬ TỔNG THỂ FASTAPI ENDPOINT /api/v1/diagnose")
    print("=" * 70)
    
    # 1. Tạo 1 ảnh giả lập trong bộ nhớ
    img = Image.new("RGB", (224, 224), color=(73, 109, 137))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    test_cases = [
        {
            "name": "Test API Đơn Lỗi",
            "complaint": "Laptop mở máy quạt quay nhưng màn hình đen thui"
        },
        {
            "name": "Test API Đa Lỗi (2 Lỗi)",
            "complaint": "Màn hình laptop bị giật sọc ngang, pin dùng 10 phút là sập nguồn tắt ngóm"
        },
        {
            "name": "Test API Đa Lỗi (3 Lỗi)",
            "complaint": "Laptop màn hình bị sọc giật, máy chạy 10 phút sập nguồn, bàn phím bị liệt phím cách gõ không ăn"
        }
    ]
    
    for tc in test_cases:
        print("\n" + "-" * 70)
        print(f"📡 {tc['name']}")
        print(f"💬 Phàn nàn: \"{tc['complaint']}\"")
        
        response = client.post(
            "/api/v1/diagnose",
            files={"image": ("test.jpg", img_bytes, "image/jpeg")},
            data={"complaint": tc["complaint"]}
        )
        
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        
        print(f"✅ Status: 200 OK")
        print(f"📱 Thiết bị nhận diện: {data.get('device', 'N/A')}")
        # V3.0: fault_count nằm ở root, không trong 'diagnosis'
        fault_count = data.get('fault_count', data.get('diagnosis', {}).get('fault_count', 'N/A'))
        print(f"🎯 Số lỗi phát hiện: {fault_count}")
        print(f"💵 Tổng giá: {data.get('estimated_price_vnd', 0):,.0f} VNĐ (Tiết kiệm: {data.get('discount_vnd', 0):,.0f} VNĐ)")
        if data.get("itemized_prices"):
            print("   Chi tiết từng mục:")
            for item in data["itemized_prices"]:
                print(f"   • {item['fault']}: {item['price_vnd']:,.0f} VNĐ")
        print("\n📝 Tin nhắn phản hồi tự nhiên (NLG):")
        print(data.get("natural_message", ""))

        
    print("\n" + "=" * 70)
    print("🎉 TOÀN BỘ CÁC BƯỚC KIỂM THỬ API ĐÃ THÀNH CÔNG RỰC RỠ!")
    print("=" * 70)

if __name__ == "__main__":
    run_api_tests()
