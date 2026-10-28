"""
MODEL 1: HUẤN LUYỆN MẮT THẦN THỊ GIÁC MÁY TÍNH (YOLO11)
Nhiệm vụ: Nhận diện đa lớp thiết bị điện tử, điện gia dụng & công nghệ qua hình ảnh.
"""

import os
import sys
import torch
from ultralytics import YOLO

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def train_yolo():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_dir = os.path.join(base_dir, "datasets", "yolo_vision")
    train_dir = os.path.join(dataset_dir, "train")
    
    # Kiểm tra danh sách class hiện diện
    detected_classes = []
    if os.path.exists(train_dir):
        detected_classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]
        detected_classes.sort()

    cuda_available = torch.cuda.is_available()
    device = 0 if cuda_available else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else "None (Sử dụng CPU)"

    print("=" * 70)
    print("🚀 BẮT ĐẦU HUẤN LUYỆN MODEL 1: YOLO11 IMAGE CLASSIFICATION")
    print(f"📁 Dataset Path : {dataset_dir}")
    print(f"📦 Số Classes   : {len(detected_classes)} thiết bị")
    print(f"📋 Danh sách    : {', '.join(detected_classes)}")
    print(f"⚡ Device       : {device} ({gpu_name})")
    print("=" * 70)
    
    # Load model nền YOLO11 Nano (Next-Gen Architecture with Attention Block)
    model = YOLO("yolo11n-cls.pt")
    
    # Huấn luyện với độ phân giải cao imgsz=416
    results = model.train(
        data=dataset_dir,
        epochs=30,
        imgsz=416,       # Độ phân giải sắc nét
        batch=16,        # Tối ưu cho VRAM
        device=device,   # Tận dụng GPU NVIDIA CUDA nếu có, hoặc fallback CPU
        workers=2,
        project=os.path.join(base_dir, "model_1_vision", "runs"),
        name="train_vision_expanded",
        exist_ok=False   # Tự động lưu các phiên bản huấn luyện
    )
    
    # Lấy đường dẫn file best.pt của chính phiên train này
    run_dir = str(results.save_dir)
    best_weight = os.path.join(run_dir, "weights", "best.pt")
    target_weight = os.path.join(base_dir, "model_1_vision", "weights", "best.pt")
    
    if os.path.exists(best_weight):
        import shutil
        os.makedirs(os.path.dirname(target_weight), exist_ok=True)
        shutil.copy(best_weight, target_weight)
        print(f"\n🎉 Huấn luyện thành công phiên bản mới!")
        print(f"📁 Thư mục kết quả & biểu đồ: {run_dir}")
        print(f"👉 Trọng số tối ưu đã cập nhật tại: {target_weight}")

if __name__ == "__main__":
    train_yolo()
