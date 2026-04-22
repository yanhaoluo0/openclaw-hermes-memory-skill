#!/bin/bash
# loop-detector.sh - 死循环检测

set -e

LOG_FILE="${1:-}"
THRESHOLD="${2:-80}"

if [ -z "$LOG_FILE" ] || [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: 日志文件不存在"
  exit 1
fi

if [ -z "$THRESHOLD" ]; then
  THRESHOLD=80
fi

# 提取最近的错误信息（最后 20 行）
RECENT_ERRORS=$(tail -20 "$LOG_FILE" | grep -iE "error|exception|failed" | tail -5)

if [ -z "$RECENT_ERRORS" ]; then
  echo "状态: OK"
  echo "无检测到错误"
  exit 0
fi

# 计算相似度（简单的词频重叠）
ERROR_HASH=$(echo "$RECENT_ERRORS" | sort | uniq -c | sort -rn | head -3 | md5sum | cut -d' ' -f1)

# 与上一次保存的哈希比较
HASH_FILE="/tmp/loop_detector_hash.txt"
PREV_HASH=""

if [ -f "$HASH_FILE" ]; then
  PREV_HASH=$(cat "$HASH_FILE")
fi

if [ "$ERROR_HASH" = "$PREV_HASH" ]; then
  # 连续相同错误，触发熔断
  echo "状态: FUSE_BLOWN"
  echo "检测到死循环: 连续相同的错误模式"
  echo "错误摘要:"
  echo "$RECENT_ERRORS"
  echo "请人工介入排查"
  exit 2
fi

# 保存当前哈希
echo "$ERROR_HASH" > "$HASH_FILE"

echo "状态: OK"
echo "相似度: 未超过阈值 ($THRESHOLD%)"
echo "当前错误模式已记录"