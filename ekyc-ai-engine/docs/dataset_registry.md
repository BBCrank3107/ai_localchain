# Dataset Registry & Acceptance Criteria

Bất kỳ bộ dữ liệu nào trước khi đưa vào thư mục `datasets/` để phục vụ huấn luyện Model đều phải vượt qua 5 tiêu chí (Acceptance Criteria) dưới đây và được ghi danh vào bảng Registry.

## Dataset Acceptance Criteria

1. **Source verified?** (Xác minh được cá nhân/tổ chức công bố dữ liệu).
2. **License verified?** (Giấy phép bản quyền phải cho phép nghiên cứu hoặc thương mại).
3. **Personal data restrictions?** (Không chứa thông tin danh tính chưa được che mờ, không rò rỉ dữ liệu cá nhân theo PDPL).
4. **Annotation verified?** (Phương pháp gán nhãn phải đạt độ chính xác > 90%).
5. **Distribution suitable?** (Phân phối dữ liệu có đủ độ đa dạng, ví dụ: tỷ lệ Nam/Nữ, vùng miền, độ tuổi).

## Dataset Registry

| Dataset ID | Name | Provenance | License | Privacy Check | Target Model | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DS-DOC-001** | Roboflow Vietnamese ID Card | Roboflow Universe | CC BY 4.0 | ⚠️ Restricted (Real Faces) | CCCD Detection | ⚠️ *Rejected for Production (Needs scrubbing)* |
| **DS-DOC-002** | Synthetic CCCD Dataset V1 | Internal Gen | Proprietary | ✅ Safe (Synthetic) | OCR & Detection | ✅ *Approved (Train/Val)* |
| **DS-FACE-001** | V-FACE (Vietnamese Face) | Academic Paper | Academic | ⚠️ Restricted | Face Recognition | ✅ *Approved for Research* |
| **DS-LIVENESS-001** | CASIA-FASD | CASIA Institute | Academic | ✅ Safe (Consented) | Temporal Liveness | ✅ *Approved for Research* |

> *Ghi chú: Unknown license = Cấm sử dụng. Các bộ dataset Academic chỉ được dùng cho mục đích Research (như dự án này), không được dùng thương mại nếu chưa xin phép tác giả.*
