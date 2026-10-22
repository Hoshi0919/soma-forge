"""
SomaForge Models: Core data structures, enums, and physiological state definitions.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional

class SubstanceType(str, Enum):
    BIOMASS = "BIOMASS"          # 原始生质 (肉泥、藻类、粗脂肪)
    CHYME = "CHYME"              # 消化食糜 (高能乳化水解物)
    TOXIN = "TOXIN"              # 强酸毒素与代谢排泄物
    NEURO_FLUID = "NEURO_FLUID"  # 高纯神经胶质液
    NEURO_CRYSTAL = "NEURO_CRYSTAL" # 稳态结晶终产物

class OrganType(str, Enum):
    HEART = "HEART"              # 动力源心室
    MAW = "MAW"                  # 生质摄食口
    STOMACH = "STOMACH"          # 消化胃囊
    LYMPH = "LYMPH"              # 淋巴滤泡 (排毒与净化)
    GLAND = "GLAND"              # 神经腺体
    BRAIN_TANK = "BRAIN_TANK"    # 神质育卵囊 / 终点囊

class OrganHealth(str, Enum):
    HEALTHY = "HEALTHY"
    INFLAMED = "INFLAMED"        # 充血红肿
    TUMOROUS = "TUMOROUS"        # 恶性增生 / 癌变
    NECROTIC = "NECROTIC"        # 坏死枯萎

@dataclass
class FluidPacket:
    """血管中蠕动行进的微流体包"""
    substance: SubstanceType
    amount: float
    position: float = 0.0  # 归一化路径位置 [0.0, 1.0]
    id: str = ""

@dataclass
class VitalSigns:
    """有机体生命指征与系统稳态"""
    heart_rate_bpm: float = 72.0
    blood_pressure_systolic: float = 120.0
    blood_pressure_diastolic: float = 80.0
    toxicity_ratio: float = 0.0     # 0.0 ~ 1.0 全身毒素浓度
    is_septic: bool = False         # 败血休克状态
    is_fibrillating: bool = False   # 室颤
    is_alive: bool = True           # 生命存活
    total_crystals_harvested: float = 0.0
    awakening_progress: float = 0.0 # 0.0 ~ 1.0 觉醒收敛进度
