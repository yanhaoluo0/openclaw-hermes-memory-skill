#!/bin/bash
# context-assemble.sh - 上下文组装（从 Hermes 提取相关规范）

set -e

WORK_ORDER_ID="${1:-}"
OUTPUT_DIR="${2:-./context_packages}"

if [ -z "$WORK_ORDER_ID" ]; then
  echo "用法: context-assemble.sh <工单ID> [输出目录]"
  exit 1
fi

# Hermes 接口（当前为占位实现）
# 实际实现需要连接到 Hermes 增量索引服务
HERMES_HOST="${HERMES_HOST:-http://localhost:8080}"
HERMES_ENDPOINT="$HERMES_HOST/api/extract"

echo "从 Hermes 提取上下文..."
echo "工单ID: $WORK_ORDER_ID"
echo "输出目录: $OUTPUT_DIR"

# 创建输出目录
mkdir -p "$OUTPUT_DIR/$WORK_ORDER_ID"

# TODO: 实现 Hermes API 调用
# curl -X POST "$HERMES_ENDPOINT" \
#   -H "Content-Type: application/json" \
#   -d "{\"work_order_id\": \"$WORK_ORDER_ID\"}" \
#   -o "$OUTPUT_DIR/$WORK_ORDER_ID/hermes_response.json"

# 当前实现：创建占位文件
cat > "$OUTPUT_DIR/$WORK_ORDER_ID/AGENTS.md" <<'EOF'
# AGENTS.md - 项目规范

本文件由 context-assemble.sh 自动生成
实际内容应从 Hermes 增量索引提取
EOF

cat > "$OUTPUT_DIR/$WORK_ORDER_ID/CODING_STANDARDS.md" <<'EOF'
# CODING_STANDARDS.md - 编码规范

本文件由 context-assemble.sh 自动生成
实际内容应从 Hermes 增量索引提取
EOF

cat > "$OUTPUT_DIR/$WORK_ORDER_ID/TESTS.md" <<'EOF'
# TESTS.md - 测试要求

本文件由 context-assemble.sh 自动生成
实际内容应从 Hermes 增量索引提取
EOF

cat > "$OUTPUT_DIR/$WORK_ORDER_ID/acceptance_criteria.md" <<'EOF'
# acceptance_criteria.md - 验收标准

本文件由 context-assemble.sh 自动生成
实际内容应从 Hermes 增量索引提取
EOF

echo "上下文包已组装: $OUTPUT_DIR/$WORK_ORDER_ID/"
echo "文件列表:"
ls -la "$OUTPUT_DIR/$WORK_ORDER_ID/"