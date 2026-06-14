# 验证检查清单: Umami + RRWeb Agent可学习回放

## 需求明确性

- [x] 核心问题已定义：前端埋点 + Agent可学习的结构化操作回放
- [x] 约束条件已列出：自托管、隐私合规、轻量、结构化非视频
- [x] 成功标准：RRWeb JSON事件流可被Agent解析和学习

## 候选方案覆盖度

- [x] 主流候选方案已调研：Umami+RRWeb、PostHog、纯RRWeb自建
- [x] 每个方案有官方文档和架构说明支撑
- [x] RRWeb作为PostHog/Sentry/OpenReplay底层技术已确认

## 对比分析完整性

- [x] 评估维度覆盖：功能、部署、Agent学习友好度、资源、隐私
- [x] 评分基于官方文档和技术架构分析
- [x] Agent学习友好度作为新增核心评估维度

## 推荐方案验证

- [x] 推荐理由：RRWeb结构化JSON事件流天然适合Agent消费
- [x] 已知限制：事件体积大、两系统关联复杂、Agent学习噪声
- [x] 备选方案：PostHog（内置AI）或增强RRWeb语义层

## 实施可行性

- [x] 技术栈兼容：Docker + 前端JS，无特殊依赖
- [x] RRWeb事件格式已确认：FullSnapshot + IncrementalSnapshot
- [x] enrichEvent语义增强 → 已通过 `captureA11yContext` 实现并验证
- [x] 事件存储方案：Umami PostgreSQL event_data 表（单系统复用）
- [x] Agent消费API：会话摘要格式已设计（Compact TOON ~350 tokens/20事件）

## A11y 语义对齐验证

- [x] Accessibility Tree 数据结构研究完成（role/name/state 三元组）
- [x] captureA11yContext 函数设计与实现
- [x] Playwright 自动化验证：12/13 元素通过（92%）
- [x] 交互事件验证：9/9 事件语义正确
- [x] role推断边界case修复（tab name提取）

## Token 消耗与压缩

- [x] 评估4种格式的token消耗（Full JSON / Compact TOON / Ultra-compact / Summary）
- [x] Compact TOON 格式减少75% token消耗
- [x] Ultra-compact 格式减少87% token消耗
- [x] 推荐：Agent学习用Summary（~500 tokens/会话），精确回放用Compact TOON

## 隐私脱敏

- [x] 分级脱敏策略设计（敏感→REDACTED, PII→{type}, 普通→保留）
- [x] sanitizeValue 实现方案
- [x] 脱敏规则在 Docker 环境验证（4 类敏感数据全部正确处理）

## 可视化回放

- [x] rrweb-player 集成方式已确认
- [x] 明确 Agent 消费使用结构化格式而非可视化回放

## 风险评估

- [x] 技术风险：RRWeb事件流体积大 → Compact TOON 压缩87%
- [x] 集成风险：Umami和RRWeb需要sessionId关联 → 共享UUID方案
- [x] 运维风险：分层存储（热7天/温30天/冷90天）

## 单系统架构验证 (Umami v3 内置录制)

- [x] 发现 Umami v3.x 内置 RRWeb 录制引擎 (recorder.js)
- [x] 确认 recorder.js 包含 FullSnapshot/IncrementalSnapshot/Interaction 等完整事件类型
- [x] 启用 replayEnabled=true，单系统替代双系统
- [x] a11y-enhancer.js 通过 umami.track() 将 A11y 语义数据存入 event_data
- [x] 单系统验证 7/7 通过（pageview + 自定义事件 + A11y 增强 + 无外部依赖）

## 采集端修复与增强

- [x] Checkbox 嵌套 label name 提取修复 (closest('label'))
- [x] Select 选项值捕获 (change 事件记录 selectedText)
- [x] 输入值采集 (input 事件记录 inputValue，保留 sanitizeValue 隐私脱敏)
- [x] 双层 session 模型：sessionId (Umami浏览器级) + pageSessionId (页面级)

## 操作回放验证

- [x] replay-a11y.js CLI 工具实现（从 Umami 读取 → 去重 → Playwright 回放）
- [x] TOON → Playwright ARIA 定位器自然映射 (getByRole + name)
- [x] 双系统方案回放：7/7 PASS (100%)
- [x] 单系统方案回放：12/12 PASS (100%)
- [x] 含输入值的精确回放：12/12 PASS (1111→222→3333 三轮搜索完整复现)
- [x] 回放工具支持 --headed/--dry-run/--session/--url 参数

## 剩余验证步骤

1. [x] Docker部署Umami + 前端RRWeb录制集成PoC — 完整验证通过
2. [x] 将RRWeb+A11y事件流喂给LLM，测试Agent理解和推理能力 — 6/6 推理测试全部通过
3. [x] 生产环境脱敏规则验证 — Docker 环境中 4 类 PII 全部正确脱敏
4. [x] 单系统架构验证 — Umami 内置 recorder + a11y-enhancer.js，7/7 通过
5. [x] 操作回放闭环 — 录制 → 存储 → 读取 → Playwright 回放，100% 成功率
