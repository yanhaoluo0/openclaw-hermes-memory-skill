#!/bin/bash
# block-until-confirm.sh - Human 确认后才允许工单流转

set -e

DB_PATH="${DB_PATH:-./work_orders.db}"
WORK_ORDER_ID="${1:-}"

if [ -z "$WORK_ORDER_ID" ]; then
  echo "用法: block-until-confirm.sh <工单ID>"
  exit 1
fi

# 检查 human_confirmed 字段是否为 1 或 true
CONFIRMED=$(sqlite3 "$DB_PATH" "SELECT human_confirmed FROM work_orders WHERE id='$WORK_ORDER_ID';" 2>/dev/null || echo "")

if [ "$CONFIRMED" = "1" ] || [ "$CONFIRMED" = "true" ]; then
  echo "CONFIRMED"
  exit 0
else
  echo "PENDING"
  exit 1
fi