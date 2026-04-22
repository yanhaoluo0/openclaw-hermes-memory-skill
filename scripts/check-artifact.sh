#!/bin/bash
# check-artifact.sh - 产物校验（防伪成功）

set -e

ARTIFACT_PATH="${1:-}"

if [ -z "$ARTIFACT_PATH" ]; then
  echo "ERROR: artifact_path 为空"
  echo "状态: FAILED"
  echo "原因: Agent 声明完成但未提供产物路径"
  exit 1
fi

# 检查文件是否存在
if [ ! -e "$ARTIFACT_PATH" ]; then
  echo "ERROR: 产物文件不存在"
  echo "路径: $ARTIFACT_PATH"
  echo "状态: FAILED"
  exit 1
fi

# 检查文件是否为空
if [ ! -s "$ARTIFACT_PATH" ]; then
  echo "ERROR: 产物文件为空"
  echo "路径: $ARTIFACT_PATH"
  echo "状态: FAILED"
  exit 1
fi

# 检查是否为目录（artifact 应为文件）
if [ -d "$ARTIFACT_PATH" ]; then
  echo "ERROR: artifact_path 是目录而非文件"
  echo "路径: $ARTIFACT_PATH"
  echo "状态: FAILED"
  exit 1
fi

# 获取文件大小
FILE_SIZE=$(stat -c%s "$ARTIFACT_PATH" 2>/dev/null || stat -f%z "$ARTIFACT_PATH" 2>/dev/null)

echo "SUCCESS: 产物校验通过"
echo "路径: $ARTIFACT_PATH"
echo "大小: $FILE_SIZE bytes"
echo "状态: VERIFIED"