"""
LOCALCHAIN AI V5.2 - DOMAIN-SYNTHESIZED STATE MACHINE DAG WORKFLOW GENERATOR
Bộ tổng hợp Quy trình Sửa chữa Đồ thị Trạng thái (DAG Synthesizer) theo Cây Quyết Định Chuyên Môn (Domain Decision Trees).
Tự động tổng hợp State Machine, mốc đo kiểm điện áp/điện trở danh định, điều kiện rẽ nhánh và QA nghiệm thu riêng biệt cho từng thiết bị.
"""

import time
import uuid
from typing import Dict, List, Any, Optional
from ..dsl.state_machine_dsl import (
    RepairWorkflowDSL, WorkflowMetadata, SafetyPrerequisite, 
    DAGStateNode, StateTransition
)
from ..validator.safety_validator import safety_validator
from ..validator.risk_scorer import risk_scorer


# CÂY QUYẾT ĐỊNH & THAO TÁC KỸ THUẬT CHUYÊN BIỆT CHO 11 THIẾT BỊ (DOMAIN KNOWLEDGE RULES)
DOMAIN_WORKFLOW_SPECS = {
    "tu_lanh": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã rút phích cắm nguồn điện AC 220V lưới trước khi thao tác."),
            ("REQ_R600A_VENTILATION", "VENTILATE_REPAIR_AREA", "Khu vực sửa chữa thông thoáng, không có tia lửa hở gần đường gas lạnh.")
        ],
        "default_assembly": "Cụm Xả Băng & Dàn Lạnh Ngăn Đông",
        "inspection": {
            "action": "MEASURE_IMPEDANCE_AND_THERMAL_CONTINUITY",
            "instruction_vn": "Tháo nắp ốp dàn lạnh ngăn đông, kiểm tra tình trạng đóng tuyết bám kín dàn. Dùng đồng hồ VOM đo điện trở thanh sấy DEFROST_HEATER (chuẩn 200-350Ω), đo thông mạch sò lạnh DEFROST_BIMETAL (ở nhiệt độ âm < 0°C đóng tiếp điểm 0Ω) và đo thông mạch cầu chì nhiệt THERMAL_FUSE (chuẩn 0Ω, đứt là hở mạch ∞Ω).",
            "voltage_checkpoint": "200-350Ω (Heater) / 0Ω (Thermal Fuse)",
            "tools": ["DIGITAL_MULTIMETER", "INSULATED_SCREWDRIVER", "FREEZE_SPRAY_TESTER"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế linh kiện phụ trợ ({target}) bị hỏng/đứt mạch, cố định lại vị trí kẹp áp sát bầu gom gas trên dàn lạnh và bọc ống co nhiệt chống ẩm nước chuyên dụng."
        },
        "replace_primary": {
            "instruction_vn": "Tháo thanh sấy / linh kiện chính ({target}) bị cháy đứt khỏi đáy máng dàn lạnh, vệ sinh sạch cặn tuyết đọng và lắp linh kiện thay thế chuẩn công suất vào đúng vị trí ngàm giữ."
        },
        "verification": {
            "action": "FORCE_DEFROST_AND_FAN_TEST",
            "instruction_vn": "Cấp điện tạm thời, chuyển tủ lạnh sang chế độ kích hoạt xả đá cưỡng bức (Force Defrost Mode), sờ ấm bề mặt thanh nhiệt và kiểm tra quạt đối lưu dàn lạnh quay êm không cạ tuyết.",
            "tools": ["DIGITAL_MULTIMETER", "INFRARED_THERMOMETER"]
        },
        "qa": {
            "action": "MONITOR_DEFROST_CYCLE_AND_COOLING",
            "instruction_vn": "Theo dõi chu trình làm lạnh sau 1-2 giờ: Ngăn đông đạt âm sâu -18°C, ngăn mát 2-4°C, quạt đối lưu gió tốt và khay thoát nước phía sau có nước xả băng chảy đều."
        }
    },
    "laptop": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã rút sạc cắm nguồn AC adapter."),
            ("REQ_BATTERY_ISOLATION", "DISCONNECT_BATTERY_PHYSICAL", "Đã tháo giắc pin vật lý khỏi bo mạch chủ trước khi tiếp xúc cáp màn hình.")
        ],
        "default_assembly": "Cụm Tấm Nền & Cáp Tín Hiệu eDP",
        "inspection": {
            "action": "MEASURE_PANEL_VOLTAGE_AND_CONTINUITY",
            "instruction_vn": "Tháo khung viền màn hình (Bezel) bằng que nạy nhựa. Dùng kính phóng đại kiểm tra cổ cáp eDP không bị dập gãy, đo điện áp đèn nền 19V_VBL và điện áp logic 3.3V_LCDVDD tại đầu nối cáp.",
            "voltage_checkpoint": "19V_VBL (Đèn nền) / 3.3V_LCDVDD",
            "tools": ["PLASTIC_SPUDGER", "DIGITAL_MULTIMETER", "TWEEZERS"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế cáp tín hiệu eDP / bản lề phụ trợ ({target}), đi dây gọn gàng theo rãnh dẫn khớp nối chống kẹt dập cáp khi gập mở máy."
        },
        "replace_primary": {
            "instruction_vn": "Tách kéo băng dính co giãn (Stretch Release Tape), tháo tấm nền LCD/OLED cũ ({target}) và lắp tấm nền mới chuẩn độ phân giải, cắm chặt thanh khóa cáp eDP."
        },
        "verification": {
            "action": "TEST_DISPLAY_POST_AND_BACKLIGHT",
            "instruction_vn": "Cắm pin tạm thời, kích nguồn kiểm tra tín hiệu khởi động POST, màn hình hiển thị logo BIOS sắc nét, đèn nền sáng đều không chớp nháy.",
            "tools": ["MULTIMETER"]
        },
        "qa": {
            "action": "RUN_RGB_FULLSCREEN_QA",
            "instruction_vn": "Chạy bài kiểm tra nghiệm thu RGB Fullscreen (Đỏ, Xanh lá, Xanh dương, Trắng, Đen) kiểm tra độ đồng màu tấm nền, kiểm tra điểm chết (Dead Pixels) và chỉnh góc gập 0°-135°."
        }
    },
    "tivi": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã rút phích cắm nguồn AC 220V lưới."),
            ("REQ_PSU_CAPACITOR_DISCHARGE", "DISCHARGE_PSU_CAPACITOR", "Đã xả tụ lọc nguồn sơ cấp 390V-450V trên bo nguồn PSU.")
        ],
        "default_assembly": "Cụm Bo Mạch T-Con & Dải LED Nền",
        "inspection": {
            "action": "MEASURE_TCON_VOLTAGE_AND_LED_STRIPS",
            "instruction_vn": "Tháo nắp lưng TV. Đo các điểm test point trên bo T-Con (VDD 3.3V, VGH +28V, VGL -6V, VCOM +7V) và dùng máy test LED đo điện áp sụt trên từng thanh LED nền.",
            "voltage_checkpoint": "VGH +28V / VGL -6V / VDD 3.3V",
            "tools": ["DIGITAL_MULTIMETER", "LED_TESTER_INSTRUMENT", "INSULATED_TWEEZERS"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế cáp dẹt LVDS / bo mạch T-Con ({target}), dùng cồn chuyên dụng vệ sinh sạch chân tiếp xúc mạ vàng."
        },
        "replace_primary": {
            "instruction_vn": "Dùng giác hút kính nâng tấm kính LCD an toàn, bóc tách bộ thanh LED nền cũ ({target}) bị chập cháy, dán keo tản nhiệt và lắp bộ thanh LED mới chính hãng."
        },
        "verification": {
            "action": "TEST_TV_BOOT_AND_BACKLIGHT_UNIFORMITY",
            "instruction_vn": "Cấp nguồn thử nghiệm, bật TV kiểm tra đèn nền LED sáng trắng đều 100%, logo thương hiệu hiển thị rõ nét không bị kẻ sọc hay tối góc.",
            "tools": ["MULTIMETER"]
        },
        "qa": {
            "action": "PLAY_4K_HDR_AND_AUDIO_QA",
            "instruction_vn": "Phát video 4K 60fps trong 15 phút kiểm tra dải màu HDR, độ tương phản mượt mà, không bị nhảy hình và nhiệt độ mặt lưng bo T-Con mát ổn định."
        }
    },
    "dieu_hoa": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã ngắt Aptomat (CB) cấp nguồn tổng của điều hòa."),
            ("REQ_REFRIGERANT_LEAK_CHECK", "CHECK_R32_FLAMMABLE", "Kiểm tra rò rỉ gas R32/R410A bằng dung dịch bọt trước khi bật nguồn.")
        ],
        "default_assembly": "Cụm Dàn Nóng & Máy Nén Inverter",
        "inspection": {
            "action": "MEASURE_COMPRESSOR_WINDING_AND_PRESSURE",
            "instruction_vn": "Mở nắp dàn nóng, đo điện trở 3 pha U-V-W của máy nén INVERTER_COMPRESSOR (chuẩn cân bằng 0.5-2.5Ω), đo điện trở cách điện cuộn dây với vỏ máy (> 10MΩ) và gắn đồng hồ đo áp suất hút gas.",
            "voltage_checkpoint": "0.5-2.5Ω (U-V-W) / 130-150 PSI (Gas R32)",
            "tools": ["DIGITAL_MULTIMETER", "MANIFOLD_GAUGE", "CLAMP_METER"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế cảm biến nhiệt độ / tụ ngậm ({target}), kiểm tra giắc cắm chống nước và bọc ống cách nhiệt chuyên dụng."
        },
        "replace_primary": {
            "instruction_vn": "Thu hồi gas lạnh, hàn tách máy nén / motor quạt ({target}), lắp ráp linh kiện thay thế, hút chân không đạt độ sâu $\le 500\text{ microns}$ và nạp lại gas lạnh chuẩn gram."
        },
        "verification": {
            "action": "TEST_COOL_MODE_AND_COMPRESSOR_RAMP",
            "instruction_vn": "Bật máy ở chế độ Cool 18°C, dùng ampe kìm kẹp dòng tải máy nén Inverter tăng dần theo tần số và kiểm tra quạt dàn nóng thổi gió ấm đều.",
            "tools": ["CLAMP_METER", "DIGITAL_THERMOMETER"]
        },
        "qa": {
            "action": "MONITOR_DELTA_T_AND_CONDENSATE",
            "instruction_vn": "Đo độ chênh lệch nhiệt độ giữa miệng gió hồi và gió thổi ra dàn lạnh đạt $\Delta T \ge 10^\circ\text{C}$, nước ngưng chảy thành dòng đều qua ống thoát nước."
        }
    },
    "may_giat": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã rút phích cắm điện 220V lưới."),
            ("REQ_WATER_ISOLATION", "SHUTOFF_WATER_SUPPLY", "Đã khóa van cấp nước vào máy giặt và chuẩn bị khay hứng nước thừa.")
        ],
        "default_assembly": "Cụm Bơm Thoát Nước & Hệ Thống Cấp Nước",
        "inspection": {
            "action": "MEASURE_PUMP_COIL_AND_VALVE_IMPEDANCE",
            "instruction_vn": "Mở nắp đáy / nắp sau máy giặt. Đo điện trở cuộn dây motor bơm xả DRAIN_PUMP (chuẩn 150-180Ω), mở hộc bẫy rác kiểm tra kẹt dị vật cánh bơm và đo cuộn van cấp nước INLET_VALVE (chuẩn 4.0-4.8kΩ).",
            "voltage_checkpoint": "150-180Ω (Pump) / 4.0-4.8kΩ (Valve)",
            "tools": ["DIGITAL_MULTIMETER", "PLIERS", "WATER_CATCH_TRAY"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế van cấp nước / phao áp lực ({target}), siết chặt cổ dê ống cao su dẫn nước chống rò rỉ."
        },
        "replace_primary": {
            "instruction_vn": "Tháo cụm bơm xả / khóa cửa ({target}) bị cháy cuộn dây hoặc mòn bạc, lắp cụm bơm mới chính hãng và siết chặt ốc định vị chống rung."
        },
        "verification": {
            "action": "TEST_SPIN_DRAIN_CYCLE",
            "instruction_vn": "Chọn chương trình Vắt (Spin Only), kiểm tra bơm xả rút kiệt nước trong lồng giặt trong vòng 90 giây và motor quay tăng tốc đạt 1000-1200 vòng/phút không rung lắc.",
            "tools": ["DIGITAL_MULTIMETER"]
        },
        "qa": {
            "action": "RUN_FULL_QUICK_WASH_QA",
            "instruction_vn": "Chạy trọn vẹn 1 chu trình giặt nhanh (Quick Wash): Cấp nước chuẩn mực $\rightarrow$ Giặt đảo chiều cân bằng $\rightarrow$ Xả sạch $\rightarrow$ Vắt khô $\rightarrow$ Mở chốt cửa an toàn."
        }
    },
    "lo_vi_song": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã rút phích cắm điện 220V lưới."),
            ("REQ_HV_CAPACITOR_DISCHARGE", "DISCHARGE_CAPACITOR_TOOL", "Đã xả tụ cao áp 2100V bằng điện trở xả cách điện an toàn trước khi chạm tay.")
        ],
        "default_assembly": "Cụm Đèn Vi Sóng & Biến Áp Cao Áp",
        "inspection": {
            "action": "MEASURE_MAGNETRON_AND_HV_DIODE",
            "instruction_vn": "Đã xả tụ 2100V. Dùng đồng hồ VOM đo thông mạch tim đèn Magnetron (< 1Ω), đo cách điện tim đèn với vỏ kim loại (∞Ω), đo đi-ốt cao áp HV_DIODE và kiểm tra hệ thống vi công tắc cửa.",
            "voltage_checkpoint": "< 1Ω (Filament) / ∞Ω (To Ground)",
            "tools": ["HV_DISCHARGE_PROBE", "DIGITAL_MULTIMETER", "INSULATED_SCREWDRIVER"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế đi-ốt cao thế / tụ điện cao áp ({target}), siết chặt ốc tiếp địa và cắm chặt các đầu cos chịu nhiệt."
        },
        "replace_primary": {
            "instruction_vn": "Tháo dỡ đèn Magnetron ({target}) bị hỏng tim đèn/nứt nam châm, kiểm tra nắp chụp buồng sóng mica và lắp đèn Magnetron mới đúng thông số công suất."
        },
        "verification": {
            "action": "TEST_MICROWAVE_WATER_HEATING",
            "instruction_vn": "Đặt cốc nước 200ml vào tâm khoang lò, đóng kín cửa, cài đặt công suất High trong 60 giây và quan sát không phát sinh tia lửa điện hồ quang.",
            "tools": ["INFRARED_THERMOMETER"]
        },
        "qa": {
            "action": "CHECK_MICROWAVE_LEAKAGE_AND_TEMP",
            "instruction_vn": "Kiểm tra nước trong cốc sôi nóng đạt $\ge 85^\circ\text{C}$, dùng máy dò sóng vi ba kiểm tra mép gioăng cửa đạt chuẩn an toàn không rò rỉ bức xạ."
        }
    },
    "noi_com_dien": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã rút phích cắm nguồn điện AC 220V lưới."),
            ("REQ_ALLOW_COOLING", "ALLOW_HEATER_COOLING", "Để mâm nhiệt nguội hoàn toàn trước khi mở đáy nồi.")
        ],
        "default_assembly": "Cụm Mâm Nhiệt & Cảm Biến Đáy",
        "inspection": {
            "action": "MEASURE_HEATING_COIL_AND_FUSE",
            "instruction_vn": "Tháo nắp đáy nồi cơm. Dùng đồng hồ đo điện trở mâm nhiệt chính HEATING_ELEMENT (chuẩn 40-60Ω), đo thông mạch cầu chì nhiệt THERMAL_FUSE (chuẩn 0Ω) và kiểm tra tiếp điểm rơ-le từ trung tâm.",
            "voltage_checkpoint": "40-60Ω (Mâm nhiệt) / 0Ω (Cầu chì)",
            "tools": ["DIGITAL_MULTIMETER", "PH2_SCREWDRIVER", "PLIERS"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế cầu chì nhiệt / rơ-le cảm biến ({target}), luồn ống gen chịu nhiệt chống cháy sợi thủy tinh bảo vệ."
        },
        "replace_primary": {
            "instruction_vn": "Tháo mâm nhiệt / bo điều khiển ({target}), vệ sinh bề mặt tiếp xúc đáy ruột nồi và lắp linh kiện thay thế chuẩn thông số."
        },
        "verification": {
            "action": "TEST_COOK_WATER_BOILING",
            "instruction_vn": "Đổ 500ml nước vào lòng nồi, nhấn nút Cook (Nấu), kiểm tra rơ-le đóng cạch dứt khoát và mâm nhiệt sôi sủi bọt nhanh chóng.",
            "tools": ["DIGITAL_MULTIMETER"]
        },
        "qa": {
            "action": "TEST_WARM_TRANSITION_QA",
            "instruction_vn": "Nồi tự động nảy sang chế độ Warm (Ủ ấm) khi cạn nước, rơ-le nhiệt ngắt chuẩn xác không gây cháy khét và lòng nồi giữ ấm đều."
        }
    },
    "may_in": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã ngắt nguồn điện máy in."),
            ("REQ_FUSER_COOLING", "WAIT_FUSER_COOLING_DOWN", "Chờ cụm sấy nguội (dưới 40°C) chống bỏng nhiệt.")
        ],
        "default_assembly": "Cụm Sấy Nhiệt (Fuser Unit)",
        "inspection": {
            "action": "INSPECT_FUSER_SLEEVE_AND_HEATER",
            "instruction_vn": "Tháo cụm sấy Fuser. Kiểm tra độ rách mòn của bao lụa sấy FUSER_FILM_SLEEVE, đo điện trở thanh nhiệt gốm HEATING_CERAMIC_ELEMENT (chuẩn 50-100Ω) và kiểm tra quả đào kéo giấy PICKUP_ROLLER.",
            "voltage_checkpoint": "50-100Ω (Thanh nhiệt gốm)",
            "tools": ["PH1_SCREWDRIVER", "DIGITAL_MULTIMETER", "TWEEZERS"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Vệ sinh quả đào kéo giấy / thay thế lô ép ({target}), bôi mỡ nhiệt chuyên dụng chịu nhiệt 300°C."
        },
        "replace_primary": {
            "instruction_vn": "Bóc bỏ bao lụa sấy cũ ({target}) bị rách, lau sạch mỡ nhiệt cũ trên thanh gốm, tra mỡ dẫn nhiệt mỏng đều và luồn bao lụa sấy mới chính hãng."
        },
        "verification": {
            "action": "TEST_PRINTER_ENGINE_AND_DEMO_PAGE",
            "instruction_vn": "Lắp ráp cụm sấy, bật máy in kiểm tra khởi động cơ êm ái, đèn Ready xanh và in trang kiểm tra (Self-Test Page).",
            "tools": []
        },
        "qa": {
            "action": "RUN_MULTI_PAGE_PRINT_QA",
            "instruction_vn": "In liên tục 10 trang văn bản kiểm tra mực chín bóng bám chắc giấy, không bị kẹt giấy, không nhăn mép và chữ in sắc nét."
        }
    },
    "may_bom_nuoc": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã ngắt nguồn điện cấp cho máy bơm."),
            ("REQ_HYDRAULIC_VALVE_CLOSE", "CLOSE_INLET_OUTLET_VALVES", "Đã khóa van nước đường hút và đường đẩy.")
        ],
        "default_assembly": "Cụm Đầu Bơm & Phớt Chắn Nước",
        "inspection": {
            "action": "INSPECT_MECHANICAL_SEAL_AND_CAPACITOR",
            "instruction_vn": "Mở nắp buồng bơm kiểm tra cánh quạt, kiểm tra rò rỉ nước tại phớt cơ khí MECHANICAL_SEAL, dùng đồng hồ đo điện dung tụ khởi động START_CAPACITOR và kiểm tra tiếp điểm rơ-le áp lực.",
            "voltage_checkpoint": "10-30μF (Tụ ngậm/đề)",
            "tools": ["CAPACITANCE_METER", "WRENCH_14MM", "FLATHEAD_SCREWDRIVER"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế rơ-le áp lực / tụ khởi động ({target}), quấn băng tan Teflon làm kín các đầu ren kết nối."
        },
        "replace_primary": {
            "instruction_vn": "Dùng cảo tháo cánh bơm, rút cụm phớt cơ khí cũ ({target}) bị mòn mặt đá, bôi mỡ silicon và lắp cụm phớt mới ép khít trục motor."
        },
        "verification": {
            "action": "TEST_PUMP_RUN_AND_PRESSURE_BUILD",
            "instruction_vn": "Mồi nước đầy buồng bơm, cắm điện kiểm tra motor quay êm, đồng hồ áp lực tăng lên 1.8 - 2.2 kg/cm².",
            "tools": ["PRESSURE_GAUGE"]
        },
        "qa": {
            "action": "RUN_AUTO_PRESSURE_SWITCH_QA",
            "instruction_vn": "Mở vòi nước kiểm tra bơm tự động đóng điện chạy khỏe, khóa vòi nước bơm tự ngắt sau 2 giây và thân bơm kín tuyệt đối không rỉ giọt nước."
        }
    },
    "quat_dien": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã rút phích cắm điện 220V khỏi ổ cắm.")
        ],
        "default_assembly": "Cụm Động Cơ Bạc Đạn & Trục Rotor",
        "inspection": {
            "action": "INSPECT_BEARING_BUSHING_AND_CAPACITOR",
            "instruction_vn": "Tháo lồng quạt và vỏ ốp motor. Dùng tay lắc kiểm tra độ dơ/bó kẹt của trục bạc BEARING_BUSHING, đo dung lượng tụ quạt FAN_CAPACITOR (chuẩn 1.5 - 2.5μF) và đo thông mạch cuộn dây stator.",
            "voltage_checkpoint": "1.5 - 2.5μF (Tụ quạt) / 0Ω (Cầu chì)",
            "tools": ["CAPACITANCE_METER", "PH2_SCREWDRIVER", "MOTOR_OIL_LUBRICANT"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế tụ quạt / tuốc năng chuyển hướng ({target}), tra dầu nhờn chuyên dụng vào dạ giữ dầu trục bạc."
        },
        "replace_primary": {
            "instruction_vn": "Tháo cụm nắp nhôm trước/sau, thay thế cặp bạc thau dầu ({target}) mới, đánh bóng trục rotor bằng giấy nhám mịn và siết ốc cân bằng tâm trục."
        },
        "verification": {
            "action": "TEST_FAN_SPEEDS_AND_OSCILLATION",
            "instruction_vn": "Cắm điện thử các mức số 1, 2, 3 kiểm tra quạt khởi động nhanh, gió mạnh êm ái và túp năng đảo hướng mượt mà không kêu cọt kẹt.",
            "tools": []
        },
        "qa": {
            "action": "RUN_30MIN_THERMAL_QA",
            "instruction_vn": "Cho quạt chạy liên tục 30 phút kiểm tra nhiệt độ vỏ động cơ ấm nhẹ $\le 55^\circ\text{C}$, không phát tiếng ồn hay mùi khét."
        }
    },
    "may_loc_nuoc": {
        "safety_rules": [
            ("REQ_POWER_OFF", "DISCONNECT_AC_POWER", "Đã rút phích cắm điện Adapter 24V."),
            ("REQ_WATER_SUPPLY_SHUTOFF", "SHUTOFF_INPUT_WATER", "Đã khóa van cấp nước nguồn đầu vào và khóa van bình áp chứa nước.")
        ],
        "default_assembly": "Cụm Bơm Tăng Áp 24V & Vỏ Màng RO",
        "inspection": {
            "action": "MEASURE_PUMP_HEAD_AND_TDS_WATER",
            "instruction_vn": "Đo điện áp Adapter nguồn 24V DC, gắn đồng hồ đo áp lực đẩy của bơm BOOSTER_PUMP_24V ($\ge 80\text{ PSI}$), kiểm tra van điện từ SOLENOID_VALVE đóng ngắt và dùng bút TDS đo chỉ số khoáng nước.",
            "voltage_checkpoint": "24V DC / $\ge 80\text{ PSI}$ (Áp lực bơm)",
            "tools": ["DIGITAL_MULTIMETER", "PRESSURE_GAUGE", "TDS_METER"]
        },
        "replace_auxiliary": {
            "instruction_vn": "Thay thế van điện từ / van áp cao / lõi lọc thô ({target}), quấn băng tan Teflon và cắm chặt các cút nối nhanh chống xì nước."
        },
        "replace_primary": {
            "instruction_vn": "Dùng vam mở cốc màng RO, bóc tách màng lọc RO ({target}) cũ bị tắc bẩn, bôi mỡ thực phẩm lên gioăng cao su và ép chặt màng RO mới vào đáy cốc lọc."
        },
        "verification": {
            "action": "TEST_PURIFIER_FLOW_AND_AUTO_SHUTOFF",
            "instruction_vn": "Mở van nước cấp và cắm điện: Bơm chạy êm, nước tinh khiết chảy thành dòng liên tục và nước thải ngắt hoàn toàn khi bình áp đầy nước.",
            "tools": ["TDS_METER"]
        },
        "qa": {
            "action": "TEST_WATER_TDS_PURITY_QA",
            "instruction_vn": "Dùng bút thử TDS đo nước tinh khiết đạt chỉ số $< 20\text{ ppm}$ (Đạt chuẩn nước uống trực tiếp QCVN 6-1:2010/BYT) và toàn bộ hệ thống cút nối không rò rỉ giọt nước nào."
        }
    }
}


class StateMachineWorkflowGenerator:
    def __init__(self):
        self.version = "2.0"

    def generate_workflow(self, expanded_ctx: Dict[str, Any], strategy: str, evidence_chunks: List[Dict[str, Any]] = None) -> RepairWorkflowDSL:
        device_id = expanded_ctx["device_id"]
        primary_comp = expanded_ctx["primary_component"]
        fault_code = expanded_ctx.get("fault_code", "GENERIC_FAULT")
        cluster = expanded_ctx.get("expanded_cluster", [primary_comp])
        skill_level = expanded_ctx.get("skill_level_required", "BASIC_TECH")
        
        # 1. Tra cứu đặc tả miền chuyên biệt theo thiết bị (Domain Specification)
        spec = DOMAIN_WORKFLOW_SPECS.get(device_id, DOMAIN_WORKFLOW_SPECS["laptop"])
        assembly_name = expanded_ctx.get("assembly_name")
        if not assembly_name or assembly_name == "Cụm tiêu chuẩn":
            assembly_name = spec.get("default_assembly", "Cụm linh kiện tiêu chuẩn")
            
        workflow_id = f"WF_{device_id.upper()}_{uuid.uuid4().hex[:8].upper()}"
        
        # 2. Khởi tạo Safety Prerequisites theo đúng chuyên môn thiết bị
        prerequisites = []
        for r_code, r_op, r_audit in spec.get("safety_rules", []):
            prerequisites.append(
                SafetyPrerequisite(
                    rule_code=r_code,
                    operation=r_op,
                    mandatory=True,
                    audit_checkpoint=r_audit
                )
            )

        # 3. Xây dựng Danh sách Trạng thái (State Machine DAG Nodes)
        states = []
        initial_state = "STATE_SAFETY_ISOLATION"

        # STATE 0: SAFETY ISOLATION
        safety_instruction = f"Ngắt hoàn toàn nguồn điện lưới và thực hiện cô lập an toàn cho {device_id.replace('_', ' ')} trước khi tháo mở thiết bị."
        if prerequisites:
            safety_instruction = prerequisites[0].audit_checkpoint

        states.append(DAGStateNode(
            state_id="STATE_SAFETY_ISOLATION",
            phase="SAFETY_PREREQUISITE",
            action="DISCONNECT_ALL_POWER_SOURCES",
            target="POWER_INPUT",
            assembly=assembly_name,
            tools=["INSULATED_SCREWDRIVER", "PLASTIC_SPUDGER"],
            instruction_vn=safety_instruction,
            transitions=[
                StateTransition(
                    event="SAFETY_CONFIRMED",
                    next_state="STATE_INSPECT_CLUSTER_INTEGRITY"
                )
            ]
        ))

        # STATE 1: INSPECTION & VOLTAGE / IMPEDANCE CHECK
        insp_spec = spec["inspection"]
        inspection_instruction = insp_spec["instruction_vn"]
        if strategy == "STRUCTURAL_INTEGRITY_FIRST":
            inspection_instruction = f"[Chiến lược Rơi vỡ / Va đập] Soi kính lúp kiểm tra nứt gãy cơ khí, cong vênh khung sườn và đo thông mạch các đường dây cáp kết nối."
        elif strategy == "CHEMICAL_ISOLATION_FIRST":
            inspection_instruction = f"[Chiến lược Ngấm nước / Ẩm mốc] Tuyệt đối không cắm điện. Dùng cồn Isopropyl 99% tẩy rửa sạch các vết ten rỉ/oxy hóa và sấy khô 60°C trước khi đo kiểm."

        states.append(DAGStateNode(
            state_id="STATE_INSPECT_CLUSTER_INTEGRITY",
            phase="INSPECTION",
            action=insp_spec["action"],
            target=primary_comp,
            assembly=assembly_name,
            tools=insp_spec.get("tools", ["DIGITAL_MULTIMETER"]),
            voltage_checkpoint=insp_spec.get("voltage_checkpoint", "NOMINAL_VOLTAGE"),
            instruction_vn=inspection_instruction,
            transitions=[
                StateTransition(
                    condition="DEFECT_DETECTED_ON_SIBLING",
                    condition_description_vn="Phát hiện đứt ngầm cáp, rách gioăng hoặc hỏng linh kiện phụ trợ trong cụm",
                    next_state="STATE_REPLACE_AUXILIARY_COMPONENT"
                ),
                StateTransition(
                    condition="DEFECT_CONFIRMED_ON_PRIMARY",
                    condition_description_vn=f"Linh kiện chính ({primary_comp}) hỏng hoàn toàn (đứt cuộn dây, chập mạch hoặc vỡ cơ khí)",
                    next_state="STATE_REPLACE_PRIMARY_COMPONENT"
                )
            ]
        ))

        # STATE 2A: REPLACE AUXILIARY (Nhánh phụ trợ)
        sibling_name = cluster[1] if len(cluster) > 1 else "LINH_KIEN_PHU_TRO"
        aux_instruction = spec["replace_auxiliary"]["instruction_vn"].replace("{target}", sibling_name)
        states.append(DAGStateNode(
            state_id="STATE_REPLACE_AUXILIARY_COMPONENT",
            phase="REPAIR",
            action="SWAP_COMPONENT",
            target=sibling_name,
            assembly=assembly_name,
            tools=insp_spec.get("tools", []),
            instruction_vn=aux_instruction,
            transitions=[
                StateTransition(
                    event="AUXILIARY_REPLACED_SUCCESS",
                    next_state="STATE_POST_REPAIR_VERIFICATION"
                )
            ]
        ))

        # STATE 2B: REPLACE PRIMARY (Nhánh chính)
        pri_instruction = spec["replace_primary"]["instruction_vn"].replace("{target}", primary_comp)
        states.append(DAGStateNode(
            state_id="STATE_REPLACE_PRIMARY_COMPONENT",
            phase="REPAIR",
            action="SWAP_COMPONENT",
            target=primary_comp,
            assembly=assembly_name,
            tools=insp_spec.get("tools", []),
            instruction_vn=pri_instruction,
            transitions=[
                StateTransition(
                    event="PRIMARY_REPLACED_SUCCESS",
                    next_state="STATE_POST_REPAIR_VERIFICATION"
                )
            ]
        ))

        # STATE 3: VERIFICATION
        verif_spec = spec["verification"]
        states.append(DAGStateNode(
            state_id="STATE_POST_REPAIR_VERIFICATION",
            phase="VERIFICATION",
            action=verif_spec["action"],
            target=primary_comp,
            assembly=assembly_name,
            tools=verif_spec.get("tools", ["DIGITAL_MULTIMETER"]),
            instruction_vn=verif_spec["instruction_vn"],
            transitions=[
                StateTransition(
                    condition="FUNCTION_NORMAL",
                    condition_description_vn="Thiết bị hoạt động ổn định, thông số danh định và chức năng đạt chuẩn",
                    next_state="STATE_QUALITY_ASSURANCE"
                ),
                StateTransition(
                    condition="STILL_FAILING",
                    condition_description_vn="Vẫn còn hiện tượng chập chờn hoặc không nhận tín hiệu",
                    next_state="STATE_INSPECT_CLUSTER_INTEGRITY"
                )
            ]
        ))

        # STATE 4: QUALITY ASSURANCE
        qa_spec = spec["qa"]
        states.append(DAGStateNode(
            state_id="STATE_QUALITY_ASSURANCE",
            phase="QUALITY",
            action=qa_spec["action"],
            target=assembly_name,
            assembly=assembly_name,
            tools=[],
            instruction_vn=qa_spec["instruction_vn"],
            transitions=[
                StateTransition(
                    event="QA_PASSED_100_PERCENT",
                    next_state="STATE_DELIVERY_HANDOVER"
                )
            ]
        ))

        # STATE 5: DELIVERY & WARRANTY
        states.append(DAGStateNode(
            state_id="STATE_DELIVERY_HANDOVER",
            phase="DELIVERY",
            action="ISSUE_WARRANTY_AND_HANDOVER",
            target="CUSTOMER_UNIT",
            assembly=assembly_name,
            tools=[],
            instruction_vn=f"Vệ sinh toàn bộ thiết bị ({device_id.replace('_', ' ')}), dán tem niêm phong bảo hành và bàn giao phiếu bảo hành điện tử minh bạch cho khách hàng.",
            transitions=[] # Trạng thái kết thúc
        ))

        # 4. Đóng gói đối tượng Workflow DSL
        workflow = RepairWorkflowDSL(
            workflow_metadata=WorkflowMetadata(
                workflow_id=workflow_id,
                dsl_version="2.2",
                knowledge_graph_version="5.2",
                planner_version="2.0",
                validator_version="1.0",
                device_id=device_id,
                fault_code=fault_code,
                strategy_applied=strategy,
                estimated_duration_minutes=45 if skill_level == "BASIC_TECH" else 60,
                required_skill_level=skill_level
            ),
            safety_prerequisites=prerequisites,
            initial_state=initial_state,
            states=states
        )

        # 5. Kiểm toán an toàn qua Pure Audit Validator
        val_result = safety_validator.validate_workflow(workflow)
        workflow.validation_status = val_result["status"]
        workflow.audit_log = val_result["audit_log"]

        # 6. Đo lường chỉ số rủi ro qua Risk Scorer
        risk_result = risk_scorer.calculate_risk_score(workflow)
        workflow.risk_score = risk_result["risk_score"]

        return workflow

workflow_generator = StateMachineWorkflowGenerator()
