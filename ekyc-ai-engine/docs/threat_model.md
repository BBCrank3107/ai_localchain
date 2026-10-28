# Liveness Threat Model (Mô hình Mối đe dọa Định danh)

Tài liệu này định nghĩa tất cả các kịch bản tấn công (Spoofing Attacks) mà hệ thống eKYC (cụ thể là Model Liveness) phải đối mặt và kiểm tra. Bất kỳ Model nào trước khi được đưa vào Production đều phải vượt qua bộ Test Set chứa các kịch bản tấn công này.

## Phân loại Tấn công (Presentation Attack Types)

| Attack Type | Mô tả | Mức độ nguy hiểm | Yêu cầu Test Set Dataset |
| :--- | :--- | :--- | :--- |
| **Printed Photo** | Kẻ gian in ảnh nạn nhân lên giấy A4 hoặc giấy in ảnh và giơ trước Camera. | Thấp | Bắt buộc có |
| **Screen Photo** | Kẻ gian dùng 1 điện thoại khác mở ảnh tĩnh của nạn nhân và giơ lên. | Trung bình | Bắt buộc có |
| **Screen Video Replay** | Kẻ gian dùng điện thoại/tablet phát lại 1 đoạn video quay sẵn của nạn nhân. | Cao | Bắt buộc có |
| **3D Mask / Silicone** | Kẻ gian đeo mặt nạ 3D in hình khuôn mặt nạn nhân. | Rất Cao | Tuỳ chọn (Dựa trên dataset có sẵn) |
| **Face Swap / Deepfake** | Dùng phần mềm thay đổi khuôn mặt ngay trên luồng camera ảo (Virtual Camera). | Cao | Đòi hỏi module Deepfake Detection (tương lai) |

## Quy trình End-to-End Verification Security

Kết quả trả về của hệ thống Verification không chỉ là `PASS/FAIL`, mà phải chia làm 3 ngưỡng:

1. **PASS:**
   - OCR Confidence > 95%
   - Face Similarity > Threshold (VD: 0.8)
   - Liveness Confidence > 98% (Xác nhận là Live Video)
2. **REVIEW (Cần người kiểm duyệt):**
   - OCR đọc bị mờ / thiếu thông tin / chói lóa.
   - Điểm Face Similarity nằm ở vùng biên (Borderline, VD: 0.7 - 0.79).
   - Liveness có dấu hiệu bị nhiễu sóng màn hình nhưng chưa chắc chắn.
3. **FAIL:**
   - Liveness phát hiện rõ đây là Printed Photo hoặc Replay Video.
   - Khuôn mặt CCCD và Selfie hoàn toàn khác nhau (Cosine Similarity < 0.5).
   - Sai lệch thông tin trường dữ liệu.

> **NGUYÊN TẮC:** Trong eKYC, False Accept Rate (Nhận diện nhầm kẻ gian thành người thật) nguy hiểm hơn hàng trăm lần so với lỗi sai chính tả của OCR.
