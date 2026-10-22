"""
SomaForge Organs: Metabolic nodes, bioprocessing kinetics, and pathological transformations.
"""
from typing import Dict, List, Optional
from soma.models import OrganType, OrganHealth, SubstanceType, FluidPacket

class Organ:
    def __init__(self, organ_id: str, organ_type: OrganType, x: float = 0.0, y: float = 0.0):
        self.id = organ_id
        self.organ_type = organ_type
        self.x = x
        self.y = y
        self.health = OrganHealth.HEALTHY
        
        # 默认容量与生化缓冲池
        self.capacity = 50.0
        self.buffers: Dict[SubstanceType, float] = {
            SubstanceType.BIOMASS: 0.0,
            SubstanceType.CHYME: 0.0,
            SubstanceType.TOXIN: 0.0,
            SubstanceType.NEURO_FLUID: 0.0,
            SubstanceType.NEURO_CRYSTAL: 0.0
        }
        
        # 病理与增生状态
        self.congestion_ticks = 0
        self.tumor_progress = 0.0  # 0.0 ~ 1.0
        self.necrosis_level = 0.0
        
        # 统计指标
        self.total_processed = 0.0
        self.efficiency = 1.0

    @property
    def current_load(self) -> float:
        return sum(self.buffers.values())

    @property
    def load_ratio(self) -> float:
        return min(1.0, self.current_load / max(1.0, self.capacity))

    @property
    def toxin_ratio(self) -> float:
        total = self.current_load
        if total <= 1e-4:
            return 0.0
        return self.buffers[SubstanceType.TOXIN] / total

    def receive_packet(self, packet: FluidPacket) -> float:
        """接收微流体包，返回实际接收量（溢出部分回阻）"""
        available_space = self.capacity - self.current_load
        accepted = min(packet.amount, max(0.0, available_space))
        self.buffers[packet.substance] += accepted
        return accepted

    def tick_metabolism(self, dt: float, pulse_power: float) -> List[FluidPacket]:
        """单步生理代谢计算，受心跳脉冲调制"""
        outgoing: List[FluidPacket] = []
        
        # 检查肿瘤病变
        if self.health == OrganHealth.TUMOROUS:
            # 恶性肿瘤不进行正常代谢，反而持续向周围渗出毒素并消耗能量
            self.buffers[SubstanceType.TOXIN] += 1.5 * dt
            # 随机渗漏毒性流体包
            if self.buffers[SubstanceType.TOXIN] >= 2.0:
                leak = min(self.buffers[SubstanceType.TOXIN], 2.0)
                self.buffers[SubstanceType.TOXIN] -= leak
                outgoing.append(FluidPacket(substance=SubstanceType.TOXIN, amount=leak))
            return outgoing

        # 更新病理倾向 (淤积与高毒素导致癌变)
        if self.load_ratio > 0.85 or self.toxin_ratio > 0.35:
            self.congestion_ticks += 1
            if self.congestion_ticks > 15:
                self.tumor_progress += 0.08 * dt
                if self.tumor_progress >= 1.0:
                    self.health = OrganHealth.TUMOROUS
                    self.efficiency = 0.0
                    return outgoing
                else:
                    self.health = OrganHealth.INFLAMED
        else:
            self.congestion_ticks = max(0, self.congestion_ticks - 1)
            self.tumor_progress = max(0.0, self.tumor_progress - 0.02 * dt)
            if self.tumor_progress == 0.0 and self.health == OrganHealth.INFLAMED:
                self.health = OrganHealth.HEALTHY

        # 各器官特异性生化代谢
        rate_modifier = max(0.3, pulse_power) * self.efficiency

        if self.organ_type == OrganType.MAW:
            # 摄食口：自主蠕动摄入外界生质
            raw_intake = 4.0 * rate_modifier * dt
            self.buffers[SubstanceType.BIOMASS] += raw_intake
            emit_amount = min(self.buffers[SubstanceType.BIOMASS], 3.0 * rate_modifier * dt)
            if emit_amount > 0.1:
                self.buffers[SubstanceType.BIOMASS] -= emit_amount
                outgoing.append(FluidPacket(substance=SubstanceType.BIOMASS, amount=emit_amount))
                self.total_processed += emit_amount

        elif self.organ_type == OrganType.STOMACH:
            # 胃囊：水解生质 -> 食糜 (70%) + 毒素/胃酸 (30%)
            bio = self.buffers[SubstanceType.BIOMASS]
            react_amount = min(bio, 5.0 * rate_modifier * dt)
            if react_amount > 0.05:
                self.buffers[SubstanceType.BIOMASS] -= react_amount
                chyme_out = react_amount * 0.70
                toxin_out = react_amount * 0.30
                self.buffers[SubstanceType.CHYME] += chyme_out
                self.buffers[SubstanceType.TOXIN] += toxin_out
                self.total_processed += react_amount

            # 优先向外排空食糜与毒素
            if self.buffers[SubstanceType.CHYME] > 0.2:
                amt = min(self.buffers[SubstanceType.CHYME], 4.0 * rate_modifier * dt)
                self.buffers[SubstanceType.CHYME] -= amt
                outgoing.append(FluidPacket(substance=SubstanceType.CHYME, amount=amt))
                
            if self.buffers[SubstanceType.TOXIN] > 0.2:
                amt = min(self.buffers[SubstanceType.TOXIN], 3.0 * rate_modifier * dt)
                self.buffers[SubstanceType.TOXIN] -= amt
                outgoing.append(FluidPacket(substance=SubstanceType.TOXIN, amount=amt))

        elif self.organ_type == OrganType.LYMPH:
            # 淋巴滤泡：强力分解与吸附毒素（过滤效率 85%）
            tox = self.buffers[SubstanceType.TOXIN]
            filter_capacity = 6.0 * rate_modifier * dt
            filtered = min(tox, filter_capacity)
            if filtered > 0.01:
                self.buffers[SubstanceType.TOXIN] -= filtered
                self.total_processed += filtered
            # 如果误吞了食糜或神经液，则原样通过
            for subst in [SubstanceType.CHYME, SubstanceType.NEURO_FLUID]:
                if self.buffers[subst] > 0.2:
                    amt = min(self.buffers[subst], 4.0 * rate_modifier * dt)
                    self.buffers[subst] -= amt
                    outgoing.append(FluidPacket(substance=subst, amount=amt))

        elif self.organ_type == OrganType.GLAND:
            # 神经腺体：将食糜转化为神经液 (需要极低毒素环境)
            if self.toxin_ratio > 0.10:
                # 毒素污染毒化腺体，转化受抑
                self.efficiency = max(0.1, 1.0 - self.toxin_ratio * 2.0)
            else:
                self.efficiency = 1.0
                
            chyme = self.buffers[SubstanceType.CHYME]
            synthesize = min(chyme, 3.5 * rate_modifier * dt)
            if synthesize > 0.05:
                self.buffers[SubstanceType.CHYME] -= synthesize
                neuro_out = synthesize * 0.65
                self.buffers[SubstanceType.NEURO_FLUID] += neuro_out
                self.total_processed += synthesize

            if self.buffers[SubstanceType.NEURO_FLUID] > 0.2:
                amt = min(self.buffers[SubstanceType.NEURO_FLUID], 3.0 * rate_modifier * dt)
                self.buffers[SubstanceType.NEURO_FLUID] -= amt
                outgoing.append(FluidPacket(substance=SubstanceType.NEURO_FLUID, amount=amt))

        elif self.organ_type == OrganType.BRAIN_TANK:
            # 神质育卵囊：凝华神经液 -> 神经晶质 (稳态核心)
            neuro = self.buffers[SubstanceType.NEURO_FLUID]
            crystallize = min(neuro, 2.5 * rate_modifier * dt)
            if crystallize > 0.05:
                self.buffers[SubstanceType.NEURO_FLUID] -= crystallize
                crystals = crystallize * 0.50
                self.buffers[SubstanceType.NEURO_CRYSTAL] += crystals
                self.total_processed += crystals

        return outgoing

    def excise_tumor(self) -> bool:
        """外科手术：切除肿瘤组织，重置健康度"""
        if self.health in [OrganHealth.TUMOROUS, OrganHealth.INFLAMED] or self.tumor_progress > 0:
            self.health = OrganHealth.HEALTHY
            self.tumor_progress = 0.0
            self.congestion_ticks = 0
            self.efficiency = 0.8  # 术后轻微创伤，随后逐渐愈合
            # 释放部分淤积毒素
            self.buffers[SubstanceType.TOXIN] = 0.0
            return True
        return False
