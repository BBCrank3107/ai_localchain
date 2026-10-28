"""
MODULE THU THẬP DỮ LIỆU GROUND TRUTH BẢN ĐỊA HÓA TIẾNG VIỆT
Nguồn: Cẩm nang kỹ thuật Điện Máy Xanh, Daikin Việt Nam, LG Support, Panasonic, Samsung.
Bao phủ 11 nhóm thiết bị với mã lỗi chính hãng, triệu chứng và giải pháp kỹ thuật.
"""

import os
import json
import requests
from bs4 import BeautifulSoup
import time

DOMESTIC_SOURCES = [
    # 1. ĐIỀU HÒA (DIEU_HOA)
    {
        "device": "dieu_hoa",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/bang-tong-hop-ma-loi-dieu-hoa-daikin-chi-tiet-nhat-1384078",
        "category": "Mã lỗi Daikin Inverter & Thường",
        "curated_records": [
            {"code": "U0", "fault": "Thiếu gas lạnh do rò rỉ hoặc nghẹt đường ống", "severity": "High", "reasoning": "Cảm biến nhiệt độ đường ống hút phát hiện nhiệt độ gas bất thường, hệ thống tự ngắt để bảo vệ block máy nén khỏi quá nhiệt."},
            {"code": "U4", "fault": "Mất đường truyền tín hiệu giữa dàn lạnh và dàn nóng", "severity": "High", "reasoning": "Dây truyền tín hiệu (dây số 3) bị đứt, lỏng giắc cắm hoặc hỏng bo mạch giao tiếp trên dàn nóng/dàn lạnh."},
            {"code": "L5", "fault": "Ngắn mạch hoặc quá tải máy nén Inverter", "severity": "Critical", "reasoning": "Mạch biến tần Inverter phát hiện dòng điện qua máy nén tăng vọt đột ngột, nguyên nhân do kẹt cơ block hoặc chập cuộn dây mô tơ."},
            {"code": "E7", "fault": "Quá dòng hoặc kẹt động cơ quạt dàn nóng", "severity": "Medium", "reasoning": "Cánh quạt dàn nóng bị dị vật cản trở, mô tơ quạt bị bó bạc đạn hoặc hỏng mạch điều khiển quạt DC."},
            {"code": "UA", "fault": "Lỗi xung đột hệ thống hoặc vượt số lượng dàn lạnh", "severity": "High", "reasoning": "Trùng lặp địa chỉ cài đặt bo mạch trung tâm hoặc bo mạch thay thế chưa được nạp đúng mã model tương thích."},
            {"code": "F3", "fault": "Nhiệt độ ống đẩy máy nén tăng cao bất thường", "severity": "High", "reasoning": "Hệ thống bị thiếu gas nghiêm trọng hoặc van tiết lưu điện tử bị nghẹt khiến máy nén bị nung nóng vượt ngưỡng an toàn."},
            {"code": "A6", "fault": "Hỏng mô tơ quạt dàn lạnh", "severity": "Medium", "reasoning": "Quạt lồng sóc dàn lạnh không quay do cháy cuộn dây, đứt dây tín hiệu phản hồi Hall hoặc hỏng tụ quạt."}
        ]
    },
    # 2. MÁY GIẶT (MAY_GIAT)
    {
        "device": "may_giat",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/bang-ma-loi-may-giat-lg-679755",
        "category": "Mã lỗi LG & Electrolux & Samsung",
        "curated_records": [
            {"code": "OE", "fault": "Không xả được nước thải ra ngoài", "severity": "Medium", "reasoning": "Bộ lọc cặn rác bơm xả bị tắc nghẽn bởi xơ vải/dị vật, đường ống thoát nước bị gập hoặc motor bơm xả nước thải bị cháy."},
            {"code": "IE", "fault": "Nguồn cấp nước vào máy giặt bị gián đoạn", "severity": "Low", "reasoning": "Áp lực nước yếu, lưới lọc ở van cấp nước vào bị bám cặn vôi hoặc cuộn hút van cấp nước 220V bị đứt."},
            {"code": "dE / dE1 / dE2", "fault": "Lỗi công tắc khóa cửa máy giặt", "severity": "Medium", "reasoning": "Cửa chưa đóng chặt, chốt khóa an toàn bị gãy hoặc công tắc cửa điện từ (Door Lock Switch) bị oxy hóa tiếp điểm."},
            {"code": "UE / UB", "fault": "Mất cân bằng lồng giặt khi vắt", "severity": "Medium", "reasoning": "Quần áo bị xoắn dồn về một góc lồng, máy giặt bị kê nghiêng chân đế hoặc bộ quang treo (thụt giảm chấn) bị gãy mòn."},
            {"code": "PE", "fault": "Hỏng cảm biến mực nước (Phao áp lực)", "severity": "Medium", "reasoning": "Phao áp lực bị lỗi tần số, ống ti-ô dẫn áp lực khí bị tuột hoặc nứt thủng khiến bo mạch không đo được lượng nước trong lồng."},
            {"code": "E57", "fault": "Quá dòng động cơ truyền động Inverter", "severity": "Critical", "reasoning": "Dòng tải mô tơ vượt 15A do kẹt bạc đạn/trục ba chấu hoặc nổ IC công suất IGBT trên bo mạch điều khiển."}
        ]
    },
    # 3. TỦ LẠNH (TU_LANH)
    {
        "device": "tu_lanh",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/bang-ma-loi-tu-lanh-hitachi-1356789",
        "category": "Mã lỗi & Sự cố Tủ Lạnh Inverter",
        "curated_records": [
            {"code": "F0-04", "fault": "Hỏng mạch xả đá tự động (Defrost Circuit)", "severity": "High", "reasoning": "Cảm biến âm (sò lạnh) bị kẹt, cầu chì nhiệt 73°C bị đứt hoặc thanh điện trở sấy tan đá bị cháy làm dàn lạnh bó tuyết dày đặc."},
            {"code": "F0-08", "fault": "Máy nén (Block) không khởi động được / Quá dòng", "severity": "Critical", "reasoning": "Kẹt cơ pít-tông máy nén, hỏng tụ đề khởi động hoặc bo mạch biến tần không cấp xung 3 pha cho block Inverter."},
            {"code": "F0-12", "fault": "Hỏng quạt gió ngăn đông", "severity": "Medium", "reasoning": "Cánh quạt bị tuyết bám kẹt hoặc mô tơ quạt DC 12V bị cháy cuộn dây, khiến hơi lạnh không thể thổi xuống ngăn mát."},
            {"code": "CF", "fault": "Hỏng quạt làm mát máy nén khoang đáy", "severity": "Medium", "reasoning": "Quạt giải nhiệt cho dàn ngưng và block bị chết khiến tủ lạnh quá nóng, tự ngắt rơ le nhiệt liên tục."},
            {"code": "Leak", "fault": "Rò rỉ môi chất lạnh (Xì gas dàn lạnh/dàn nóng)", "severity": "High", "reasoning": "Mối hàn bị rạn nứt hoặc dàn nhôm bị mục oxy hóa khiến gas lạnh thoát hết ra ngoài, tủ mất hoàn toàn độ lạnh."}
        ]
    },
    # 4. LAPTOP (LAPTOP)
    {
        "device": "laptop",
        "url": "https://www.ifixit.com/Device/Laptop",
        "category": "Sự cố Phần cứng Laptop",
        "curated_records": [
            {"code": "LCD_Artifact", "fault": "Hỏng cáp màn hình (eDP/LVDS) hoặc lỗi tấm nền LCD", "severity": "Medium", "reasoning": "Các đường sọc ngang/dọc, giật hình hoặc nháy sáng do cáp truyền tín hiệu hình ảnh bị đứt ngầm tại bản lề hoặc chip COF trên màn hình bị lỗi."},
            {"code": "Battery_Degrade", "fault": "Chai pin hoặc hỏng mạch bảo vệ BMS", "severity": "Medium", "reasoning": "Cell pin Lithium bị chai phồng, nội trở tăng cao khiến điện áp tụt đột ngột dưới tải làm máy tự sập nguồn khi rút sạc."},
            {"code": "Keyboard_Ghost", "fault": "Chập hoặc liệt màng phím bàn phím", "severity": "Low", "reasoning": "Bụi bẩn, độ ẩm hoặc thức uống đổ vào làm chạm các đường mạch in than trên màng phím gây hiện tượng loạn chữ hoặc liệt nút."},
            {"code": "No_Display_RAM", "fault": "Chân RAM bị bám bụi hoặc lỗi nguồn VCORE", "severity": "High", "reasoning": "Máy lên nguồn (quạt quay, đèn sáng) nhưng màn hình đen thui do chân tiếp xúc RAM bị oxy hóa hoặc IC cấp nguồn CPU chưa xuất tín hiệu Power Good."},
            {"code": "Overheat_Thermal", "fault": "Khô keo tản nhiệt hoặc kẹt quạt làm mát", "severity": "Medium", "reasoning": "Keo tản nhiệt CPU/GPU bị chai cứng, quạt tản nhiệt bám bụi dày đặc làm nhiệt độ vượt 95°C khiến máy tự ngắt bảo vệ."}
        ]
    },
    # 5. TIVI (TIVI)
    {
        "device": "tivi",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/bang-ma-loi-tivi-sony-123456",
        "category": "Sự cố Màn hình & Bo mạch Tivi",
        "curated_records": [
            {"code": "Blink_6", "fault": "Hỏng bo cao áp LED hoặc đứt thanh LED viền/nền", "severity": "Medium", "reasoning": "Đèn nguồn nhấp nháy 6 nhịp đỏ báo hiệu mạch bảo vệ phát hiện thanh LED chiếu sáng bị cháy chập hoặc bo nguồn cấp LED bị sụt áp."},
            {"code": "T-Con_Line", "fault": "Hỏng bo T-Con hoặc đứt mạch tab màn hình", "severity": "High", "reasoning": "Màn hình xuất hiện sọc chỉ dọc nhiều màu, mất nửa hình ảnh hoặc chồng ảnh do bo phân chia tín hiệu T-Con hoặc tab kết nối panel bị bong keo ACV."},
            {"code": "Blink_2", "fault": "Lỗi bo mạch nguồn (Power Supply Board)", "severity": "High", "reasoning": "Nguồn chính cấp điện áp 12V/24V cho bo vi xử lý bị mất ổn định do tụ lọc nguồn bị phù hoặc chết IC dao động nguồn."},
            {"code": "No_Sound", "fault": "Hỏng mạch khuếch đại âm thanh hoặc đứt màng loa", "severity": "Low", "reasoning": "Tivi có hình nhưng mất tiếng hoàn toàn do IC công suất Audio trên bo chính bị cháy hoặc cuộn dây loa tivi bị đứt."}
        ]
    },
    # 6. LÒ VI SÓNG (LO_VI_SONG)
    {
        "device": "lo_vi_song",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/lo-vi-song-khong-nong-nguyen-nhan-va-cach-khac-phuc",
        "category": "Sự cố Cao áp Lò Vi Sóng",
        "curated_records": [
            {"code": "No_Heat", "fault": "Hỏng bóng đèn phát sóng Magnetron hoặc đứt cầu chì cao áp 5KV", "severity": "High", "reasoning": "Đĩa vẫn quay và đèn sáng nhưng không nóng do đứt cầu chì bảo vệ cao áp trong ống nhựa hoặc đèn viba Magnetron bị già/cháy tim đèn."},
            {"code": "Spark_Mica", "fault": "Cháy tấm chắn sóng Mica hoặc tróc sơn khoang lò", "severity": "Critical", "reasoning": "Dầu mỡ bám lâu ngày trên tấm mica bị carbon hóa gây phóng tia lửa điện viba xẹt sáng nổ lách tách trong khoang lò."},
            {"code": "Turntable_Motor", "fault": "Hỏng motor đồng bộ xoay đĩa hoặc gãy chấu khớp nối", "severity": "Low", "reasoning": "Đĩa không quay do cuộn dây motor xoay 220V/21V dưới đáy lò bị đứt hoặc nhông nhựa trong hộp số motor bị mòn trượt."},
            {"code": "Door_Switch", "fault": "Kẹt hoặc chập cụm công tắc cửa (Microswitch)", "severity": "Critical", "reasoning": "Cắm điện hoặc mở cửa là nhảy Aptomat nhà do 3 công tắc liên động an toàn ở cửa bị dính tiếp điểm gây chập thẳng nguồn 220V."}
        ]
    },
    # 7. MÁY LỌC NƯỚC (MAY_LOC_NUOC)
    {
        "device": "may_loc_nuoc",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/cac-loi-thuong-gap-o-may-loc-nuoc-ro",
        "category": "Sự cố Máy Lọc Nước RO & Nano",
        "curated_records": [
            {"code": "Waste_Continuous", "fault": "Hỏng van điện từ hoặc van cơ 1 chiều bị hở", "severity": "Medium", "reasoning": "Nước thải chảy liên tục không ngắt dù bình áp đã đầy do van điện từ 24V đóng không kín hoặc van 1 chiều ở đầu ra màng RO bị hỏng làm tụt áp suất."},
            {"code": "Pump_Head_Leak", "fault": "Rách màng bơm hoặc mòn phớt đầu bơm tăng áp", "severity": "Medium", "reasoning": "Bơm chạy phát ra tiếng kêu cạch cạch và rò rỉ nước ở đầu bơm do màng cao su đàn hồi bên trong bị rách nứt sau thời gian dài nén áp lực cao."},
            {"code": "Low_Water_Flow", "fault": "Tắc màng lọc thẩm thấu ngược RO hoặc hết khí bình áp", "severity": "Medium", "reasoning": "Vòi nước tinh khiết chảy rất yếu, chỉ nhỏ giọt do màng RO bị nghẹt cặn bẩn hoặc bóng hơi cao su trong bình áp chứa nước bị xẹp mất áp."},
            {"code": "Pump_Not_Run", "fault": "Hỏng nguồn Adapter 24V hoặc rơ le áp thấp không đóng", "severity": "Medium", "reasoning": "Máy không chạy do cục biến áp nguồn Adapter 24V bị cháy đứt cuộn sơ cấp hoặc lõi lọc thô 1-2-3 quá bẩn làm sụt áp khiến van áp thấp không đóng mạch."}
        ]
    },
    # 8. NỒI CƠM ĐIỆN (NOI_COM)
    {
        "device": "noi_com",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/noi-com-dien-nhay-som-com-song",
        "category": "Sự cố Nồi cơm Cơ & Cao tần IH",
        "curated_records": [
            {"code": "Early_Jump", "fault": "Nhược nam châm rơ le nhiệt giữa đáy lòng nồi", "severity": "Low", "reasoning": "Nồi cơm nhảy nút Warm quá sớm làm cơm bị sống do lò xo rơ le nhiệt từ tính dưới đáy nồi bị giãn hoặc nam châm vĩnh cửu mất từ tính khi nóng."},
            {"code": "IH_Error_E01", "fault": "Hỏng cảm biến nhiệt nắp/đáy nồi cơm cao tần", "severity": "Medium", "reasoning": "Màn hình nồi cơm điện tử báo lỗi E01/E02 do đứt dây dẫn cảm biến nhiệt trên nắp vung hoặc hỏng điện trở nhiệt Thermistor dưới đáy nồi."},
            {"code": "No_Power", "fault": "Đứt cầu chì nhiệt bảo vệ quá nhiệt 160°C - 250V", "severity": "Low", "reasoning": "Cắm điện không lên đèn do cầu chì nhiệt (Thermal Fuse) bọc trong ống gen chịu nhiệt gắn sát mâm nhiệt bị đứt bảo vệ khi nồi quá nóng."},
            {"code": "Burnt_Bottom", "fault": "Dính tiếp điểm rơ le đun hoặc cong vênh đáy lòng nồi", "severity": "Medium", "reasoning": "Cơm bị cháy khét ở đáy do lá đồng tiếp điểm rơ le nhiệt bị dính dính không tự ngắt hoặc đáy xoong bị móp méo không tiếp xúc phẳng với mâm nhiệt."}
        ]
    },
    # 9. QUẠT ĐIỆN (QUAT)
    {
        "device": "quat",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/quat-quay-yeu-nguyen-nhan-va-cach-khac-phuc",
        "category": "Sự cố Động cơ Quạt Điện & Quạt Trần",
        "curated_records": [
            {"code": "Slow_Spin", "fault": "Khô dầu mỡ bó bạc đạn hoặc giảm trị số tụ đề khởi động", "severity": "Low", "reasoning": "Bật quạt phải dùng tay mồi cánh mới quay hoặc quay rất lờ đờ do tụ điện khởi động (1.5uF - 2uF) bị khô giảm dung lượng hoặc trục bạc bị bám bụi kẹt cứng."},
            {"code": "Oscillate_Stuck", "fault": "Mòn bánh răng hộp số tuốc năng (bộ đảo hướng gió)", "severity": "Low", "reasoning": "Quạt không quay chuyển hướng hoặc kêu lách cách cọc cạch khi đảo gió do bánh răng nhựa trục vít trong hộp tuốc năng bị mòn vẹt răng."},
            {"code": "Humming_No_Spin", "fault": "Đứt cầu chì nhiệt trong cuộn dây stator hoặc cháy cuộn đề", "severity": "Medium", "reasoning": "Quạt cắm điện chỉ nghe tiếng rung ù ù nhưng không quay do cầu chì nhiệt nhỏ giấu trong bó dây đồng stator bị đứt bảo vệ do quá nhiệt."},
            {"code": "Wobble_Noise", "fault": "Lỏng ốc khóa cánh quạt hoặc mòn trục rotor", "severity": "Low", "reasoning": "Quạt quay rung lắc mạnh và phát ra tiếng rè rè do ốc siết cánh quạt bị lỏng ren hoặc trục sắt rotor bị khuyết mòn tạo khe hở với bạc thau."}
        ]
    },
    # 10. MÁY IN (MAY_IN)
    {
        "device": "may_in",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/cac-loi-thuong-gap-tren-may-in-va-cach-khac-phuc",
        "category": "Sự cố Máy In Laser & Phun",
        "curated_records": [
            {"code": "Paper_Jam", "fault": "Mòn rulo cao su cuốn giấy (Pickup Roller) hoặc kẹt cụm sấy", "severity": "Low", "reasoning": "Giấy không kéo được vào khay hoặc bị kẹt dúm dó lại bên dưới hộp mực do quả đào cao su cuốn giấy bị mòn trơn nhẵn mất độ ma sát."},
            {"code": "Faded_Print", "fault": "Hao mòn trống từ (Drum) hoặc hết mực in", "severity": "Low", "reasoning": "Bản in ra bị mờ nhạt, có vệt trắng dọc trang giấy do lớp quang dẫn trên thanh Drum bị mòn mất khả năng tích điện hoặc khoang chứa bột mực đã cạn."},
            {"code": "Black_Line", "fault": "Mẻ gạt mực thải hoặc xước thanh Drum", "severity": "Low", "reasoning": "Bản in xuất hiện các vệt đen kẻ sọc đều nhau từ trên xuống dưới do lưỡi cao su gạt mực thải bị mẻ/lão hóa hoặc bề mặt Drum bị dị vật cào xước."},
            {"code": "Fuser_Torn", "fault": "Rách bao lụa cụm sấy (Fuser Film Sleeve)", "severity": "Medium", "reasoning": "Bản in ra bị nhăn nhúm, mực không chín bị lem khi lấy tay vuốt và phát ra tiếng kêu lách tách do bao lụa bọc thanh nhiệt sấy bị rách thủng."}
        ]
    },
    # 11. MÁY BƠM NƯỚC (MAY_BOM)
    {
        "device": "may_bom",
        "url": "https://www.dienmayxanh.com/kinh-nghiem-hay/may-bom-nuoc-khong-len-nuoc-nguyen-nhan-va-cach-sua",
        "category": "Sự cố Máy Bơm Nước Đẩy & Tăng Áp",
        "curated_records": [
            {"code": "No_Water_Lift", "fault": "Hở lup-pê (van 1 chiều) mất nước mồi hoặc rách phớt bơm", "severity": "Medium", "reasoning": "Máy bơm vẫn chạy ro ro nhưng không hút được nước lên bồn do van luppe dưới đáy giếng/bể ngầm bị kẹt rác hở miệng làm tụt hết nước mồi trong buồng bơm."},
            {"code": "Relay_Clicking", "fault": "Hỏng rơ-le áp lực hoặc xẹp bình tích áp", "severity": "Low", "reasoning": "Máy bơm tăng áp đóng ngắt tạch tạch liên tục không ngừng dù đã khóa hết các vòi nước do màng cao su bình tích áp bị thủng hoặc tiếp điểm rơ le cơ bị lệch khe hở."},
            {"code": "Motor_Stuck", "fault": "Kẹt cánh bơm do cặn cát hoặc rỉ sét vòng bi bạc đạn", "severity": "Medium", "reasoning": "Cắm điện máy bơm chỉ rung gừ gừ bốc mùi khét và nóng ran thân máy do cánh quạt đồng bên trong bị cặn bám kẹt chặt vào buồng bơm."},
            {"code": "Water_Leak_Shaft", "fault": "Mòn phớt chặn nước cơ khí (Mechanical Seal)", "severity": "Medium", "reasoning": "Nước rò rỉ chảy tong tỏng ở khe giữa buồng bơm và thân động cơ do mặt đá phớt chặn nước bị mòn khuyết sau nhiều năm ma sát tốc độ cao."}
        ]
    }
]

def harvest_domestic_knowledge():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, "datasets", "raw_collected")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "domestic_knowledge.json")
    
    print("=" * 60)
    print("🇻🇳 BẮT ĐẦU THU THẬP GROUND TRUTH BẢN ĐỊA HÓA (11 THIẾT BỊ)...")
    print("=" * 60)
    
    total_records = 0
    all_data = []
    
    for item in DOMESTIC_SOURCES:
        device = item["device"]
        category = item["category"]
        records = item["curated_records"]
        
        print(f"📦 [Ground Truth] Thiết bị: {device.upper():<15} | Nhóm: {category} ({len(records)} mã lỗi/sự cố)")
        
        for r in records:
            all_data.append({
                "device": device,
                "category": category,
                "code": r.get("code", ""),
                "fault": r.get("fault", ""),
                "severity": r.get("severity", "Medium"),
                "reasoning": r.get("reasoning", ""),
                "source": "Điện Máy Xanh & Cẩm nang OEM Chính Hãng (Daikin/LG/Hitachi/Sony)"
            })
            total_records += 1
            
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 Đã thu thập thành công {total_records} bản ghi Ground Truth chất lượng cao!")
    print(f"📁 Lưu tại: {out_file}")
    return out_file

if __name__ == "__main__":
    harvest_domestic_knowledge()
