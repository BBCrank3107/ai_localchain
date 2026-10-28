"""
HUẤN LUYỆN MODEL 2 MULTI-HEAD TRANSFORMER V2 (SSOT DRIVEN)
Kiến trúc:
- 1 Shared Deep Semantic Backbone (256 dims -> Residual GELU -> LayerNorm 512 dims)
- 11 Pure Failure Classification Heads (Zero Device Bleed)
- Auxiliary Severity Head (Low, Medium, High, Critical, UNKNOWN)
- Chạy tăng tốc trên GPU NVIDIA GeForce GTX 1650 (CUDA).
- Lưu checkpoint tại: model_2_diagnosis/weights_transformer_multihead/
"""

import os
import sys
import json
import time
import argparse
import random
import numpy as np
import joblib

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.model_selection import train_test_split

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SEVERITY_MAP = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3, "UNKNOWN": 4}
REV_SEVERITY_MAP = {0: "Low", 1: "Medium", 2: "High", 3: "Critical", 4: "UNKNOWN"}

class ResidualBlock(nn.Module):
    def __init__(self, dim, dropout=0.2):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(dim, dim),
            nn.LayerNorm(dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
            nn.LayerNorm(dim)
        )
        self.gelu = nn.GELU()

    def forward(self, x):
        return self.gelu(x + self.block(x))

class LocalChainMultiHeadDiagnosisNet(nn.Module):
    def __init__(self, text_dim=256, num_brands=30, brand_embed_dim=32, hidden_dim=512, device_head_classes: dict = None):
        super().__init__()
        self.brand_embedding = nn.Embedding(num_brands, brand_embed_dim)
        
        # 1. SHARED BACKBONE ENCODER
        self.shared_encoder = nn.Sequential(
            nn.Linear(text_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.2),
            ResidualBlock(hidden_dim, dropout=0.2),
            ResidualBlock(hidden_dim, dropout=0.2),
            nn.Linear(hidden_dim, 256),
            nn.LayerNorm(256),
            nn.GELU()
        )
        
        # 2. 11 MODULAR DEVICE CLASSIFICATION HEADS
        self.device_heads = nn.ModuleDict()
        head_in_dim = 256 + brand_embed_dim
        for dev_name, num_classes in device_head_classes.items():
            self.device_heads[dev_name] = nn.Sequential(
                nn.Linear(head_in_dim, 128),
                nn.LayerNorm(128),
                nn.GELU(),
                nn.Dropout(0.1),
                nn.Linear(128, num_classes)
            )
            
        # 3. AUXILIARY HEADS
        self.severity_head = nn.Sequential(
            nn.Linear(256, 64),
            nn.GELU(),
            nn.Linear(64, len(SEVERITY_MAP))
        )
        
        self.confidence_head = nn.Sequential(
            nn.Linear(256, 32),
            nn.GELU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, text_vec, brand_idx, target_device=None):
        feat = self.shared_encoder(text_vec)
        b_embed = self.brand_embedding(brand_idx)
        combined_feat = torch.cat([feat, b_embed], dim=-1)
        
        sev_logits = self.severity_head(feat)
        conf_pred = self.confidence_head(feat)
        
        if target_device and target_device in self.device_heads:
            fault_logits = self.device_heads[target_device](combined_feat)
            return fault_logits, sev_logits, conf_pred
            
        return feat, combined_feat, sev_logits, conf_pred

class MultiHeadDiagnosisDataset(Dataset):
    def __init__(self, text_features, dev_indices, brand_indices, fault_indices, sev_labels, device_keys):
        self.text_features = torch.tensor(text_features, dtype=torch.float32)
        self.dev_indices = torch.tensor(dev_indices, dtype=torch.long)
        self.brand_indices = torch.tensor(brand_indices, dtype=torch.long)
        self.fault_indices = torch.tensor(fault_indices, dtype=torch.long)
        self.sev_labels = torch.tensor(sev_labels, dtype=torch.long)
        self.device_keys = device_keys

    def __len__(self):
        return len(self.text_features)

    def __getitem__(self, idx):
        return (
            self.text_features[idx],
            self.dev_indices[idx],
            self.brand_indices[idx],
            self.fault_indices[idx],
            self.sev_labels[idx],
            self.device_keys[idx]
        )

def train_multihead_model(epochs=20, batch_size=64, lr=0.001, data_path=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if data_path is None:
        data_path = os.path.join(base_dir, "datasets", "diagnosis", "localchain_canonical_augmented.json")
    taxonomy_path = os.path.join(base_dir, "datasets", "diagnosis", "fault_taxonomy.json")
    weights_dir = os.path.join(base_dir, "model_2_diagnosis", "weights_transformer_multihead")
    os.makedirs(weights_dir, exist_ok=True)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 85)
    print("🚀 KHỞI ĐỘNG HUẤN LUYỆN MULTI-HEAD TRANSFORMER V2 (SSOT SCHEMA)")
    print("=" * 85)
    print(f"💻 Thiết bị tính toán: {device}")
    if torch.cuda.is_available():
        print(f"🔥 Card đồ họa: {torch.cuda.get_device_name(0)} | VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    print("-" * 85)
    
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)
        
    device_fault_maps = {}
    device_head_classes = {}
    
    for dev_name, info in taxonomy["devices"].items():
        fault_list = [f["fault_code"] for f in info["faults"]]
        device_fault_maps[dev_name] = {f_code: idx for idx, f_code in enumerate(fault_list)}
        device_head_classes[dev_name] = len(fault_list)
        
    with open(data_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    print(f"📖 Đã nạp thành công {len(dataset):,} mẫu huấn luyện từ {data_path}.")
    
    unique_brands = sorted(list(set(d.get("brand", "Unknown") for d in dataset)))
    brand2idx = {b: i for i, b in enumerate(unique_brands)}
    unique_devices = list(taxonomy["devices"].keys())
    dev2idx = {d: i for i, d in enumerate(unique_devices)}
    
    texts = []
    dev_idxs = []
    brand_idxs = []
    fault_idxs = []
    sev_labels = []
    dev_keys = []
    
    for d in dataset:
        dev = d.get("device", "laptop")
        if dev not in device_fault_maps:
            continue
        f_code = d.get("fault_code")
        if f_code not in device_fault_maps[dev]:
            continue
            
        texts.append(d.get("symptom", ""))
        dev_idxs.append(dev2idx[dev])
        brand_idxs.append(brand2idx.get(d.get("brand", "Unknown"), 0))
        fault_idxs.append(device_fault_maps[dev][f_code])
        sev_labels.append(SEVERITY_MAP.get(d.get("severity", "Medium"), 1))
        dev_keys.append(dev)
        
    print(f"🎯 Số lượng mẫu hợp lệ đưa vào huấn luyện: {len(texts):,} mẫu.")
    print(f"🏛️ Khởi tạo 11 Heads chuyên biệt: {json.dumps(device_head_classes, ensure_ascii=False)}")
    print("-" * 85)
    
    print("🧠 Đang tính toán ma trận biểu diễn ngữ nghĩa (TF-IDF N-gram + SVD 256 chiều)...")
    tfidf = TfidfVectorizer(max_features=12000, ngram_range=(1, 2), sublinear_tf=True)
    svd = TruncatedSVD(n_components=256, random_state=42)
    
    tfidf_mat = tfidf.fit_transform(texts)
    text_features = svd.fit_transform(tfidf_mat).astype(np.float32)
    joblib.dump({"tfidf": tfidf, "svd": svd}, os.path.join(weights_dir, "tfidf_svd.pkl"))
    
    indices = np.arange(len(texts))
    train_idx, val_idx = train_test_split(indices, test_size=0.15, random_state=42, stratify=dev_idxs)
    
    train_dataset = MultiHeadDiagnosisDataset(
        text_features[train_idx],
        [dev_idxs[i] for i in train_idx],
        [brand_idxs[i] for i in train_idx],
        [fault_idxs[i] for i in train_idx],
        [sev_labels[i] for i in train_idx],
        [dev_keys[i] for i in train_idx]
    )
    
    val_dataset = MultiHeadDiagnosisDataset(
        text_features[val_idx],
        [dev_idxs[i] for i in val_idx],
        [brand_idxs[i] for i in val_idx],
        [fault_idxs[i] for i in val_idx],
        [sev_labels[i] for i in val_idx],
        [dev_keys[i] for i in val_idx]
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    print(f"📊 Tập huấn luyện (Train): {len(train_dataset):,} mẫu ({len(train_loader)} batches/epoch)")
    print(f"📊 Tập kiểm thử (Validation): {len(val_dataset):,} mẫu ({len(val_loader)} batches)")
    print("-" * 85)
    
    model = LocalChainMultiHeadDiagnosisNet(
        text_dim=256,
        num_brands=len(unique_brands),
        brand_embed_dim=32,
        hidden_dim=512,
        device_head_classes=device_head_classes
    ).to(device)
    
    ce_loss_fn = nn.CrossEntropyLoss()
    mse_loss_fn = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    
    best_val_acc = 0.0
    best_model_path = os.path.join(weights_dir, "best_multihead_model.pt")
    
    print("⚡ BẮT ĐẦU VÒNG LẶP HUẤN LUYỆN THEO TỪNG EPOCH...")
    print("=" * 85)
    print(f"{'Epoch':<10}|{'Train Loss':<14}|{'Val Loss':<12}|{'Val Acc@1':<12}|{'LR':<12}|{'Thời gian':<16}")
    print("-" * 85)
    
    start_total_time = time.time()
    
    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        model.train()
        total_train_loss = 0.0
        
        for t_feat, d_idx, b_idx, f_idx, s_idx, d_key in train_loader:
            t_feat = t_feat.to(device)
            b_idx = b_idx.to(device)
            f_idx = f_idx.to(device)
            s_idx = s_idx.to(device)
            
            optimizer.zero_grad()
            feat, comb_feat, sev_logits, conf_pred = model(t_feat, b_idx)
            
            head_loss = torch.tensor(0.0, device=device)
            valid_heads_count = 0
            
            for dev_name in device_head_classes.keys():
                mask = [k == dev_name for k in d_key]
                if any(mask):
                    mask_tensor = torch.tensor(mask, dtype=torch.bool, device=device)
                    sub_feat = comb_feat[mask_tensor]
                    sub_targets = f_idx[mask_tensor]
                    
                    sub_logits = model.device_heads[dev_name](sub_feat)
                    h_loss = ce_loss_fn(sub_logits, sub_targets)
                    head_loss = head_loss + h_loss
                    valid_heads_count += 1
                    
            if valid_heads_count > 0:
                head_loss = head_loss / valid_heads_count
                
            sev_loss = ce_loss_fn(sev_logits, s_idx)
            conf_targets = torch.ones_like(conf_pred)
            conf_loss = mse_loss_fn(conf_pred, conf_targets)
            
            loss = head_loss + 0.3 * sev_loss + 0.1 * conf_loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            total_train_loss += loss.item()
            
        scheduler.step()
        avg_train_loss = total_train_loss / len(train_loader)
        
        model.eval()
        total_val_loss = 0.0
        correct_count = 0
        total_count = 0
        device_correct = {dev: 0 for dev in device_head_classes.keys()}
        device_total = {dev: 0 for dev in device_head_classes.keys()}
        
        with torch.no_grad():
            for t_feat, d_idx, b_idx, f_idx, s_idx, d_key in val_loader:
                t_feat = t_feat.to(device)
                b_idx = b_idx.to(device)
                f_idx = f_idx.to(device)
                s_idx = s_idx.to(device)
                
                feat, comb_feat, sev_logits, conf_pred = model(t_feat, b_idx)
                
                head_loss = torch.tensor(0.0, device=device)
                valid_heads_count = 0
                
                for dev_name in device_head_classes.keys():
                    mask = [k == dev_name for k in d_key]
                    if any(mask):
                        mask_tensor = torch.tensor(mask, dtype=torch.bool, device=device)
                        sub_feat = comb_feat[mask_tensor]
                        sub_targets = f_idx[mask_tensor]
                        
                        sub_logits = model.device_heads[dev_name](sub_feat)
                        h_loss = ce_loss_fn(sub_logits, sub_targets)
                        head_loss = head_loss + h_loss
                        valid_heads_count += 1
                        
                        preds = torch.argmax(sub_logits, dim=-1)
                        c = (preds == sub_targets).sum().item()
                        t = len(sub_targets)
                        
                        correct_count += c
                        total_count += t
                        device_correct[dev_name] += c
                        device_total[dev_name] += t
                        
                if valid_heads_count > 0:
                    head_loss = head_loss / valid_heads_count
                    
                sev_loss = ce_loss_fn(sev_logits, s_idx)
                loss = head_loss + 0.3 * sev_loss
                total_val_loss += loss.item()
                
        avg_val_loss = total_val_loss / len(val_loader)
        val_acc = (correct_count / max(1, total_count)) * 100.0
        epoch_time = time.time() - epoch_start
        current_lr = scheduler.get_last_lr()[0]
        
        is_best = val_acc > best_val_acc
        star = "⭐ (Best Checkpoint)" if is_best else ""
        
        if is_best:
            best_val_acc = val_acc
            torch.save(model.state_dict(), best_model_path)
            
        print(f"[{epoch:<2}/{epochs}]    |    {avg_train_loss:<10.4f}|   {avg_val_loss:<9.4f}|   {val_acc:>5.2f}  % |  {current_lr:<10.6f}|   {epoch_time:>5.2f}  s {star}")
        
    total_time = time.time() - start_total_time
    print("-" * 85)
    print(f"🎉 HOÀN TẤT HUẤN LUYỆN MULTI-HEAD V2! Tổng thời gian: {total_time:.1f}s ({total_time/60:.2f} phút)")
    print(f"🏆 Độ chính xác toàn thể cao nhất (Best Val Acc@1): {best_val_acc:.2f}%")
    print(f"💾 Checkpoint mô hình: {best_model_path}")
    print("=" * 85)
    
    print("📊 ĐỘ CHÍNH XÁC CHI TIẾT TỪNG HEAD THIẾT BỊ (VAL ACCURACY):")
    for dev, c in device_correct.items():
        tot = device_total[dev]
        acc = (c / max(1, tot)) * 100.0
        name_vn = taxonomy["devices"][dev]["device_name_vn"]
        print(f"   • [{dev.upper():<15}] : {acc:>6.2f}% ({c}/{tot} mẫu) - {name_vn}")
    print("=" * 85)
    
    meta_path = os.path.join(weights_dir, "multihead_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "unique_devices": unique_devices,
            "unique_brands": unique_brands,
            "dev2idx": dev2idx,
            "brand2idx": brand2idx,
            "device_fault_maps": device_fault_maps,
            "device_head_classes": device_head_classes,
            "best_val_acc": best_val_acc,
            "hidden_dim": 512,
            "text_dim": 256,
            "severity_map": SEVERITY_MAP
        }, f, ensure_ascii=False, indent=2)
    print(f"📁 Đã lưu Metadata tại: {meta_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Huấn luyện Multi-Head Model 2 với PyTorch")
    parser.add_argument("--epochs", type=int, default=20, help="Số epoch huấn luyện")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--data_path", type=str, default=None, help="Đường dẫn file dataset huấn luyện (.json)")
    args = parser.parse_args()
    
    train_multihead_model(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, data_path=args.data_path)
