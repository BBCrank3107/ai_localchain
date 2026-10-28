import os
import torch
import sys

# Đảm bảo import được module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline.stage_3_face_matching.models.mobilefacenet import MobileFaceNet
from pipeline.stage_2_liveness.models.temporal_liveness import TemporalLivenessNet

def export_face_model(model_path=None, output_path="export/mobilefacenet.onnx"):
    print("[*] Bắt đầu xuất mô hình MobileFaceNet sang ONNX...")
    model = MobileFaceNet(embedding_dim=128)
    model.eval() # Bắt buộc phải đưa model về chế độ đánh giá trước khi export
    
    # Tạo Input giả lập (Dummy Input) cho Batch Size = 1
    # Model mong đợi: (Batch, Channels, Height, Width) -> (1, 3, 112, 112)
    dummy_input = torch.randn(1, 3, 112, 112)
    
    os.makedirs("export", exist_ok=True)
    
    # Export
    torch.onnx.export(
        model, 
        dummy_input, 
        output_path, 
        export_params=True, 
        opset_version=11, 
        do_constant_folding=True, 
        input_names=['input_image'], 
        output_names=['face_embedding'],
        dynamic_axes={'input_image': {0: 'batch_size'}, 'face_embedding': {0: 'batch_size'}}
    )
    
    print(f"[+] Xuất thành công: {output_path}")
    print("[+] Model này có thể chạy trên thiết bị Mobile thông qua ONNX Runtime (C++ / Java).")

def export_liveness_model(model_path=None, output_path="export/temporal_liveness.onnx"):
    print("[*] Bắt đầu xuất mô hình Temporal Liveness sang ONNX...")
    model = TemporalLivenessNet()
    model.eval()
    
    # Giả lập Video: 1 Batch, 5 Frames, 3 Channels, 224x224
    dummy_video = torch.randn(1, 5, 3, 224, 224)
    
    torch.onnx.export(
        model, 
        dummy_video, 
        output_path, 
        export_params=True, 
        opset_version=11, 
        do_constant_folding=True, 
        input_names=['input_video_frames'], 
        output_names=['liveness_score'],
        dynamic_axes={
            'input_video_frames': {0: 'batch_size', 1: 'seq_length'}, 
            'liveness_score': {0: 'batch_size'}
        }
    )
    
    print(f"[+] Xuất thành công: {output_path}")

if __name__ == "__main__":
    print("=" * 50)
    print(" CÔNG CỤ CHUYỂN ĐỔI MÔ HÌNH SANG ONNX (CHO MOBILE)")
    print("=" * 50)
    
    export_face_model()
    export_liveness_model()
    
    print("=" * 50)
    print("[!] Ghi chú: Sau khi xuất ra file .onnx, cần chạy thêm công cụ 'onnx-simplifier'")
    print("    để tối ưu hóa kích thước file trước khi nạp vào App Android/iOS.")
