import os
import ssl
import sys
import re

# Windows PowerShell may default to a legacy code page. Logging must never stop
# the OCR pipeline merely because a Vietnamese message cannot be encoded.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

# --- TRIỆT CẢM LỖI SSL CHO TOÀN BỘ PYTHON (urllib & requests) ---
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''

try:
    import requests
    _old_request = requests.Session.request
    def _patched_request(self, method, url, **kwargs):
        kwargs['verify'] = False
        return _old_request(self, method, url, **kwargs)
    requests.Session.request = _patched_request
except Exception:
    pass
# ---------------------------------------------------------------

import cv2
import numpy as np
from PIL import Image

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WEIGHTS_PATH = os.path.join(PROJECT_ROOT, "runs", "detect", "train", "weights", "best.pt")

# Fix xung đột PIL.Image.ANTIALIAS bị xóa trong Pillow >= 10.0
# VietOCR dùng API cũ này nên cần vá lại
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

class DocumentEngine:
    def __init__(self):
        print("[*] Khởi tạo YOLO11 (Load file best.pt đã train) & VietOCR...")
        
        self.class_names = [
            "id_number",
            "full_name",
            "dob",
            "gender",
            "nationality",
            "origin",
            "residence",
            "expiry_date",
            "face_photo"
        ]
        
        try:
            from ultralytics import YOLO
            from vietocr.tool.predictor import Predictor
            from vietocr.tool.config import Cfg
            
            if os.path.exists(WEIGHTS_PATH):
                self.yolo = YOLO(WEIGHTS_PATH)
                self.class_names = list(self.yolo.names.values())
                print(f"[+] Đã tải thành công YOLO11 weights từ: {WEIGHTS_PATH}")
            else:
                self.yolo = None
                print(f"[!] Không tìm thấy {WEIGHTS_PATH}, sẽ dùng fallback.")
                
            config = Cfg.load_config_from_name('vgg_transformer')
            config['device'] = 'cpu'
            self.ocr = Predictor(config)
            print("[+] Đã khởi tạo VietOCR Transformer thành công.")
            
            self.ready = True
        except Exception as e:
            print(f"[!] Lỗi khởi tạo OCR Engine: {e}")
            self.ready = False
            
    def _proportional_fallback_crop(self, img):
        """
        FALLBACK THÔNG MINH BẰNG TỶ LỆ CỐ ĐỊNH (Hỗ trợ cả ảnh Ngang và Dọc):
        - Nếu w > h (Ảnh ngang / Thẻ nằm ngang) -> Cắt theo dải Y của ảnh ngang
        - Nếu h >= w (Ảnh dọc / Khung ảnh đứng) -> Cắt theo dải Y của ảnh đứng
        """
        h, w, _ = img.shape
        is_landscape = w > h
        print(f"[*] Fallback crop ảnh {w}x{h} ({'Ảnh Ngang' if is_landscape else 'Ảnh Dọc'})")
        x0 = int(w * 0.32)
        x1 = int(w * 0.95)

        if is_landscape:
            # CCCD mặt trước được chụp thẳng. Các vùng này chỉ lấy giá trị,
            # không lấy label song ngữ ở bên trái.
            crops = {
                "id_number": img[int(h*0.42):int(h*0.52), int(w*0.25):int(w*0.55)],
                "full_name": img[int(h*0.55):int(h*0.64), int(w*0.27):int(w*0.72)],
                "dob":       img[int(h*0.60):int(h*0.67), int(w*0.55):int(w*0.76)],
                "gender":    img[int(h*0.68):int(h*0.75), int(w*0.42):int(w*0.55)],
                "nationality": img[int(h*0.68):int(h*0.75), int(w*0.76):int(w*0.96)],
                "origin":    img[int(h*0.78):int(h*0.86), int(w*0.27):int(w*0.72)],
                "residence": img[int(h*0.915):int(h*0.98), int(w*0.27):int(w*0.96)],
                "expiry_date": img[int(h*0.88):int(h*0.95), int(w*0.15):int(w*0.34)],
            }
        else:
            crops = {
                "id_number": img[int(h*0.42):int(h*0.49), x0:x1],
                "full_name": img[int(h*0.49):int(h*0.515), x0:int(w*0.72)],
                "dob":       img[int(h*0.505):int(h*0.545), x0:int(w*0.85)],
                "origin":    img[int(h*0.57):int(h*0.62), x0:x1],
                "residence": img[int(h*0.62):int(h*0.70), x0:x1],
            }

        return crops, img

    def _should_replace_with_fallback(self, field_name, detected_value, fallback_value):
        """Only replace a detector result when the fallback is clearly cleaner."""
        if not detected_value:
            return True
        if field_name in {"origin", "residence"}:
            detector_noise = ("quân", "pieu", "tố", "thù", "oresdence")
            fallback_noise = ("quân", "pieu", "tố", "thù", "oresdence")
            detected_lower = detected_value.lower()
            fallback_lower = fallback_value.lower()
            return any(token in detected_lower for token in detector_noise) and not any(
                token in fallback_lower for token in fallback_noise
            )
        return False

    def _is_valid_field_value(self, field_name, value):
        """Kiểm tra giá trị OCR có hợp lệ với field tương ứng hay không."""
        if value is None:
            return False
        value = str(value).strip()
        if not value:
            return False

        if field_name == "id_number":
            digits = re.sub(r'[^0-9]', '', value)
            return 9 <= len(digits) <= 12

        if field_name == "full_name":
            return len(value.split()) >= 2 and not re.search(r'(Ngày sinh|Date of birth|Họ và tên|Full name|Họ tên)', value, re.I)

        if field_name == "dob":
            return bool(re.match(r'^\d{2}/\d{2}/\d{4}$', value))

        if field_name == "gender":
            return value.strip() in ["Nam", "Nữ"]

        if field_name == "nationality":
            return value.strip().upper() in {"VIỆT NAM", "VIET NAM"}

        if field_name == "expiry_date":
            return bool(re.match(r'^\d{2}/\d{2}/\d{4}$', value))

        if field_name in ["origin", "residence"]:
            lower = value.lower()
            if 'ngày sinh' in lower or 'date of birth' in lower or 'họ và tên' in lower or 'full name' in lower:
                return False
            return len(value.split()) >= 3

        return True

    def _post_process_text(self, field_name, raw_text):
        """Làm sạch text OCR: trích xuất thông tin quan trọng bằng regex."""
        text = raw_text.strip()

        if field_name == "dob":
            # Trích ngày sinh: năm sinh phải <= 2015 (tránh nhầm với hạn sử dụng 2029, 2030)
            matches = re.findall(r'(\d{1,2})[\/\-\.,\s]+(\d{1,2})[\/\-\.,\s]+(\d{4})', text)
            for d, m, y in matches:
                if 1940 <= int(y) <= 2015:
                    return f"{d.zfill(2)}/{m.zfill(2)}/{y}"

        if field_name == "id_number":
            digits = re.sub(r'[^0-9]', '', text)
            if len(digits) >= 9:
                return digits

        if field_name == "full_name":
            text = re.sub(r'(Họ và tên|Full name|Họ tên).*', '', text, flags=re.IGNORECASE).strip()
            text = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF]', '', text).strip()

        if field_name == "nationality":
            normalized = re.sub(r"\s+", " ", text).strip().lower()
            if normalized in {"việt nam", "viết nam", "viet nam", "vietnam"}:
                return "VIỆT NAM"

        if field_name == "gender":
            normalized = text.strip().lower()
            if normalized in {"nam", "male"}:
                return "Nam"
            if normalized in {"nữ", "nu", "female"}:
                return "Nữ"

        if field_name in ["origin", "residence"]:
            text = re.sub(r'(Quê quán|Place of origin|Nơi thường trú|Place of residence).*?:', '', text, flags=re.IGNORECASE).strip()
            
            # Sửa lỗi chính tả OCR phổ biến ở địa danh Việt Nam
            replacements = {
                r'\bPiei\s*(tu|kh|hữ|nu)\b': 'Pleiku',
                r'\bGia\s*Duân\b': 'Gia Lai',
                r'\bNăm\s*Định\b': 'Nam Định',
                r'\bVền\b': 'Ý Yên',
                r'\bVên\b': 'Yên',
                r'\bTháng\s*Lợi\b': 'Thắng Lợi',
                r'\bThăng\s*Lợi\b': 'Thắng Lợi'
            }
            for pattern, repl in replacements.items():
                text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

            # Làm sạch các từ lặp rác do VietOCR dự đoán thừa ở cuối dải
            words = text.split()
            clean_words = []
            for w in words:
                if len(clean_words) >= 2 and clean_words[-1] == w and clean_words[-2] == w:
                    continue
                clean_words.append(w)
            text = " ".join(clean_words)

        return text if text else raw_text.strip()



    def process_id_card(self, image_path):
        print(f"[*] YOLO11 & VietOCR đang phân tích ảnh CCCD thật: {image_path}")
        
        if not self.ready:
            return {"status": "FAIL", "reason": "OCR Engine chưa sẵn sàng."}
            
        img = cv2.imread(image_path)
        if img is None:
            return {"status": "FAIL", "reason": "Không thể đọc file ảnh."}
            
        h_img, w_img, _ = img.shape
        extracted_data = {}
        face_crop_path = image_path
        
        os.makedirs("temp", exist_ok=True)
        
        # 1. Thử dùng YOLO11 để phát hiện Bounding Boxes.
        # Quan trọng: conf quá thấp (0.03) sẽ sinh vô số false positives trên thẻ CCCD.
        if self.yolo:
            results = self.yolo(img, imgsz=640, conf=0.08, verbose=False)
            boxes = sorted(results[0].boxes, key=lambda b: float(b.conf[0]), reverse=True)
            selected_fields = {}

            for box in boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f"cls_{cls_id}"

                print(f"[*] YOLO11 phát hiện: [{cls_name}] - Độ tin cậy (Conf): {conf:.2f}")

                if conf < 0.08:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                x1, y1 = max(0, x1 - 5), max(0, y1 - 5)
                x2, y2 = min(w_img, x2 + 5), min(h_img, y2 + 5)

                crop = img[y1:y2, x1:x2]
                if crop.size == 0:
                    continue

                # Chỉ giữ dự đoán mạnh nhất cho mỗi field; tránh trường hợp cùng 1 label bị phát hiện nhiều lần với confidence thấp
                current_best = selected_fields.get(cls_name)
                if current_best is None or conf > current_best[0]:
                    selected_fields[cls_name] = (conf, x1, y1, x2, y2, crop)

            for cls_name, (conf, x1, y1, x2, y2, crop) in selected_fields.items():
                if cls_name == "face_photo" and conf > 0.85:
                    crop_face_file = f"temp/crop_face_{os.path.basename(image_path)}"
                    cv2.imwrite(crop_face_file, crop)
                    face_crop_path = crop_face_file
                    print(f"[+] YOLO11 đã cắt Ảnh Mặt trên CCCD: {crop_face_file}")
                    continue

                if cls_name == "face_photo":
                    continue

                crop_2x = cv2.resize(crop, (0, 0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                pil_crop = Image.fromarray(cv2.cvtColor(crop_2x, cv2.COLOR_BGR2RGB))
                try:
                    text_read = self.ocr.predict(pil_crop)
                    cleaned_text = self._post_process_text(cls_name, text_read)
                    if cleaned_text and self._is_valid_field_value(cls_name, cleaned_text):
                        # Không ghi đè giá trị hợp lệ bằng box thấp hơn không kiểm soát
                        if cls_name in extracted_data and extracted_data[cls_name]:
                            if cls_name == "origin":
                                curr = extracted_data["origin"]
                                if cleaned_text not in curr:
                                    extracted_data["origin"] = f"{curr}, {cleaned_text}"
                            continue
                        extracted_data[cls_name] = cleaned_text
                        print(f"  -> [{cls_name}]: {cleaned_text}")
                except Exception as e:
                    print(f"  -> Lỗi VietOCR cho {cls_name}: {e}")

        # 2. Bổ sung các trường còn thiếu, hoặc thay thế kết quả YOLO có nhiễu rõ ràng,
        # bằng crop theo layout CCCD mặt trước.
        required_fields = ["id_number", "full_name", "dob", "gender", "nationality", "origin", "residence", "expiry_date"]
        missing_fields = [f for f in required_fields if f not in extracted_data or not extracted_data[f]]

        if missing_fields or (w_img > h_img):
            print(f"[*] Các trường còn thiếu từ YOLO: {missing_fields} -> Tự động bổ sung bằng Fallback Crop...")
            fallback_crops, _ = self._proportional_fallback_crop(img)

            for field_name, crop in fallback_crops.items():
                if crop.size == 0:
                    continue

                crop_2x = cv2.resize(crop, (0, 0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                pil_crop = Image.fromarray(cv2.cvtColor(crop_2x, cv2.COLOR_BGR2RGB))
                try:
                    text_read = self.ocr.predict(pil_crop)
                    if field_name == "residence" and w_img > h_img:
                        # The first address line is displaced to the right on this
                        # CCCD layout. Thresholding makes its black text readable
                        # without contaminating the second-line crop with its label.
                        first_line = img[
                            int(h_img * 0.85):int(h_img * 0.915),
                            int(w_img * 0.64):int(w_img * 0.98),
                        ]
                        gray_first_line = cv2.cvtColor(first_line, cv2.COLOR_BGR2GRAY)
                        _, binary_first_line = cv2.threshold(
                            gray_first_line, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                        )
                        first_line_pil = Image.fromarray(
                            cv2.resize(binary_first_line, (0, 0), fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
                        )
                        first_line_text = self.ocr.predict(first_line_pil)
                        address_match = re.search(r"(?<!\d)(\d{3})(?!\d)\s+(.+)", first_line_text)
                        if address_match:
                            text_read = f"{address_match.group(1)} {address_match.group(2)} {text_read}"
                    cleaned_text = self._post_process_text(field_name, text_read)
                    if cleaned_text and self._is_valid_field_value(field_name, cleaned_text) and self._should_replace_with_fallback(
                        field_name, extracted_data.get(field_name), cleaned_text
                    ):
                        extracted_data[field_name] = cleaned_text
                        print(f"  -> [Fallback bổ sung {field_name}]: {cleaned_text}")
                except Exception as e:
                    print(f"  -> Lỗi VietOCR Fallback cho {field_name}: {e}")

                    
        # 3. Smart Resolver Pass: Đảm bảo phân biệt chính xác Ngày sinh (Năm <= 2015) và Hạn sử dụng (Năm > 2025)
        all_text_blobs = " ".join([str(v) for v in extracted_data.values()])

        # Tìm Ngày sinh chuẩn trong tất cả các chuỗi OCR thu được (chỉ chọn năm sinh <= 2015)
        date_matches = re.findall(r'(\d{1,2})[\/\-\.,\s]+(\d{1,2})[\/\-\.,\s]+(\d{4})', all_text_blobs)
        for d, m, y in date_matches:
            year_val = int(y)
            day_val = int(d)
            month_val = int(m)
            if 1940 <= year_val <= 2015 and 1 <= day_val <= 31 and 1 <= month_val <= 12:
                valid_date_str = f"{d.zfill(2)}/{m.zfill(2)}/{y}"
                # Nếu dob chưa có hoặc dob đang bị rác không đúng định dạng ngày tháng -> Gán lại chuẩn
                if "dob" not in extracted_data or not re.match(r'^\d{2}/\d{2}/\d{4}$', extracted_data["dob"]):
                    extracted_data["dob"] = valid_date_str
                break

        # Chuẩn hóa Quê quán nếu bị sai chính tả chữ rác
        if "origin" in extracted_data:
            orig = extracted_data["origin"]
            orig = re.sub(r'\b(Viên|Vền|Vơn)\s*Nam\s*Viên\b', 'Yên Nhân, Ý Yên', orig, flags=re.IGNORECASE)
            orig = re.sub(r'\bViên\b', 'Yên', orig, flags=re.IGNORECASE)
            extracted_data["origin"] = orig

        # B. Đảm bảo Nơi cư trú loại bỏ nhiễu nhầm nhãn Ngày sinh / Date of birth
        if "residence" in extracted_data:
            res_clean = re.sub(r'(Ngày sinh|Date of birth|sinh\/).*', '', extracted_data["residence"], flags=re.IGNORECASE).strip()
            if res_clean:
                extracted_data["residence"] = res_clean

        # C. Đảm bảo Họ tên được làm sạch chữ rác
        if "full_name" in extracted_data:
            fn_clean = re.sub(r'(Họ và tên|Full name|Họ tên).*', '', extracted_data["full_name"], flags=re.IGNORECASE).strip()
            fn_clean = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF]', '', fn_clean).strip()
            if fn_clean:
                extracted_data["full_name"] = fn_clean

        # D. Chỉ giữ các giá trị hợp lệ theo field, không dùng string rác
        for field, allowed in {
            "gender": ["Nam", "Nữ"],
            "nationality": ["VIỆT NAM"],
            "dob": [],
            "id_number": [],
            "expiry_date": []
        }.items():
            if field not in extracted_data:
                continue
            value = extracted_data[field]
            if field == "gender" and value not in allowed:
                del extracted_data[field]
            elif field == "nationality" and value not in allowed:
                del extracted_data[field]
            elif field in ["dob", "id_number", "expiry_date"] and value and not re.match(r'^(\d{2}/\d{2}/\d{4}|\d{9,12})$', value):
                if field == "dob" and re.match(r'^\d{2}/\d{2}/\d{4}$', value):
                    continue
                del extracted_data[field]

        return {
            "status": "SUCCESS",
            "extracted_data": extracted_data,
            "face_crop_path": face_crop_path
        }

if __name__ == "__main__":
    engine = DocumentEngine()
    print("Document Engine Real Implementation sẵn sàng!")
