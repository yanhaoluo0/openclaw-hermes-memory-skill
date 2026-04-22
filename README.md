# Multi-Agent Collaboration System

标准化多智能体协同开发 Skill，基于 Hook 体系实现确定性工单流转。

## 核心特性

- **PM 无状态设计** - 每次从 SQLite 重建状态
- **7 个确定性 Hook** - 白名单校验、语法检查、产物验证等全部脚本化
- **角色权限隔离** - Frontend/Backend/Test/DevOps 命令白名单分离
- **防幻觉机制** - 产物校验、死循环熔断、堆栈压缩

## 目录结构

```
├── SKILL.md                    # 技能主定义
├── scripts/                   # Shell 脚本
│   ├── init-db.sh            # SQLite 初始化
│   ├── create-work-order.sh  # 创建工单
│   ├── command-whitelist.sh  # 命令白名单校验
│   ├── check-artifact.sh     # 产物校验
│   ├── loop-detector.sh      # 死循环检测
│   ├── trace-compressor.sh    # 堆栈压缩
│   └── context-assemble.sh    # 上下文组装
├── hooks/                     # Python Hooks
│   ├── pre_command_execution.py  # 前置命令拦截
│   ├── dry_run_validation.py     # AST 语法检查
│   └── post_artifact_verify.py   # 产物实体校验
├── prompts/                   # Agent 角色定义
│   ├── pm.md                 # PM 角色
│   ├── frontend-agent.md     # Frontend Agent
│   ├── backend-agent.md      # Backend Agent
│   └── test-agent.md         # Test Agent
├── context/
│   └── work-order-template.md  # 工单填空模板
└── references/
    └── architecture.md         # 架构说明
```

## 快速开始

### 1. 初始化数据库

```bash
bash scripts/init-db.sh
```

### 2. 创建工单

```bash
DB_PATH=./work_orders.db bash scripts/create-work-order.sh "实现登录页面" frontend "包含表单验证"
```

### 3. 测试命令白名单

```bash
# 通过
bash scripts/command-whitelist.sh frontend "npm install"

# 拒绝（不在白名单）
bash scripts/command-whitelist.sh frontend "docker ps"

# 拦截（危险命令）
bash scripts/command-whitelist.sh frontend "rm -rf /"
```

### 4. 测试产物校验

```bash
# 空路径 → 失败
bash scripts/check-artifact.sh ""

# 存在文件 → 通过
bash scripts/check-artifact.sh "SKILL.md"
```

## Hook 体系

| Hook | 层级 | 作用 | 实现 |
|------|------|------|------|
| pre_task_dispatch | PM | 人类确认后才行 | 脚本检查 |
| context_assemble | PM | 精准裁剪上下文 | Hermes 查询 |
| pre_command_execution | 执行 | 白名单校验 | 正则匹配 |
| dry_run_validation | 执行 | AST 语法检查 | Python AST |
| post_artifact_verify | QA | 产物存在性校验 | 文件系统检查 |
| infinite_loop_breaker | 熔断 | 死循环检测 | 日志相似度 |
| trace_compression | 熔断 | 堆栈压缩 | 规则提取 |

## 工单状态流转

```
pending → in_progress → review → testing → done
                  ↓           ↓
                failed    (retry ≤ 2)
                  ↓
              (人工介入)
```

## 角色命令白名单

| 角色 | 允许命令 | 禁止命令 |
|------|---------|---------|
| frontend | npm, npx, git, node | docker, git push |
| backend | npm, git, docker, python3 | rm -rf / |
| test | pytest, playwright, npm test | 生产级操作 |
| devops | docker, kubectl, ssh | 常规开发 |

## 依赖

- `bash` - Shell 脚本
- `sqlite3` - 数据库
- `python3` - Hook 脚本

## 核心约束

1. 同一时刻只允许 1 个 Claude Code CLI 运行
2. 单个工单开发时长不超过 30 分钟
3. context_package 大小不超过 30KB
4. Agent 输出必须结构化（填空模板）

## 测试示例

| 文件 | 说明 |
|------|------|
| `examples/frontend-e2e-example.md` | 前端 Playwright E2E 测试伪代码示例，覆盖登录、用户管理、商品、订单等模块 |
| `examples/backend-api-example.md` | 后端 pytest 接口测试伪代码示例，覆盖认证、用户、商品、订单等模块 |

## 相关文档

- [SKILL.md](SKILL.md) - 完整技能定义
- [references/architecture.md](references/architecture.md) - 架构详情
- [prompts/pm.md](prompts/pm.md) - PM 角色定义