---
name: multi-agent-collaboration
description: Multi-Agent 协同开发框架 - PM 工单管理 + Agent 执行 + Hooks 防幻觉
version: 1.0.0
---

# Multi-Agent Collaboration System

标准化多智能体协同开发框架，包含 PM 角色、工单管理、确定性 Hook 体系。

## 核心约束

- **同一时刻只允许 1 个 Claude Code CLI 运行**
- **单个工单开发时长不超过 30 分钟**
- **context_package 大小不超过 30KB**
- **Agent 设计输出必须结构化（填空式模板）**

## 系统架构

```
Human (人)
    │ 飞书
    ▼
┌─────────────────────────────────────┐
│  PM (无状态，每次从 SQLite 重建)      │
│  ├── 规划阶段: 智能参与                │
│  └── 编码阶段: 定时自动苏醒            │
└────┬────────────────────┬───────────┘
     │                    │
     ▼                    ▼
Frontend Agent        Backend Agent
├── 结构化设计         ├── 结构化设计
├── 调用 CLI          ├── 调用 CLI
└── 写 Playwright     └── 写接口测试
          │                    │
          └──────────┬──────────┘
                     ▼
            ┌─────────────────┐
            │   Test Agent    │
            │   执行验证脚本   │
            └────────┬────────┘
                     │
                     ▼
┌─────────────────────────────────────┐
│  SQLite: work_orders               │
│  Claude Code CLI: 纯执行           │
└─────────────────────────────────────┘
```

## Hook 体系

所有 Hook 都是**确定性脚本**，无 LLM 判断。

### 1. pre_task_dispatch (PM 层)

**作用**: 人类确认后才允许工单流转

**实现**: `scripts/block-until-confirm.sh` - 检查工单是否有 `human_confirmed` 标记

### 2. context_assemble (PM 层)

**作用**: 精准裁剪上下文，只包含当前任务相关文件

**实现**: `scripts/context-assemble.sh` - 根据工单 ID 从 Hermes 提取相关规范

### 3. pre_command_execution (执行层)

**作用**: 白名单校验，限制物理操作边界

**实现**: `scripts/command-whitelist.sh` - 正则匹配命令，拒绝非白名单命令

角色白名单:
- `frontend`: npm, npx, git status, git diff, git add, git commit (禁止 docker/git push)
- `backend`: git, docker, npm, python, node, curl (允许更多系统命令)
- `test`: pytest, npm test, playwright, curl
- `devops`: docker, kubectl, git, ssh, systemctl

### 4. dry_run_validation (执行层)

**作用**: AST 语法预检，避免混杂 Markdown 的非标准代码

**实现**: `hooks/dry_run_validation.py` - 用 py/pytsx/tsc 检查语法

### 5. post_artifact_verify (QA 层)

**作用**: 治疗"伪成功"幻觉，校验产物文件存在

**实现**: `scripts/check-artifact.sh` - 检查 artifact_path 文件存在且非空

### 6. infinite_loop_breaker (熔断层)

**作用**: 防止 Agent 在修 Bug 中死循环

**实现**: `scripts/loop-detector.sh` - 计算日志相似度，超过 80% 触发熔断

### 7. trace_compression (熔断层)

**作用**: 压缩报错堆栈，防止上下文污染

**实现**: `scripts/trace-compressor.sh` - 提取 Exception 关键行

## 工单流程

```
PM 创建工单
    │
    ├── [pre_task_dispatch: 人类确认?]
    │         ↓ No → 等待确认
    │         ↓ Yes
    │
    ├── [context_assemble: 组装上下文包]
    │
    ├── 状态 → in_progress
    │
    └── PM 通知 Agent

Agent 执行
    │
    ├── 做设计 (输出到 context_package/design.md)
    │
    ├── [pre_command_execution: 白名单校验]
    │         ↓ 拒绝 → 返回错误，不执行
    │         ↓ 通过
    │
    ├── 调用 Claude Code CLI
    │
    ├── [dry_run_validation: 语法检查]
    │         ↓ 失败 → 要求重写
    │         ↓ 通过
    │
    ├── 写验证脚本
    │
    ├── [post_artifact_verify: 产物校验]
    │         ↓ 不存在 → 打回 in_progress
    │         ↓ 存在
    │
    └── 通知 PM 完成

Test Agent 验证
    │
    ├── 通过 → Git 提交代码 → 归档 artifact → 状态 → done
    └── 不通过 → 创建 Child Issue (最多 3 层继承)

Git 提交规则:
- 分支名: `work-order/{work_order_id}`
- Commit Message 格式:
  ```
  [{工单ID}] {标题}

  - 测试通过: {验证方式} ({通过数}/{总数})
  - 产物: {artifact_path}
  - 耗时: {actual_minutes}min
  ```

超时监控 (独立 cron)
    │
    ├── 未超时 → 继续等待
    └── 超时 2× 预估时长 → PM 上报 Human
```

## Child Issue 机制

- 最多继承 3 层
- 同一问题最多重试 2 次
- 2 次后仍失败 → 引入 Human

## 关键脚本

| 脚本 | 用途 |
|------|------|
| `scripts/init-db.sh` | 初始化 SQLite 数据库 |
| `scripts/create-work-order.sh` | 创建新工单 |
| `scripts/command-whitelist.sh` | 命令白名单校验 |
| `scripts/check-artifact.sh` | 产物存在性校验 |
| `scripts/loop-detector.sh` | 死循环检测 |
| `scripts/trace-compressor.sh` | 堆栈压缩 |
| `hooks/dry_run_validation.py` | AST 语法检查 |

## 数据模型

### work_orders 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 工单 ID (UUID) |
| parent_id | TEXT | 父工单 ID |
| title | TEXT | 工单标题 |
| description | TEXT | 工单描述 |
| status | TEXT | pending/in_progress/review/testing/done/failed |
| assigned_role | TEXT | pm/frontend/backend/test/devops |
| blocked_by_id | TEXT | 阻塞工单 ID |
| context_package | TEXT | 上下文包路径 |
| artifact_path | TEXT | 产物路径 |
| execution_log | TEXT | 执行日志 |
| estimated_minutes | INTEGER | 预估时长 |
| actual_minutes | INTEGER | 实际时长 |
| retry_count | INTEGER | 重试次数 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |
| completed_at | TEXT | 完成时间 |

## 验证方式

```bash
# 1. 初始化数据库
bash scripts/init-db.sh

# 2. 创建测试工单
bash scripts/create-work-order.sh "实现登录页面" "frontend"

# 3. 测试命令白名单
bash scripts/command-whitelist.sh frontend "npm install"  # 应通过
bash scripts/command-whitelist.sh frontend "docker ps"   # 应拒绝

# 4. 测试产物校验
bash scripts/check-artifact.sh ""        # 应失败
bash scripts/check-artifact.sh "README.md"  # 应成功（如果文件存在）

# 5. 测试死循环检测
bash scripts/loop-detector.sh "logs/recent.log" 80  # 相似度阈值 80%
```

## 依赖

- `sqlite3` - 数据库
- `python3` - Hook 脚本
- `bash` - Shell 脚本
- `git` - 版本控制

## 参考

- `prompts/pm.md` - PM 角色定义
- `prompts/frontend-agent.md` - Frontend Agent
- `prompts/backend-agent.md` - Backend Agent
- `prompts/test-agent.md` - Test Agent
- `context/work-order-template.md` - 工单填空模板