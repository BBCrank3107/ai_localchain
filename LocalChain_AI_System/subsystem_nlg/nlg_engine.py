"""
HỆ THỐNG PHỤ TRỢ 2: BỘ TẠO CÂU NGỮ NGHĨA TỰ NHIÊN (DYNAMIC BRAND-AWARE SEMANTIC NLG ENGINE)
Nhiệm vụ: Tạo câu phản hồi tiếng Việt tự nhiên, chuyên nghiệp cho cả ca bệnh đơn lẻ, đa lỗi và tương tác theo hãng.
Hiển thị minh bạch chi phí bóc tách: [Phương án xử lý + Tiền linh kiện BOM + Tiền công thợ].
"""

DEVICE_NAME_MAP = {
    "dieu_hoa": "máy điều hòa không khí",
    "tu_lanh": "tủ lạnh",
    "may_giat": "máy giặt",
    "laptop": "máy tính xách tay (laptop)",
    "may_in": "máy in",
    "may_bom": "máy bơm nước",
    "quat": "quạt điện",
    "tivi": "ti vi (TV)",
    "may_loc_nuoc": "máy lọc nước",
    "noi_com": "nồi cơm điện",
    "lo_vi_song": "lò vi sóng"
}

SEVERITY_MAP = {
    "Low": "Nhẹ (Có thể tự khắc phục hoặc bảo dưỡng định kỳ)",
    "Medium": "Trung bình (Cần kiểm tra kỹ thuật hoặc thay thế linh kiện hao mòn)",
    "High": "Nghiêm trọng (Cần ngắt nguồn ngay để tránh chập cháy, hư hỏng lan rộng)",
    "Critical": "Rất nguy hiểm (Nguy cơ chập điện/cháy nổ cao, ngắt điện khẩn cấp)"
}

SAFETY_ADVICE_MAP = {
    "Critical": "**CẢNH BÁO AN TOÀN KHẨN CẤP:** Hãy ngắt cầu dao/Aptomat nguồn điện của thiết bị ngay lập tức để phòng ngừa nguy cơ chập cháy nổ hoặc giật điện.",
    "High": "**Cảnh báo an toàn:** Hãy ngắt nguồn điện của thiết bị ngay lập tức để phòng ngừa nguy cơ chập cháy hoặc hư hỏng linh kiện lân cận.",
    "Medium": "**Lời khuyên an toàn:** Khuyến nghị không nên tự ý tháo dỡ các bo mạch phức tạp nếu không có dụng cụ đo lường chuyên dụng.",
    "Low": "**Gợi ý:** Bạn có thể tham khảo quy trình vệ sinh và siết chặt các điểm tiếp xúc cơ học theo hướng dẫn bên dưới."
}

CONTEXT_ADVICE_MAP = {
    "PHYSICAL_IMPACT": (
        "**LƯU Ý DO VA ĐẬP VẬT LÝ:** Thiết bị có dấu hiệu rơi/vỡ ngoại lực. Quý khách tuyệt đối **không nên ấn mạnh** vào vùng màn hình bị nứt/sọc để tránh chập mạch đèn nền hoặc làm mảnh kính vỡ đâm thủng cell pin Lithium bên trong. Khuyến cáo mang máy đến kỹ thuật viên để thay cụm hiển thị và kiểm tra độ ổn định của khung vỏ/bản lề."
    ),
    "WATER_INGRESS": (
        "**CẢNH BÁO KHẨN CẤP DO NGẤM NƯỚC:** Tuyệt đối **không cắm sạc** hoặc cố bật nguồn thiết bị! Hãy ngắt nguồn/tháo pin ngay và đưa máy đi sấy khô, vệ sinh chống rỉ sét bo mạch để tránh chập cháy CPU và IC nguồn."
    ),
    "POWER_SURGE": (
        "**LƯU Ý VỀ XUNG ĐIỆN/QUÁ ÁP:** Thiết bị vừa trải qua sự cố nguồn điện. Cần kỹ thuật viên đo kiểm tra tụ lọc nguồn và cầu chì bảo vệ trước khi cấp điện trở lại."
    ),
    "OVERHEATING": (
        "**LƯU Ý VỀ QUÁ NHIỆT:** Hệ thống tản nhiệt đang hoạt động quá tải. Khuyến nghị vệ sinh bụi bẩn quạt tản nhiệt và tra keo gốm tản nhiệt chuyên dụng."
    )
}

def generate_natural_message(
    device_key: str,
    complaint: str,
    predicted_fault: str,
    severity: str,
    estimated_price: float,
    brand: str = None,
    predicted_faults: list = None,
    itemized_prices: list = None,
    discount_vnd: float = 0.0,
    has_guide: bool = False,
    clarification_prompt: str = "",
    difficulty_score: float = None,
    difficulty_obj: dict = None,
    root_cause_assessment: dict = None,
    detected_contexts: list = None
) -> str:
    dev_name = DEVICE_NAME_MAP.get(device_key.lower().strip(), "thiết bị")
    if brand and brand.lower() not in ["unknown", "none", "không", "bỏ qua", "string"]:
        dev_name = f"{dev_name} hãng **{brand}**"
        
    sev_desc = SEVERITY_MAP.get(severity, "Cần theo dõi kỹ thuật")
    
    # Xác định difficulty_obj và difficulty_score tổng thể nếu chưa truyền
    if difficulty_obj is None:
        if itemized_prices and len(itemized_prices) > 0 and "difficulty" in itemized_prices[0] and itemized_prices[0]["difficulty"]:
            difficulty_obj = itemized_prices[0]["difficulty"]
        elif predicted_faults and len(predicted_faults) > 0 and "difficulty" in predicted_faults[0] and predicted_faults[0]["difficulty"]:
            difficulty_obj = predicted_faults[0]["difficulty"]
            
    if difficulty_score is None:
        if difficulty_obj and "score" in difficulty_obj:
            difficulty_score = difficulty_obj["score"]
        elif itemized_prices and len(itemized_prices) > 0 and "difficulty_score" in itemized_prices[0]:
            difficulty_score = itemized_prices[0]["difficulty_score"]
        elif predicted_faults and len(predicted_faults) > 0 and "difficulty_score" in predicted_faults[0]:
            difficulty_score = predicted_faults[0]["difficulty_score"]
        else:
            difficulty_score = 2.0
            
    diff_score_float = float(difficulty_score)
    est_minutes = difficulty_obj.get("estimated_minutes", int(diff_score_float * 25)) if difficulty_obj else int(diff_score_float * 25)
    requires_pro = difficulty_obj.get("requires_professional", diff_score_float >= 3.0) if difficulty_obj else (diff_score_float >= 3.0)
            
    # Lời khuyên an toàn & Hướng dẫn kỹ thuật đa tầng
    diff_advice = ""
    # Ưu tiên cảnh báo bối cảnh ngoại lực (rơi vỡ / ngấm nước)
    ctx_list = detected_contexts or []
    if root_cause_assessment and "detected_contexts" in root_cause_assessment:
        ctx_list = list(set(ctx_list + root_cause_assessment.get("detected_contexts", [])))
        
    for ctx in ctx_list:
        if ctx in CONTEXT_ADVICE_MAP:
            diff_advice += f"\n\n{CONTEXT_ADVICE_MAP[ctx]}"
            
    if not diff_advice:
        if diff_score_float <= 1.8:
            diff_advice = f"\n\n**Gợi ý tự xử lý (DIY Friendly):** Sự cố này có mức độ kỹ thuật rất dễ (Độ khó: {diff_score_float:.1f}/5 - Ước tính: ~{est_minutes} phút). Quý khách có thể tự kiểm tra, vệ sinh hoặc thay thế nhanh tại nhà theo cẩm nang."
        elif diff_score_float <= 2.8:
            diff_advice = f"\n\n**Gợi ý kiểm tra:** Sự cố ở mức độ cơ bản (Độ khó: {diff_score_float:.1f}/5 - Ước tính: ~{est_minutes} phút). Bạn có thể kiểm tra giắc cắm/vệ sinh bề mặt trước khi quyết định mang đi sửa hoặc thay thế linh kiện."
        elif diff_score_float <= 3.8:
            diff_advice = f"\n\n**Lời khuyên kỹ thuật:** Sự cố có độ phức tạp trung bình (Độ khó: {diff_score_float:.1f}/5 - Thời gian ước tính: ~{est_minutes} phút). Khuyến nghị chuẩn bị dụng cụ mở máy chuyên dụng và thao tác cẩn thận, hoặc nhờ thợ hỗ trợ."
        elif diff_score_float < 4.5:
            diff_advice = f"\n\n**CẢNH BÁO AN TOÀN KỸ THUẬT:** Sự cố mức độ khó (Độ khó: {diff_score_float:.1f}/5 - Ước tính: ~{est_minutes} phút - Yêu cầu thợ chuyên môn). Khuyến cáo ngắt nguồn điện và không tự ý chọc đo mạch khi chưa có đồ nghề chuyên dụng để tránh chập cháy."
        else:
            diff_advice = f"\n\n**CẢNH BÁO CHUYÊN GIA PHÒNG LAB:** Sự cố chuyên sâu đặc biệt (Độ khó: {diff_score_float:.1f}/5 - Ước tính: ~{est_minutes} phút). Bắt buộc phải có trang thiết bị máy móc chuyên dụng và kỹ thuật viên bậc cao xử lý."

    price_formatted = f"{int(estimated_price):,} VNĐ".replace(",", ".")
    faults = predicted_faults or [{"fault": predicted_fault, "severity": severity, "confidence": 80.0, "difficulty_score": diff_score_float, "difficulty": difficulty_obj}]
    
    # Root Cause Section
    root_cause_text = ""
    if root_cause_assessment:
        c_desc = root_cause_assessment.get("cause_description_vn", "")
        r_risks = root_cause_assessment.get("risks_if_ignored", [])
        if c_desc:
            root_cause_text += f"\n\n**Phân tích nguyên nhân gốc rễ:** {c_desc}"
        if r_risks:
            root_cause_text += f"\n**Rủi ro nếu chậm xử lý:**\n" + "\n".join([f"  • {r}" for r in r_risks])
    
    if len(faults) > 1:
        header = f"Kính gửi Quý khách, dựa trên mô tả tình trạng ('{complaint}'), hệ thống chẩn đoán {dev_name} của bạn đang gặp **{len(faults)} sự cố đồng thời** sau:"
        
        faults_bullet = []
        for i, f in enumerate(faults, 1):
            f_name = f.get("fault", "")
            f_conf = f.get("probability", f.get("confidence", 80.0))
            f_sev = f.get("severity", "Medium")
            f_diff = f.get("difficulty_score", diff_score_float)
            faults_bullet.append(f"  {i}. **{f_name}** (Độ tin cậy: {f_conf:.0f}% - Mức độ: {f_sev} - Độ khó: {float(f_diff):.1f}/5)")
            
        body = "\n\n" + "\n".join(faults_bullet)
        body += f"\n\n**Mức độ ảnh hưởng tổng thể:** {sev_desc}"
        body += root_cause_text
        
        if itemized_prices and len(itemized_prices) > 0:
            body += "\n\n**Báo giá chi tiết từng hạng mục & Phương án xử lý:**\n"
            for item in itemized_prices:
                p_item_str = f"{int(item['price_vnd']):,} VNĐ".replace(",", ".")
                labor_str = f"{int(item.get('labor_fee', 100000)):,} VNĐ".replace(",", ".")
                comp_str = f"{int(item.get('component_price', item['price_vnd'] - item.get('labor_fee', 0))):,} VNĐ".replace(",", ".")
                action_str = f" [{item.get('action', 'Thay thế/Xử lý')}: {item.get('key_component', '')}]" if "action" in item or "key_component" in item else ""
                body += f"  • **{item['fault']}**{action_str}:\n    - Linh kiện: {comp_str} | Công thợ: {labor_str} -> Tổng: **{p_item_str}**\n"
                
            if discount_vnd > 0:
                disc_str = f"{int(discount_vnd):,} VNĐ".replace(",", ".")
                body += f"  *Ưu đãi trọn gói combo (Giảm tiền công tháo lắp trùng lặp):* Giảm **-{disc_str}**\n"
                
        body += f"\n**Tổng chi phí dự kiến trọn gói:** **{price_formatted}** (Báo giá AI bám sát dữ liệu thị trường thực tế){diff_advice}"
    else:
        header = f"Kính gửi Quý khách, dựa trên mô tả tình trạng ('{complaint}'), hệ thống xác định {dev_name} của bạn đang gặp phải sự cố sau:"
        action_note = ""
        if itemized_prices and len(itemized_prices) > 0:
            it = itemized_prices[0]
            if "action" in it or "key_component" in it:
                labor_str = f"{int(it.get('labor_fee', 100000)):,} VNĐ".replace(",", ".")
                comp_str = f"{int(it.get('component_price', it['price_vnd'] - it.get('labor_fee', 0))):,} VNĐ".replace(",", ".")
                action_note = f"\n**Phương án đề xuất:** {it.get('action', 'Thay thế')} ({it.get('key_component', '')}) [Linh kiện: {comp_str} | Công thợ: {labor_str}]"
                
        body = (
            f"\n\n**Sự cố xác định:** {predicted_fault}"
            f"{action_note}"
            f"\n**Độ khó kỹ thuật:** Cấp {diff_score_float:.1f}/5 (Thời gian xử lý: ~{est_minutes} phút)"
            f"\n**Mức độ ảnh hưởng:** {sev_desc}"
            f"{root_cause_text}"
            f"\n**Chi phí khắc phục dự kiến:** **{price_formatted}** (Mức giá tham khảo minh bạch theo thị trường)"
            f"{diff_advice}"
        )
        
    footer = ""
    if clarification_prompt:
        footer += f"\n\n**Thăm dò thêm thông tin từ AI:**\n{clarification_prompt}"
    elif has_guide:
        footer += "\n\nChúng tôi đã đính kèm cẩm nang kỹ thuật chi tiết bên dưới để bạn tiện theo dõi và giám sát thợ."
    else:
        footer += "\n\nChúng tôi sẵn sàng kết nối bạn với thợ kỹ thuật tay nghề cao gần nhất để xử lý dứt điểm sự cố."
        
    return header + body + footer


