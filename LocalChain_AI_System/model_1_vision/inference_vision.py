"""
MODEL 1: MODULE SUY LUẬN NHẬN DIỆN THIẾT BỊ (VISION INFERENCE)
"""

import os
import sys
from PIL import Image
from ultralytics import YOLO

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

class VisionEngine:
    def __init__(self, weight_path=None):
        if weight_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            weight_path = os.path.join(base_dir, "model_1_vision", "weights", "best.pt")
            if not os.path.exists(weight_path):
                # Fallback to base weights
                weight_path = os.path.join(base_dir, "yolo11n-cls.pt")
                
        self.weight_path = weight_path
        self.model = None
        self.load_model()
        
    def load_model(self):
        if os.path.exists(self.weight_path):
            try:
                self.model = YOLO(self.weight_path)
                print("[Model 1] Mắt thần Vision YOLO11 đã sẵn sàng!")
            except Exception as e:
                print(f"[Model 1] Lỗi nạp YOLO: {e}")
        else:
            print(f"[Model 1] Chưa tìm thấy trọng số tại {self.weight_path}")

    def predict(self, image_input):
        """
        Nhận diện thiết bị từ đường dẫn file hoặc đối tượng PIL Image.
        Trả về: device_name (str), confidence (float)
        """
        if self.model is None:
            return "dieu_hoa", 0.5
            
        try:
            results = self.model(image_input, verbose=False)
            for r in results:
                top_class_id = r.probs.top1
                device_name = r.names[top_class_id]
                confidence = float(r.probs.top1conf)
                return device_name, round(confidence, 2)
        except Exception as e:
            print(f"Lỗi nhận diện ảnh: {e}")
            return "dieu_hoa", 0.5
            
        return "không_xác_định", 0.0

vision_ai = VisionEngine()

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_img = os.path.join(base_dir, "test_anh.jpg")
    if os.path.exists(test_img):
        dev, conf = vision_ai.predict(test_img)
        print(f"Ảnh: test_anh.jpg -> Thiết bị: {dev} (Độ tin cậy: {conf*100:.1f}%)")
