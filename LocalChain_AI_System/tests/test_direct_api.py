import asyncio
import io
import os
import sys
from PIL import Image
from fastapi import UploadFile

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server_api.app import diagnose

async def test():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    laptop_img_path = os.path.join(base_dir, "datasets", "yolo_vision", "val", "laptop", "laptop_00001.jpg")
    
    with open(laptop_img_path, "rb") as f:
        img_bytes = f.read()
        
    buf = io.BytesIO(img_bytes)
    upload = UploadFile(filename="laptop_test.jpg", file=buf)
    
    complaint = "Màn hình laptop bị giật sọc ngang, pin dùng 10 phút là sập nguồn tắt ngóm"
    res = await diagnose(image=upload, complaint=complaint)
    
    print("=" * 70)
    print("🎉 KẾT QUẢ CHẨN ĐOÁN TOÀN DIỆN VỚI ẢNH THỰC TẾ & MÔ TẢ ĐA LỖI:")
    print("=" * 70)
    print(f"📱 Thiết bị nhận diện bởi YOLO11: [{res.device.upper()}]")
    print(f"🎯 Số lượng sự cố phát hiện: {res.diagnosis.get('fault_count')}")
    print(f"💵 Tổng chi phí combo: {res.estimated_price_vnd:,.0f} VNĐ (Đã giảm ưu đãi combo: {res.discount_vnd:,.0f} VNĐ)")
    print("📋 Báo giá chi tiết từng hạng mục:")
    for item in (res.itemized_prices or []):
        print(f"  • {item['fault']}: {item['price_vnd']:,.0f} VNĐ")
        
    print("\n💬 Tin nhắn phản hồi tự nhiên (NLG):")
    print(res.natural_message)
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test())
