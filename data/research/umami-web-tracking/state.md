# Research State: umami-web-tracking

## Metadata
- topic: "使用Umami+RRWeb进行埋点，捕捉用户操作轨迹，产出Agent可学习的结构化回放（含A11y语义对齐）"
- created: 2026-06-12
- last_updated: 2026-06-14
- total_sessions: 7
- project: umami-web-tracking

## Current Phase: complete
## Status: complete
## Confidence: 98%
## Next Action: 无（研究完成）。可选方向：SOP自动切分、跨页面session关联、Agent自动执行

## Phase History

### discovery (sessions: 1)
- Session 1: 搜索Umami官方文档、对比方案

### analysis (sessions: 1)
- Session 2: 对比方案，确认RRWeb，设计双层架构

### solution_draft (sessions: 2)
- Session 3: A11y Tree对齐分析，设计captureA11yContext
- Session 4: 存储方案设计 + 会话摘要格式 + PoC创建

### validation (sessions: 1)
- Session 5 (前半): Playwright自动化验证完成，12/13通过(92%)

### finalization (sessions: 1)
- Session 5 (后半): token消耗评估、压缩策略、隐私脱敏、rrweb-player、checklist完善

### validation+finalization (sessions: 2)
- Session 6: Docker部署验证（9/9 RRWeb管线 + 6/6 LLM消费 + Umami双层追踪）
- Session 7: 单系统重构 + 采集端修复 + 操作回放闭环（100%回放成功率）

## Summary
方案研究完成。从双系统演进为单系统架构：
- Umami v3 内置 RRWeb 录制引擎 + a11y-enhancer.js 语义增强层
- captureA11yContext A11y语义增强（role/name/state 三元组）
- 输入值采集 + 隐私脱敏 + select选项值 + checkbox嵌套label修复
- 双层 session：sessionId（Umami浏览器级）+ pageSessionId（页面级）
- TOON → Playwright ARIA 回放（getByRole），100%操作复现
- 录制→存储→读取→回放完整闭环验证通过
