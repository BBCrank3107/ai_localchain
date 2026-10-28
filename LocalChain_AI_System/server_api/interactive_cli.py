"""
LOCALCHAIN AI - INTERACTIVE CLI TEST TOOL
Cho phép kỹ sư / người dùng kiểm thử trực tiếp các câu phàn nàn trên Terminal.
"""

import sys
from model_2_diagnosis.inference_multihead import multihead_ai
from model_3_pricing.inference_pricing import pricing_ai
from subsystem_rag.retriever import rag_ai
from subsystem_nlg.nlg_engine import generate_natural_message

def main():
    print("=" * 75)
    print("🤖 CHƯƠNG TRÌNH KIỂM THỬ TRỰC TIẾP HỆ SINH THÁI LOCALCHAIN AI")
    print("=" * 75)
    devices = [
        "dieu_hoa", "tu_lanh", "may_giat", "laptop", "quat", 
        "tivi", "may_loc_nuoc", "may_in", "may_bom", "noi_com", "lo_vi_song"
    ]
    print("Danh sách 11 thiết bị hỗ trợ: " + ", ".join(devices))
    print("💡 Gõ 'exit' hoặc 'quit' để dừng.\n")

    while True:
        try:
            device = input("\n📱 Nhập mã thiết bị (vd: laptop, dieu_hoa, tu_lanh...): ").strip().lower()
            if device in ["exit", "quit", "q"]:
                break
            if not device:
                continue

            complaint = input("✍️ Nhập mô tả triệu chứng hư hỏng (tiếng Việt): ").strip()
            if complaint in ["exit", "quit", "q"]:
                break
            if not complaint:
                print("⚠️ Vui lòng nhập mô tả lỗi!")
                continue

            print("\n⏳ Đang phân tích qua Mạng Nơ-ron Chẩn Đoán Multi-Head & Định Giá ML...")
            diag_res = multihead_ai.diagnose(device, complaint)
            if not diag_res.get("success", False):
                print(f"❌ {diag_res.get('error', 'Lỗi phân tích')}")
                continue
                
            if not diag_res.get("is_fault", True):
                print(f"\n🎉 {diag_res.get('natural_message')}")
                continue
                
            primary = diag_res["primary_diagnosis"]
            fault = primary["fault_name_vn"]
            severity = primary["severity"]
            predicted_faults = diag_res.get("predicted_faults", [primary])
            pricing_result = pricing_ai.predict_compound_prices(device, predicted_faults, complaint_text=complaint)
            total_price = pricing_result["total_price_vnd"]
            itemized_prices = pricing_result["itemized_prices"]
            discount_vnd = pricing_result["discount_vnd"]
            
            guide = rag_ai.query(device, complaint)
            has_guide = bool(guide and len(guide) > 30)

            print("\n" + "-" * 60)
            print("🎯 KẾT QUẢ PHÂN TÍCH KỸ THUẬT:")
            print(f"  • Thiết bị           : {diag_res.get('device_name_vn', device)}")
            print(f"  • Bệnh chẩn đoán chính: {fault}")
            print(f"  • Mức độ nghiêm trọng: {severity}")
            print(f"  • Độ tin cậy         : {primary.get('probability', 95):.1f}%")
            print(f"  • Chi phí dự kiến    : {int(total_price):,} VNĐ".replace(",", "."))
            print("-" * 60)

            msg = generate_natural_message(
                device_key=device,
                complaint=complaint,
                predicted_fault=fault,
                severity=severity,
                estimated_price=total_price,
                predicted_faults=predicted_faults,
                itemized_prices=itemized_prices,
                discount_vnd=discount_vnd,
                has_guide=has_guide,
                difficulty_score=primary.get("difficulty_score", 2.0),
                difficulty_obj=primary.get("difficulty")
            )
            print("\n💬 CÂU TRẢ LỜI CHO KHÁCH HÀNG:")
            print(msg)
            
            if guide and has_guide:
                print("\n📖 CẨM NANG HƯỚNG DẪN XỬ LÝ (RAG):")
                print(guide[:400] + "...\n")
                
        except KeyboardInterrupt:
            print("\nĐã dừng chương trình.")
            break
        except Exception as e:
            print(f"❌ Lỗi: {str(e)}")

if __name__ == "__main__":
    main()

