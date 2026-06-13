# MSS SOP 自动化服务 - 架构设计文档

> 版本: 2.0 | 日期: 2026-06-01 | 状态: 预研确认阶段
> 
> v2.0 更新：基于技术调研调整捕捉方案（mitmproxy → Playwright HAR）、
> 补充人机协同审批机制、增加步骤重试、适配国内安全平台 API 特征。

## 1. 背景与目标

### 1.1 问题

MSS (Managed Security Service) 安全服务平台的服务经理手动执行安全操作（告警处理、威胁调查、工单创建等），存在：人力依赖、流程不一致、非工作时间无法响应、操作经验无法复用。

### 1.2 目标

1. **动作捕捉** — 记录服务经理在 MSS 平台上的操作序列和 API 参数
2. **SOP 建模** — 将操作序列转化为结构化 SOP（标准操作流程）
3. **Agent 执行** — AI Agent 根据 SOP 自动调用 MSS API，**关键步骤需人工审批**

### 1.3 需求边界

| 维度 | 决定 |
|------|------|
| MSS 平台形态 | Web 浏览器操作 |
| 操作粒度 | 高频场景优先（告警处理、威胁调查），后续逐步扩展 |
| 自动化程度 | **人机协同** — Agent 执行到关键步骤暂停，等人工确认后继续 |
| 目标厂商 | 国内安全厂商（阿里云安全、奇安信、深信服、安恒等） |
| SOP 规模 | 预计 20-50 个 SOP，每个 3-10 步 |

---

## 2. 技术调研结论

### 2.1 动作捕捉方案：Playwright HAR 录制（替代 mitmproxy）

经调研比较 5 种捕捉方案，**Playwright + HAR 录制**为最优选择：

| | mitmproxy | Playwright HAR | 浏览器扩展 | HAR(手动) |
|---|---|---|---|---|
| **证书要求** | 需安装 CA 证书到系统信任库 | **无需** | 无需 | 无需 |
| **用户操作** | 配置浏览器代理 | **双击快捷方式启动"录制浏览器"** | 安装扩展 | 打开 DevTools |
| **捕获完整性** | 完整 | **完整（HAR 标准格式）** | 缺响应体 | 完整 |
| **回放验证** | 需自建 | **Playwright routeFromHAR() 内置** | 不支持 | Playwright 支持 |
| **维护成本** | 证书管理、代理漂移 | **极低** | MV3 限制 | 低 |

**选型理由**：
- 服务经理是非技术用户，Playwright 方案零配置（无需证书/代理设置）
- HAR 是 W3C 标准格式，Playwright 原生支持 HAR 回放验证捕捉是否正确
- 微软维护的一流 Windows 支持

### 2.2 国内安全平台 API 特征

| 厂商 | API 风格 | 认证方式 | 文档公开 |
|------|---------|---------|---------|
| 阿里云安全中心 | RPC OpenAPI | AccessKey 签名 | 公开 |
| 奇安信 NGSOC | RESTful | Bearer Token（需"API管理员"角色） | 客户交付 |
| 深信服 | RESTful | Token/Session | 社区部分 |
| 安恒 AiLPHA | RESTful | Bearer Token | 客户交付 |
| 绿盟 | RESTful | API Key / Token | 部分公开 |

**共性特征**：
- 绝大多数使用 `POST /api/v1/auth/login → Bearer token` 认证
- Token 通常 30 分钟 ~ 24 小时过期
- 响应格式：JSON，数据在 `$.data` 路径下
- **本地部署常有自签名 TLS 证书** → 需支持 `verify_ssl: false`
- API 文档很少公开，需在 MSS 平台内部获取

### 2.3 工作流引擎选型：增强自定义引擎

| 方案 | 结论 |
|------|------|
| Temporal.io | 过重（需 PostgreSQL + Java 服务端），20-50 个 SOP 不值得 |
| Prefect | 偏数据管道，无额外价值 |
| Airflow | 调度器范式，不适合事件驱动 SOP |
| N8N | GUI 优先，与代码优先方案冲突 |
| **自定义引擎（增强）** | **正确选择**：补上 retry + approval + 状态持久化 |

### 2.4 SOAR 行业标准参考

- **OASIS CACAO v2.0**：安全 playbook 国际标准，支持 action/if-condition/while-condition/parallel/switch-condition 步骤类型
- **Splunk SOAR / Cortex XSOAR**：通过 Prompt/Task 节点实现人工审批
- **FortiSOAR**：Approval Step 暂停执行，向审批人发送通知

---

## 3. 系统架构

### 3.1 总体架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          用户交互层                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Playwright    │  │ Web 管理界面   │  │ CLI 命令行   │  │Skill命令 │ │
│  │ 录制浏览器    │  │ /mss/*        │  │ src.mss      │  │ /mss-sop │ │
│  └───────┬───────┘  └───────┬───────┘  └──────┬───────┘  └────┬─────┘ │
│          │                  │                  │                │       │
├──────────┼──────────────────┼──────────────────┼────────────────┼───────┤
│          │         捕捉服务层       │       执行服务层             │       │
│   ┌──────▼──────┐         │  ┌────────▼────────┐  ┌────────────▼─────┐ │
│   │ HAR 录制    │         │  │ SopExecutor     │  │ Agent (SDK)      │ │
│   │ (Playwright)│         │  │ + retry/approval│  │ + 人机协同       │ │
│   └──────┬──────┘         │  └────────┬────────┘  └────────────┬─────┘ │
│          │                │           │                        │       │
├──────────┼────────────────┼───────────┼────────────────────────┼───────┤
│          │       数据与配置层        │                        │       │
│   ┌──────▼───────────┐  ┌──────────┐│  ┌──────────┐  ┌───────▼─────┐ │
│   │data/mss_captures/│  │config/   ││  │ AuthMgr  │  │  通知服务   │ │
│   │  *.har           │  │ mss_sops/││  │(认证)    │  │ webhook     │ │
│   │data/mss_         │  │ mss_auth ││  └──────────┘  │ 企微/钉钉  │ │
│   │  executions/     │  └──────────┘│                └─────────────┘ │
│   └──────────────────┘              │                                  │
│                                     │                                  │
├─────────────────────────────────────┼──────────────────────────────────┤
│                外部系统             │                                  │
│                ┌────────────────────▼──────────────────────┐           │
│                │  MSS 平台 REST API (国内安全厂商)         │           │
│                └───────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 层次说明

| 层 | 职责 | 关键组件 |
|---|------|---------|
| **用户交互层** | 提供操作入口 | Playwright 录制浏览器、Web UI、CLI、Skill |
| **捕捉服务层** | 记录 MSS 操作为 HAR 文件 | Playwright HAR 录制 (`scripts/mss_record.py`) |
| **执行服务层** | 执行 SOP + 人机协同 | SopExecutor (retry/approval/resume) + Agent |
| **数据与配置层** | 持久化 | HAR 文件、SOP YAML、认证配置、执行记录 |
| **通知服务** | 审批通知 | 企业微信/钉钉 webhook |

---

## 4. 核心数据流

### 4.1 动作捕捉流程（Playwright HAR）

```
服务经理双击快捷方式
        │
   ┌────▼──────────────────────────┐
   │ Python 脚本启动 Playwright     │
   │ - 非无头模式打开 Chromium      │
   │ - 启用 HAR 录制               │
   │ - record_har_content="embed" │
   └────┬─────────────────────────┘
        │
   ┌────▼──────────────────────────┐
   │ 服务经理在 Playwright 浏览器中 │
   │ 正常操作 MSS 平台              │
   │ (与普通浏览器几乎无差别)        │
   └────┬─────────────────────────┘
        │
   ┌────▼──────────────────────────┐
   │ 关闭浏览器时自动保存           │
   │ data/mss_captures/            │
   │   session_20260601_143022.har │
   └───────────────────────────────┘
```

### 4.2 SOP 生成流程

```
HAR 文件 → 解析为统一 JSON → mss-capture Skill (Agent 分析)
                                     │
                            ┌────────┤
                            │ 分析动作  │
                            │ 1. API 端点分组
                            │ 2. 请求顺序识别
                            │ 3. 动态参数检测
                            │ 4. 响应-请求关联
                            └────┬───┘
                                 │
                            ┌────▼────────────┐
                            │ config/mss_sops/ │
                            │   handle_alert.yaml
                            └─────────────────┘
```

### 4.3 SOP 执行流程（含审批）

```
输入: sop_name + params
         │
    ┌────▼─────┐
    │ 加载 YAML │
    └────┬─────┘
         │
    ┌────▼─────────┐
    │ 验证参数      │
    └────┬─────────┘
         │
    ┌────▼─────┐
    │ 获取 Auth │ → Bearer token (login API)
    └────┬─────┘
         │
    ┌────▼──────┐
    │ 执行 Steps │◄──────────────────────────┐
    └────┬──────┘                            │
         │ 每个 step:                         │
    ┌────▼──────────────────┐                │
    │ type=approval?        │                │
    │  ├─ 是 → 暂停,发通知  │                │
    │  │   等待人工审批      │                │
    │  │   ↓ 批准/拒绝/超时  │                │
    │  └─ 否 → 继续         │                │
    │                      │                │
    │ 检查 condition       │                │
    │ 替换 {{变量}}         │                │
    │ 发起 HTTP 请求        │                │
    │  ├─ 成功 → extract   │──────┐         │
    │  └─ 失败 → retry?    │      │         │
    │      ├─ 重试(带退避)  │      │         │
    │      └─ 超限 → 报错  │      │         │
    └──────────────────────┘      │         │
         │                        │         │
    ┌────▼──────┐                  │         │
    │ 合并变量   │◄─────────────────┘         │
    └────┬──────┘                            │
         │ 还有下一步 ────────────────────────┘
         │ 全部完成
    ┌────▼──────────────┐
    │ 保存执行记录       │
    │ 构建 output        │
    └───────────────────┘
```

---

## 5. SOP YAML Schema（v2）

在 v1 基础上增加 retry、approval、notify：

```yaml
name: handle_alert
description: "处理高危告警 - 调查、审批、响应"
version: "2.0"

auth:
  profile: mss_prod

base_url: "https://mss.example.com"

input_parameters:
  alert_id:
    type: string
    required: true
    description: "告警 ID"
  operator_id:
    type: string
    default: "agent"

steps:
  - id: query_alert
    name: "查询告警详情"
    method: GET
    path: "/api/v1/alerts/{{alert_id}}"
    headers:
      Authorization: "Bearer {{session_token}}"
    retry:
      max_attempts: 3
      backoff_seconds: [1, 2, 4]
      retry_on: [timeout, 5xx]
    expect:
      status: 200
    extract:
      source_ip: "$.data.source_ip"
      alert_type: "$.data.alert_type"

  - id: query_threat_intel
    name: "查询威胁情报"
    method: POST
    path: "/api/v1/threat_intel/query"
    body:
      indicators: ["{{source_ip}}"]
    expect:
      status: 200
    extract:
      threat_level: "$.data.risk_level"

  - id: approve_block
    name: "审批：封禁源 IP"
    type: approval
    timeout: 3600                    # 等待审批超时（秒）
    timeout_action: escalate          # 超时后动作: escalate | auto_approve | auto_reject
    notify:
      type: webhook
      target: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
      message: "告警 {{alert_id}} 威胁等级 {{threat_level}}，源IP {{source_ip}}，请审批是否封禁"
    on_approve: block_ip              # 批准后执行的步骤 id
    on_reject: close_alert            # 拒绝后执行的步骤 id

  - id: block_ip
    name: "封禁源 IP"
    method: POST
    path: "/api/v1/firewall/block"
    body:
      ip: "{{source_ip}}"
      reason: "Alert {{alert_id}}: {{threat_level}} threat"
      operator: "{{operator_id}}"
      approval_id: "{{approval.approve_block.id}}"
    expect:
      status: 201

  - id: close_alert
    name: "关闭告警"
    method: PUT
    path: "/api/v1/alerts/{{alert_id}}/status"
    body:
      status: "closed"
      operator: "{{operator_id}}"
    expect:
      status: 200

output:
  summary: "告警 {{alert_id}} 已处理。威胁等级: {{threat_level}}"
  fields:
    - threat_level
    - source_ip
```

### 新增字段说明

| 字段 | 位置 | 说明 |
|------|------|------|
| `retry.max_attempts` | step | 最大重试次数（默认 0） |
| `retry.backoff_seconds` | step | 退避间隔列表 [1, 2, 4] |
| `retry.retry_on` | step | 触发重试的条件: [timeout, 5xx] |
| `type: approval` | step | 审批关卡步骤 |
| `timeout` | approval step | 等待审批超时秒数 |
| `timeout_action` | approval step | 超时后动作: escalate/auto_approve/auto_reject |
| `notify.type` | approval step | 通知方式: webhook/email |
| `notify.target` | approval step | webhook URL 或 email 地址 |
| `notify.message` | approval step | 通知消息模板（含 {{变量}}） |
| `on_approve` | approval step | 批准后跳转的步骤 id |
| `on_reject` | approval step | 拒绝后跳转的步骤 id |

### Auth Config 新增字段

```yaml
profiles:
  mss_prod:
    base_url: "https://mss.example.com"
    auth_type: "login"
    login_url: "/api/v1/auth/login"
    login_body: { username: "...", password: "..." }
    token_path: "$.data.token"
    token_header: "Authorization"
    token_prefix: "Bearer "
    verify_ssl: false                  # 新增：本地部署自签名证书支持
```

---

## 6. 审批机制设计

### 6.1 状态机

```
执行中 → 遇到 approval step → awaiting_approval（暂停）
                                    │
                      ┌─────────────┼─────────────┐
                      │             │             │
                  人工批准      人工拒绝       超时
                      │             │             │
                 执行 on_approve  执行 on_reject  执行 timeout_action
```

### 6.2 暂停与恢复

**暂停**：
1. Executor 遇到 `type: approval` 步骤
2. 保存当前执行状态（context、step_index）到 `data/mss_executions/` 记录
3. 执行状态标记为 `awaiting_approval`
4. 通过 webhook 发送审批通知到企业微信/钉钉

**恢复**：
```bash
# CLI 方式
python -m src.mss resume --execution-id <id> --decision approve --approver "张三"

# Web API 方式
POST /api/mss/executions/<id>/approve
POST /api/mss/executions/<id>/reject
```

### 6.3 通知模板（企业微信 webhook）

```json
{
  "msgtype": "markdown",
  "markdown": {
    "content": "## MSS SOP 审批请求\n> **SOP**: 告警处理\n> **告警ID**: ALT-12345\n> **威胁等级**: 高危\n> **源IP**: 10.0.0.1\n\n请点击审批：<http://localhost:8000/mss/executions/2026-06-01/handle_alert_143022>"
  }
}
```

### 6.4 审计要求

执行记录必须包含审批元数据：
```json
{
  "step_id": "approve_block",
  "type": "approval",
  "status": "approved",
  "approver": "zhangsan",
  "decision_time": "2026-06-01T14:35:00Z",
  "notification_sent": "2026-06-01T14:30:00Z",
  "justification": "确认封禁"
}
```

符合 GB/T 22239（等级保护）对安全响应操作的可审计性要求。

---

## 7. 技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| 动作捕捉 | **Playwright** + HAR 录制 | 无证书配置、HAR 标准格式、内置回放 |
| HTTP 客户端 | httpx (async) | 原生 async，与 Sanic 兼容 |
| SOP 定义 | YAML | 人类可读，便于版本管理 |
| 工作流引擎 | **自定义增强** | 20-50 SOP 规模不需要 Temporal/Prefect |
| JSONPath | 自实现（简化版） | 只需 `$.a.b[0].c`，避免重依赖 |
| 通知 | webhook（企微/钉钉） | 国内安全运营主流集成方式 |
| Agent 调度 | Claude Agent SDK | 复用项目现有 Skill + Agent |
| Web 框架 | Sanic | 复用项目现有框架 |

---

## 8. 目录结构

```
auto-research/
├── scripts/
│   ├── mss_record.py               # Playwright HAR 录制启动器（替代 mitmproxy）
│   └── mss_capture.py              # (保留) mitmproxy 方式备选
├── addons/
│   └── mitmproxy_mss_capture.py    # (保留) mitmproxy addon 备选
├── config/
│   ├── mss_sops/                   # SOP 定义 (YAML)
│   └── mss_auth.yaml               # 认证配置 (gitignored)
├── data/
│   ├── mss_captures/               # HAR/JSON 捕捉记录
│   └── mss_executions/             # 执行记录（含审批状态）
├── src/
│   └── mss/
│       ├── auth.py                 # 认证（+verify_ssl）
│       ├── substitution.py         # 模板替换 + JSONPath
│       ├── executor.py             # SOP 执行器（+retry/approval/resume）
│       └── __main__.py             # CLI（+resume 命令）
├── .claude/skills/
│   ├── mss-capture/                # HAR → SOP 生成 Skill
│   └── mss-sop/                    # SOP 执行 Skill
└── docs/
    └── mss_architecture.md         # 本文档
```

---

## 9. 与 v1 原型的差异

| 组件 | v1 (原型) | v2 (调研后) | 变更原因 |
|------|-----------|-------------|---------|
| 捕捉方式 | mitmproxy proxy | **Playwright HAR 录制** | 无需证书配置，用户体验好 |
| 步骤重试 | 无 | **retry 字段** | 网络抖动是主要失败原因 |
| 人工审批 | 无 | **approval 步骤类型** | 人机协同是核心需求 |
| 通知 | 无 | **webhook (企微/钉钉)** | 国内安全运营主流方式 |
| SSL 验证 | 默认验证 | **支持 verify_ssl: false** | 本地部署自签名证书 |
| 暂停恢复 | 无 | **resume 命令/API** | 审批后恢复执行 |
| 执行状态 | success/failed | **+awaiting_approval** | 审批暂停状态 |
