# -*- coding: utf-8 -*-
"""
Enterprise Pricing SSOT Knowledge Base & Training Datasets Generator (V3.2)
Bao phủ 100% 196+ linh kiện kỹ thuật từ SSOT Taxonomy của 11 thiết bị.
Tạo 4 tệp SSOT độc lập:
1. component_market_db.json (100% linh kiện taxonomy)
2. labor_market_db.json (100% mã lỗi taxonomy)
3. warranty_policy.json
4. pricing_statistics.json (Keyed by component_id_brandtier_parttype)

Và sinh 2 tập dữ liệu huấn luyện ML tách rời:
- component_train_dataset.csv
- labor_train_dataset.csv
"""

import os
import sys
import json
import random
import re
import numpy as np
import pandas as pd

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAXONOMY_PATH = os.path.join(BASE_DIR, "datasets", "diagnosis", "fault_taxonomy.json")
BENCHMARK_PATH = os.path.join(BASE_DIR, "datasets", "pricing", "pricing_benchmark_matrix.json")
PRICING_DIR = os.path.join(BASE_DIR, "datasets", "pricing")

os.makedirs(PRICING_DIR, exist_ok=True)

# 1. Nạp Taxonomy và Benchmark hiện có
with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
    taxonomy = json.load(f)

existing_bench = {}
if os.path.exists(BENCHMARK_PATH):
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        existing_bench = json.load(f)

# Từ điển ánh xạ tên tiếng Việt và đơn giá tham chiếu cho 196 linh kiện
COMPONENT_KNOWLEDGE = {
    # 1. Laptop & Thiết bị IT
    "LCD_PANEL": {"name": "Tấm nền màn hình LCD/IPS Laptop", "replace": 1450000, "repair": 350000, "warranty": 6},
    "LCD_OLED_PANEL": {"name": "Tấm nền màn hình OLED/4K cao cấp", "replace": 2650000, "repair": 650000, "warranty": 6},
    "EDP_CABLE": {"name": "Cáp màn hình eDP tín hiệu", "replace": 280000, "repair": 120000, "warranty": 3},
    "LVDS_CABLE": {"name": "Cáp tín hiệu LVDS", "replace": 250000, "repair": 100000, "warranty": 3},
    "LVDS_FLEX_CABLE": {"name": "Cáp dẹp LVDS Flex", "replace": 250000, "repair": 100000, "warranty": 3},
    "BACKLIGHT_LED": {"name": "Dải đèn LED nền màn hình", "replace": 320000, "repair": 150000, "warranty": 3},
    "POLARIZER_FILM": {"name": "Tấm phim phân cực hiển thị", "replace": 350000, "repair": 150000, "warranty": 3},
    "GPU": {"name": "Chip đồ họa rời GPU / Đóng lại chip", "replace": 1850000, "repair": 550000, "warranty": 3},
    "RAM_MODULE": {"name": "Thanh bộ nhớ RAM (DDR4/DDR5)", "replace": 550000, "repair": 150000, "warranty": 12},
    "SSD_NVME": {"name": "Ổ cứng thể rắn SSD M.2 NVMe", "replace": 750000, "repair": 200000, "warranty": 12},
    "HDD_SATA": {"name": "Ổ cứng cơ HDD 2.5 inch", "replace": 600000, "repair": 180000, "warranty": 12},
    "STORAGE_CONTROLLER": {"name": "IC điều khiển lưu trữ / Cầu Nam", "replace": 650000, "repair": 280000, "warranty": 3},
    "EMMC_MEMORY": {"name": "Chip nhớ eMMC hàn trên bo mạch", "replace": 550000, "repair": 250000, "warranty": 3},
    "KEYBOARD_MEMBRANE": {"name": "Bàn phím Laptop (Cụm phím)", "replace": 450000, "repair": 150000, "warranty": 6},
    "KEY_SWITCH": {"name": "Cụm switch nút phím đơn", "replace": 150000, "repair": 80000, "warranty": 3},
    "KEYBOARD_FLEX_CABLE": {"name": "Cáp kết nối bàn phím", "replace": 180000, "repair": 80000, "warranty": 3},
    "INTERNAL_SPEAKER": {"name": "Cặp loa trong laptop", "replace": 350000, "repair": 120000, "warranty": 3},
    "INTERNAL_STEREO_SPEAKERS": {"name": "Cụm loa âm thanh nổi Stereo", "replace": 400000, "repair": 150000, "warranty": 3},
    "AUDIO_CODEC_CHIP": {"name": "IC xử lý âm thanh Audio Codec", "replace": 420000, "repair": 180000, "warranty": 3},
    "AUDIO_AMPLIFIER_IC": {"name": "IC khuếch đại công suất âm thanh", "replace": 380000, "repair": 160000, "warranty": 3},
    "HEADPHONE_JACK": {"name": "Cổng cắm tai nghe 3.5mm", "replace": 180000, "repair": 80000, "warranty": 3},
    "BATTERY_CELL": {"name": "Cụm pin Laptop Lithium-ion/Polymer", "replace": 650000, "repair": 250000, "warranty": 6},
    "CHARGING_IC": {"name": "IC quản lý sạc nguồn", "replace": 450000, "repair": 200000, "warranty": 3},
    "DC_JACK": {"name": "Chân cắm nguồn DC Jack", "replace": 180000, "repair": 90000, "warranty": 3},
    "POWER_JACK": {"name": "Cổng cắm nguồn Power Jack", "replace": 180000, "repair": 90000, "warranty": 3},
    "BMS_CIRCUIT": {"name": "Mạch quản lý pin BMS bảo vệ", "replace": 320000, "repair": 150000, "warranty": 3},
    "TRACKPAD_MODULE": {"name": "Bàn di chuột cảm ứng Trackpad", "replace": 380000, "repair": 140000, "warranty": 6},
    "TRACKPAD_FLEX_CABLE": {"name": "Cáp nối bàn di chuột", "replace": 160000, "repair": 70000, "warranty": 3},
    "CLICK_BUTTON": {"name": "Nút bấm chuột cơ học", "replace": 120000, "repair": 60000, "warranty": 3},
    "CPU_FAN": {"name": "Quạt tản nhiệt CPU", "replace": 280000, "repair": 100000, "warranty": 3},
    "GPU_FAN": {"name": "Quạt tản nhiệt GPU", "replace": 280000, "repair": 100000, "warranty": 3},
    "HEATSINK": {"name": "Cụm ống đồng dẫn nhiệt tản nhiệt", "replace": 320000, "repair": 120000, "warranty": 3},
    "COOLING_FINS": {"name": "Lá nhôm tản nhiệt làm mát", "replace": 220000, "repair": 90000, "warranty": 3},
    "THERMAL_PASTE": {"name": "Keo tản nhiệt cao cấp (Thermal Grizzly/MX4)", "replace": 120000, "repair": 80000, "warranty": 1},
    "WIFI_CARD": {"name": "Card mạng Wi-Fi không dây", "replace": 320000, "repair": 120000, "warranty": 6},
    "WIFI_MODULE": {"name": "Module thu phát sóng Wi-Fi", "replace": 300000, "repair": 120000, "warranty": 6},
    "WLAN_ANTENNA": {"name": "Dây ăng-ten ngầm Wi-Fi", "replace": 150000, "repair": 70000, "warranty": 3},
    "BLUETOOTH_MODULE": {"name": "Module Bluetooth tích hợp", "replace": 220000, "repair": 90000, "warranty": 3},
    "METAL_HINGE": {"name": "Bản lề kim loại gập mở laptop", "replace": 350000, "repair": 180000, "warranty": 6},
    "DOOR_HINGE_ALIGNMENT": {"name": "Cân chỉnh bản lề cửa", "replace": 200000, "repair": 100000, "warranty": 3},
    "TOP_CASE": {"name": "Mặt vỏ A/C (Khung trên)", "replace": 550000, "repair": 200000, "warranty": 3},
    "BOTTOM_CASE": {"name": "Mặt vỏ D (Đáy máy)", "replace": 450000, "repair": 180000, "warranty": 3},
    "BEZEL": {"name": "Viền màn hình B Bezel", "replace": 250000, "repair": 100000, "warranty": 3},
    "MAINBOARD": {"name": "Bo mạch chủ Mainboard", "replace": 2250000, "repair": 650000, "warranty": 6},
    "MAIN_MOTHERBOARD": {"name": "Bo mạch chủ tổng Tivi/Thiết bị", "replace": 1650000, "repair": 550000, "warranty": 6},
    "MAIN_MCU": {"name": "Vi điều khiển trung tâm Main MCU", "replace": 550000, "repair": 250000, "warranty": 3},
    "MAIN_CONTROL_BOARD": {"name": "Bo mạch điều khiển trung tâm", "replace": 850000, "repair": 350000, "warranty": 6},
    "SOC_PROCESSOR": {"name": "Bộ vi xử lý trung tâm SoC", "replace": 1450000, "repair": 450000, "warranty": 3},
    "POWER_IC_PWM": {"name": "IC dao động nguồn PWM", "replace": 380000, "repair": 180000, "warranty": 3},
    "POWER_MOSFET": {"name": "Transistor công suất nguồn MOSFET", "replace": 250000, "repair": 120000, "warranty": 3},
    "FILTER_CAPACITOR": {"name": "Tụ điện lọc nguồn cao cấp", "replace": 150000, "repair": 80000, "warranty": 3},
    "POWER_FUSE": {"name": "Cầu chì nguồn bảo vệ", "replace": 100000, "repair": 50000, "warranty": 1},
    "POWER_SUPPLY_UNIT": {"name": "Bo nguồn tổng PSU", "replace": 750000, "repair": 300000, "warranty": 6},
    "SWITCHING_POWER_SUPPLY": {"name": "Nguồn xung Switching", "replace": 450000, "repair": 180000, "warranty": 6},
    "SWITCHING_TRANSFORMER": {"name": "Biến áp xung Switching", "replace": 320000, "repair": 140000, "warranty": 3},
    "STANDBY_TRANSFORMER": {"name": "Biến áp nguồn phụ Standby", "replace": 250000, "repair": 100000, "warranty": 3},
    "BRIDGE_RECTIFIER": {"name": "Cầu đi-ốt nắn dòng Rectifier", "replace": 180000, "repair": 80000, "warranty": 3},
    "TCON_BOARD": {"name": "Bo xử lý hình ảnh T-Con", "replace": 650000, "repair": 250000, "warranty": 6},
    "COF_TAB_BONDING": {"name": "Đóng ép cáp COF màn hình chuyên dụng", "replace": 850000, "repair": 450000, "warranty": 3},
    "GAMMA_IC": {"name": "IC hiệu chỉnh màu sắc Gamma", "replace": 350000, "repair": 160000, "warranty": 3},
    "LED_BACKLIGHT_STRIP": {"name": "Bộ thanh LED viền / LED nền Tivi", "replace": 550000, "repair": 220000, "warranty": 6},
    "LED_DRIVER_CIRCUIT": {"name": "Mạch điều khiển LED Driver", "replace": 380000, "repair": 150000, "warranty": 3},
    "USB_INTERFACE_CHIP": {"name": "IC giao tiếp cổng USB", "replace": 280000, "repair": 120000, "warranty": 3},

    # 2. Điều hòa & Tủ lạnh (HVAC & Cooling)
    "COMPRESSOR": {"name": "Máy nén lạnh (Lốc điều hòa/tủ lạnh)", "replace": 2150000, "repair": 650000, "warranty": 12},
    "INVERTER_COMPRESSOR": {"name": "Máy nén biến tần Inverter", "replace": 2850000, "repair": 850000, "warranty": 12},
    "OUTDOOR_INVERTER_BOARD": {"name": "Bo mạch biến tần dàn nóng Inverter", "replace": 1350000, "repair": 450000, "warranty": 6},
    "INVERTER_PCB": {"name": "Bo mạch Inverter điều khiển", "replace": 1150000, "repair": 400000, "warranty": 6},
    "INVERTER_CONTROL_BOARD": {"name": "Bo mạch điều khiển Inverter tủ lạnh", "replace": 950000, "repair": 350000, "warranty": 6},
    "IPM_MODULE": {"name": "IC công suất biến tần IPM", "replace": 650000, "repair": 280000, "warranty": 3},
    "IPM_INVERTER_DRIVER": {"name": "Khối điều khiển công suất IPM", "replace": 680000, "repair": 300000, "warranty": 3},
    "INDOOR_FAN_MOTOR": {"name": "Mô tơ quạt dàn lạnh", "replace": 480000, "repair": 180000, "warranty": 6},
    "OUTDOOR_FAN_MOTOR": {"name": "Mô tơ quạt dàn nóng", "replace": 550000, "repair": 200000, "warranty": 6},
    "EVAPORATOR_FAN_MOTOR": {"name": "Mô tơ quạt gió dàn lạnh tủ lạnh", "replace": 380000, "repair": 150000, "warranty": 6},
    "EXPANSION_VALVE": {"name": "Van tiết lưu điện tử", "replace": 450000, "repair": 180000, "warranty": 6},
    "CAPILLARY_TUBE": {"name": "Ống mao tiết lưu", "replace": 250000, "repair": 100000, "warranty": 3},
    "REFRIGERANT_R32_R410A": {"name": "Nạp ga lạnh chuyên dụng R32 / R410A", "replace": 450000, "repair": 250000, "warranty": 6},
    "REFRIGERANT_R600A": {"name": "Nạp ga tủ lạnh R600a an toàn", "replace": 350000, "repair": 200000, "warranty": 6},
    "ROOM_THERMISTOR": {"name": "Cảm biến nhiệt độ phòng", "replace": 180000, "repair": 80000, "warranty": 3},
    "PIPE_THERMISTOR": {"name": "Cảm biến nhiệt độ ống đồng", "replace": 180000, "repair": 80000, "warranty": 3},
    "DISCHARGE_THERMISTOR": {"name": "Cảm biến nhiệt độ đầu đẩy máy nén", "replace": 220000, "repair": 90000, "warranty": 3},
    "DEFROST_SENSOR": {"name": "Cảm biến xả đá tủ lạnh", "replace": 160000, "repair": 70000, "warranty": 3},
    "DEFROST_HEATER": {"name": "Thanh sấy xả băng dàn lạnh", "replace": 280000, "repair": 120000, "warranty": 6},
    "DEFROST_THERMOSTAT_BIMETAL": {"name": "Sò lạnh / Rơ-le xả đá lưỡng kim", "replace": 150000, "repair": 60000, "warranty": 3},
    "DEFROST_TIMER": {"name": "Đồng hồ hẹn giờ xả đá cơ học", "replace": 220000, "repair": 90000, "warranty": 6},
    "PTC_STARTER_RELAY": {"name": "Rơ-le khởi động máy nén PTC", "replace": 160000, "repair": 70000, "warranty": 3},
    "OVERLOAD_PROTECTOR": {"name": "Rơ-le bảo vệ quá tải nhiệt", "replace": 140000, "repair": 60000, "warranty": 3},
    "OVERLOAD_PROTECTOR_KLIXON": {"name": "Rơ-le téc-mít bảo vệ Klixon", "replace": 140000, "repair": 60000, "warranty": 3},
    "MAGNETIC_DOOR_GASKET": {"name": "Gioăng cao su hít cửa tủ lạnh", "replace": 350000, "repair": 140000, "warranty": 6},
    "DRAIN_PUMP_MOTOR": {"name": "Bơm xả nước ngưng / Bơm xả đáy", "replace": 450000, "repair": 180000, "warranty": 6},
    "CONDENSATE_PUMP": {"name": "Bơm thoát nước ngưng điều hòa", "replace": 420000, "repair": 160000, "warranty": 6},
    "DRAIN_PAN": {"name": "Máng hứng nước ngưng tụ", "replace": 220000, "repair": 90000, "warranty": 3},
    "DRAIN_VALVE": {"name": "Van xả nước tự động", "replace": 280000, "repair": 110000, "warranty": 3},
    "COPPER_PIPE": {"name": "Ống đồng dẫn môi chất lạnh", "replace": 350000, "repair": 150000, "warranty": 6},
    "COPPER_ALUMINUM_EVAPORATOR": {"name": "Dàn lạnh nhôm đồng", "replace": 850000, "repair": 320000, "warranty": 6},
    "FLARE_NUT": {"name": "Rắc co / Khớp nối loe ống đồng", "replace": 120000, "repair": 50000, "warranty": 3},
    "DRIER_FILTER": {"name": "Phin lọc sấy ẩm hệ thống lạnh", "replace": 160000, "repair": 70000, "warranty": 3},
    "CAPACITOR": {"name": "Tụ đề khởi động lốc / quạt", "replace": 180000, "repair": 80000, "warranty": 3},
    "SWING_MOTOR": {"name": "Mô tơ đảo gió cánh vẫy", "replace": 180000, "repair": 80000, "warranty": 3},

    # 3. Máy giặt (Washing Machine)
    "INLET_SOLENOID_VALVE": {"name": "Van cấp nước điện từ đơn/đôi", "replace": 280000, "repair": 110000, "warranty": 6},
    "WATER_LEVEL_PRESSURE_SENSOR": {"name": "Phao áp lực cảm biến mực nước", "replace": 220000, "repair": 90000, "warranty": 6},
    "DIRECT_DRIVE_MOTOR": {"name": "Động cơ truyền động trực tiếp DD", "replace": 1650000, "repair": 500000, "warranty": 12},
    "STATOR_COPPER_COIL": {"name": "Cuộn dây đồng Stator động cơ", "replace": 750000, "repair": 280000, "warranty": 6},
    "ROTOR_STATOR": {"name": "Bộ Rotor và Stator máy giặt", "replace": 850000, "repair": 320000, "warranty": 6},
    "BELT_PULLEY": {"name": "Dây curoa truyền động máy giặt", "replace": 180000, "repair": 70000, "warranty": 6},
    "CARBON_BRUSHES": {"name": "Chổi than động cơ máy giặt", "replace": 190000, "repair": 80000, "warranty": 3},
    "SUSPENSION_SPRING": {"name": "Bộ lò xo treo giảm chấn", "replace": 250000, "repair": 100000, "warranty": 6},
    "SHOCK_ABSORBER": {"name": "Bộ thụt giảm xóc máy giặt lồng ngang", "replace": 350000, "repair": 130000, "warranty": 6},
    "DOOR_LOCK_SWITCH": {"name": "Công tắc khóa cửa an toàn", "replace": 280000, "repair": 110000, "warranty": 6},
    "DOOR_LATCH": {"name": "Lẫy tay nắm cửa máy giặt", "replace": 150000, "repair": 60000, "warranty": 3},
    "DOOR_SWITCH": {"name": "Công tắc tiếp điểm nắp cửa", "replace": 160000, "repair": 70000, "warranty": 3},
    "PTC_HEATER_LOCK": {"name": "Khóa cửa nhiệt điện PTC", "replace": 260000, "repair": 100000, "warranty": 6},
    "RUBBER_BELLOW": {"name": "Gioăng cao su lồng giặt cửa ngang", "replace": 550000, "repair": 200000, "warranty": 6},
    "LINT_FILTER": {"name": "Bộ túi lưới lọc xơ vải", "replace": 120000, "repair": 50000, "warranty": 1},
    "AIR_TRAP_DOME": {"name": "Bầu bẫy khí tạo áp", "replace": 140000, "repair": 60000, "warranty": 3},
    "AIR_PRESSURE_TUBE": {"name": "Ống dẫn áp lực nước mềm", "replace": 90000, "repair": 40000, "warranty": 3},
    "INLET_FILTER_MESH": {"name": "Lưới lọc cặn đầu van cấp nước", "replace": 80000, "repair": 30000, "warranty": 1},
    "HALL_SENSOR": {"name": "Cảm biến tốc độ vòng quay Hall Sensor", "replace": 220000, "repair": 90000, "warranty": 3},

    # 4. Máy in (Printer)
    "PICKUP_ROLLER": {"name": "Quả đào kéo giấy Pickup Roller", "replace": 180000, "repair": 70000, "warranty": 3},
    "FEED_ROLLER": {"name": "Trục cao su cuốn giấy Feed Roller", "replace": 180000, "repair": 70000, "warranty": 3},
    "SEPARATION_PAD": {"name": "Đệm tách giấy cao su", "replace": 120000, "repair": 50000, "warranty": 3},
    "OPTICAL_PAPER_SENSOR": {"name": "Cảm biến quang nhận diện giấy", "replace": 180000, "repair": 80000, "warranty": 3},
    "SENSOR_FLAG": {"name": "Cò cờ cảm biến giấy cơ học", "replace": 100000, "repair": 40000, "warranty": 1},
    "FUSER_ASSEMBLY": {"name": "Cụm sấy nhiệt máy in Fuser", "replace": 850000, "repair": 320000, "warranty": 6},
    "HEATING_CERAMIC_ELEMENT": {"name": "Thanh nhiệt gốm nung sấy", "replace": 280000, "repair": 110000, "warranty": 3},
    "PRESSURE_ROLLER": {"name": "Lô ép sấy cao su chịu nhiệt", "replace": 220000, "repair": 90000, "warranty": 3},
    "FIXING_FILM": {"name": "Bao lụa sấy chịu nhiệt Teflon", "replace": 190000, "repair": 80000, "warranty": 3},
    "LASER_SCANNER_UNIT": {"name": "Hộp gương Laser quang học", "replace": 650000, "repair": 250000, "warranty": 6},
    "POLYGON_MIRROR": {"name": "Gương đa giác xoay quét tia laser", "replace": 350000, "repair": 140000, "warranty": 3},
    "LASER_DIODE": {"name": "Đi-ốt phát tia Laser", "replace": 280000, "repair": 110000, "warranty": 3},
    "TONER_CARTRIDGE": {"name": "Hộp mực in Laser Cartridge", "replace": 380000, "repair": 120000, "warranty": 3},
    "OPC_DRUM": {"name": "Trống mực quang học OPC Drum", "replace": 180000, "repair": 70000, "warranty": 3},
    "MAGNETIC_ROLLER": {"name": "Trục từ hút mực", "replace": 150000, "repair": 60000, "warranty": 3},
    "WIPER_BLADE": {"name": "Gạt mực lớn gạt trống", "replace": 110000, "repair": 40000, "warranty": 1},
    "INKJET_PRINTHEAD": {"name": "Đầu phun mực máy in màu Printhead", "replace": 1250000, "repair": 450000, "warranty": 3},
    "INK_DAMPER": {"name": "Tép giảm áp mực Damper", "replace": 120000, "repair": 50000, "warranty": 3},
    "PIEZO_ACTUATOR": {"name": "Bộ rung thạch anh áp điện phun mực", "replace": 450000, "repair": 180000, "warranty": 3},
    "FORMATTER_BOARD": {"name": "Bo mạch xử lý Formatter máy in", "replace": 750000, "repair": 280000, "warranty": 6},

    # 5. Máy bơm nước (Water Pump)
    "PRESSURE_SWITCH_AUTO": {"name": "Rơ-le áp lực tự động máy bơm", "replace": 220000, "repair": 90000, "warranty": 6},
    "PRESSURE_STORAGE_TANK": {"name": "Bình tích áp cao su máy bơm", "replace": 350000, "repair": 120000, "warranty": 6},
    "DIAPHRAGM_SPRING": {"name": "Màng cao su & Lò xo hồi áp", "replace": 150000, "repair": 60000, "warranty": 3},
    "CONTACT_POINTS": {"name": "Tiếp điểm má vít đóng ngắt", "replace": 110000, "repair": 50000, "warranty": 1},
    "MECHANICAL_WATER_SEAL": {"name": "Phớt cơ năng chặn nước trục bơm", "replace": 180000, "repair": 80000, "warranty": 6},
    "CERAMIC_RING": {"name": "Vành gốm làm kín cơ học", "replace": 120000, "repair": 50000, "warranty": 3},
    "CARBON_FACE": {"name": "Mặt trượt carbon chịu mòn", "replace": 120000, "repair": 50000, "warranty": 3},
    "BRASS_IMPELLER": {"name": "Cánh bơm nước bằng đồng thau", "replace": 280000, "repair": 100000, "warranty": 6},
    "ROTOR_SHAFT": {"name": "Trục Rotor quay máy bơm/quạt", "replace": 320000, "repair": 120000, "warranty": 6},
    "PUMP_HOUSING_CHAMBER": {"name": "Buồng bơm đúc gang/nhôm", "replace": 450000, "repair": 160000, "warranty": 6},
    "WEAR_RING": {"name": "Vành chống mòn buồng bơm", "replace": 140000, "repair": 50000, "warranty": 3},
    "MOTOR_STATOR_COIL": {"name": "Cuộn dây đồng Stator mô tơ bơm", "replace": 450000, "repair": 190000, "warranty": 6},
    "PUMP_STARTING_CAPACITOR": {"name": "Tụ ngâm khởi động máy bơm nước", "replace": 160000, "repair": 70000, "warranty": 3},
    "THERMAL_OVERLOAD_PROTECTOR": {"name": "Rơ-le nhiệt bảo vệ cuộn dây", "replace": 150000, "repair": 60000, "warranty": 3},
    "CHECK_VALVE": {"name": "Van một chiều giữ nước mồi", "replace": 160000, "repair": 60000, "warranty": 3},
    "FOOT_VALVE_LUPPE": {"name": "Rúp-bê / Luppe hút chân không", "replace": 140000, "repair": 50000, "warranty": 3},
    "AIR_VALVE": {"name": "Van nạp xả khí bình tích áp", "replace": 90000, "repair": 40000, "warranty": 1},
    "AIR_BLADDER": {"name": "Ruột bóng cao su bình tích áp", "replace": 220000, "repair": 80000, "warranty": 3},
    "SUCTION_PIPE_COUPLING": {"name": "Rắc co khớp nối ống hút", "replace": 110000, "repair": 40000, "warranty": 1},
    "TERMINAL_BOX": {"name": "Hộp đấu dây điện chống nước", "replace": 120000, "repair": 50000, "warranty": 3},

    # 6. Quạt điện (Electric Fan)
    "FAN_STATOR_COPPER_COIL": {"name": "Cuộn dây đồng Stator quạt", "replace": 180000, "repair": 80000, "warranty": 6},
    "FAN_STARTING_CAPACITOR_AC": {"name": "Tụ đề quạt điện 1.5uF - 2.5uF", "replace": 80000, "repair": 40000, "warranty": 3},
    "THERMAL_FUSE_130C": {"name": "Cầu chì nhiệt quạt 130 độ C", "replace": 70000, "repair": 35000, "warranty": 1},
    "BRONZE_BUSHING": {"name": "Cặp bạc thau dầu đỡ trục quạt", "replace": 120000, "repair": 50000, "warranty": 3},
    "FELT_OIL_RING": {"name": "Vòng nỉ giữ dầu bôi trơn trục", "replace": 50000, "repair": 25000, "warranty": 1},
    "SWING_GEARBOX": {"name": "Bộ tuốc-năng chuyển hướng đảo gió", "replace": 110000, "repair": 45000, "warranty": 3},
    "LINKAGE_ARM": {"name": "Thanh truyền nhôm tuốc-năng", "replace": 60000, "repair": 25000, "warranty": 1},
    "COUPLER_SHAFT": {"name": "Khớp nối trục đảo", "replace": 70000, "repair": 30000, "warranty": 1},
    "FAN_BLADE": {"name": "Cánh quạt làm mát 3-5 cánh", "replace": 90000, "repair": 40000, "warranty": 1},
    "SPEED_SWITCH_MECHANICAL": {"name": "Bộ phím bấm chuyển tốc độ cơ", "replace": 80000, "repair": 35000, "warranty": 3},
    "REMOTE_CONTROL_RECEIVER_PCB": {"name": "Mạch mắt nhận điều khiển từ xa", "replace": 180000, "repair": 70000, "warranty": 3},

    # 7. Máy lọc nước (Water Purifier)
    "RO_MEMBRANE": {"name": "Màng lọc thẩm thấu ngược RO Filmtec", "replace": 550000, "repair": 150000, "warranty": 12},
    "SEDIMENT_FILTER_123": {"name": "Bộ 3 lõi lọc thô 1-2-3", "replace": 220000, "repair": 80000, "warranty": 3},
    "POST_CARBON_MINERAL_FILTERS": {"name": "Bộ lõi khoáng bổ trợ T33 Nano", "replace": 380000, "repair": 120000, "warranty": 6},
    "BOOSTER_PUMP_HEAD": {"name": "Bơm áp lực máy lọc nước RO 24V", "replace": 480000, "repair": 180000, "warranty": 6},
    "PUMP_HEAD_DIAPHRAGM": {"name": "Đầu màng bơm cao áp", "replace": 180000, "repair": 70000, "warranty": 3},
    "SOLENOID_VALVE_24V": {"name": "Van điện từ ngắt nước tự động 24V", "replace": 160000, "repair": 60000, "warranty": 6},
    "HIGH_PRESSURE_SWITCH": {"name": "Van áp cao tự ngắt bơm khi đầy", "replace": 140000, "repair": 50000, "warranty": 6},
    "LOW_PRESSURE_SWITCH": {"name": "Van áp thấp ngắt khi mất nước nguồn", "replace": 140000, "repair": 50000, "warranty": 6},
    "POWER_ADAPTOR_24V": {"name": "Cục đổi nguồn Adapter 24V", "replace": 240000, "repair": 90000, "warranty": 6},
    "AUTO_FLUSH_VALVE": {"name": "Van xả rửa màng RO tự động", "replace": 150000, "repair": 60000, "warranty": 3},
    "FLOW_RESTRICTOR_300": {"name": "Van tiết lưu nước thải Flow 300", "replace": 80000, "repair": 30000, "warranty": 1},
    "PRESSURE_TANK_BLADDER": {"name": "Bình áp chứa nước tinh khiết", "replace": 380000, "repair": 120000, "warranty": 6},

    # 8. Nồi cơm điện (Rice Cooker)
    "BOTTOM_HEATING_PLATE": {"name": "Mâm nhiệt đúc đáy nồi cơm", "replace": 280000, "repair": 110000, "warranty": 6},
    "MAGNETIC_THERMOSTAT": {"name": "Rơ-le nam châm vĩnh cửu đáy nồi", "replace": 120000, "repair": 50000, "warranty": 3},
    "BI_METALLIC_STRIP": {"name": "Lá đồng lưỡng kim cảm ứng nhiệt", "replace": 80000, "repair": 35000, "warranty": 1},
    "THERMAL_FUSE_160C": {"name": "Cầu chì nhiệt nồi cơm 160-250 độ C", "replace": 70000, "repair": 30000, "warranty": 1},
    "MICRO_SWITCH": {"name": "Công tắc vi động đóng ngắt hành trình", "replace": 90000, "repair": 40000, "warranty": 3},
    "LEVER_MECHANISM": {"name": "Cần gạt chuyển chế độ Nấu / Giữ ấm", "replace": 80000, "repair": 35000, "warranty": 1},
    "LID_THERMISTOR_SENSOR": {"name": "Cảm biến nhiệt độ nắp trên", "replace": 150000, "repair": 60000, "warranty": 3},
    "BOTTOM_THERMISTOR_SENSOR": {"name": "Cảm biến nhiệt độ mâm đáy", "replace": 150000, "repair": 60000, "warranty": 3},
    "IH_HEATING_COIL": {"name": "Mâm cuộn dây cảm ứng từ IH", "replace": 450000, "repair": 180000, "warranty": 6},
    "IGBT_TRANSISTOR": {"name": "Sò công suất đóng cắt từ IGBT", "replace": 220000, "repair": 90000, "warranty": 3},
    "IH_CONTROL_BOARD": {"name": "Bo mạch điện tử nồi cơm cao tần IH", "replace": 650000, "repair": 250000, "warranty": 6},
    "STEAM_VENT_VALVE": {"name": "Cụm van thoát hơi nước chống trào", "replace": 120000, "repair": 45000, "warranty": 1},
    "INNER_POT_TEFLON_COATING": {"name": "Phục hồi tráng men chống dính lòng nồi", "replace": 280000, "repair": 140000, "warranty": 3},

    # 9. Lò vi sóng (Microwave)
    "MAGNETRON_VACUUM_TUBE": {"name": "Đèn phát sóng vi ba Magnetron", "replace": 550000, "repair": 220000, "warranty": 6},
    "FILAMENT_EMITTER": {"name": "Tim đèn phát xạ điện tử vi ba", "replace": 250000, "repair": 100000, "warranty": 3},
    "HV_TRANSFORMER": {"name": "Biến áp cao thế lò vi sóng", "replace": 480000, "repair": 190000, "warranty": 6},
    "HV_DIODE": {"name": "Đi-ốt cao áp chống ngược 12kV", "replace": 110000, "repair": 45000, "warranty": 3},
    "HV_CAPACITOR": {"name": "Tụ điện cao thế lò vi sóng 2100V", "replace": 180000, "repair": 70000, "warranty": 3},
    "HV_FUSE": {"name": "Cầu chì cao áp ống thủy tinh 5kV", "replace": 90000, "repair": 40000, "warranty": 1},
    "TURNTABLE_SYNCHRONOUS_MOTOR": {"name": "Mô tơ quay đĩa thủy tinh đồng bộ", "replace": 160000, "repair": 65000, "warranty": 6},
    "ROLLER_RING": {"name": "Vòng con lăn đỡ đĩa quay", "replace": 80000, "repair": 30000, "warranty": 1},
    "COUPLER_PLASTIC": {"name": "Khớp nối tam giác trục đĩa quay", "replace": 60000, "repair": 25000, "warranty": 1},
    "PRIMARY_DOOR_SWITCH": {"name": "Công tắc cửa sơ cấp an toàn", "replace": 120000, "repair": 50000, "warranty": 3},
    "SECONDARY_DOOR_SWITCH": {"name": "Công tắc cửa thứ cấp", "replace": 120000, "repair": 50000, "warranty": 3},
    "MONITOR_SWITCH": {"name": "Công tắc giám sát ngắn mạch cửa", "replace": 120000, "repair": 50000, "warranty": 3},
    "MICA_WAVEGUIDE_SHEET": {"name": "Tấm chắn sóng mica cách điện", "replace": 70000, "repair": 30000, "warranty": 1},
    "WAVEGUIDE_CHANNEL": {"name": "Ống dẫn hướng sóng vi ba", "replace": 180000, "repair": 70000, "warranty": 3},
    "CONTROL_PCB": {"name": "Bo mạch điều khiển hiển thị lò vi sóng", "replace": 450000, "repair": 180000, "warranty": 6},
    "TIMER": {"name": "Bộ đếm thời gian cơ học", "replace": 180000, "repair": 70000, "warranty": 3},
    "THERMAL_FUSE_160C": {"name": "Cầu chì nhiệt bảo vệ vách lò", "replace": 70000, "repair": 30000, "warranty": 1},
    "THERMISTOR": {"name": "Cảm biến nhiệt độ điện trở", "replace": 140000, "repair": 60000, "warranty": 3},
    "CERAMIC_HEATER": {"name": "Thanh nung nhiệt gốm đối lưu", "replace": 280000, "repair": 110000, "warranty": 6},
    "HEATING_ELEMENT_WIRE": {"name": "Dây mayso đốt nóng lò nướng", "replace": 160000, "repair": 60000, "warranty": 3},
    "SIGNAL_WIRE_3": {"name": "Dây truyền tín hiệu 3 lõi điều hòa", "replace": 120000, "repair": 50000, "warranty": 3},
    "HINGE_WIRE_HARNESS": {"name": "Cụm dây cáp đi qua bản lề", "replace": 180000, "repair": 80000, "warranty": 3},

    # 10. Bếp từ / Bếp hồng ngoại (Induction Stove)
    "IGBT_TRANSISTOR": {"name": "Sò công suất IGBT bếp từ", "replace": 300000, "repair": 120000, "warranty": 3},
    "CERAMIC_GLASS_TOP": {"name": "Mặt kính gốm Ceramic chịu nhiệt bếp từ", "replace": 500000, "repair": 200000, "warranty": 6},
    "COMPARATOR_LM339": {"name": "IC so sánh bảo vệ LM339", "replace": 150000, "repair": 70000, "warranty": 3},
    "CURRENT_TRANSFORMER": {"name": "Biến dòng cảm ứng dòng tải", "replace": 120000, "repair": 60000, "warranty": 3},
    "DISPLAY_BOARD": {"name": "Bo mạch hiển thị & phím điều khiển bếp từ", "replace": 350000, "repair": 150000, "warranty": 6},
    "FLEX_RIBBON_CABLE": {"name": "Cáp bẹ kết nối bo công suất và bo hiển thị", "replace": 100000, "repair": 50000, "warranty": 3},
    "INDUCTION_COIL": {"name": "Mâm cuộn dây đồng cảm ứng từ", "replace": 350000, "repair": 150000, "warranty": 6},
    "METAL_CHASSIS": {"name": "Khung vỏ kim loại đáy tản nhiệt", "replace": 200000, "repair": 80000, "warranty": 3},
    "NTC_TEMPERATURE_SENSOR": {"name": "Cảm biến nhiệt độ mâm từ NTC", "replace": 150000, "repair": 70000, "warranty": 3},
    "PAN_SENSOR_COIL": {"name": "Cuộn dây cảm biến nhận diện đáy nồi", "replace": 150000, "repair": 70000, "warranty": 3},
    "RESONANT_CAPACITOR": {"name": "Tụ cộng hưởng cao tần MKP", "replace": 120000, "repair": 60000, "warranty": 3},
    "SILICONE_GASKET": {"name": "Gioăng cao su làm kín chống nước mặt kính", "replace": 80000, "repair": 40000, "warranty": 1},
    "TOUCH_KEY_IC": {"name": "IC điều khiển cảm ứng điện dung", "replace": 180000, "repair": 80000, "warranty": 3},

    # 11. Ấm siêu tốc & Bình đun nước (Electric Kettle)
    "BIMETAL_THERMOSTAT": {"name": "Rơ-le nhiệt lưỡng kim ngắt đáy ấm", "replace": 100000, "repair": 50000, "warranty": 3},
    "HEATING_PLATE": {"name": "Mâm nhiệt đúc đáy ấm siêu tốc", "replace": 100000, "repair": 50000, "warranty": 6},
    "LID_LATCH": {"name": "Lẫy khóa nắp gài ấm", "replace": 60000, "repair": 30000, "warranty": 1},
    "LID_STEAM_PIPE": {"name": "Ống dẫn hơi nước ngắt tự động lên tay cầm", "replace": 60000, "repair": 30000, "warranty": 1},
    "MICA_INSULATION": {"name": "Tấm đệm cách điện chịu nhiệt mica", "replace": 50000, "repair": 25000, "warranty": 1},
    "OPEN_BUTTON_SPRING": {"name": "Lò xo nút bấm mở nắp cơ học", "replace": 40000, "repair": 20000, "warranty": 1},
    "PLASTIC_HINGE": {"name": "Bản lề nắp ấm nhựa chịu nhiệt", "replace": 50000, "repair": 25000, "warranty": 1},
    "POWER_CORD": {"name": "Dây nguồn 3 chấu chống cháy chịu tải", "replace": 80000, "repair": 40000, "warranty": 3},
    "ROTARY_BASE_CONNECTOR": {"name": "Cụm tiếp điểm xoay 360 độ chân đế ấm", "replace": 150000, "repair": 60000, "warranty": 3},
    "SILICONE_BASE_SEAL": {"name": "Vòng đệm silicone chống rò rỉ nước đáy ấm", "replace": 50000, "repair": 25000, "warranty": 1},
    "SPRING_CONTACTS": {"name": "Lưỡi gà tiếp điểm lò xo đàn hồi", "replace": 60000, "repair": 30000, "warranty": 1},
    "STAINLESS_STEEL_BODY": {"name": "Thân ấm inox 304 nguyên khối", "replace": 150000, "repair": 60000, "warranty": 6},
    "STEAM_SWITCH": {"name": "Công tắc hơi tự ngắt khi nước sôi", "replace": 100000, "repair": 50000, "warranty": 3},
    "WATER_LEVEL_WINDOW": {"name": "Cột báo mực nước trong suốt chịu nhiệt", "replace": 50000, "repair": 25000, "warranty": 1},

    # 12. Bàn là & Bàn ủi hơi nước (Electric Iron)
    "ANTI_DRIP_VALVE": {"name": "Van bi chống nhỏ giọt nước bàn ủi", "replace": 60000, "repair": 30000, "warranty": 1},
    "BALL_SWIVEL_CORD": {"name": "Khớp cầu xoay 360 độ chống xoắn dây nguồn", "replace": 80000, "repair": 40000, "warranty": 3},
    "CALC_CLEAN_NEEDLE": {"name": "Kim xả cặn vôi buồng hơi Calc-Clean", "replace": 50000, "repair": 25000, "warranty": 1},
    "CORD_BUSHING": {"name": "Đầu chụp cao su bảo vệ cổ dây nguồn", "replace": 40000, "repair": 20000, "warranty": 1},
    "HEAT_RESISTANT_CABLE": {"name": "Dây nguồn bọc sợi thủy tinh chống cháy bàn là", "replace": 100000, "repair": 50000, "warranty": 3},
    "SILVER_CONTACT_POINTS": {"name": "Tiếp điểm mạ bạc ngắt mở rơ-le nhiệt", "replace": 70000, "repair": 35000, "warranty": 1},
    "SOLEPLATE_HEATING_ELEMENT": {"name": "Mặt đế mâm nhiệt phủ men chống dính bàn là", "replace": 150000, "repair": 70000, "warranty": 6},
    "STEAM_BOILER_CHAMBER": {"name": "Buồng tạo hơi nước áp suất cao", "replace": 200000, "repair": 80000, "warranty": 6},
    "STEAM_PIPE_O_RING": {"name": "Vòng đệm O-ring làm kín đường ống hơi", "replace": 40000, "repair": 20000, "warranty": 1},
    "STEAM_PUMP_VALVE": {"name": "Van bơm phun hơi nước tăng cường", "replace": 80000, "repair": 40000, "warranty": 3},
    "TEMPERATURE_DIAL": {"name": "Núm xoay điều chỉnh nhiệt độ theo vải", "replace": 60000, "repair": 30000, "warranty": 1},
    "THERMAL_FUSE_240C": {"name": "Cầu chì nhiệt chống quá nhiệt 240 độ C", "replace": 60000, "repair": 30000, "warranty": 1},
    "WATER_TANK_GASKET": {"name": "Gioăng cao su làm kín nắp bình chứa nước", "replace": 50000, "repair": 25000, "warranty": 1},
    "WIRING_TERMINAL": {"name": "Cầu đấu dây gốm sứ chịu nhiệt cao", "replace": 50000, "repair": 25000, "warranty": 1},

    # 13. Điện thoại thông minh (Smartphone)
    "BATTERY_BMS_BOARD": {"name": "Mạch quản lý sạc xả pin điện thoại BMS", "replace": 250000, "repair": 100000, "warranty": 3},
    "BOTTOM_MICROPHONE": {"name": "Cụm micro đàm thoại phía dưới máy", "replace": 120000, "repair": 60000, "warranty": 3},
    "CHARGING_PINS": {"name": "Chân tiếp xúc sạc Type-C/Lightning", "replace": 150000, "repair": 70000, "warranty": 3},
    "CHARGING_PORT_SUB_BOARD": {"name": "Bo mạch phụ chân sạc điện thoại", "replace": 200000, "repair": 90000, "warranty": 3},
    "CPU_AP": {"name": "Chip vi xử lý ứng dụng CPU AP / Đóng chân", "replace": 1500000, "repair": 500000, "warranty": 3},
    "DISPLAY_FLEX_CABLE": {"name": "Cáp liên kết màn hình bo mạch chủ", "replace": 180000, "repair": 80000, "warranty": 3},
    "EARPIECE_SPEAKER": {"name": "Loa trong nghe cuộc gọi đàm thoại", "replace": 100000, "repair": 50000, "warranty": 3},
    "FLEX_CABLE": {"name": "Cáp dẹt liên bo mạch điện thoại", "replace": 150000, "repair": 70000, "warranty": 3},
    "FRONT_GLASS": {"name": "Mặt kính cường lực bảo vệ màn hình (Ép kính)", "replace": 350000, "repair": 150000, "warranty": 3},
    "LITHIUM_BATTERY_PACK": {"name": "Cụm pin điện thoại dung lượng chuẩn", "replace": 800000, "repair": 250000, "warranty": 6},
    "LOUD_SPEAKER_MODULE": {"name": "Cụm loa ngoài phát chuông / loa media", "replace": 150000, "repair": 70000, "warranty": 3},
    "MAINBOARD_PCB": {"name": "Bo mạch chủ điện thoại Mainboard PCB", "replace": 2200000, "repair": 650000, "warranty": 6},
    "NAND_FLASH_MEMORY": {"name": "Chip bộ nhớ lưu trữ NAND Flash", "replace": 650000, "repair": 250000, "warranty": 3},
    "PMIC_POWER_IC": {"name": "IC quản lý nguồn tổng PMIC điện thoại", "replace": 400000, "repair": 180000, "warranty": 3},
    "OLED_PANEL": {"name": "Màn hình nguyên bộ OLED / Super Retina", "replace": 2000000, "repair": 600000, "warranty": 6},
    "TOUCH_DIGITIZER": {"name": "Cảm ứng màn hình điện thoại Digitizer", "replace": 400000, "repair": 180000, "warranty": 3},

    # 14. Máy hút bụi & Robot hút bụi (Vacuum Cleaner)
    "BRUSHLESS_SUCTION_MOTOR": {"name": "Động cơ hút chân không không chổi than", "replace": 400000, "repair": 180000, "warranty": 6},
    "BUMPER_SWITCH": {"name": "Công tắc cảm biến va chạm cản trước robot", "replace": 90000, "repair": 40000, "warranty": 1},
    "CHARGING_PCB": {"name": "Bo mạch quản lý sạc dock robot hút bụi", "replace": 250000, "repair": 100000, "warranty": 3},
    "CLIFF_INFRARED_SENSORS": {"name": "Cụm cảm biến hồng ngoại chống rơi cầu thang", "replace": 200000, "repair": 90000, "warranty": 3},
    "CYCLONIC_CONE": {"name": "Côn xoáy lọc bụi công nghệ Cyclone", "replace": 150000, "repair": 60000, "warranty": 3},
    "DOCK_CHARGING_CONTACTS": {"name": "Bản cực tiếp xúc sạc chân đế dock sạc", "replace": 100000, "repair": 50000, "warranty": 3},
    "DRIVE_BELT": {"name": "Dây curoa truyền động chổi cuộn robot", "replace": 80000, "repair": 40000, "warranty": 1},
    "FAN_IMPELLER": {"name": "Cánh quạt ly tâm hút chân không nhôm đúc", "replace": 150000, "repair": 70000, "warranty": 3},
    "GEARBOX_BEARING": {"name": "Vòng bi hộp số giảm tốc bánh xe robot", "replace": 110000, "repair": 50000, "warranty": 3},
    "HEPA_FILTER_CARTRIDGE": {"name": "Màng lọc bụi mịn HEPA kháng khuẩn", "replace": 120000, "repair": 40000, "warranty": 1},
    "LIDAR_TURRET_MOTOR": {"name": "Cụm tháp quét Laser LiDAR định vị vẽ bản đồ", "replace": 1000000, "repair": 350000, "warranty": 6},
    "LI_ION_BATTERY_PACK": {"name": "Khối pin sạc Li-ion 14.4V-21.6V robot", "replace": 800000, "repair": 250000, "warranty": 6},
    "MAIN_ROLLER_BRUSH": {"name": "Chổi cuộn chính cao su silicone chống rối", "replace": 100000, "repair": 50000, "warranty": 1},
    "SEALING_GASKET": {"name": "Gioăng cao su làm kín khoang chứa bụi", "replace": 70000, "repair": 30000, "warranty": 1},

    # 15. Máy khoan & Máy bắn vít (Power Drill)
    "18650_CELLS": {"name": "Cell pin dòng xả cao 18650 máy công cụ", "replace": 300000, "repair": 120000, "warranty": 6},
    "ARMATURE_ROTOR": {"name": "Ruột Rotor mô tơ máy khoan cầm tay", "replace": 280000, "repair": 120000, "warranty": 6},
    "ARMATURE_SPINDLE": {"name": "Trục ren xoay gắn mũi khoan Spindle", "replace": 180000, "repair": 80000, "warranty": 3},
    "BALL_BEARING_608": {"name": "Vòng bi đỡ trục cốt motor 608zz cao tốc", "replace": 80000, "repair": 40000, "warranty": 3},
    "BATTERY_TERMINALS": {"name": "Giắc tiếp điểm chân cài pin máy khoan", "replace": 70000, "repair": 35000, "warranty": 1},
    "BMS_PROTECTION_BOARD": {"name": "Bo mạch bảo vệ sạc xả pin máy khoan BMS", "replace": 150000, "repair": 70000, "warranty": 3},
    "CARBON_BRUSH": {"name": "Cặp chổi than tự động ngắt máy khoan", "replace": 100000, "repair": 40000, "warranty": 3},
    "COMMUTATOR": {"name": "Cổ góp đồng tiếp xúc chổi than rotor", "replace": 150000, "repair": 60000, "warranty": 3},
    "FRONT_GEAR_HOUSING": {"name": "Vỏ nhôm đầu hộp số máy khoan búa", "replace": 180000, "repair": 80000, "warranty": 3},
    "HEAT_SINK_MOSFET": {"name": "Tản nhiệt nhôm làm mát Mosfet điều tốc", "replace": 120000, "repair": 50000, "warranty": 3},
    "KEYLESS_CHUCK": {"name": "Đầu kẹp mũi khoan tự khóa Keyless", "replace": 150000, "repair": 70000, "warranty": 6},
    "PLANETARY_GEARBOX": {"name": "Hộp số bánh răng hành tinh 2 cấp tốc độ", "replace": 200000, "repair": 90000, "warranty": 6},
    "REVERSE_LEVER": {"name": "Cần gạt đảo chiều quay trái phải", "replace": 60000, "repair": 30000, "warranty": 1},
    "STATOR_FIELD_COIL": {"name": "Cuộn dây bối Stator đồng từ trường máy khoan", "replace": 250000, "repair": 100000, "warranty": 6},
    "TORQUE_CLUTCH": {"name": "Cụm trượt chỉnh cấp độ lực siết mô-men", "replace": 150000, "repair": 70000, "warranty": 6},
    "TRIGGER_SPEED_SWITCH": {"name": "Công tắc cò bấm bóp điều tốc điện tử", "replace": 100000, "repair": 50000, "warranty": 3},

    # 16. Máy pha cà phê (Coffee Maker)
    "FLOWMETER_TURBINE": {"name": "Cảm biến lưu lượng cánh tuabin định lượng nước", "replace": 180000, "repair": 80000, "warranty": 3},
    "GROUPHEAD_RUBBER_GASKET": {"name": "Gioăng cao su làm kín họng pha Grouphead", "replace": 50000, "repair": 25000, "warranty": 1},
    "HALL_SENSOR_FLOW": {"name": "Cảm biến Hall đo tốc độ xung nước lưu lượng kế", "replace": 120000, "repair": 50000, "warranty": 3},
    "NTC_TEMPERATURE_PROBE": {"name": "Đầu dò nhiệt độ nước NTC nồi hơi", "replace": 120000, "repair": 50000, "warranty": 3},
    "PORTAFILTER_EARS": {"name": "Cánh gài tay cầm cà phê Portafilter hợp kim", "replace": 150000, "repair": 60000, "warranty": 3},
    "PRESSURE_OVERPRESSURE_VALVE": {"name": "Van xả quá áp an toàn OPV 15-19 bar", "replace": 180000, "repair": 80000, "warranty": 3},
    "PUMP_VALVE_SPRING": {"name": "Lò xo van một chiều bi sứ bơm áp suất", "replace": 60000, "repair": 30000, "warranty": 1},
    "SHOWER_SCREEN": {"name": "Lưới phân phối nước họng pha inox Shower Screen", "replace": 70000, "repair": 35000, "warranty": 1},
    "STEAM_VALVE_TAP": {"name": "Cụm núm vặn van cấp hơi nước Steam Valve", "replace": 200000, "repair": 90000, "warranty": 3},
    "STEAM_WAND_TIP": {"name": "Đầu tán hơi nước vòi đánh sữa inox", "replace": 80000, "repair": 40000, "warranty": 1},
    "TEFLON_HOSE": {"name": "Ống dẫn nước chịu áp lực và nhiệt độ Teflon", "replace": 90000, "repair": 40000, "warranty": 1},
    "THERMAL_CUTOFF_FUSE": {"name": "Cầu chì nhiệt chống quá nhiệt nồi đun", "replace": 70000, "repair": 35000, "warranty": 1},
    "THERMOBLOCK_HEATER": {"name": "Khối nhôm gia nhiệt nhanh Thermoblock", "replace": 500000, "repair": 200000, "warranty": 6},
    "VIBRATION_PUMP_ULKA": {"name": "Bơm rung điện từ ULKA Italia 15-19 bar", "replace": 1000000, "repair": 350000, "warranty": 6},

    # 17. Máy sấy tóc (Hair Dryer)
    "CONTACT_SPRINGS": {"name": "Lò xo lá đồng dẫn điện tiếp điểm", "replace": 40000, "repair": 20000, "warranty": 1},
    "DC_FAN_MOTOR": {"name": "Mô tơ quạt gió một chiều DC tốc độ cao", "replace": 200000, "repair": 80000, "warranty": 3},
    "FLEXIBLE_POWER_CORD": {"name": "Dây nguồn cao su mềm dẻo chịu nhiệt", "replace": 80000, "repair": 40000, "warranty": 3},
    "MICA_INSULATING_FRAME": {"name": "Khung mica định hình cuộn dây mayso", "replace": 70000, "repair": 30000, "warranty": 1},
    "NICHROME_HEATING_ELEMENT": {"name": "Dây lò xo mayso gia nhiệt Niken-Crom", "replace": 100000, "repair": 45000, "warranty": 3},
    "PLASTIC_IMPELLER": {"name": "Cánh quạt gió lồng sóc nhựa cân bằng động", "replace": 60000, "repair": 25000, "warranty": 1},
    "PLUG": {"name": "Phích cắm đúc liền chân tròn chịu tải", "replace": 40000, "repair": 20000, "warranty": 1},
    "POWER_CIRCUIT": {"name": "Mạch điện tử nắn dòng motor và ion âm", "replace": 120000, "repair": 50000, "warranty": 3},
    "ROCKER_SWITCH_HEAT": {"name": "Công tắc bập bênh chuyển mức sấy nóng/ấm", "replace": 80000, "repair": 40000, "warranty": 3},
    "RUBBER_CORD_PROTECTOR": {"name": "Đệm chụp đuôi dây chống gãy gập", "replace": 40000, "repair": 20000, "warranty": 1},
    "SLIDE_SWITCH_SPEED": {"name": "Công tắc gạt chọn tốc độ gió 2-3 nấc", "replace": 100000, "repair": 45000, "warranty": 3},
    "THERMAL_CUTOFF": {"name": "Rơ-le bảo vệ quá tải nhiệt buồng gió", "replace": 60000, "repair": 30000, "warranty": 1},
    "THERMAL_FUSE_125C": {"name": "Cầu chì nhiệt chống cháy nổ 125 độ C", "replace": 50000, "repair": 25000, "warranty": 1},

    # 18. Máy xay sinh tố (Blender)
    "AC_UNIVERSAL_MOTOR": {"name": "Động cơ vạn năng AC công suất lớn 300W-1000W", "replace": 500000, "repair": 180000, "warranty": 6},
    "BLADE_BEARING_BUSHING": {"name": "Ổ bạc đồng trục quay cụm dao xay", "replace": 90000, "repair": 40000, "warranty": 1},
    "BLADE_GEAR_TEETH": {"name": "Bánh răng khía truyền động trục dao", "replace": 80000, "repair": 35000, "warranty": 1},
    "CUP_LOCK_LATCH": {"name": "Lẫy ngàm gài đáy cối xay an toàn", "replace": 60000, "repair": 25000, "warranty": 1},
    "DIODE_RECTIFIER": {"name": "Đi-ốt nắn dòng điều khiển xung động cơ", "replace": 60000, "repair": 30000, "warranty": 1},
    "DRIVE_SPINDLE": {"name": "Trục truyền động chính động cơ cốt thép", "replace": 120000, "repair": 50000, "warranty": 3},
    "INTERLOCK_PUSH_ROD": {"name": "Ty đẩy khóa công tắc an toàn cối xay", "replace": 50000, "repair": 25000, "warranty": 1},
    "PUSH_BUTTON_ARRAY": {"name": "Hàng phím bấm cơ học chọn chế độ xay", "replace": 90000, "repair": 40000, "warranty": 1},
    "ROTARY_SPEED_SELECTOR": {"name": "Núm xoay vô cấp điều chỉnh tốc độ xay", "replace": 80000, "repair": 35000, "warranty": 1},
    "RUBBER_COUPLER_CLUTCH": {"name": "Bánh răng nấm cao su truyền động giảm giật", "replace": 100000, "repair": 40000, "warranty": 3},
    "SAFETY_MICROSWITCH": {"name": "Công tắc hành trình an toàn cối xay", "replace": 80000, "repair": 35000, "warranty": 1},
    "SILICONE_FLUID_SEAL": {"name": "Phớt chặn chất lỏng silicone chống rò nước", "replace": 50000, "repair": 25000, "warranty": 1},
    "STAINLESS_STEEL_BLADES": {"name": "Cụm lưỡi dao inox 4-6 cánh sắc bén", "replace": 150000, "repair": 60000, "warranty": 3},
    "STATOR_ARMATURE": {"name": "Cuộn dây đồng quấn bối Stator mô tơ", "replace": 280000, "repair": 110000, "warranty": 6},
    "THERMAL_OVERLOAD_FUSE": {"name": "Cầu chì nhiệt tự ngắt khi kẹt cối quá tải", "replace": 60000, "repair": 30000, "warranty": 1},

    # 19. Máy may gia đình (Sewing Machine)
    "BOBBIN_CASE": {"name": "Thoi suốt chỉ ổ chao máy may", "replace": 80000, "repair": 35000, "warranty": 1},
    "CHECK_SPRING": {"name": "Lò xo giữ giật chỉ đàn hồi", "replace": 30000, "repair": 15000, "warranty": 1},
    "DRIVE_MOTOR": {"name": "Động cơ mô tơ truyền động máy may", "replace": 350000, "repair": 140000, "warranty": 6},
    "FEED_DOG": {"name": "Cụm răng cưa đẩy vải bước đi kim", "replace": 60000, "repair": 25000, "warranty": 1},
    "FOOT_PEDAL_RHEOSTAT": {"name": "Bàn đạp ga điện tử điều chỉnh tốc độ may", "replace": 100000, "repair": 45000, "warranty": 3},
    "NEEDLE_BAR": {"name": "Trụ kim nâng hạ tịnh tiến máy may", "replace": 80000, "repair": 35000, "warranty": 1},
    "NEEDLE_CLAMP": {"name": "Ốc siết giữ chân kim may gia đình", "replace": 40000, "repair": 20000, "warranty": 1},
    "PRESSER_FOOT": {"name": "Chân vịt may cơ bản & đa năng kim loại", "replace": 50000, "repair": 25000, "warranty": 1},
    "ROTARY_HOOK": {"name": "Ổ chao xoay bắt chỉ thuyền thoi", "replace": 180000, "repair": 70000, "warranty": 3},
    "THREAD_TENSION_DISC": {"name": "Cụm đĩa đồng tiền điều chỉnh căng chỉ", "replace": 50000, "repair": 25000, "warranty": 1},

    # 20. Máy nướng bánh mì & Toaster
    "BIMETAL_STRIP": {"name": "Thanh lưỡng kim cảm biến nhiệt độ nướng", "replace": 50000, "repair": 25000, "warranty": 1},
    "CARRIAGE_LATCH": {"name": "Lẫy khóa ngàm giữ vỉ nướng hạ xuống", "replace": 40000, "repair": 20000, "warranty": 1},
    "CRUMB_TRAY": {"name": "Khay hứng vụn bánh mì rút rời inox", "replace": 40000, "repair": 20000, "warranty": 1},
    "FUSE": {"name": "Cầu chì nguồn chống quá tải quá nhiệt", "replace": 50000, "repair": 25000, "warranty": 1},
    "HEAT_RESISTANT_CORD": {"name": "Dây nguồn vỏ sợi bọc cách nhiệt", "replace": 60000, "repair": 30000, "warranty": 1},
    "HOLD_DOWN_ELECTROMAGNET": {"name": "Nam châm điện hút giữ cần gạt khi cấp nguồn", "replace": 50000, "repair": 25000, "warranty": 1},
    "INTERIOR_CHAMBER": {"name": "Buồng nướng bánh mì phản xạ nhiệt inox", "replace": 100000, "repair": 45000, "warranty": 3},
    "MICA_HEATING_ELEMENT": {"name": "Tấm vách mica quấn dây mayso tỏa nhiệt", "replace": 50000, "repair": 25000, "warranty": 1},
    "NICHROME_WIRE": {"name": "Sợi dây điện trở Niken-Crom đốt nóng", "replace": 40000, "repair": 20000, "warranty": 1},
    "TIMER_POTENTIOMETER": {"name": "Chiết áp xoay chỉnh độ giòn hẹn giờ nướng", "replace": 100000, "repair": 45000, "warranty": 3},

    # 21. Đèn bàn học (Desk Lamp)
    "18650_LITHIUM_BATTERY": {"name": "Pin sạc Lithium 18650 tích điện cho đèn bàn", "replace": 150000, "repair": 60000, "warranty": 3},
    "BASE_PIVOT_SCREW": {"name": "Ốc vít và khớp nối siết chỉnh góc chân đế", "replace": 40000, "repair": 20000, "warranty": 1},
    "CHARGING_MODULE": {"name": "Module sạc pin lithium tự ngắt bảo vệ pin", "replace": 90000, "repair": 40000, "warranty": 3},
    "CONSTANT_CURRENT_LED_DRIVER": {"name": "Bo mạch nguồn Driver LED dòng không đổi", "replace": 200000, "repair": 80000, "warranty": 3},
    "DIMMER_IC": {"name": "IC xử lý dimmer điều chỉnh độ sáng PWM", "replace": 80000, "repair": 35000, "warranty": 1},
    "FLEXIBLE_GOOSENECK": {"name": "Cổ ngỗng kim loại bọc silicon bẻ cong linh hoạt", "replace": 80000, "repair": 35000, "warranty": 1},
    "POWER_PCB": {"name": "Mạch nguồn chỉnh lưu và phân phối điện áp đèn bàn", "replace": 150000, "repair": 60000, "warranty": 3},
    "SMD_LED_CHIPS": {"name": "Dải chip LED SMD chống mỏi mắt quang phổ đều", "replace": 100000, "repair": 40000, "warranty": 1},
    "TOUCH_SENSOR_PAD": {"name": "Mắt cảm ứng chạm bật tắt và đổi màu ánh sáng", "replace": 100000, "repair": 40000, "warranty": 3},
    "USB_CHARGING_PORT": {"name": "Cổng sạc Type-C/Micro-USB đèn bàn", "replace": 70000, "repair": 35000, "warranty": 1},

    # 22. Máy tính bảng (Tablet)
    "DIGITIZER_GLASS": {"name": "Mặt kính cảm ứng đa điểm Tablet (Ép kính)", "replace": 450000, "repair": 180000, "warranty": 3},
    "LIGHTNING_PORT": {"name": "Cổng sạc chân cắm Lightning iPad", "replace": 120000, "repair": 50000, "warranty": 3},
    "PMIC_IC": {"name": "IC điều khiển quản lý nguồn tổng Tablet PMIC", "replace": 400000, "repair": 160000, "warranty": 3},
    "STEREO_SPEAKERS": {"name": "Cặp cụm loa âm thanh nổi 4 loa trên dưới Tablet", "replace": 200000, "repair": 80000, "warranty": 3},
    "TABLET_LIPO_BATTERY": {"name": "Cụm pin Li-Po dung lượng lớn 6000-10000mAh", "replace": 1200000, "repair": 350000, "warranty": 6},
    "TABLET_LOGIC_BOARD": {"name": "Bo mạch chủ Tablet Logic Board / Sửa chập nguồn", "replace": 1800000, "repair": 600000, "warranty": 6},
    "TYPE_C_CONNECTOR": {"name": "Cụm cáp sạc nhanh Type-C Tablet", "replace": 100000, "repair": 45000, "warranty": 3},
    "VOLUME_POWER_FLEX": {"name": "Dây cáp phím bấm nguồn và âm lượng", "replace": 120000, "repair": 50000, "warranty": 1},

    # 23. Tai nghe Bluetooth & Headphone
    "AUDIO_CABLE_35MM": {"name": "Dây cáp tín hiệu âm thanh bọc dù jack 3.5mm", "replace": 80000, "repair": 35000, "warranty": 1},
    "BLUETOOTH_SOC_CHIP": {"name": "Chip Bluetooth vi xử lý âm thanh SOC", "replace": 150000, "repair": 60000, "warranty": 3},
    "BUTTON_CELL_BATTERY": {"name": "Cặp pin cúc áo Lithium cho tai nghe TWS", "replace": 200000, "repair": 80000, "warranty": 3},
    "CASE_CHARGING_PCB": {"name": "Bo mạch điều khiển sạc hộp kén tai nghe", "replace": 200000, "repair": 80000, "warranty": 3},
    "CERAMIC_ANTENNA": {"name": "Ăng-ten gốm thu phát sóng Bluetooth không dây", "replace": 60000, "repair": 25000, "warranty": 1},
    "DYNAMIC_DRIVER_40MM": {"name": "Màng loa Dynamic Driver 40mm Hi-Res", "replace": 200000, "repair": 80000, "warranty": 3},
    "HEADBAND_PLASTIC": {"name": "Khung gọng choàng đầu Headphone đệm da", "replace": 100000, "repair": 45000, "warranty": 1},
    "MAGNETIC_CRADLE": {"name": "Nam châm hít giữ tai nghe trong dock sạc", "replace": 80000, "repair": 35000, "warranty": 1},
    "POGO_PIN_CONTACTS": {"name": "Chân kim tiếp xúc sạc Pogo Pin mạ vàng", "replace": 100000, "repair": 40000, "warranty": 1},
    "VOICE_COIL": {"name": "Cuộn cảm âm thanh siêu nhẹ Voice Coil", "replace": 120000, "repair": 50000, "warranty": 1},

    # 24. Loa Bluetooth & Dàn âm thanh
    "ANTENNA": {"name": "Cáp ăng-ten thu tín hiệu Bluetooth/FM xa 10m", "replace": 60000, "repair": 25000, "warranty": 1},
    "BATTERY_PACK_74V": {"name": "Khối pin sạc lithium 7.4V loa di động", "replace": 500000, "repair": 180000, "warranty": 6},
    "CHARGE_MANAGEMENT_IC": {"name": "IC quản lý sạc nhanh và cân bằng pack pin", "replace": 200000, "repair": 80000, "warranty": 3},
    "ROTARY_POTENTIOMETER": {"name": "Chiết áp núm xoay điều chỉnh Volume/Bass/Treble", "replace": 80000, "repair": 35000, "warranty": 1},
    "RUBBER_SURROUND_CONE": {"name": "Màng loa bass và gân cao su đàn hồi", "replace": 200000, "repair": 80000, "warranty": 3},
    "VOICE_COIL_MAGNET": {"name": "Côn loa và nam châm Neodymium từ lực mạnh", "replace": 180000, "repair": 70000, "warranty": 3},
    "VOLUME_KNOB": {"name": "Núm vặn kim loại phay xước điều khiển âm lượng", "replace": 40000, "repair": 20000, "warranty": 1},

    # 25. Máy tính để bàn (Desktop PC)
    "ATX_POWER_SUPPLY": {"name": "Bộ nguồn máy tính ATX 450W-750W 80Plus", "replace": 1000000, "repair": 350000, "warranty": 12},
    "CHIPSET_B660": {"name": "Chip cầu Nam PCH / Chipset bo mạch chủ Mainboard", "replace": 850000, "repair": 320000, "warranty": 6},
    "CPU_COOLER_FAN": {"name": "Tản nhiệt khí/nước CPU kèm quạt làm mát tháp", "replace": 250000, "repair": 90000, "warranty": 3},
    "DDR4_RAM_STICK": {"name": "Thanh bộ nhớ RAM máy tính DDR4/DDR5 8GB-16GB", "replace": 600000, "repair": 150000, "warranty": 12},
    "GRAPHICS_CARD_VGA": {"name": "Card màn hình rời VGA / Đóng chip GPU", "replace": 1000000, "repair": 400000, "warranty": 6},
    "MOTHERBOARD_VRM_MOSFET": {"name": "Dàn Mosfet cấp nguồn VRM CPU Mainboard", "replace": 400000, "repair": 180000, "warranty": 3},
    "PCIE_SLOT": {"name": "Khe cắm mở rộng PCIe x16 gia cố kim loại", "replace": 180000, "repair": 80000, "warranty": 3},
    "PRIMARY_CAPACITOR": {"name": "Tụ lọc nguồn sơ cấp cao áp 450V nguồn ATX", "replace": 150000, "repair": 60000, "warranty": 1},
    "THERMAL_COMPOUND": {"name": "Keo tản nhiệt hiệu năng cao MX4/Thermal Grizzly", "replace": 120000, "repair": 50000, "warranty": 1},

    # 26. Đồng hồ thông minh (Smartwatch)
    "AMOLED_DISPLAY": {"name": "Màn hình cong AMOLED/OLED hiển thị sắc nét", "replace": 1000000, "repair": 350000, "warranty": 6},
    "CURVED_COVER_GLASS": {"name": "Mặt kính cong Sapphire cảm ứng (Ép kính)", "replace": 400000, "repair": 160000, "warranty": 3},
    "DOCK_CABLE": {"name": "Cáp sạc hít từ tính không dây đế tròn nam châm", "replace": 100000, "repair": 40000, "warranty": 1},
    "MAGNETIC_POGO_PINS": {"name": "Chân đế tiếp xúc sạc hít nam châm chống nước", "replace": 150000, "repair": 60000, "warranty": 1},
    "MAIN_PCB": {"name": "Bo mạch chủ tích hợp siêu nhỏ Smartwatch", "replace": 800000, "repair": 300000, "warranty": 6},
    "MINI_LIPO_BATTERY": {"name": "Pin Lithium-Polymer 300-500mAh Smartwatch", "replace": 400000, "repair": 150000, "warranty": 6},
    "OPTICAL_HEART_RATE_SENSOR": {"name": "Cảm biến quang học đo nhịp tim & SpO2 đáy đồng hồ", "replace": 200000, "repair": 90000, "warranty": 3},
    "PHOTODIODE": {"name": "Cảm biến quang đi-ốt nhận tia phản hồi nhịp tim", "replace": 90000, "repair": 40000, "warranty": 1},
    "WATERPROOF_GASKET": {"name": "Vòng gioăng keo chống nước áp suất cao 5ATM IP68", "replace": 80000, "repair": 35000, "warranty": 1},

    # 27. Máy ảnh kỹ thuật số (Camera)
    "APERTURE_FLEX_CABLE": {"name": "Cáp dẹt điều khiển khẩu độ và chống rung ống kính", "replace": 250000, "repair": 100000, "warranty": 3},
    "CMOS_SENSOR_FILTER": {"name": "Kính lọc hồng ngoại bảo vệ cảm biến CMOS", "replace": 500000, "repair": 200000, "warranty": 6},
    "EJECT_MECHANISM": {"name": "Khóa cơ bấm mở nảy thẻ nhớ và nắp pin", "replace": 150000, "repair": 60000, "warranty": 1},
    "EVF_VIEWFINDER": {"name": "Kính ngắm điện tử OLED độ phân giải cao EVF", "replace": 800000, "repair": 300000, "warranty": 6},
    "LOW_PASS_GLASS": {"name": "Kính lọc quang thông thấp khử răng cưa cảm biến", "replace": 350000, "repair": 140000, "warranty": 3},
    "MECHANICAL_SHUTTER_BLADES": {"name": "Cụm rèm màn trập cơ học tốc độ cao máy ảnh", "replace": 1000000, "repair": 380000, "warranty": 6},
    "ROTATING_LCD_FLEX": {"name": "Cáp dẹt cổ xoay lật màn hình LCD máy ảnh", "replace": 300000, "repair": 120000, "warranty": 3},
    "SD_CARD_SLOT": {"name": "Khe cắm đọc thẻ nhớ SD/CFexpress tốc độ cao", "replace": 250000, "repair": 100000, "warranty": 3},
    "SHUTTER_MOTOR": {"name": "Động cơ mô tơ lên cò và kéo màn trập Shutter", "replace": 600000, "repair": 220000, "warranty": 3},
    "ULTRASONIC_AF_MOTOR": {"name": "Động cơ siêu âm lấy nét tự động ống kính USM", "replace": 600000, "repair": 220000, "warranty": 3},

    # 28. Máy chiếu (Projector)
    "3LCD_PRISM": {"name": "Lăng kính hội tụ hợp màu quang học cụm 3LCD", "replace": 1500000, "repair": 500000, "warranty": 6},
    "BALLAST_POWER_BOARD": {"name": "Bo mạch nguồn cao áp kích bóng đèn chiếu Ballast", "replace": 650000, "repair": 250000, "warranty": 6},
    "BLOWER_FAN_12V": {"name": "Quạt sò lồng sóc thổi mát buồng đèn 12V", "replace": 220000, "repair": 90000, "warranty": 3},
    "COLOR_WHEEL_DISC": {"name": "Bánh xe lọc màu quang học 6 phân vùng Color Wheel", "replace": 500000, "repair": 190000, "warranty": 3},
    "DMD_CHIP_065": {"name": "Chip xử lý hình ảnh vi gương kỹ thuật số DLP DMD", "replace": 2000000, "repair": 600000, "warranty": 6},
    "HIGH_PRESSURE_MERCURY_LAMP": {"name": "Bóng đèn chiếu thủy ngân siêu cao áp UHP/OSRAM", "replace": 700000, "repair": 250000, "warranty": 3},
    "INDEX_SENSOR": {"name": "Mắt cảm biến quang học đồng bộ bánh xe màu", "replace": 180000, "repair": 75000, "warranty": 1},
    "POLARIZING_FILTER_GLASS": {"name": "Kính phân cực và gương phản xạ quang học", "replace": 350000, "repair": 140000, "warranty": 3},
    "THERMAL_NTC_SENSOR": {"name": "Cảm biến nhiệt điện trở bảo vệ buồng đèn", "replace": 150000, "repair": 65000, "warranty": 1},
    "THERMAL_PAD_HEATSINK": {"name": "Miếng đệm tản nhiệt kim loại làm mát chip DMD", "replace": 80000, "repair": 35000, "warranty": 1}
}

# Gom tất cả component từ taxonomy để đảm bảo 100% không sót bất kỳ component nào
all_taxonomy_components = set()
dev_dict = taxonomy.get("devices", taxonomy)
for dev_id, d_info in dev_dict.items():
    if not isinstance(d_info, dict):
        continue
    for fault in d_info.get("faults", []):
        for c in fault.get("components", []):
            all_taxonomy_components.add(c)

print(f"Tổng số components thực tế trong taxonomy: {len(all_taxonomy_components)}")

for c_id, c_data in existing_bench.items():
    if c_id not in COMPONENT_KNOWLEDGE:
        COMPONENT_KNOWLEDGE[c_id] = {
            "name": c_data.get("name", c_id),
            "replace": float(c_data.get("replace", 650000)),
            "repair": float(c_data.get("repair", 250000)),
            "warranty": int(c_data.get("warranty", 6))
        }

for c_id in all_taxonomy_components:
    if c_id not in COMPONENT_KNOWLEDGE:
        clean_name = c_id.replace("_", " ").title()
        is_high = any(k in c_id for k in ["PANEL", "COMPRESSOR", "MAINBOARD", "MOTOR", "HEAD", "PRINTHEAD"])
        rep = 1200000 if is_high else 450000
        COMPONENT_KNOWLEDGE[c_id] = {
            "name": f"Linh kiện {clean_name}",
            "replace": rep,
            "repair": int(rep * 0.35),
            "warranty": 6
        }

print(f"Đã chuẩn hóa toàn diện {len(COMPONENT_KNOWLEDGE)} linh kiện vào Knowledge Base!")

BRAND_TIERS = {
    # Tier A: Premium
    "Apple": "A", "Sony": "A", "Panasonic": "A", "Daikin": "A", "Mitsubishi": "A", 
    "Dell": "A", "HP": "A", "Bosch": "A", "Hitachi": "A", "Dyson": "A", 
    "Canon": "A", "Nikon": "A", "Fujifilm": "A", "DeLonghi": "A", "Breville": "A", 
    "Brother": "A", "Garmin": "A",
    # Tier B: Standard / Mid-range
    "Samsung": "B", "LG": "B", "Toshiba": "B", "Electrolux": "B", "Asus": "B", 
    "Acer": "B", "Lenovo": "B", "Aqua": "B", "Sharp": "B", "Philips": "B",
    "Xiaomi": "B", "Oppo": "B", "Makita": "B", "Dewalt": "B", "Milwaukee": "B", 
    "JBL": "B", "Marshall": "B", "Gemilai": "B", "Singer": "B", "Juki": "B", 
    "BenQ": "B", "Epson": "B", "Kangaroo": "B", "Sunhouse": "B",
    # Tier C: Budget / Value
    "Midea": "C", "Funiki": "C", "Casper": "C", "Gree": "C", "Sanaky": "C", 
    "Senko": "C", "Asia": "C", "Generic": "C", "Khác": "C"
}

BRAND_MULTIPLIER = {"A": 1.25, "B": 1.0, "C": 0.85}
PART_TYPE_MULTIPLIER = {"Genuine": 1.15, "OEM": 1.0, "Aftermarket": 0.75}
CONDITION_MULTIPLIER = {"NEW": 1.0, "REFURBISHED": 0.75, "USED": 0.55}
REGION_LABOR_MULTIPLIER = {"Metro": 1.20, "Urban": 1.0, "Province": 0.85}

# -------------------------------------------------------------
# XÂY DỰNG 4 TỆP SSOT KNOWLEDGE BASE
# -------------------------------------------------------------
component_market_db = {}
labor_market_db = {}
warranty_policy = {}
pricing_statistics = {}

for comp_id, comp_info in COMPONENT_KNOWLEDGE.items():
    name = comp_info.get("name", comp_id)
    repair_price = float(comp_info.get("repair", 300000))
    replace_price = float(comp_info.get("replace", 850000))
    warranty_months = int(comp_info.get("warranty", 6))
    
    is_rare = any(k in comp_id for k in ["CHIP", "VRM", "MAGNETRON", "COMPRESSOR", "INVERTER", "OLED", "PRINTHEAD"])
    availability = "Rare" if is_rare else "Normal"
    
    component_market_db[comp_id] = {
        "component_id": comp_id,
        "component_name_vn": name,
        "baseline_replace_price": replace_price,
        "baseline_repair_price": repair_price,
        "availability": availability,
        "default_part_type": "OEM",
        "market_age_days": 180,
        "supported_brands": ["Apple", "Dell", "HP", "Asus", "Lenovo", "Samsung", "LG", "Sony", "Panasonic", "Daikin", "Toshiba", "Electrolux", "Aqua", "Midea", "Casper", "Xiaomi", "Bosch", "Makita", "JBL", "Canon", "DeLonghi", "Brother"]
    }
    
    warranty_policy[f"{comp_id}_replace"] = warranty_months
    warranty_policy[f"{comp_id}_repair"] = max(1, warranty_months // 2)

for dev_id, dev_data in dev_dict.items():
    if not isinstance(dev_data, dict):
        continue
    for fault in dev_data.get("faults", []):
        f_code = fault.get("fault_code", "")
        f_comps = fault.get("components", [])
        f_comp = f_comps[0] if f_comps else "GENERIC_MODULE"
        
        diff_obj = fault.get("difficulty") or {}
        raw_diff = fault.get("difficulty_score")
        if raw_diff is None and isinstance(diff_obj, dict):
            raw_diff = diff_obj.get("score")
        diff = float(raw_diff if raw_diff is not None else 2.0)
        
        mins = int(diff_obj.get("estimated_minutes", int(diff * 25))) if isinstance(diff_obj, dict) else int(diff * 25)
        tools = int(diff_obj.get("tools", 2)) if isinstance(diff_obj, dict) else 2
        req_pro = bool(diff_obj.get("requires_professional", diff >= 3.0)) if isinstance(diff_obj, dict) else (diff >= 3.0)
        
        disassembly_level = min(5, max(1, int(diff)))
        waterproof = 1 if dev_id in ["may_giat", "dieu_hoa", "may_bom", "may_loc_nuoc", "ban_ui", "dong_ho"] else 0
        
        base_labor = int(round((diff * 45000 + (mins / 60.0) * 80000) / 10000.0) * 10000)
        base_labor = max(80000, min(650000, base_labor))
        
        labor_market_db[f_code] = {
            "device_id": dev_id,
            "primary_component": f_comp,
            "difficulty_score": diff,
            "estimated_minutes": mins,
            "tools_count": tools,
            "requires_professional": req_pro,
            "disassembly_level": disassembly_level,
            "waterproof_level": waterproof,
            "base_labor_vnd": base_labor
        }

for comp_id, comp_info in component_market_db.items():
    base_price = comp_info["baseline_replace_price"]
    avail = comp_info["availability"]
    avail_mult = 1.20 if avail == "Rare" else 1.0
    
    for tier in ["A", "B", "C"]:
        t_mult = BRAND_MULTIPLIER[tier]
        for ptype in ["Genuine", "OEM", "Aftermarket"]:
            p_mult = PART_TYPE_MULTIPLIER[ptype]
            
            med = int(round(base_price * t_mult * p_mult * avail_mult / 10000.0) * 10000)
            p_min = int(round(med * 0.88 / 10000.0) * 10000)
            p_max = int(round(med * 1.15 / 10000.0) * 10000)
            std = int(round((p_max - p_min) / 4.0))
            iqr = int(round((p_max - p_min) * 0.5))
            
            src_count = random.randint(6, 18) if tier in ["A", "B"] else random.randint(4, 10)
            
            key = f"{comp_id}_{tier}_{ptype}"
            pricing_statistics[key] = {
                "min": p_min,
                "median": med,
                "max": p_max,
                "std": std,
                "iqr": iqr,
                "source_count": src_count
            }

with open(os.path.join(PRICING_DIR, "component_market_db.json"), "w", encoding="utf-8") as f:
    json.dump(component_market_db, f, ensure_ascii=False, indent=2)

with open(os.path.join(PRICING_DIR, "labor_market_db.json"), "w", encoding="utf-8") as f:
    json.dump(labor_market_db, f, ensure_ascii=False, indent=2)

with open(os.path.join(PRICING_DIR, "warranty_policy.json"), "w", encoding="utf-8") as f:
    json.dump(warranty_policy, f, ensure_ascii=False, indent=2)

with open(os.path.join(PRICING_DIR, "pricing_statistics.json"), "w", encoding="utf-8") as f:
    json.dump(pricing_statistics, f, ensure_ascii=False, indent=2)

print(f"✅ Đã tạo thành công 4 tệp SSOT trong {PRICING_DIR}:")
print(f"   • component_market_db.json: {len(component_market_db)} linh kiện (100% Taxonomy Coverage)")
print(f"   • labor_market_db.json: {len(labor_market_db)} mã lỗi")
print(f"   • warranty_policy.json: {len(warranty_policy)} chính sách")
print(f"   • pricing_statistics.json: {len(pricing_statistics)} mục thống kê thị trường")

# -------------------------------------------------------------
# SINH 2 TẬP DỮ LIỆU HUẤN LUYỆN ML
# -------------------------------------------------------------

# Tập 1: component_train_dataset.csv
comp_rows = []
for comp_id, comp_meta in component_market_db.items():
    base_rep = comp_meta["baseline_replace_price"]
    base_fix = comp_meta["baseline_repair_price"]
    avail = comp_meta["availability"]
    
    for brand, tier in BRAND_TIERS.items():
        t_mult = BRAND_MULTIPLIER[tier]
        for ptype in ["Genuine", "OEM", "Aftermarket"]:
            p_mult = PART_TYPE_MULTIPLIER[ptype]
            for cond in ["NEW", "REFURBISHED", "USED"]:
                c_mult = CONDITION_MULTIPLIER[cond]
                for action in ["replace", "repair"]:
                    base_val = base_rep if action == "replace" else base_fix
                    
                    noise = np.random.normal(0, 0.02)
                    avail_mult = 1.20 if avail == "Rare" else 1.0
                    actual_price = base_val * t_mult * p_mult * c_mult * avail_mult * (1.0 + noise)
                    actual_price = int(round(actual_price / 10000.0) * 10000)
                    
                    comp_rows.append({
                        "component_id": comp_id,
                        "brand": brand,
                        "brand_tier": tier,
                        "part_type": ptype,
                        "availability": avail,
                        "component_condition": cond,
                        "action_type": action,
                        "baseline_price_vnd": base_val,
                        "market_age_days": comp_meta["market_age_days"],
                        "target_component_price_vnd": actual_price
                    })

df_comp = pd.DataFrame(comp_rows)
comp_csv_path = os.path.join(PRICING_DIR, "component_train_dataset.csv")
df_comp.to_csv(comp_csv_path, index=False, encoding="utf-8")
print(f"✅ Đã sinh component_train_dataset.csv: {len(df_comp)} mẫu.")

# Tập 2: labor_train_dataset.csv
labor_rows = []
for f_code, l_meta in labor_market_db.items():
    dev_id = l_meta["device_id"]
    comp_id = l_meta["primary_component"]
    diff = l_meta["difficulty_score"]
    mins = l_meta["estimated_minutes"]
    tools = l_meta["tools_count"]
    req_pro = 1 if l_meta["requires_professional"] else 0
    dis_lvl = l_meta["disassembly_level"]
    waterproof = l_meta["waterproof_level"]
    base_labor = l_meta["base_labor_vnd"]
    
    for brand, tier in BRAND_TIERS.items():
        t_mult = 1.10 if tier == "A" else (0.95 if tier == "C" else 1.0)
        for reg in ["Metro", "Urban", "Province"]:
            r_mult = REGION_LABOR_MULTIPLIER[reg]
            for action in ["replace", "repair"]:
                action_mult = 0.85 if action == "repair" else 1.0
                
                noise = np.random.normal(0, 0.03)
                actual_labor = base_labor * t_mult * r_mult * action_mult * (1.0 + noise)
                actual_labor = int(round(actual_labor / 10000.0) * 10000)
                
                labor_rows.append({
                    "device_id": dev_id,
                    "region_class": reg,
                    "action_type": action,
                    "base_labor_vnd": base_labor,
                    "difficulty_score": diff,
                    "estimated_minutes": mins,
                    "tools_count": tools,
                    "requires_professional": req_pro,
                    "disassembly_level": dis_lvl,
                    "waterproof_level": waterproof,
                    "target_labor_price_vnd": actual_labor
                })

df_labor = pd.DataFrame(labor_rows)
labor_csv_path = os.path.join(PRICING_DIR, "labor_train_dataset.csv")
df_labor.to_csv(labor_csv_path, index=False, encoding="utf-8")
print(f"✅ Đã sinh labor_train_dataset.csv: {len(df_labor)} mẫu.")
print("🎉 TOÀN BỘ SSOT KNOWLEDGE BASE VÀ TRAINING DATASETS ĐÃ HOÀN TẤT 100%!")
