from ultralytics import YOLO
import os

if __name__ == '__main__':
    print("[*] Bắt đầu quá trình huấn luyện YOLO11 (Training)...")
    
    # 1. Tải mô hình YOLO11 Nano (yolo11n.pt) cực nhẹ và siêu nhanh cho GPU GTX 1650
    model = YOLO("yolo11n.pt") 
    
    # 2. Bắt đầu Train với Dataset đã tạo
    dataset_yaml_path = "d:/Application/local-chain-app/ekyc-ai-engine/datasets/synthetic/cccd_yolo/dataset.yaml"
    
    print(f"[*] Cấu hình dữ liệu: {dataset_yaml_path}")
    print("[*] Tối ưu tốc độ cho GTX 1650: Dự kiến train xong trong ~1.5 phút!")
    
    import torch
    device_setting = 0 if torch.cuda.is_available() else "cpu"
    print(f"[*] Sử dụng thiết bị tính toán: {device_setting}")
    
    results = model.train(
        data=dataset_yaml_path,
        epochs=35,       # 35 epochs cho mô hình hội tụ đủ nhanh và nét
        imgsz=640,       # Kích thước ảnh đầu vào cho AI
        batch=16,        # Batch size 16 vừa khít với 4GB VRAM của card GTX 1650 (tránh tràn bộ nhớ)
        device=device_setting,
        workers=2 if torch.cuda.is_available() else 0,
        exist_ok=True    # Ghi đè đợt train cũ
    )
    
    print("[+] Hoàn tất huấn luyện!")
    print("[+] File weights tốt nhất (best.pt) thường nằm trong thư mục: runs/detect/train/weights/")
