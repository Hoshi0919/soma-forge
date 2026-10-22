# SomaForge (生质工厂：原质代谢)

> **基于心跳节律驱动、肌肉导管蠕动输送、生化病理与稳态平衡的有机生命体工厂模拟器**
>
> 体验 Live Demo：[https://hoshi0919.github.io/soma-forge/](https://hoshi0919.github.io/soma-forge/)

一个基于「心跳节律驱动、肌肉导管蠕动输送、生化病理与稳态平衡」的有机生命体工厂概念原型 (Prototype MVP)。

区别于以静止传输带与恒流电网为基础的传统工业流水线建造游戏，SomaForge 将工厂系统彻底有机生物化：整个流水线是一具拥有心率、血压、血浆容积、毒素浓度的活体生物。

---

## 核心设计机制

1. **心跳动力源 (Cardiovascular Rhythm Core)**：
   - 工厂不依赖无限恒流电网，而是由中枢活体心脏提供节律跳动（基准 72 BPM，伴随心室收缩 QRS 脉冲波形）；
   - 心脏收缩压激增时推动全身管道流速加速，舒张期维持基底灌注；
   - 伴随实时动态 ECG 心电图描记与 Web Audio 原生合成的收缩-舒张双相心音。

2. **蠕动血管导管 (Peristaltic Vascular Conduits)**：
   - 取代冰冷僵硬的铁质传送带，两座器官之间通过嫁接肌肉血管连通；
   - 微流体包（Biomass、Chyme、Toxin、Neuro-Fluid）在管腔内伴随心搏脉冲以正弦蠕动波向前行进；
   - 包含背压回阻（Backpressure）机制：当下游器官满载溢出时，流体会滞留管腔末端造成拥堵，甚至诱发血管膨胀瘤（Aneurysm）。

3. **器官代谢网络 (Metabolic Organs)**：
   - **生质摄食口 (Maw)**：具有进食反馈与咀嚼动画，自主吞咽环境未加工粗生物质；
   - **消化胃囊 (Stomach)**：水解生质生成高能乳化浆料（Chyme 食糜），但必然伴生强酸毒性副产物（Toxin）；
   - **淋巴滤泡 (Lymph Node)**：高效率免疫吸附与毒素降解节点，维系全身流体纯度；
   - **神经腺体 (Gland)**：在极低毒血环境下将浓缩食糜转化为高导电性神经胶质液（Neuro-Fluid）；
   - **拟态脑囊 (Brain Tank)**：悬浮神经核心，凝华神经液析出终极产物「神经晶质 (Neuro-Crystal)」。

4. **病理学与稳态调谐 (Pathology & Homeostasis)**：
   - **器官癌变与恶性增生 (Tumor/Hyperplasia)**：器官长期高负荷淤积 (>85% 负荷) 或严重酸毒浸润 (>35% 毒比) 会诱发肉芽肿甚至癌变，彻底瘫痪代谢机能并疯狂向外渗毒；
   - **全身脓毒症休克 (Sepsis Shock)**：毒素超标会导致心动过速（Tachycardia > 150 BPM），若不干预会恶化为心室纤颤（Ventricular Fibrillation）直至心力衰竭猝死；
   - **活体干预工具箱**：
     - **外科手术刀 (Scalpel)**：精准切除肿瘤组织，或切断病变管路；
     - **急救肾上腺素 (Adrenaline)**：起搏升压、逆转室颤、强心急救；
     - **广谱抗毒血清 (Antitoxin)**：快速中和循环系统游离毒素。

5. **升华觉醒终局目标 (Homeostatic Ascension)**：
   - 维持生命体在健康低毒稳态（<15% 全身毒血比）的前提下，累积收获 100 单位神经晶质，触发高维意识蜕变。

---

## 项目结构

```
soma-forge/
├── soma/
│   ├── models.py       # 生理学数据结构、物质枚举与 VitalSigns 生命指征
│   ├── organ.py        # 器官生化动力学、负荷容量与病理癌变转化
│   ├── vessel.py       # 肌肉导管蠕动行波、微流体包推进与动脉瘤风险
│   └── engine.py       # 循环系统全局闭环调度、收缩舒张心搏与稳态平衡
├── tests/
│   └── test_simulation.py # 14 项自动化测试全绿 (覆盖全链路反应、毒血症、手术切除与觉醒)
├── index.html          # 原生 Canvas + Web Audio API 独立纯前端交互原型 (0 CDN 依赖)
└── screenshot.png      # 实时交互运行画面截图
```

## 测试与运行

```bash
# 运行底层生理学自动化测试
PYTHONPATH=. uv run --with pytest pytest tests/

# 启动或直接在浏览器中打开前端界面
xdg-open index.html # 或在任何现代浏览器中打开
```
