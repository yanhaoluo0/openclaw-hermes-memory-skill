#!/bin/bash
# init-db.sh - 初始化 SQLite 工单数据库

set -e

DB_PATH="${1:-./work_orders.db}"

echo "初始化 SQLite 数据库: $DB_PATH"

# 创建数据库和表
sqlite3 "$DB_PATH" <<'EOF'
CREATE TABLE IF NOT EXISTS work_orders (
  id TEXT PRIMARY KEY,
  parent_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'review', 'testing', 'done', 'failed')),
  assigned_role TEXT CHECK(assigned_role IN ('pm', 'frontend', 'backend', 'test', 'devops')),
  blocked_by_id TEXT,
  context_package TEXT,
  artifact_path TEXT,
  execution_log TEXT,
  estimated_minutes INTEGER DEFAULT 30,
  actual_minutes INTEGER,
  retry_count INTEGER DEFAULT 0,
  human_confirmed INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT,
  FOREIGN KEY (parent_id) REFERENCES work_orders(id),
  FOREIGN KEY (blocked_by_id) REFERENCES work_orders(id)
);

CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_orders_assigned_role ON work_orders(assigned_role);
CREATE INDEX IF NOT EXISTS idx_work_orders_parent_id ON work_orders(parent_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_blocked_by_id ON work_orders(blocked_by_id);
EOF

echo "数据库初始化完成: $DB_PATH"
echo "工单表已创建，共 14 个字段"