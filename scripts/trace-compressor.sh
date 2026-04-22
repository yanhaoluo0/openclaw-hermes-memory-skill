#!/bin/bash
# trace-compressor.sh - 堆栈压缩

set -e

INPUT="${1:-}"
OUTPUT="${2:-}"

if [ -z "$INPUT" ]; then
  echo "用法: trace-compressor.sh <输入文件> [输出文件]"
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "ERROR: 输入文件不存在"
  exit 1
fi

# 提取关键行
# 1. Exception 类型和消息
# 2. 文件路径和行号
# 3. 最内层调用栈

COMPRESSED=$(cat "$INPUT" | grep -E "^(\s*(at|Exception|Error|Caused by)|.*\.py.*:.*|.*\.js.*:.*)" | head -30 | sed 's/^[[:space:]]*/  /')

# 如果输出文件指定，写入文件
if [ -n "$OUTPUT" ]; then
  echo "$COMPRESSED" > "$OUTPUT"
  echo "压缩完成: $OUTPUT"
else
  # 否则输出到 stdout
  echo "=== 压缩后的堆栈跟踪 ==="
  echo "$COMPRESSED"
fi

# 统计原始行数和压缩后行数
ORIG_LINES=$(wc -l < "$INPUT")
COMP_LINES=$(echo "$COMPRESSED" | wc -l)
RATIO=$((100 * COMP_LINES / ORIG_LINES))

echo ""
echo "压缩率: $RATIO% (原始: $ORIG_LINES 行, 压缩后: $COMP_LINES 行)"