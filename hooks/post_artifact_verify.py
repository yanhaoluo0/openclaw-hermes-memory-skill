#!/usr/bin/env python3
"""
post_artifact_verify.py - 产物实体校验

当 Agent 标记任务为 Done 时，验证产物是否真实存在。
治疗大模型的"伪装成功"幻觉。
"""

import sys
import os
import json
import csv


def verify_artifact(artifact_path: str, min_size: int = 10) -> tuple[bool, str]:
    """
    验证产物文件是否存在且有效

    Args:
        artifact_path: 产物文件路径
        min_size: 最小文件大小（字节），默认 10

    Returns:
        (success, message)
    """
    if not artifact_path:
        return False, "artifact_path 为空"

    if not os.path.exists(artifact_path):
        return False, f"文件不存在: {artifact_path}"

    if not os.path.isfile(artifact_path):
        return False, f"路径是目录而非文件: {artifact_path}"

    size = os.path.getsize(artifact_path)
    if size < min_size:
        return False, f"文件太小 ({size} bytes, 最小 {min_size})"

    return True, f"OK ({size} bytes)"


def verify_json_artifact(artifact_path: str) -> tuple[bool, str]:
    """验证 JSON 文件结构"""
    success, msg = verify_artifact(artifact_path)
    if not success:
        return success, msg

    try:
        with open(artifact_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, "JSON 结构有效"
    except json.JSONDecodeError as e:
        return False, f"JSON 解析失败: {e}"


def verify_markdown_artifact(artifact_path: str) -> tuple[bool, str]:
    """验证 Markdown 文件结构"""
    success, msg = verify_artifact(artifact_path)
    if not success:
        return success, msg

    try:
        with open(artifact_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 基本 Markdown 检查
        lines = content.split('\n')
        has_content = any(len(line.strip()) > 0 for line in lines)

        if not has_content:
            return False, "Markdown 文件为空"

        # 检查是否混杂了代码块以外的内容
        if content.count('```') >= 2:
            # 有代码块，检查是否有实际描述
            code_blocks = content.count('```')
            if code_blocks % 2 != 0:
                return False, "不匹配的 Markdown 代码块"

        return True, "Markdown 结构有效"
    except Exception as e:
        return False, str(e)


def main():
    if len(sys.argv) < 2:
        print("用法: post_artifact_verify.py <artifact_path> [类型]")
        print("  类型: auto (默认), json, markdown, file")
        sys.exit(1)

    artifact_path = sys.argv[1]
    file_type = sys.argv[2] if len(sys.argv) > 2 else "auto"

    # 根据扩展名自动判断类型
    if file_type == "auto":
        ext = os.path.splitext(artifact_path)[1].lower()
        if ext == '.json':
            file_type = "json"
        elif ext in ['.md', '.markdown']:
            file_type = "markdown"
        else:
            file_type = "file"

    if file_type == "json":
        success, msg = verify_json_artifact(artifact_path)
    elif file_type == "markdown":
        success, msg = verify_markdown_artifact(artifact_path)
    else:
        success, msg = verify_artifact(artifact_path)

    if success:
        print(f"VERIFIED: {artifact_path}")
        print(f"Message: {msg}")
        sys.exit(0)
    else:
        print(f"FAILED: {artifact_path}")
        print(f"Message: {msg}")
        print("状态: IN_PROGRESS (打回重新处理)")
        sys.exit(1)


if __name__ == '__main__':
    main()