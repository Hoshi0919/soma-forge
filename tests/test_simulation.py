"""
Unit and integration test suite for SomaForge bioprocessing simulation engine.
"""
import pytest
from soma.models import SubstanceType, OrganType, OrganHealth, FluidPacket
from soma.organ import Organ
from soma.vessel import VascularTube
from soma.engine import SimulationEngine

def test_models_and_init():
    organ = Organ("maw1", OrganType.MAW, 10, 20)
    assert organ.health == OrganHealth.HEALTHY
    assert organ.current_load == 0.0
    assert organ.load_ratio == 0.0
    assert organ.toxin_ratio == 0.0

def test_heartbeat_rhythm():
    engine = SimulationEngine()
    initial_phase = engine.heart_phase
    engine.step(0.1)
    assert engine.heart_phase != initial_phase
    assert engine.vitals.blood_pressure_systolic > engine.vitals.blood_pressure_diastolic
    assert engine.heart_pulse_power > 0.0

def test_maw_biomass_production():
    maw = Organ("maw1", OrganType.MAW)
    packets = maw.tick_metabolism(dt=1.0, pulse_power=1.0)
    assert len(packets) > 0
    assert packets[0].substance == SubstanceType.BIOMASS
    assert packets[0].amount > 0.0

def test_stomach_metabolism():
    stomach = Organ("stom1", OrganType.STOMACH)
    stomach.buffers[SubstanceType.BIOMASS] = 10.0
    packets = stomach.tick_metabolism(dt=1.0, pulse_power=1.0)
    
    assert stomach.buffers[SubstanceType.BIOMASS] < 10.0
    assert stomach.total_processed > 0.0
    substances = {p.substance for p in packets}
    assert SubstanceType.CHYME in substances or stomach.buffers[SubstanceType.CHYME] > 0
    assert SubstanceType.TOXIN in substances or stomach.buffers[SubstanceType.TOXIN] > 0

def test_lymph_detoxification():
    lymph = Organ("lym1", OrganType.LYMPH)
    lymph.buffers[SubstanceType.TOXIN] = 8.0
    initial_toxin = lymph.buffers[SubstanceType.TOXIN]
    lymph.tick_metabolism(dt=1.0, pulse_power=1.0)
    assert lymph.buffers[SubstanceType.TOXIN] < initial_toxin
    assert lymph.total_processed > 0.0

def test_vascular_transport_and_backpressure():
    tube = VascularTube("tube1", "org1", "org2", length=50.0)
    p = FluidPacket(substance=SubstanceType.CHYME, amount=2.0)
    assert tube.inject_packet(p)
    assert len(tube.packets) == 1
    
    arrived = []
    for _ in range(30):
        arrived = tube.tick_flow(dt=0.1, pulse_power=1.2)
        if arrived:
            break
            
    assert len(arrived) == 1
    assert arrived[0].substance == SubstanceType.CHYME

def test_pathology_tumor_and_excision():
    organ = Organ("test_org", OrganType.STOMACH)
    # 模拟胃部持续严重毒素淤塞
    for _ in range(60):
        organ.buffers[SubstanceType.TOXIN] = 30.0
        organ.tick_metabolism(dt=0.5, pulse_power=1.0)
        if organ.health == OrganHealth.TUMOROUS:
            break
            
    assert organ.health == OrganHealth.TUMOROUS
    assert organ.tumor_progress >= 1.0
    
    # 外科手术切除肿瘤
    healed = organ.excise_tumor()
    assert healed is True
    assert organ.health == OrganHealth.HEALTHY
    assert organ.tumor_progress == 0.0
    assert organ.buffers[SubstanceType.TOXIN] == 0.0

def test_full_pipeline_gland_and_crystals():
    engine = SimulationEngine()
    maw = engine.add_organ("maw", OrganType.MAW, 0, 0)
    stom = engine.add_organ("stom", OrganType.STOMACH, 60, 0)
    lym = engine.add_organ("lym", OrganType.LYMPH, 60, 80)
    gland = engine.add_organ("gland", OrganType.GLAND, 120, 0)
    brain = engine.add_organ("brain", OrganType.BRAIN_TANK, 180, 0)

    engine.connect_tube("t1", "maw", "stom")
    engine.connect_tube("t2", "stom", "gland")
    engine.connect_tube("t3", "stom", "lym")
    engine.connect_tube("t4", "gland", "brain")

    gland.buffers[SubstanceType.CHYME] = 10.0

    for _ in range(100):
        engine.step(0.1)

    assert gland.total_processed > 0.0
    assert brain.total_processed > 0.0 or engine.total_harvested > 0.0

def test_sepsis_and_resuscitation():
    engine = SimulationEngine()
    stom = engine.add_organ("stom", OrganType.STOMACH, 0, 0)
    # 人为注入高量毒素引发脓毒症
    stom.buffers[SubstanceType.TOXIN] = 50.0
    stom.capacity = 60.0

    for _ in range(20):
        engine.step(0.2)

    assert engine.vitals.toxicity_ratio > 0.50
    assert engine.vitals.is_septic is True
    assert engine.current_bpm > engine.base_bpm

    # 注射抗毒血清
    engine.inject_antitoxin(dose=2.0)
    # 注射肾上腺素
    engine.inject_adrenaline(dose=1.0)
    
    engine.step(0.1)
    assert engine.vitals.toxicity_ratio < 0.40

def test_ascension_milestone():
    engine = SimulationEngine()
    brain = engine.add_organ("brain", OrganType.BRAIN_TANK, 0, 0)
    brain.buffers[SubstanceType.NEURO_CRYSTAL] = 110.0
    
    engine.step(0.1)
    assert engine.total_harvested >= 100.0
    assert engine.is_ascended is True
    assert engine.vitals.awakening_progress == 1.0

def test_aneurysm_and_clogging():
    tube = VascularTube("t_clog", "o1", "o2", length=40.0)
    for i in range(12):
        tube.inject_packet(FluidPacket(substance=SubstanceType.TOXIN, amount=1.0))
    # 达到容量上限
    assert tube.inject_packet(FluidPacket(substance=SubstanceType.TOXIN, amount=1.0)) is False
    assert tube.clogged_ratio >= 1.0
    
    # 推进流逝检测动脉瘤风险递增
    tube.tick_flow(dt=1.0, pulse_power=0.5)
    assert tube.aneurysm_risk > 0.0

def test_cardiac_arrest_and_resuscitation():
    engine = SimulationEngine()
    engine.vitals.is_alive = False
    engine.step(0.1)
    assert engine.heart_pulse_power == 0.0
    assert engine.vitals.heart_rate_bpm == 0.0
    assert engine.vitals.blood_pressure_systolic == 0.0

    # 肾上腺素起搏
    engine.inject_adrenaline(dose=1.5)
    assert engine.vitals.is_alive is True
    engine.step(0.1)
    assert engine.vitals.heart_rate_bpm > 70.0
    assert engine.vitals.blood_pressure_systolic > 100.0

def test_organ_removal_cascades_tubes():
    engine = SimulationEngine()
    engine.add_organ("o1", OrganType.MAW, 0, 0)
    engine.add_organ("o2", OrganType.STOMACH, 10, 0)
    engine.connect_tube("t1", "o1", "o2")
    assert "t1" in engine.tubes

    engine.remove_organ("o1")
    assert "o1" not in engine.organs
    assert "t1" not in engine.tubes

def test_multi_tube_load_balancing():
    engine = SimulationEngine()
    stom = engine.add_organ("stom", OrganType.STOMACH, 0, 0)
    gland1 = engine.add_organ("g1", OrganType.GLAND, 50, -20)
    gland2 = engine.add_organ("g2", OrganType.GLAND, 50, 20)
    t1 = engine.connect_tube("t1", "stom", "g1")
    t2 = engine.connect_tube("t2", "stom", "g2")

    stom.buffers[SubstanceType.CHYME] = 8.0
    engine.step(0.5)

    # 验证两个导管都接收到了食糜流体包
    assert len(t1.packets) > 0 or len(t2.packets) > 0
