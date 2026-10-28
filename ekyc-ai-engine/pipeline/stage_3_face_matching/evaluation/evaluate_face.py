import numpy as np
import matplotlib.pyplot as plt
import os

def generate_mock_scores():
    """Giả lập điểm số Cosine Similarity của 1 hệ thống Face Recognition"""
    # Positive pairs (Cùng một người): Điểm tập trung cao (0.6 -> 1.0)
    pos_scores = np.random.normal(loc=0.8, scale=0.1, size=1000)
    pos_scores = np.clip(pos_scores, 0.0, 1.0)
    
    # Negative pairs (Khác người): Điểm tập trung thấp (0.0 -> 0.5)
    neg_scores = np.random.normal(loc=0.3, scale=0.15, size=10000) # Negative bao giờ cũng nhiều hơn
    neg_scores = np.clip(neg_scores, 0.0, 1.0)
    
    return pos_scores, neg_scores

def compute_far_frr_eer(pos_scores, neg_scores, num_thresholds=1000):
    """Tính toán FAR, FRR và tìm EER"""
    thresholds = np.linspace(0, 1, num_thresholds)
    
    fars = []
    frrs = []
    
    for th in thresholds:
        # Nhận diện sai kẻ gian thành người thật (False Accept)
        fa = np.sum(neg_scores >= th)
        far = fa / len(neg_scores)
        
        # Nhận diện sai người thật thành kẻ gian (False Reject)
        fr = np.sum(pos_scores < th)
        frr = fr / len(pos_scores)
        
        fars.append(far)
        frrs.append(frr)
        
    fars = np.array(fars)
    frrs = np.array(frrs)
    
    # Tìm ngưỡng mà FAR và FRR gần nhau nhất (EER)
    diff = np.abs(fars - frrs)
    eer_index = np.argmin(diff)
    eer = (fars[eer_index] + frrs[eer_index]) / 2
    best_threshold = thresholds[eer_index]
    
    return thresholds, fars, frrs, eer, best_threshold

def plot_roc_curve(fars, frrs, eer, eer_th):
    """Vẽ biểu đồ ROC (FAR vs FRR)"""
    os.makedirs("docs/plots", exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    plt.plot(fars, frrs, label='ROC Curve', color='blue', linewidth=2)
    
    # Điểm EER
    plt.plot(fars[np.argmin(np.abs(fars-frrs))], frrs[np.argmin(np.abs(fars-frrs))], 
             marker='o', markersize=8, color='red', label=f'EER = {eer:.4f} @ Th={eer_th:.3f}')
    
    # Đường x = y
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Random Guess')
    
    plt.xscale('log') # Thường dùng log scale cho trục x (FAR) trong nhận diện khuôn mặt
    plt.yscale('log')
    plt.xlim([1e-4, 1])
    plt.ylim([1e-4, 1])
    
    plt.title('Face Recognition - Detection Error Tradeoff (DET/ROC)', fontsize=14)
    plt.xlabel('False Acceptance Rate (FAR)', fontsize=12)
    plt.ylabel('False Rejection Rate (FRR)', fontsize=12)
    plt.grid(True, which="both", ls="--")
    plt.legend(fontsize=12)
    
    plot_path = "docs/plots/face_roc_curve.png"
    plt.savefig(plot_path)
    print(f"[+] Đã lưu biểu đồ ROC tại: {plot_path}")
    plt.close()

if __name__ == "__main__":
    print("[*] Đang đánh giá (Evaluation) model Face Recognition...")
    pos, neg = generate_mock_scores()
    
    print("[*] Tính toán dải FAR, FRR và EER...")
    thresholds, fars, frrs, eer, best_th = compute_far_frr_eer(pos, neg)
    
    print("-" * 40)
    print(" BÁO CÁO ĐÁNH GIÁ MÔ HÌNH KHUÔN MẶT")
    print("-" * 40)
    print(f"Equal Error Rate (EER)  : {eer*100:.2f} %")
    print(f"Ngưỡng Tối Ưu (Threshold) : {best_th:.3f}")
    
    # Trong thực tế ngân hàng thường chọn FAR rất thấp (0.01% hoặc 0.1%)
    target_far = 0.001 # 0.1%
    idx = np.argmin(np.abs(fars - target_far))
    print(f"Ngưỡng tại FAR=0.1% (An toàn cao): {thresholds[idx]:.3f} (FRR: {frrs[idx]*100:.2f}%)")
    
    plot_roc_curve(fars, frrs, eer, best_th)
