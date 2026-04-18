# 论文追踪报告

**搜索关键词**: large language model, agent, reinforcement learning, agent application
**报告日期**: 2026-04-17
**论文数量**: 5

---

## 论文列表

### 1. FlashSAC: Fast and Stable Off-Policy Reinforcement Learning for High-Dimensional Robot Control

- **作者**: Donghu Kim, Youngdo Lee, Minho Park, Kinam Kim, I Made Aswin Nahendra, Takuma Seno, Sehee Min, Daniel Palenicek, Florian Vogt, Danica Kragic, Jan Peters, Jaegul Choo, Hojoon Lee
- **日期**: 2026-04-06
- **核心贡献**: 提出 FlashSAC 算法，一种基于 Soft Actor-Critic (SAC) 的快速稳定的离策略强化学习算法。该算法受监督学习中的缩放定律 (Scaling Laws) 启发，通过大幅减少梯度更新次数、增大模型规模和提高数据吞吐量来加速训练，同时通过对权重范数、特征范数和梯度范数进行显式约束来保持训练稳定性。在 10 个模拟器的 60+ 任务中，FlashSAC 在最终性能和训练效率上均优于 PPO 和其他离策略基线方法，在人形机器人 Sim-to-Real 迁移中将训练时间从数小时缩短至数分钟。
- **关键方法**: 离策略强化学习 (Off-Policy RL)、Soft Actor-Critic (SAC)、缩放定律 (Scaling Laws)、范数约束 (Norm Bounding)、Sim-to-Real 迁移
- **链接**: https://arxiv.org/abs/2604.04539

---

### 2. The Attack and Defense Landscape of Agentic AI: A Comprehensive Survey

- **作者**: Juhee Kim, Xiaoyuan Liu, Zhun Wang, Shi Qiu, Bo Li, Wenbo Guo, Dawn Song
- **日期**: 2026-03-11
- **核心贡献**: 首篇系统性全面综述 AI Agent 安全的论文，涵盖设计空间分析、攻击面梳理和防御机制总结。论文指出，将 LLM 与非 AI 系统组件结合的 AI Agent 带来了与传统软件系统根本不同的安全挑战。研究团队还通过案例研究指出了当前 Agentic AI 系统安全保护的不足，并提出了首个理解 AI Agent 安全风险与防御策略的系统性框架。已被 USENIX Security 2026 接收。
- **关键方法**: Agent 安全框架 (Agent Security Framework)、攻击分类学 (Attack Taxonomy)、防御机制 (Defense Mechanisms)、案例研究
- **链接**: https://arxiv.org/abs/2603.11088

---

### 3. AI Agents Under EU Law

- **作者**: Luca Nannini, Adam Leon Smith, Michele Joshua Maggini, Enrico Panai, Sandra Feliciano, Aleksandr Tiulkanov, Elena Maran, James Gealy, Piercosma Bisconti
- **日期**: 2026-04-06
- **核心贡献**: 首篇为 AI Agent 提供系统性监管映射的论文，整合了 EU AI Act、GDPR、Cyber Resilience Act、Digital Services Act、Data Act 等多项法规要求。论文提出了九类 Agent 部署分类法 (Taxonomy) 和十二步合规架构，识别了 Agent 在网络安全、人类监督、多方行动链透明度和运行时行为漂移 (Behavioral Drift) 等方面的合规挑战。论文结论指出，具有不可追踪行为漂移的高风险 Agentic 系统目前尚无法满足 AI Act 的基本要求。
- **关键方法**: 监管映射 (Regulatory Mapping)、合规架构 (Compliance Architecture)、风险分类框架 (Risk-based Framework)、Agent 部署分类法
- **链接**: https://arxiv.org/abs/2604.04604

---

### 4. Agent-as-a-Judge

- **作者**: Runyang You, Hongru Cai, Caiqi Zhang, Qiancheng Xu, Meng Liu, Tiezheng Yu, Yongqi Li, Wenjie Li
- **日期**: 2026-01-08
- **核心贡献**: 首篇全面综述 Agent-as-a-Judge 范式的论文，系统追踪了从 LLM-as-a-Judge 到 Agent-as-a-Judge 的演进过程。Agentic Judge 通过规划 (Planning)、工具增强验证 (Tool-augmented Verification)、多 Agent 协作 (Multi-Agent Collaboration) 和持久记忆 (Persistent Memory) 实现更稳健、可验证和细致的评估。论文建立了关键维度的分类法和核心方法论体系，覆盖通用和专业领域的应用，并识别了前沿挑战和有前景的研究方向。
- **关键方法**: Agentic 评估 (Agentic Evaluation)、工具增强验证 (Tool-augmented Verification)、多 Agent 协作 (Multi-Agent Collaboration)、持久记忆 (Persistent Memory)
- **链接**: https://arxiv.org/abs/2601.05111

---

### 5. Large Language Model Reasoning Failures

- **作者**: Peiyang Song, Pengrui Han, Noah Goodman
- **日期**: 2026-02-05
- **核心贡献**: 首篇专门针对 LLM 推理失败 (Reasoning Failures) 的全面综述。论文引入了全新的分类框架，将推理分为具身 (Embodied) 和非具身 (Non-embodied) 两类，后者进一步细分为非形式化推理 (Informal/Intuitive) 和形式化推理 (Formal/Logical)。同时沿互补轴将推理失败分为三类：影响广泛下游任务的基础性失败 (Fundamental Failures)、特定领域的应用性限制 (Application-specific Limitations)，以及对微小变化表现不一致的鲁棒性问题 (Robustness Issues)。发表于 TMLR 2026，并附有持续更新的 GitHub 论文合集。
- **关键方法**: 推理分类框架 (Reasoning Categorization)、失败分类学 (Failure Taxonomy)、具身 vs 非具身推理 (Embodied vs Non-embodied Reasoning)、缓解策略 (Mitigation Strategies)
- **链接**: https://arxiv.org/abs/2602.06176

---

## 研究趋势分析

### 1. Agent 安全与合规成为核心议题

随着 AI Agent 从研究原型走向大规模部署，安全与合规问题正迅速成为研究热点。本次追踪中，**The Attack and Defense Landscape of Agentic AI**（USENIX Security 2026 接收）和 **AI Agents Under EU Law** 两篇论文分别从技术安全和法律合规两个维度深入探讨了 Agent 的治理问题。这表明学术界和产业界正在为 Agent 的负责任部署建立理论基础和监管框架。

### 2. 从能力提升到失败分析的研究范式转变

**Large Language Model Reasoning Failures**（TMLR 2026）代表了当前研究的一个重要转向：从单纯追求 LLM 能力提升，转向系统性理解其推理失败的根源。这种"反向工程"式的分析思路有助于更精准地定位模型弱点，指导下一代模型的设计。

### 3. Agent 评估方法学的范式演进

**Agent-as-a-Judge** 展示了 AI 评估方法学的重大演进：从简单的 LLM-as-a-Judge 过渡到具备规划、工具调用、多 Agent 协作和持久记忆的 Agentic Judge。这反映了 AI 系统复杂度的提升需要更强大的评估工具来匹配。

### 4. 强化学习的实用性突破

**FlashSAC** 通过借鉴监督学习的缩放定律，在离策略 RL 中实现了训练效率的量级提升（从小时级到分钟级），同时在高维机器人控制任务中保持稳定性和性能。这标志着 RL 在实际机器人控制中的应用正变得更加可行。

### 5. 跨学科融合加速

本次追踪的论文覆盖了安全学、法学、机器人学、评估方法学等多个领域，反映出 AI Agent 和 LLM 研究正在深度融入传统学科，形成更加完整的研究生态。

## 推荐关注

- **FlashSAC** (2604.04539): 对机器人控制和强化学习领域的研究者具有直接参考价值，其范数约束策略对其他 RL 算法设计也有启发意义。建议关注其开源代码实现。
- **The Attack and Defense Landscape of Agentic AI** (2603.11088): 作为 USENIX Security 2026 的论文，对 Agent 安全领域进行了全面梳理，是安全研究者和 Agent 开发者的必读综述。
- **AI Agents Under EU Law** (2604.04604): 对于计划在欧洲市场部署 AI Agent 的团队，该论文提供了实际可用的合规架构和监管映射，具有极高的实用价值。
- **Large Language Model Reasoning Failures** (2602.06176): 提供了最全面的 LLM 推理失败分类框架，配套 GitHub 仓库持续更新，适合作为 LLM 推理研究的入门参考。
- **Agent-as-a-Judge** (2601.05111): 对于关注 AI 评估方法学的研究者，该论文梳理了从 LLM-as-a-Judge 到 Agent-as-a-Judge 的完整演进路径，为设计更强大的评估系统提供了路线图。

---

*报告由 arxiv-tracker skill 自动生成*
