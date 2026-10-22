"""
SomaForge Vascular Tubes: Peristaltic conduits, fluid transport waves, and hydraulic hemodynamics.
"""
import math
from typing import List, Optional
from soma.models import FluidPacket, SubstanceType

class VascularTube:
    def __init__(self, tube_id: str, from_organ_id: str, to_organ_id: str, length: float = 100.0):
        self.id = tube_id
        self.from_organ_id = from_organ_id
        self.to_organ_id = to_organ_id
        self.length = max(20.0, length)
        
        # 蠕动管腔内的流动液滴包
        self.packets: List[FluidPacket] = []
        self.max_capacity_packets = 12
        self.aneurysm_risk = 0.0

    @property
    def total_fluid(self) -> float:
        return sum(p.amount for p in self.packets)

    @property
    def clogged_ratio(self) -> float:
        return len(self.packets) / float(self.max_capacity_packets)

    def inject_packet(self, packet: FluidPacket) -> bool:
        """注入流体包到管道入口"""
        if len(self.packets) >= self.max_capacity_packets:
            return False
        packet.position = 0.0
        self.packets.append(packet)
        return True

    def tick_flow(self, dt: float, pulse_power: float) -> List[FluidPacket]:
        """按心跳脉动推进蠕动波，返回到达末端待注入下游的流体包"""
        arrived: List[FluidPacket] = []
        
        speed_factor = 45.0 * max(0.2, pulse_power)
        progress_delta = (speed_factor / self.length) * dt

        surviving_packets: List[FluidPacket] = []
        for packet in self.packets:
            packet.position += progress_delta
            if packet.position >= 1.0:
                packet.position = 1.0
                arrived.append(packet)
            else:
                surviving_packets.append(packet)

        self.packets = surviving_packets
        
        # 评估管道淤滞与动脉瘤风险
        if self.clogged_ratio > 0.8:
            self.aneurysm_risk = min(1.0, self.aneurysm_risk + 0.1 * dt)
        else:
            self.aneurysm_risk = max(0.0, self.aneurysm_risk - 0.05 * dt)

        return arrived

    def reject_backflow(self, packet: FluidPacket):
        """当下游器官爆满无法吸纳时，滞留末端形成背压"""
        packet.position = 0.98
        self.packets.append(packet)
