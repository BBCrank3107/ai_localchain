from deepface import DeepFace

class FaceMatchingEngine:
    def __init__(self):
        print("[*] Khởi tạo mô hình DeepFace (ArcFace pre-trained)...")
        self.model_name = "ArcFace"
        self.distance_metric = "cosine"
        self.threshold = 0.68
        
    def match_faces(self, face_image_1_path, face_image_2_path):
        """
        Nhận vào 2 ĐƯỜNG DẪN ẢNH (Ảnh cắt từ CCCD và Ảnh cắt từ Selfie).
        Dùng DeepFace để kiểm tra có phải cùng 1 người không.
        """
        print(f"[*] Đang so khớp khuôn mặt bằng DeepFace: {face_image_1_path} vs {face_image_2_path}...")
        
        try:
            # Code thực tế gọi DeepFace
            result = DeepFace.verify(
                img1_path = face_image_1_path, 
                img2_path = face_image_2_path, 
                model_name = self.model_name,
                distance_metric = self.distance_metric,
                enforce_detection = False # Tắt tự động dò mặt nếu ảnh đầu vào đã cắt sẵn khuôn mặt
            )
            
            return {
                "verified": result["verified"],
                "distance": result["distance"], 
                "threshold": result["threshold"],
                "time": result["time"]
            }
        except Exception as e:
            print(f"[!] Lỗi khi gọi DeepFace: {e}")
            return {"verified": False, "error": str(e), "distance": 1.0}

if __name__ == "__main__":
    # Test script - Yêu cầu phải có 2 ảnh img1.jpg và img2.jpg
    engine = FaceMatchingEngine()
    print("Vui lòng truyền vào đường dẫn ảnh thật để test.")
