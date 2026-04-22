# Multi-Agent Collaboration System - 架构说明

## 系统定位

**核心定位**: Human 作为最终决策者，PM 作为战略协调者，Agent 作为执行单元的多智能体协同开发框架。

## 设计目标

1. **Human 深度参与设计阶段，执行阶段低干预**
2. **通过小工单、短上下文、可控调用避免 LLM 降智**
3. **经验可沉淀，问题可追溯**

## 角色定义

| 角色 | 职责 | 约束 |
|------|------|------|
| Human | 确认方案，最终验收，介入超时/重大问题 | 最终决策者 |
| PM | 规划、调度、监控、协调 | 无状态，每次从 DB 重建 |
| Frontend Agent | 前端开发，Playwright 测试 | 命令白名单限制 |
| Backend Agent | 后端开发，接口测试 | 命令白名单限制 |
| Test Agent | 验证脚本执行，Child Issue 创建 | 判定通过/失败 |

## 核心约束

1. **同一时刻只允许 1 个 Claude Code CLI 运行**
2. **单个工单开发时长不超过 30 分钟**
3. **context_package 大小不超过 30KB**
4. **Agent 设计输出必须结构化（填空式模板）**
5. **PM 采用无状态设计，状态全存 SQLite**

## 数据存储

### SQLite 工单表 (work_orders)

```sql
CREATE TABLE work_orders (
  id TEXT PRIMARY KEY,
  parent_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending',
  assigned_role TEXT,
  blocked_by_id TEXT,
  context_package TEXT,
  artifact_path TEXT,
  execution_log TEXT,
  estimated_minutes INTEGER DEFAULT 30,
  actual_minutes INTEGER,
  retry_count INTEGER DEFAULT 0,
  human_confirmed INTEGER DEFAULT 0,
  created_at TEXT,
  updated_at TEXT,
  completed_at TEXT
);
```

### Hermes 存储

- 增量索引
- 经验沉淀
- 规范文档

## 流程设计

### 完整流程

```
Human 确认整体方案
    │
    ├── PM 写入 Hermes: 完整开发计划
    ├── PM 写入 SQLite: 主工单 + 子工单 (含 blocked_by 关系)
    └── PM 通知对应 Agent

Agent 领取工单
    │
    ├── 做设计 (结构化输出到 context_package/design.md)
    ├── 调用 Claude Code CLI (加载 context_package)
    ├── 执行完成后写验证脚本
    └── 通知 PM 完成

Test Agent 验证
    │
    ├── 通过 → 归档 artifact → PM 更新状态
    └── 不通过 → 创建 Child Issue (继承诊断链)

独立定时任务监控超时
    │
    ├── 未超时 → 继续等待
    └── 超时 2× 预估时长 → PM 上报 Human
```

### 工单状态流转

```
pending → in_progress → review → testing → done
                  ↓           ↓
                failed    (retry <= 2)
                  ↓
              (人工介入)
```

### Child Issue 机制

- 最多继承 3 层
- 同一问题最多重试 2 次
- 2 次后仍失败 → 引入 Human

继承内容:
- 问题描述
- 诊断历史 (摘要，非全量)
- 未尝试的解决方案

## Hook 体系

所有 Hook 都是确定性脚本，无 LLM 判断。

| Hook | 层级 | 作用 | 实现 |
|------|------|------|------|
| pre_task_dispatch | PM | 人类确认后才行 | 检查 human_confirmed 标记 |
| context_assemble | PM | 精准裁剪上下文 | Hermes 查询 |
| pre_command_execution | 执行 | 白名单校验 | 正则匹配 |
| dry_run_validation | 执行 | AST 语法检查 | Python AST |
| post_artifact_verify | QA | 产物存在性校验 | 文件系统检查 |
| infinite_loop_breaker | 熔断 | 死循环检测 | 日志相似度 |
| trace_compression | 熔断 | 堆栈压缩 | 规则提取 |

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                      Human (人)                         │
│         确认方案 + 最终验收 + 介入超时/重大问题          │
└─────────────────────────┬───────────────────────────────┘
                          │ 飞书
                          ▼
┌─────────────────────────────────────────────────────────┐
│  OpenClaw PM                                           │
│  ├── 设计阶段: 智能参与                                 │
│  ├── 编码阶段: 定时自动苏醒（独立 cron 任务触发）       │
│  ├── 读取: Hermes 增量索引                               │
│  └── 写入: Hermes (计划/经验/超时记录)                  │
└────┬──────────────┬────────────────────────────────────┘
     │              │
     ▼              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│    Frontend Agent       │    │    Backend Agent        │
│    ├── 做结构化设计     │    │    ├── 做结构化设计     │
│    ├── 调用 CLI          │    │    ├── 调用 CLI          │
│    └── 写 Playwright    │    │    └── 写接口测试       │
└───────────┬─────────────┘    └───────────┬─────────────┘
            │                              │
            └──────────────┬───────────────┘
                           ▼
            ┌─────────────────────────────┐
            │       Test Agent            │
            │       执行验证脚本           │
            └─────────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  SQLite: work_orders + context_package + artifact       │
│  Hermes: 增量索引 + 经验沉淀                              │
│  Claude Code CLI: 纯执行（小工单 + 预审 SQL）           │
└─────────────────────────────────────────────────────────┘
```

## 技术约束

1. **context_package 大小不超过 30KB**
2. **PM 采用无状态设计，状态全存 SQLite，每次苏醒从 SQLite 重建**
3. **超时监控为独立定时任务（非 PM 自身计时）**
4. **SQLite 状态更新必须同步写入执行日志**

## 测试策略

- 后端接口测试必须包含在 context_package 中
- 前端允许一定漏洞（Playwright 覆盖主要流程）

## 与飞书交互

PM 通过飞书通知 Human:
- 工单完成
- 超时报警
- 需要人工介入