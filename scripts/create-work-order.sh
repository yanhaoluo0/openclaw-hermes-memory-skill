#!/bin/bash
# create-work-order.sh - 创建新工单

DB_PATH="${DB_PATH:-./work_orders.db}"
TITLE="${1:-}"
ROLE="${2:-frontend}"
DESCRIPTION="${3:-}"
PARENT_ID="${4:-}"
BLOCKED_BY="${5:-}"
ESTIMATED_MINUTES="${6:-30}"

if [ -z "$TITLE" ]; then
  echo "用法: create-work-order.sh <标题> [角色] [描述] [父工单ID] [阻塞工单ID] [预估分钟]"
  echo "示例: create-work-order.sh \"实现登录页面\" frontend \"包含表单验证\""
  exit 1
fi

# 生成 UUID
PYTHON_CMD=""
for py in python3 python /d/Anaconda/python /c/Users/A/AppData/Local/Microsoft/WindowsApps/python3; do
  if command -v $py > /dev/null 2>&1; then
    PYTHON_CMD="$py"
    break
  fi
done

if [ -n "$PYTHON_CMD" ]; then
  ID=$($PYTHON_CMD -c "import uuid; print(uuid.uuid4())" 2>/dev/null)
fi

if [ -z "$ID" ]; then
  ID="$$-$(date +%s%N)"
fi

# 处理 NULL 值
PARENT_VAL="NULL"
if [ -n "$PARENT_ID" ]; then
  PARENT_VAL="'$PARENT_ID'"
fi

DESC_VAL="NULL"
if [ -n "$DESCRIPTION" ]; then
  DESC_VAL="'$DESCRIPTION'"
fi

BLOCKED_VAL="NULL"
if [ -n "$BLOCKED_BY" ]; then
  BLOCKED_VAL="'$BLOCKED_BY'"
fi

# SQL 插入
SQL="INSERT INTO work_orders (id, parent_id, title, description, status, assigned_role, blocked_by_id, estimated_minutes, retry_count) VALUES ('$ID', $PARENT_VAL, '$TITLE', $DESC_VAL, 'pending', '$ROLE', $BLOCKED_VAL, $ESTIMATED_MINUTES, 0);"

sqlite3 "$DB_PATH" "$SQL"

echo "工单创建成功:"
echo "  ID: $ID"
echo "  标题: $TITLE"
echo "  角色: $ROLE"
echo "  状态: pending"

# 输出 JSON 格式方便脚本解析
echo ""
echo "{\"id\":\"$ID\",\"title\":\"$TITLE\",\"status\":\"pending\",\"assigned_role\":\"$ROLE\"}"