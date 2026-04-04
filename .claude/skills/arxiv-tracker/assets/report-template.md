# 论文追踪报告

**搜索关键词**: {{ keywords }}
**报告日期**: {{ date }}
**论文数量**: {{ count }}

---

## 论文列表

{{#each papers}}
### {{ ordinal }}. {{ title }}

- **作者**: {{ authors }}
- **日期**: {{ date }}
- **核心贡献**: {{ contribution }}
- **关键方法**: {{ methods }}
- **链接**: {{ url }}

---
{{/each}}

## 研究趋势分析

{{ trends }}

## 推荐关注

{{ recommendations }}

---

*报告由 arxiv-tracker skill 自动生成*
