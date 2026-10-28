# Tiêu chuẩn Tái tạo Thực nghiệm (Reproducibility & Experiment Tracking)

Bởi vì dự án huấn luyện Model 100% From Scratch (Random Initialization), số lượng thí nghiệm (Experiment) sẽ sinh ra rất lớn. Để đảm bảo mọi thí nghiệm đều có thể lặp lại chính xác (Reproducibility) bởi bất kỳ kỹ sư nào khác, chúng ta tuân thủ quy tắc ghi log (Tracking) như sau:

## Experiment Config Log Template

Mỗi lần chạy huấn luyện, hệ thống phải sinh ra một file config lưu lại tại thư mục `docs/experiments/`.

**Ví dụ một file `EXP-FACE-00017.yaml`:**
```yaml
experiment_id: "EXP-FACE-00017"
model: 
  architecture: "MobileFaceNet"
  embedding_dim: 128
  pretrained: false
  initialization: "random"
dataset:
  name: "face_v3_augmented"
  version: "v3.1.0"
  train_identities: 80000
  val_identities: 10000
training:
  seed: 42
  optimizer: "AdamW"
  lr: 0.001
  batch_size: 128
  epochs: 50
  loss: "ArcFace"
metrics:
  best_val_accuracy: 0.985
  EER: 0.012
checkpoint_path: "export/EXP-FACE-00017_best.pt"
```

## Quy tắc Bắt buộc
1. **Pretrained Weights:** Luôn phải khai báo `pretrained: false` trong config. Nghiêm cấm việc load ngầm trọng số từ `torchvision` (VD: `weights=ResNet50_Weights.IMAGENET1K_V1`).
2. **Random Seed:** Luôn phải ghim cứng (fix) random seed cho `torch`, `numpy`, `random` ở đầu file train để đảm bảo thuật toán sinh số ngẫu nhiên giống hệt nhau ở các lần chạy lại.
3. **Identity Leakage Check:** Bộ dữ liệu phải đi qua script kiểm tra trùng lặp danh tính (Identity) trước khi cấp phiên bản (dataset version) đưa vào config.
