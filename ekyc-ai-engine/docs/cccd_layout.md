# Cấu trúc Thẻ Căn cước (CCCD / Căn cước mới) Việt Nam

Tài liệu này lưu trữ đặc tả chi tiết các trường thông tin trên thẻ ID của Việt Nam, phục vụ cho việc gán nhãn (Labeling) huấn luyện YOLOv8 và trích xuất OCR.

Dữ liệu hỗ trợ cả 2 phiên bản: **Căn cước công dân** (Mẫu cũ) và **Căn cước** (Mẫu mới).

## 1. Mặt trước (Obverse Side)

### Phần Tiêu đề (Header)
*   **Quốc hiệu:** `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM` / `SOCIALIST REPUBLIC OF VIET NAM`
*   **Tiêu ngữ:** `Độc lập - Tự do - Hạnh phúc` / `Independence - Freedom - Happiness`
*   **Tên thẻ:** 
    *   Mẫu cũ: `CĂN CƯỚC CÔNG DÂN` / `CITIZEN IDENTITY CARD`
    *   Mẫu mới: `CĂN CƯỚC` / `IDENTITY CARD`

### Các trường thông tin cá nhân (Fields)
1.  **Số định danh / ID Number:**
    *   Mẫu cũ: `Số / No.:`
    *   Mẫu mới: `Số định danh cá nhân / No.:`
    *   *Định dạng:* Chuỗi 12 chữ số.
2.  **Họ và tên / Full Name:**
    *   Mẫu cũ: `Họ và tên / Full name:`
    *   Mẫu mới: `Họ, chữ đệm và tên khai sinh / Surname, given names:`
3.  **Ngày sinh / Date of Birth:**
    *   `Ngày, tháng, năm sinh / Date of birth:`
4.  **Giới tính / Sex:**
    *   `Giới tính / Sex:` (Nam/Male hoặc Nữ/Female)
5.  **Quốc tịch / Nationality:**
    *   `Quốc tịch / Nationality:` (VIỆT NAM / VIETNAMESE)
6.  **Quê quán / Nơi đăng ký khai sinh:**
    *   Mẫu cũ: `Quê quán / Place of origin:`
    *   Mẫu mới: `Nơi đăng ký khai sinh / Place of birth registration:` (Lưu ý: Mẫu mới chuyển trường này sang mặt sau)
7.  **Nơi thường trú / Nơi cư trú:**
    *   Mẫu cũ: `Nơi thường trú / Place of residence:`
    *   Mẫu mới: `Nơi cư trú / Place of residence:` (Nằm ở mặt sau)
8.  **Ngày hết hạn / Expiry Date:**
    *   `Có giá trị đến / Date of expiry:`

## 2. Mặt sau (Reverse Side)

1.  **Đặc điểm nhân dạng (Chỉ mẫu cũ):**
    *   `Đặc điểm nhân dạng / Personal identification:`
2.  **Ngày cấp thẻ:**
    *   `Ngày, tháng, năm / Date, month, year:`
    *   Mẫu mới: `Ngày, tháng, năm cấp / Date, month, year:`
3.  **Cơ quan cấp:**
    *   Mẫu cũ: `CỤC TRƯỞNG CỤC CẢNH SÁT QUẢN LÝ HÀNH CHÍNH VỀ TRẬT TỰ XÃ HỘI`
    *   Mẫu mới: `BỘ CÔNG AN / MINISTRY OF PUBLIC SECURITY`

## 3. Cấu trúc JSON dự kiến từ OCR Engine

Hệ thống OCR sẽ trả về cấu trúc chuẩn hóa sau:

```json
{
  "id_number": "001099123456",
  "full_name": "NGUYỄN VĂN A",
  "dob": "01/01/2000",
  "sex": "Nam",
  "nationality": "VIỆT NAM",
  "place_of_origin": "Xã X, Huyện Y, Tỉnh Z",
  "place_of_residence": "Phường A, Quận B, TP C",
  "date_of_expiry": "01/01/2040"
}
```
