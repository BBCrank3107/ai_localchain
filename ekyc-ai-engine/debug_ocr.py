"""
Debug v11 - Test final OCR với tọa độ mới (không CLAHE, có regex post-processing)
"""
import os, ssl, glob
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

import requests as _req
_orig = _req.Session.request
def _patch(self, method, url, **kwargs):
    kwargs['verify'] = False
    return _orig(self, method, url, **kwargs)
_req.Session.request = _patch

from PIL import Image as _PIL
if not hasattr(_PIL, 'ANTIALIAS'): _PIL.ANTIALIAS = _PIL.LANCZOS

import cv2, re
from PIL import Image
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

IMAGE_PATH = r"C:\Users\binhn\AppData\Local\Temp\gradio\da545c79cbe2a47592d2fbaba150738ad5842c5e5e6030315953f28859c5699b\20260901_092405.jpg"
if not os.path.exists(IMAGE_PATH):
    cands = glob.glob(r"C:\Users\binhn\AppData\Local\Temp\gradio\**\*.jpg", recursive=True)
    IMAGE_PATH = max(cands, key=os.path.getsize)

img = cv2.imread(IMAGE_PATH)
h, w, _ = img.shape
print(f"[+] Ảnh gốc: {w}x{h}")

x0 = int(w * 0.35)
x1 = int(w * 0.92)

crops = {
    "id_number": img[int(h*0.42):int(h*0.50), x0:x1],
    "full_name": img[int(h*0.49):int(h*0.515), x0:int(w*0.72)],
    "dob":       img[int(h*0.515):int(h*0.555), x0:int(w*0.75)],
    "origin":    img[int(h*0.57):int(h*0.62), x0:x1],
    "residence": img[int(h*0.62):int(h*0.68), x0:x1],
}

os.makedirs("debug_crops_v11", exist_ok=True)
for name, crop in crops.items():
    cv2.imwrite(f"debug_crops_v11/{name}.jpg", crop)
    print(f"  [{name}]: {crop.shape[1]}x{crop.shape[0]}")

def post_process(field_name, raw_text):
    text = raw_text.strip()
    if field_name == "dob":
        match = re.search(r'(\d{1,2})[\/\-\.,\s]+(\d{1,2})[\/\-\.,\s]+(\d{4})', text)
        if match:
            return f"{match.group(1).zfill(2)}/{match.group(2).zfill(2)}/{match.group(3)}"
    if field_name == "id_number":
        digits = re.sub(r'[^0-9]', '', text)
        if len(digits) >= 9:
            return digits
    if field_name == "full_name":
        text = re.sub(r'(Họ và tên|Full name|Họ tên).*', '', text, flags=re.IGNORECASE).strip()
        text = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF]', '', text).strip()
    return text if text else raw_text.strip()

print("\n[*] Chạy VietOCR (không CLAHE, với regex post-process)...")
config = Cfg.load_config_from_name('vgg_transformer')
config['device'] = 'cpu'
ocr = Predictor(config)

for name, crop in crops.items():
    pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    raw = ocr.predict(pil)
    clean = post_process(name, raw)
    print(f"  [{name}] RAW: '{raw}'")
    print(f"         CLEAN: '{clean}'")
