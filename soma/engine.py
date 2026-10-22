"""
SomaForge Simulation Engine: Physiological loops, cardiovascular rhythms, and organ metabolic orchestration.
"""
import math
from typing import Dict, List, Optional, Tuple
from soma.models import (
    OrganType, OrganHealth, SubstanceType, FluidPacket, VitalSigns
)
from soma.organ import Organ
from soma.vessel import VascularTube

class SimulationEngine:
    def __init__(self):
        self.organs: Dict[str, Organ] = {}
        self.tubes: Dict[str, VascularTube] = {}
        self.vitals = VitalSigns()
        
        # 心搏生物钟
        self.heart_phase = 0.0      # 0.0 ~ 1.0 (一个完整心搏周期的相位)
        self.base_bpm = 72.0
        self.current_bpm = 72.0
        self.heart_pulse_power = 0.3 # 瞬时心缩压能量
        
        # 计时与稳态
        self.elapsed_time = 0.0
        self.sepsis_duration = 0.0
        self.total_harvested = 0.0
        self.is_ascended = False

    def add_organ(self, organ_id: str, organ_type: OrganType, x: float = 0.0, y: float = 0.0) -> Organ:
        organ = Organ(organ_id, organ_type, x, y)
        self.organs[organ_id] = organ
        return organ

    def remove_organ(self, organ_id: str):
        if organ_id in self.organs:
            del self.organs[organ_id]
            dead_tubes = [tid for tid, tube in self.tubes.items() 
                          if tube.from_organ_id == organ_id or tube.to_organ_id == organ_id]
            for tid in dead_tubes:
                del self.tubes[tid]

    def connect_tube(self, tube_id: str, from_id: str, to_id: str) -> Optional[VascularTube]:
        if from_id not in self.organs or to_id not in self.organs:
            return None
        o1, o2 = self.organs[from_id], self.organs[to_id]
        dist = math.hypot(o2.x - o1.x, o2.y - o1.y)
        tube = VascularTube(tube_id, from_id, to_id, length=max(50.0, dist))
        self.tubes[tube_id] = tube
        return tube

    def remove_tube(self, tube_id: str):
        if tube_id in self.tubes:
            del self.tubes[tube_id]

    def excise_organ_pathology(self, organ_id: str) -> bool:
        if organ_id in self.organs:
            return self.organs[organ_id].excise_tumor()
        return False

    def defibrillate(self, energy_joules: float = 200.0) -> bool:
        """电击除颤：终止室颤与心搏骤停，重建窦性心律"""
        was_dead = not self.vitals.is_alive
        self.vitals.is_alive = True
        self.vitals.is_fibrillating = False
        self.sepsis_duration = max(0.0, self.sepsis_duration - 15.0)
        self.current_bpm = 70.0
        return was_dead

    def load_scenario(self, scenario_name: str):
        """加载不同情景模拟挑战"""
        self.organs.clear()
        self.tubes.clear()
        self.total_harvested = 0.0
        self.sepsis_duration = 0.0
        self.is_ascended = False
        self.vitals = VitalSigns()

        if scenario_name == "standard":
            self.base_bpm = 72.0
            self.current_bpm = 72.0
            maw = self.add_organ("maw", OrganType.MAW, 180, 240)
            stom = self.add_organ("stom", OrganType.STOMACH, 360, 240)
            lym = self.add_organ("lym", OrganType.LYMPH, 360, 420)
            gland = self.add_organ("gland", OrganType.GLAND, 560, 240)
            brain = self.add_organ("brain", OrganType.BRAIN_TANK, 760, 240)
            maw.buffers[SubstanceType.BIOMASS] = 10.0
            self.connect_tube("t1", "maw", "stom")
            self.connect_tube("t2", "stom", "gland")
            self.connect_tube("t3", "stom", "lym")
            self.connect_tube("t4", "gland", "brain")
        elif scenario_name == "crisis":
            self.base_bpm = 72.0
            self.current_bpm = 155.0
            maw = self.add_organ("maw", OrganType.MAW, 180, 240)
            stom = self.add_organ("stom", OrganType.STOMACH, 360, 240)
            lym = self.add_organ("lym", OrganType.LYMPH, 360, 420)
            gland = self.add_organ("gland", OrganType.GLAND, 560, 240)
            brain = self.add_organ("brain", OrganType.BRAIN_TANK, 760, 240)
            maw.buffers[SubstanceType.BIOMASS] = 30.0
            stom.buffers[SubstanceType.BIOMASS] = 15.0
            stom.buffers[SubstanceType.CHYME] = 10.0
            stom.buffers[SubstanceType.TOXIN] = 25.0
            stom.health = OrganHealth.INFLAMED
            stom.tumor_progress = 0.70
            lym.buffers[SubstanceType.TOXIN] = 35.0
            gland.buffers[SubstanceType.TOXIN] = 15.0
            gland.health = OrganHealth.INFLAMED
            self.connect_tube("t1", "maw", "stom")
            self.connect_tube("t2", "stom", "gland")
            self.connect_tube("t3", "stom", "lym")
            self.connect_tube("t4", "gland", "brain")
            self.sepsis_duration = 20.0
            self.vitals.is_septic = True
        elif scenario_name == "sandbox":
            self.base_bpm = 72.0
            self.current_bpm = 72.0

    def inject_adrenaline(self, dose: float = 1.0):
        """肾上腺素急救：逆转室颤、强心升压、加速血流代谢"""
        if not self.vitals.is_alive:
            self.vitals.is_alive = True
        self.vitals.is_fibrillating = False
        self.current_bpm = min(160.0, self.current_bpm + 30.0 * dose)
        self.vitals.blood_pressure_systolic += 30.0 * dose

    def inject_antitoxin(self, dose: float = 1.0):
        """广谱抗毒血清：净化全身 75% 游离毒素"""
        decay = max(0.0, 1.0 - 0.75 * dose)
        for organ in self.organs.values():
            organ.buffers[SubstanceType.TOXIN] *= decay
        for tube in self.tubes.values():
            for p in tube.packets:
                if p.substance == SubstanceType.TOXIN:
                    p.amount *= decay

    def harvest_crystals(self) -> float:
        """从所有脑囊收获已成熟的神经晶质"""
        total = 0.0
        for organ in self.organs.values():
            if organ.organ_type == OrganType.BRAIN_TANK:
                amt = organ.buffers[SubstanceType.NEURO_CRYSTAL]
                if amt > 0.1:
                    total += amt
                    organ.buffers[SubstanceType.NEURO_CRYSTAL] = 0.0
        self.total_harvested += total
        self.vitals.total_crystals_harvested = self.total_harvested
        return total

    def update_cardiovascular_rhythm(self, dt: float):
        """心血管泵动：收缩波形与心律失常动力学"""
        if not self.vitals.is_alive:
            self.heart_pulse_power = 0.0
            self.vitals.heart_rate_bpm = 0.0
            self.vitals.blood_pressure_systolic = 0.0
            self.vitals.blood_pressure_diastolic = 0.0
            return

        freq = self.current_bpm / 60.0
        self.heart_phase = (self.heart_phase + freq * dt) % 1.0

        # 高斯型心室收缩脉冲波 (QRS complex wave)
        pulse = math.exp(-18.0 * ((self.heart_phase - 0.15) ** 2))
        self.heart_pulse_power = 0.25 + 0.95 * pulse

        self.vitals.blood_pressure_systolic = 100.0 + 35.0 * self.heart_pulse_power
        self.vitals.blood_pressure_diastolic = 70.0 + 15.0 * self.heart_pulse_power
        self.vitals.heart_rate_bpm = self.current_bpm

    def evaluate_homeostasis_and_sepsis(self, dt: float):
        """评估全身毒素负荷、败血休克与升华觉醒"""
        total_toxin = 0.0
        total_fluid = 0.0

        for organ in self.organs.values():
            total_toxin += organ.buffers[SubstanceType.TOXIN]
            total_fluid += organ.current_load

        for tube in self.tubes.values():
            for p in tube.packets:
                total_fluid += p.amount
                if p.substance == SubstanceType.TOXIN:
                    total_toxin += p.amount

        # 基底血浆容积恒为 40.0 单位，确保毒素浓度定义符合生理学
        plasma_base = 40.0
        toxicity = total_toxin / (total_fluid + plasma_base)
        self.vitals.toxicity_ratio = min(1.0, toxicity)

        # 毒素反馈调节心率
        if toxicity > 0.50:
            # 重度毒血症 -> 频发室速或室颤
            self.vitals.is_septic = True
            self.current_bpm = min(190.0, self.current_bpm + 8.0 * dt)
            self.sepsis_duration += dt
            if self.sepsis_duration > 25.0:
                self.vitals.is_fibrillating = True
            if self.sepsis_duration > 40.0:
                self.vitals.is_alive = False
        elif toxicity > 0.25:
            # 轻度充血代偿
            self.vitals.is_septic = False
            self.sepsis_duration = max(0.0, self.sepsis_duration - 0.5 * dt)
            target_bpm = self.base_bpm + (toxicity - 0.25) * 120.0
            self.current_bpm += (target_bpm - self.current_bpm) * 0.1 * dt
        else:
            # 稳态健康
            self.vitals.is_septic = False
            self.vitals.is_fibrillating = False
            self.sepsis_duration = max(0.0, self.sepsis_duration - dt)
            self.current_bpm += (self.base_bpm - self.current_bpm) * 0.2 * dt

        # 终极目标：升华觉醒评估
        self.harvest_crystals()
        self.vitals.awakening_progress = min(1.0, self.total_harvested / 100.0)
        if self.total_harvested >= 100.0 and self.vitals.toxicity_ratio < 0.15:
            self.is_ascended = True

    def step(self, dt: float):
        """全局模拟单步推演"""
        self.elapsed_time += dt
        self.update_cardiovascular_rhythm(dt)

        if not self.vitals.is_alive:
            return

        # 1. 各器官生化代谢推演
        organ_emissions: Dict[str, List[FluidPacket]] = {}
        for oid, organ in self.organs.items():
            packets = organ.tick_metabolism(dt, self.heart_pulse_power)
            if packets:
                organ_emissions[oid] = packets

        # 2. 将代谢排出的流体包分发给相连的导管
        for from_id, packets in organ_emissions.items():
            out_tubes = [t for t in self.tubes.values() if t.from_organ_id == from_id]
            if not out_tubes:
                for p in packets:
                    self.organs[from_id].buffers[p.substance] += p.amount
                continue

            for packet in packets:
                chosen_tube = None
                if packet.substance == SubstanceType.TOXIN:
                    for t in out_tubes:
                        target = self.organs.get(t.to_organ_id)
                        if target and target.organ_type == OrganType.LYMPH:
                            chosen_tube = t
                            break

                if not chosen_tube:
                    out_tubes.sort(key=lambda t: len(t.packets))
                    chosen_tube = out_tubes[0]

                injected = chosen_tube.inject_packet(packet)
                if not injected:
                    self.organs[from_id].buffers[packet.substance] += packet.amount

        # 3. 血管蠕动推进流体
        for tube in self.tubes.values():
            arrived = tube.tick_flow(dt, self.heart_pulse_power)
            target_organ = self.organs.get(tube.to_organ_id)
            if not target_organ:
                continue

            for packet in arrived:
                accepted = target_organ.receive_packet(packet)
                remainder = packet.amount - accepted
                if remainder > 1e-4:
                    rejected_packet = FluidPacket(substance=packet.substance, amount=remainder)
                    tube.reject_backflow(rejected_packet)

        # 4. 评估系统整体生命稳态
        self.evaluate_homeostasis_and_sepsis(dt)
