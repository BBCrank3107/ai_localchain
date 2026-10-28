import numpy as np

def generate_mock_liveness_scores():
    """Giả lập điểm số Xác suất Live (0 -> 1) của mô hình Temporal Liveness"""
    # Bona Fide (Người thật, Video Live): Điểm gần 1
    bona_fide = np.random.normal(loc=0.85, scale=0.1, size=500)
    bona_fide = np.clip(bona_fide, 0.0, 1.0)
    
    # Attack Presentations (Ảnh in, Video phát lại): Điểm gần 0
    # Giả lập 2 loại tấn công
    attack_print = np.random.normal(loc=0.1, scale=0.05, size=200)
    attack_replay = np.random.normal(loc=0.3, scale=0.15, size=300) # Replay thường khó phát hiện hơn ảnh in
    
    return bona_fide, attack_print, attack_replay

def compute_apcer_bpcer(bona_fide, attack_1, attack_2, threshold=0.5):
    """
    Tính toán theo chuẩn ISO/IEC 30107-3:
    APCER: Tỷ lệ tấn công vượt qua thành công (Nhận nhầm là Live).
    BPCER: Tỷ lệ người thật bị từ chối (Nhận nhầm là Tấn công).
    """
    # 1. BPCER (Bona Fide Presentation Classification Error Rate)
    # Lỗi khi Người thật (Bona Fide) có điểm thấp hơn Threshold
    false_rejects = np.sum(bona_fide < threshold)
    bpcer = false_rejects / len(bona_fide)
    
    # 2. APCER (Attack Presentation Classification Error Rate)
    # Lỗi khi Kẻ tấn công (Attack) có điểm cao hơn Threshold
    # Tính riêng cho từng loại tấn công, APCER của hệ thống là giá trị TỒI TỆ NHẤT (Max)
    apcer_1 = np.sum(attack_1 >= threshold) / len(attack_1)
    apcer_2 = np.sum(attack_2 >= threshold) / len(attack_2)
    
    apcer = max(apcer_1, apcer_2)
    
    # 3. ACER (Average Classification Error Rate)
    acer = (apcer + bpcer) / 2
    
    return apcer, bpcer, acer, apcer_1, apcer_2

if __name__ == "__main__":
    print("[*] Đang đánh giá (Evaluation) model Temporal Liveness theo chuẩn ISO/IEC 30107-3...")
    bona_fide, attack_print, attack_replay = generate_mock_liveness_scores()
    
    thresholds_to_test = [0.3, 0.5, 0.7, 0.8]
    
    print("-" * 60)
    print(" BÁO CÁO ĐÁNH GIÁ MÔ HÌNH CHỐNG GIẢ MẠO (ANTI-SPOOFING)")
    print("-" * 60)
    
    for th in thresholds_to_test:
        apcer, bpcer, acer, ap1, ap2 = compute_apcer_bpcer(bona_fide, attack_print, attack_replay, threshold=th)
        print(f"Ngưỡng (Threshold): {th:.2f}")
        print(f"  - BPCER (Từ chối nhầm người thật): {bpcer*100:.2f}%")
        print(f"  - APCER (Ảnh in qua mặt)         : {ap1*100:.2f}%")
        print(f"  - APCER (Replay qua mặt)         : {ap2*100:.2f}%")
        print(f"  => Tổng thể APCER hệ thống (Max) : {apcer*100:.2f}%")
        print(f"  => ACER (Điểm trung bình)        : {acer*100:.2f}%\n")
    
    print("[!] Ghi chú: Trong ngân hàng, ưu tiên giảm APCER (Không để lọt tội phạm), chấp nhận BPCER cao một chút (Khách hàng thử lại lần 2).")
