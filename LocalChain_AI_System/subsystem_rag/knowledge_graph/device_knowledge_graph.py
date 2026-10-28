"""
LOCALCHAIN AI V5.2 - DEVICE KNOWLEDGE GRAPH MANAGER
Bộ quản lý 5-Layer Device Knowledge Graph bao phủ 11 nhóm thiết bị.
Cung cấp API truy vấn topo, tìm Assembly cha, tìm cụm linh kiện liên đới (Cluster expansion),
tra cứu điện áp, tín hiệu, rủi ro và các thao tác kỹ thuật hợp lệ.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Set, Any
from .graph_schema import DeviceTopology, SubsystemNode, AssemblyNode, ComponentNode, OperationNode, SkillLevel, RiskLevel
from .capability_matrix import validate_operation_against_component_type

# Dữ liệu chuẩn hóa 5-Layer Knowledge Graph cho toàn bộ 11 thiết bị
TOPOLOGY_KNOWLEDGE_SSOT: Dict[str, Dict[str, Any]] = {
    "laptop": {
        "name_vn": "Máy tính xách tay (Laptop)",
        "subsystems": {
            "DISPLAY_SUBSYSTEM": {
                "name_vn": "Phân hệ Hiển thị Màn hình",
                "assemblies": {
                    "DISPLAY_PANEL_ASSEMBLY": {
                        "name_vn": "Cụm Tấm Nền & Khung Viền Màn Hình",
                        "components": {
                            "LCD_PANEL": {
                                "name_vn": "Tấm nền màn hình LCD/OLED",
                                "voltage_rails": ["19V_VBL (Đèn nền)", "3.3V_LCDVDD (Logic)", "0V_GND"],
                                "signal_lines": ["eDP_LANE0..3", "AUX_CH", "HPD (Hot Plug Detect)"],
                                "required_tools": ["PLASTIC_SPUDGER", "TORX_T5", "PH00"],
                                "allowed_operations": ["REMOVE_BEZEL", "REMOVE_SCREWS", "SWAP_COMPONENT", "TEST_RGB_FULLSCREEN"],
                                "risks": ["ESD_SENSITIVE", "GLASS_HAZARD"],
                                "skill_required": "BASIC_TECH"
                            },
                            "EDP_CABLE": {
                                "name_vn": "Cáp truyền tín hiệu hình ảnh eDP/LVDS",
                                "voltage_rails": ["19V_VBL", "3.3V_LCDVDD"],
                                "signal_lines": ["30-pin / 40-pin eDP Data Bus", "Camera USB", "Mic Signal"],
                                "required_tools": ["TWEEZERS", "DIGITAL_MULTIMETER"],
                                "allowed_operations": ["MEASURE_CONTINUITY", "MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["SHORT_CIRCUIT_IF_BATTERY_CONNECTED"],
                                "skill_required": "BASIC_TECH"
                            },
                            "BACKLIGHT_LED": {
                                "name_vn": "Dải đèn LED nền siêu sáng",
                                "voltage_rails": ["19V - 45V DC"],
                                "signal_lines": ["BL_ENABLE", "BL_PWM_DIMMING"],
                                "required_tools": ["LED_TESTER", "MULTIMETER"],
                                "allowed_operations": ["MEASURE_VOLTAGE", "SWAP_COMPONENT"],
                                "risks": ["HIGH_DC_VOLTAGE"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    },
                    "HINGE_ASSEMBLY": {
                        "name_vn": "Cụm Bản Lề Cơ Khí Màn Hình",
                        "components": {
                            "METAL_HINGE": {
                                "name_vn": "Bản lề kim loại chịu lực trái/phải",
                                "voltage_rails": [],
                                "signal_lines": [],
                                "required_tools": ["PH0", "SCREW_THREADLOCKER", "MINI_WRENCH"],
                                "allowed_operations": ["REMOVE_SCREWS", "SWAP_COMPONENT", "CALIBRATE_SENSOR"],
                                "risks": ["CHASSIS_CRACK_RISK"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            },
            "POWER_SUBSYSTEM": {
                "name_vn": "Phân hệ Nguồn & Năng Lượng",
                "assemblies": {
                    "BATTERY_ASSEMBLY": {
                        "name_vn": "Cụm Pin Lithium-Ion Nội Bộ",
                        "components": {
                            "BATTERY_CELL": {
                                "name_vn": "Khối Pin Lithium Li-ion/Li-Po",
                                "voltage_rails": ["11.4V - 15.4V DC Nominal"],
                                "signal_lines": ["SMBUS_SDA", "SMBUS_SCL", "BAT_TEMP_NTC"],
                                "required_tools": ["PLASTIC_SPUDGER", "TORX_T5"],
                                "allowed_operations": ["DISCONNECT_POWER", "MEASURE_VOLTAGE", "SWAP_COMPONENT"],
                                "risks": ["FIRE_HAZARD_IF_PUNCTURED", "CHEMICAL_BURN"],
                                "skill_required": "BASIC_TECH"
                            },
                            "BATTERY": {
                                "name_vn": "Bộ Pin sạc máy tính",
                                "voltage_rails": ["11.4V - 15.4V DC"],
                                "signal_lines": ["SMBUS_DATA", "SMBUS_CLK"],
                                "required_tools": ["PLASTIC_SPUDGER", "TORX_T5"],
                                "allowed_operations": ["DISCONNECT_POWER", "SWAP_COMPONENT"],
                                "risks": ["FIRE_HAZARD_IF_PUNCTURED"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    },
                    "CHARGING_ASSEMBLY": {
                        "name_vn": "Cụm Jack Cắm Sạc & Quản Lý Nguồn",
                        "components": {
                            "DC_JACK": {
                                "name_vn": "Cổng cắm sạc DC-IN / Cổng Type-C PD",
                                "voltage_rails": ["19.5V - 20.0V DC Main Rail"],
                                "signal_lines": ["ADAPTER_ID / CC_PINS"],
                                "required_tools": ["MULTIMETER", "SOLDERING_IRON"],
                                "allowed_operations": ["MEASURE_VOLTAGE", "MEASURE_CONTINUITY", "SWAP_COMPONENT"],
                                "risks": ["SHORT_TO_GROUND"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "tu_lanh": {
        "name_vn": "Tủ lạnh & Tủ đông (Refrigerator)",
        "subsystems": {
            "DEFROST_SUBSYSTEM": {
                "name_vn": "Phân hệ Xả Đá Tự Động (Defrost System)",
                "assemblies": {
                    "EVAPORATOR_DEFROST_ASSEMBLY": {
                        "name_vn": "Cụm Xả Băng & Dàn Lạnh Ngăn Đông",
                        "components": {
                            "DEFROST_HEATER": {
                                "name_vn": "Thanh sấy / Điện trở nhiệt xả băng (200-350Ω)",
                                "voltage_rails": ["220V AC Mains (Khi kích xả đá)"],
                                "signal_lines": ["DEFROST_TRIGGER_LINE"],
                                "required_tools": ["DIGITAL_MULTIMETER", "INSULATED_SCREWDRIVER", "HEAT_SHRINK_TUBING"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "MEASURE_CONTINUITY", "SWAP_COMPONENT"],
                                "risks": ["220V_AC_MAINS_HAZARD", "GLASS_TUBE_FRAGILE"],
                                "skill_required": "BASIC_TECH"
                            },
                            "DEFROST_BIMETAL": {
                                "name_vn": "Sò lạnh âm nhiệt độ (Đóng tiếp điểm < 0°C)",
                                "voltage_rails": ["220V AC Series Loop"],
                                "signal_lines": [],
                                "required_tools": ["DIGITAL_MULTIMETER", "FREEZE_SPRAY_TESTER"],
                                "allowed_operations": ["MEASURE_CONTINUITY", "SWAP_COMPONENT"],
                                "risks": ["MOISTURE_INGRESS_LEAK"],
                                "skill_required": "BASIC_TECH"
                            },
                            "THERMAL_FUSE": {
                                "name_vn": "Cầu chì nhiệt bảo vệ chống cháy (73°C - 77°C)",
                                "voltage_rails": ["220V AC Series Protection"],
                                "signal_lines": [],
                                "required_tools": ["DIGITAL_MULTIMETER", "WATERPROOF_CONNECTORS"],
                                "allowed_operations": ["MEASURE_CONTINUITY", "SWAP_COMPONENT"],
                                "risks": ["OVERHEAT_FIRE_HAZARD_IF_BYPASSED"],
                                "skill_required": "BASIC_TECH"
                            },
                            "DEFROST_SENSOR": {
                                "name_vn": "Cảm biến nhiệt độ rã đông (Sensor NTC 5kΩ - 10kΩ)",
                                "voltage_rails": ["5V DC Logic Reference"],
                                "signal_lines": ["TEMP_ANALOG_IN"],
                                "required_tools": ["DIGITAL_MULTIMETER"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["ESD_SENSITIVE"],
                                "skill_required": "BASIC_TECH"
                            },
                            "TIMER": {
                                "name_vn": "Đồng hồ định thời xả đá (Defrost Timer 6-8 tiếng)",
                                "voltage_rails": ["220V AC Motor Coil (Chân 1-3)"],
                                "signal_lines": ["CONTACT_2_COMPRESSOR", "CONTACT_4_HEATER"],
                                "required_tools": ["FLATHEAD_SCREWDRIVER", "MULTIMETER"],
                                "allowed_operations": ["MANUAL_TIMER_ROTATION", "MEASURE_CONTINUITY", "SWAP_COMPONENT"],
                                "risks": ["220V_AC_MAINS_HAZARD"],
                                "skill_required": "BASIC_TECH"
                            },
                            "EVAPORATOR_FAN": {
                                "name_vn": "Quạt gió đối lưu dàn lạnh (12V DC / 220V AC)",
                                "voltage_rails": ["12V DC / 220V AC"],
                                "signal_lines": ["PWM_SPEED", "FG_FEEDBACK"],
                                "required_tools": ["PH2_SCREWDRIVER", "MULTIMETER"],
                                "allowed_operations": ["MEASURE_VOLTAGE", "CLEAN_ICE_JAM", "SWAP_COMPONENT"],
                                "risks": ["ROTATING_BLADE_HAZARD"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            },
            "COOLING_CYCLE_SUBSYSTEM": {
                "name_vn": "Phân hệ Chu Trình Làm Lạnh & Máy Nén",
                "assemblies": {
                    "COMPRESSOR_BLOCK_ASSEMBLY": {
                        "name_vn": "Cụm Máy Nén & Rơ Le Khởi Động Phía Sau",
                        "components": {
                            "COMPRESSOR": {
                                "name_vn": "Máy nén làm lạnh (Block Lốc Tủ Lạnh)",
                                "voltage_rails": ["220V AC / 3-Phase Inverter U-V-W"],
                                "signal_lines": ["INVERTER_DRIVE_PWM"],
                                "required_tools": ["MANIFOLD_GAUGE", "CLAMP_METER", "WELDING_TORCH"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "CHECK_GROUND_INSULATION", "SWAP_COMPONENT"],
                                "risks": ["R600A_ISOBUTANE_EXPLOSION_HAZARD", "HIGH_PRESSURE"],
                                "skill_required": "LICENSED_HVAC_TECH"
                            },
                            "START_RELAY": {
                                "name_vn": "Rơ-le khởi động máy nén (PTC Relay 15-30Ω)",
                                "voltage_rails": ["220V AC"],
                                "signal_lines": [],
                                "required_tools": ["MULTIMETER"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["220V_AC_MAINS_HAZARD"],
                                "skill_required": "BASIC_TECH"
                            },
                            "OVERLOAD_PROTECTOR": {
                                "name_vn": "Rơ-le bảo vệ quá tải nhiệt (Klixon Overload)",
                                "voltage_rails": ["220V AC Series Protection"],
                                "signal_lines": [],
                                "required_tools": ["MULTIMETER"],
                                "allowed_operations": ["MEASURE_CONTINUITY", "SWAP_COMPONENT"],
                                "risks": ["220V_AC_MAINS_HAZARD"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "tivi": {
        "name_vn": "Tivi & Màn hình hiển thị (Smart TV)",
        "subsystems": {
            "DISPLAY_SUBSYSTEM": {
                "name_vn": "Phân hệ Hiển Thị & Bo Mạch T-Con",
                "assemblies": {
                    "PANEL_TCON_ASSEMBLY": {
                        "name_vn": "Cụm Màn Hình & Bo Xử Lý Hình Ảnh T-Con",
                        "components": {
                            "TCON_BOARD": {
                                "name_vn": "Bo mạch xử lý quét hình T-Con (VGH, VGL, VDD)",
                                "voltage_rails": ["VDD +3.3V", "VGH +28V DC", "VGL -6V DC", "VCOM +7V DC"],
                                "signal_lines": ["LVDS / mini-LVDS Bus", "V-by-One Data"],
                                "required_tools": ["DIGITAL_MULTIMETER", "MAGNIFIER_MICROSCOPE", "INSULATED_TWEEZERS"],
                                "allowed_operations": ["MEASURE_VOLTAGE", "MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["STATIC_ELECTRICITY_ESD"],
                                "skill_required": "BASIC_TECH"
                            },
                            "LED_BACKLIGHT_STRIPS": {
                                "name_vn": "Thanh đèn LED nền chiếu sáng (Backlight Strips)",
                                "voltage_rails": ["60V - 180V DC Driver Output"],
                                "signal_lines": ["LED_DRIVE_PWM"],
                                "required_tools": ["LED_TESTER_INSTRUMENT", "SUCTION_CUPS", "PH0_SCREWDRIVER"],
                                "allowed_operations": ["TEST_LED_VOLTAGE", "SWAP_COMPONENT", "REPLACE_LED_STRIPS"],
                                "risks": ["PANEL_GLASS_CRACK_RISK", "HIGH_DC_VOLTAGE"],
                                "skill_required": "BASIC_TECH"
                            },
                            "LCD_PANEL": {
                                "name_vn": "Tấm kính tinh thể lỏng màn hình TV",
                                "voltage_rails": ["VGH", "VGL", "VDD"],
                                "signal_lines": ["SOURCE_COF", "GATE_COF"],
                                "required_tools": ["SCREEN_SUCTION_CUPS"],
                                "allowed_operations": ["SWAP_COMPONENT"],
                                "risks": ["GLASS_CRACK_FRAGILE"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            },
            "POWER_SUPPLY_SUBSYSTEM": {
                "name_vn": "Phân hệ Nguồn TV (Power Supply Board)",
                "assemblies": {
                    "PSU_ASSEMBLY": {
                        "name_vn": "Cụm Bo Nguồn Cao Áp & Hạ Áp",
                        "components": {
                            "POWER_SUPPLY_BOARD": {
                                "name_vn": "Bo mạch nguồn chính TV (PSU)",
                                "voltage_rails": ["220V AC Input", "PFC 390V DC", "12V DC Main", "24V Inverter"],
                                "signal_lines": ["PS_ON / POWER_ENABLE", "BL_ON"],
                                "required_tools": ["MULTIMETER", "SOLDERING_STATION"],
                                "allowed_operations": ["MEASURE_VOLTAGE", "CHECK_CAPACITOR_ESR", "SWAP_COMPONENT"],
                                "risks": ["HIGH_VOLTAGE_390V_CAPACITOR"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "dieu_hoa": {
        "name_vn": "Điều hòa không khí (Air Conditioner)",
        "subsystems": {
            "REFRIGERATION_SUBSYSTEM": {
                "name_vn": "Phân hệ Môi chất Lạnh & Áp suất",
                "assemblies": {
                    "OUTDOOR_CONDENSER_ASSEMBLY": {
                        "name_vn": "Cụm Dàn Nóng & Máy Nén Inverter",
                        "components": {
                            "INVERTER_COMPRESSOR": {
                                "name_vn": "Máy nén biến tần (Block Inverter)",
                                "voltage_rails": ["3-Phase U-V-W 50V-280V AC Variable"],
                                "signal_lines": ["IPM_DRIVE_PWM"],
                                "required_tools": ["MANIFOLD_GAUGE", "CLAMP_METER", "VACUUM_PUMP"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "VACUUM_EVACUATION", "GAS_CHARGING", "PRESSURE_SEAL_TEST", "SWAP_COMPONENT"],
                                "risks": ["R32_FLAMMABLE_GAS", "HIGH_PRESSURE_450PSI"],
                                "skill_required": "LICENSED_HVAC_TECH"
                            },
                            "COMPRESSOR": {
                                "name_vn": "Máy nén làm lạnh (Block máy lạnh)",
                                "voltage_rails": ["220V AC / Inverter U-V-W"],
                                "signal_lines": [],
                                "required_tools": ["MANIFOLD_GAUGE", "CLAMP_METER"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["HIGH_PRESSURE_GAS"],
                                "skill_required": "LICENSED_HVAC_TECH"
                            },
                            "OUTDOOR_FAN_MOTOR": {
                                "name_vn": "Motor quạt tản nhiệt dàn nóng",
                                "voltage_rails": ["310V DC / 220V AC"],
                                "signal_lines": ["HALL_SPEED_FEEDBACK"],
                                "required_tools": ["WRENCH_13MM", "MULTIMETER"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["HIGH_VOLTAGE_DC"],
                                "skill_required": "BASIC_TECH"
                            },
                            "START_CAPACITOR": {
                                "name_vn": "Tụ ngậm khởi động máy nén/quạt (25-50μF/450V)",
                                "voltage_rails": ["450V AC Rated"],
                                "signal_lines": [],
                                "required_tools": ["CAPACITANCE_METER", "INSULATED_PLIERS"],
                                "allowed_operations": ["MEASURE_CAPACITANCE", "SWAP_COMPONENT"],
                                "risks": ["STORED_ELECTRIC_CHARGE"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            },
            "ELECTRONICS_SUBSYSTEM": {
                "name_vn": "Phân hệ Bo Mạch Điều Khiển",
                "assemblies": {
                    "INDOOR_CONTROL_ASSEMBLY": {
                        "name_vn": "Cụm Bo Mạch Dàn Lạnh",
                        "components": {
                            "INDOOR_PCB": {
                                "name_vn": "Bo mạch chính dàn lạnh",
                                "voltage_rails": ["220V AC Input", "12V DC Relay", "5V DC Logic"],
                                "signal_lines": ["DATA_BUS_LINE_3", "IR_REMOTE_RECEIVER"],
                                "required_tools": ["MULTIMETER", "INSULATED_SCREWDRIVER"],
                                "allowed_operations": ["MEASURE_VOLTAGE", "MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["220V_AC_MAINS_HAZARD"],
                                "skill_required": "BASIC_TECH"
                            },
                            "ROOM_SENSOR": {
                                "name_vn": "Cảm biến nhiệt độ phòng & ống đồng (5k-15kΩ)",
                                "voltage_rails": ["5V DC Reference"],
                                "signal_lines": ["ANALOG_TEMP_SIGNAL"],
                                "required_tools": ["MULTIMETER"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": [],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "may_giat": {
        "name_vn": "Máy giặt (Washing Machine)",
        "subsystems": {
            "DRAIN_INTAKE_SUBSYSTEM": {
                "name_vn": "Phân hệ Cấp & Thoát Nước",
                "assemblies": {
                    "DRAIN_PUMP_ASSEMBLY": {
                        "name_vn": "Cụm Bơm Thoát Nước & Hộp Bẫy Rác",
                        "components": {
                            "DRAIN_PUMP": {
                                "name_vn": "Motor bơm thoát nước thải (150-180Ω)",
                                "voltage_rails": ["220V AC Mains"],
                                "signal_lines": ["TRIAC_GATE_TRIGGER"],
                                "required_tools": ["PLIERS", "MULTIMETER", "WATER_CATCH_TRAY"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "CLEAN_ISOPROPYL", "SWAP_COMPONENT", "PRESSURE_SEAL_TEST"],
                                "risks": ["WATER_LEAKAGE", "220V_MAINS"],
                                "skill_required": "BASIC_TECH"
                            },
                            "INLET_VALVE": {
                                "name_vn": "Van điện từ cấp nước đầu vào (4.0-4.8kΩ)",
                                "voltage_rails": ["220V AC"],
                                "signal_lines": [],
                                "required_tools": ["WRENCH", "MULTIMETER"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["WATER_FLOOD_RISK"],
                                "skill_required": "BASIC_TECH"
                            },
                            "PRESSURE_SENSOR": {
                                "name_vn": "Phao cảm biến áp lực nước (Tần số 21kHz - 27kHz)",
                                "voltage_rails": ["5V DC"],
                                "signal_lines": ["FREQUENCY_OUT"],
                                "required_tools": ["MULTIMETER", "FREQUENCY_COUNTER"],
                                "allowed_operations": ["CHECK_AIR_TUBE_SEAL", "SWAP_COMPONENT"],
                                "risks": ["AIR_LEAK_INCORRECT_LEVEL"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            },
            "MOTOR_DRIVE_SUBSYSTEM": {
                "name_vn": "Phân hệ Động Cơ & Khóa Cửa",
                "assemblies": {
                    "DIRECT_DRIVE_ASSEMBLY": {
                        "name_vn": "Cụm Động Cơ Dẫn Động & Khóa Cửa",
                        "components": {
                            "HALL_SENSOR_RPS": {
                                "name_vn": "Cảm biến vị trí mâm từ (RPS Sensor)",
                                "voltage_rails": ["12V DC Supply", "5V DC Signal"],
                                "signal_lines": ["HALL_A", "HALL_B"],
                                "required_tools": ["SOCKET_WRENCH_17MM", "MULTIMETER"],
                                "allowed_operations": ["MEASURE_VOLTAGE", "SWAP_COMPONENT"],
                                "risks": ["STRONG_MAGNET_PINCH_HAZARD"],
                                "skill_required": "BASIC_TECH"
                            },
                            "DOOR_LOCK": {
                                "name_vn": "Công tắc khóa chốt cửa an toàn (PTC Lock)",
                                "voltage_rails": ["220V AC"],
                                "signal_lines": ["DOOR_CLOSED_SENSE"],
                                "required_tools": ["PH2_SCREWDRIVER", "MULTIMETER"],
                                "allowed_operations": ["MEASURE_CONTINUITY", "SWAP_COMPONENT"],
                                "risks": ["DOOR_JAM_TRAPPED_CLOTHES"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "lo_vi_song": {
        "name_vn": "Lò vi sóng (Microwave Oven)",
        "subsystems": {
            "HIGH_VOLTAGE_SUBSYSTEM": {
                "name_vn": "Phân hệ Phát Sóng Vi Ba Cao Áp",
                "assemblies": {
                    "MAGNETRON_HV_ASSEMBLY": {
                        "name_vn": "Cụm Đèn Vi Sóng & Biến Áp Cao Áp",
                        "components": {
                            "MAGNETRON": {
                                "name_vn": "Đèn phát sóng vi ba Magnetron (Tim đèn < 1Ω)",
                                "voltage_rails": ["4000V DC High Voltage", "3.3V AC Filament"],
                                "signal_lines": [],
                                "required_tools": ["HV_DISCHARGE_PROBE", "INSULATED_SCREWDRIVER", "MULTIMETER"],
                                "allowed_operations": ["MEASURE_CONTINUITY", "MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["FATAL_HIGH_VOLTAGE_2100V_4000V", "BERYLLIUM_CERAMIC_TOXIC"],
                                "skill_required": "ADVANCED_SMD_TECH"
                            },
                            "HIGH_VOLTAGE_CAPACITOR": {
                                "name_vn": "Tụ điện cao thế tích điện (1.0μF/2100V tích hợp trở xả 10MΩ)",
                                "voltage_rails": ["2100V AC / 4000V DC"],
                                "signal_lines": [],
                                "required_tools": ["HV_DISCHARGE_RESISTOR_TOOL"],
                                "allowed_operations": ["MEASURE_CAPACITANCE", "SWAP_COMPONENT"],
                                "risks": ["FATAL_STORED_CHARGE_AFTER_UNPLUG"],
                                "skill_required": "ADVANCED_SMD_TECH"
                            },
                            "HV_DIODE": {
                                "name_vn": "Đi-ốt chỉnh lưu cao áp (Chịu áp 12kV)",
                                "voltage_rails": ["12kV Blocking Voltage"],
                                "signal_lines": [],
                                "required_tools": ["9V_BATTERY_TEST_RIG", "MULTIMETER"],
                                "allowed_operations": ["CHECK_DIODE_FORWARD_DROP", "SWAP_COMPONENT"],
                                "risks": ["HIGH_VOLTAGE"],
                                "skill_required": "ADVANCED_SMD_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "noi_com_dien": {
        "name_vn": "Nồi cơm điện & Nồi áp suất (Rice Cooker)",
        "subsystems": {
            "HEATING_CONTROL_SUBSYSTEM": {
                "name_vn": "Phân hệ Mâm Nhiệt & Cảm Biến Đáy",
                "assemblies": {
                    "HEATER_SENSOR_ASSEMBLY": {
                        "name_vn": "Cụm Mâm Nhiệt / Cuộn Từ IH & Rơ-le Cảm Biến",
                        "components": {
                            "HEATING_ELEMENT": {
                                "name_vn": "Mâm nhiệt đun nấu / Mâm điện trở chính (40-60Ω)",
                                "voltage_rails": ["220V AC Mains"],
                                "signal_lines": [],
                                "required_tools": ["DIGITAL_MULTIMETER", "PH2_SCREWDRIVER"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "MEASURE_INSULATION", "SWAP_COMPONENT"],
                                "risks": ["THERMAL_BURN_HAZARD", "220V_AC_MAINS"],
                                "skill_required": "BASIC_TECH"
                            },
                            "THERMAL_FUSE": {
                                "name_vn": "Cầu chì nhiệt bảo vệ đáy nồi (160°C - 192°C)",
                                "voltage_rails": ["220V AC Series"],
                                "signal_lines": [],
                                "required_tools": ["DIGITAL_MULTIMETER", "FIBERGLASS_SLEEVING"],
                                "allowed_operations": ["MEASURE_CONTINUITY", "SWAP_COMPONENT"],
                                "risks": ["OVERHEAT_MELT_HAZARD"],
                                "skill_required": "BASIC_TECH"
                            },
                            "CENTER_THERMOSTAT": {
                                "name_vn": "Rơ-le từ trung tâm cảm ứng ngắt cơm chín",
                                "voltage_rails": [],
                                "signal_lines": [],
                                "required_tools": ["PLIERS", "FLATHEAD_SCREWDRIVER"],
                                "allowed_operations": ["CLEAN_CONTACTS", "ADJUST_SPRING_TENSION", "SWAP_COMPONENT"],
                                "risks": ["MECHANICAL_JAM"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "may_in": {
        "name_vn": "Máy in & Máy photocopy (Laser/Inkjet Printer)",
        "subsystems": {
            "FUSER_MECHANISM_SUBSYSTEM": {
                "name_vn": "Phân hệ Sấy Nóng & Kéo Giấy",
                "assemblies": {
                    "FUSER_UNIT_ASSEMBLY": {
                        "name_vn": "Cụm Sấy Nhiệt (Fuser Assembly)",
                        "components": {
                            "FUSER_FILM_SLEEVE": {
                                "name_vn": "Bao lụa sấy ống kim loại bọc teflon chịu nhiệt",
                                "voltage_rails": [],
                                "signal_lines": [],
                                "required_tools": ["HIGH_TEMP_GREASE", "TWEEZERS", "PH1_SCREWDRIVER"],
                                "allowed_operations": ["APPLY_THERMAL_GREASE", "SWAP_COMPONENT"],
                                "risks": ["BURNS_HOT_FUSER_200C", "TEAR_FRAGILE_FILM"],
                                "skill_required": "BASIC_TECH"
                            },
                            "HEATING_CERAMIC_ELEMENT": {
                                "name_vn": "Thanh nhiệt gốm nung nóng sấy mực (50-100Ω)",
                                "voltage_rails": ["220V AC Pulse Controlled"],
                                "signal_lines": ["THERMISTOR_FEEDBACK"],
                                "required_tools": ["MULTIMETER"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["CERAMIC_CRACK_HAZARD", "220V_AC"],
                                "skill_required": "BASIC_TECH"
                            },
                            "PICKUP_ROLLER": {
                                "name_vn": "Quả đào / Cao su kéo cuốn giấy khay nạp",
                                "voltage_rails": [],
                                "signal_lines": [],
                                "required_tools": ["RUBBER_CLEANER_SOLUTION", "SPUDGER"],
                                "allowed_operations": ["CLEAN_RUBBER", "SWAP_COMPONENT"],
                                "risks": [],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "may_bom_nuoc": {
        "name_vn": "Máy bơm nước gia đình & tăng áp (Water Pump)",
        "subsystems": {
            "PUMP_MOTOR_SUBSYSTEM": {
                "name_vn": "Phân hệ Động Cơ & Buồng Cánh Bơm",
                "assemblies": {
                    "HYDRAULIC_HEAD_ASSEMBLY": {
                        "name_vn": "Cụm Đầu Bơm & Phớt Chắn Nước",
                        "components": {
                            "MECHANICAL_SEAL": {
                                "name_vn": "Phớt cơ khí chặn nước kín trục (Mechanical Seal)",
                                "voltage_rails": [],
                                "signal_lines": [],
                                "required_tools": ["BEARING_PULLER", "WRENCH_14MM", "SILICONE_GREASE"],
                                "allowed_operations": ["CLEAN_SEAL_FACE", "SWAP_COMPONENT", "PRESSURE_SEAL_TEST"],
                                "risks": ["WATER_FLOOD_LEAKAGE"],
                                "skill_required": "BASIC_TECH"
                            },
                            "START_CAPACITOR": {
                                "name_vn": "Tụ đề khởi động motor (10-30μF/450V)",
                                "voltage_rails": ["450V AC Rated"],
                                "signal_lines": [],
                                "required_tools": ["CAPACITANCE_METER", "INSULATED_SCREWDRIVER"],
                                "allowed_operations": ["MEASURE_CAPACITANCE", "SWAP_COMPONENT"],
                                "risks": ["STORED_CHARGE_HAZARD"],
                                "skill_required": "BASIC_TECH"
                            },
                            "PRESSURE_SWITCH": {
                                "name_vn": "Rơ-le đóng ngắt áp lực tự động (1.2 - 2.2 kg/cm²)",
                                "voltage_rails": ["220V AC"],
                                "signal_lines": [],
                                "required_tools": ["FLATHEAD_SCREWDRIVER", "MULTIMETER"],
                                "allowed_operations": ["ADJUST_PRESSURE_SPRING", "CLEAN_PLATINUM_CONTACTS", "SWAP_COMPONENT"],
                                "risks": ["220V_AC_MAINS"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "quat_dien": {
        "name_vn": "Quạt điện & Quạt hơi nước (Electric Fan)",
        "subsystems": {
            "FAN_MOTOR_SUBSYSTEM": {
                "name_vn": "Phân hệ Động Cơ Bạc Đạn & Tuốc Năng",
                "assemblies": {
                    "STATOR_ROTOR_ASSEMBLY": {
                        "name_vn": "Cụm Cuộn Dây Stator & Trục Bạc Đồng",
                        "components": {
                            "BEARING_BUSHING": {
                                "name_vn": "Cặp bạc thau dầu / Bạc đạn ổ bi (Trục 8mm)",
                                "voltage_rails": [],
                                "signal_lines": [],
                                "required_tools": ["MOTOR_OIL_LUBRICANT", "SANDPAPER_1000", "PH2_SCREWDRIVER"],
                                "allowed_operations": ["CLEAN_AXLE_RUST", "OIL_SOAK_FELT_PAD", "SWAP_COMPONENT"],
                                "risks": ["ROTOR_LOCK_OVERHEAT_FIRE"],
                                "skill_required": "BASIC_TECH"
                            },
                            "FAN_CAPACITOR": {
                                "name_vn": "Tụ điện quạt khởi động (1.5μF - 2.5μF / 400V AC)",
                                "voltage_rails": ["400V AC"],
                                "signal_lines": [],
                                "required_tools": ["CAPACITANCE_METER", "SOLDERING_IRON"],
                                "allowed_operations": ["MEASURE_CAPACITANCE", "SWAP_COMPONENT"],
                                "risks": ["220V_AC"],
                                "skill_required": "BASIC_TECH"
                            },
                            "THERMAL_FUSE": {
                                "name_vn": "Cầu chì nhiệt kẹp cuộn stator (130°C/2A)",
                                "voltage_rails": ["220V AC Series"],
                                "signal_lines": [],
                                "required_tools": ["MULTIMETER", "INSULATION_TAPE"],
                                "allowed_operations": ["MEASURE_CONTINUITY", "SWAP_COMPONENT"],
                                "risks": ["STATOR_COIL_FRAGILE_BREAK"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    },
    "may_loc_nuoc": {
        "name_vn": "Máy lọc nước RO & Nano (Water Purifier)",
        "subsystems": {
            "RO_HYDRAULIC_SUBSYSTEM": {
                "name_vn": "Phân hệ Thủy Lực & Màng Lọc RO",
                "assemblies": {
                    "MEMBRANE_PUMP_ASSEMBLY": {
                        "name_vn": "Cụm Bơm Tăng Áp 24V & Vỏ Màng RO",
                        "components": {
                            "RO_MEMBRANE": {
                                "name_vn": "Màng thẩm thấu ngược RO (Kích thước khe lọc 0.0001 micromet)",
                                "voltage_rails": [],
                                "signal_lines": [],
                                "required_tools": ["MEMBRANE_HOUSING_WRENCH", "TDS_METER"],
                                "allowed_operations": ["MEASURE_TDS_WATER", "SWAP_COMPONENT", "FLUSH_MEMBRANE"],
                                "risks": ["WATER_LEAKAGE_PRESSURE_100PSI"],
                                "skill_required": "BASIC_TECH"
                            },
                            "BOOSTER_PUMP_24V": {
                                "name_vn": "Bơm tăng áp trợ lực màng RO (24V DC / Head 125 PSI)",
                                "voltage_rails": ["24V DC Adapter Output"],
                                "signal_lines": [],
                                "required_tools": ["MULTIMETER", "PRESSURE_GAUGE"],
                                "allowed_operations": ["MEASURE_VOLTAGE", "MEASURE_HEAD_PRESSURE", "SWAP_COMPONENT"],
                                "risks": ["DIAPHRAGM_TEAR_LEAK"],
                                "skill_required": "BASIC_TECH"
                            },
                            "SOLENOID_VALVE": {
                                "name_vn": "Van điện từ đóng mở ngắt nước tự động (24V DC)",
                                "voltage_rails": ["24V DC"],
                                "signal_lines": [],
                                "required_tools": ["MULTIMETER"],
                                "allowed_operations": ["MEASURE_IMPEDANCE", "SWAP_COMPONENT"],
                                "risks": ["CONSTANT_WASTE_WATER_LEAK"],
                                "skill_required": "BASIC_TECH"
                            }
                        }
                    }
                }
            }
        }
    }
}

class DeviceKnowledgeGraph:
    def __init__(self):
        self.topologies: Dict[str, DeviceTopology] = {}
        self._load_topologies()
        
    def _load_topologies(self):
        for dev_id, data in TOPOLOGY_KNOWLEDGE_SSOT.items():
            top = DeviceTopology(device_id=dev_id, device_name_vn=data["name_vn"])
            
            for sub_id, sub_data in data.get("subsystems", {}).items():
                sub_node = SubsystemNode(subsystem_id=sub_id, name_vn=sub_data["name_vn"], device_id=dev_id)
                
                for asm_id, asm_data in sub_data.get("assemblies", {}).items():
                    asm_node = AssemblyNode(assembly_id=asm_id, name_vn=asm_data["name_vn"], subsystem_id=sub_id)
                    sub_node.assemblies.append(asm_id)
                    
                    for comp_id, comp_data in asm_data.get("components", {}).items():
                        comp_node = ComponentNode(
                            component_id=comp_id,
                            name_vn=comp_data["name_vn"],
                            assembly_id=asm_id,
                            voltage_rails=comp_data.get("voltage_rails", []),
                            signal_lines=comp_data.get("signal_lines", []),
                            required_tools=comp_data.get("required_tools", []),
                            allowed_operations=comp_data.get("allowed_operations", []),
                            risks=comp_data.get("risks", []),
                            skill_required=SkillLevel(comp_data.get("skill_required", "BASIC_TECH"))
                        )
                        asm_node.components.append(comp_id)
                        top.components[comp_id] = comp_node
                        
                    top.assemblies[asm_id] = asm_node
                top.subsystems[sub_id] = sub_node
            self.topologies[dev_id] = top

    def get_topology(self, device_id: str) -> Optional[DeviceTopology]:
        return self.topologies.get(device_id)

    def find_parent_assembly(self, device_id: str, component_id: str) -> Optional[AssemblyNode]:
        top = self.get_topology(device_id)
        if not top:
            return None
        comp = top.components.get(component_id)
        if comp and comp.assembly_id in top.assemblies:
            return top.assemblies[comp.assembly_id]
        return None

    def expand_component_cluster(self, device_id: str, primary_component: str) -> List[str]:
        """Mở rộng cụm linh kiện liên đới trong cùng Assembly và Subsystem"""
        top = self.get_topology(device_id)
        if not top:
            return [primary_component]
            
        cluster = [primary_component]
        parent_asm = self.find_parent_assembly(device_id, primary_component)
        if parent_asm:
            for sibling in parent_asm.components:
                if sibling not in cluster:
                    cluster.append(sibling)
        return cluster

# Singleton instance
device_kg = DeviceKnowledgeGraph()
