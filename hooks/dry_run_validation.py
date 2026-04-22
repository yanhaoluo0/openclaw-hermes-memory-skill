#!/usr/bin/env python3
"""
dry_run_validation.py - AST 语法预检

在 Agent 宣称代码编写完毕前，检查语法是否正确。
支持: Python (.py), JavaScript/TypeScript (.js/.ts/.jsx/.tsx), Shell (.sh)
"""

import sys
import os
import subprocess
import ast


def validate_python(file_path: str) -> tuple[bool, str]:
    """检查 Python 文件语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, "OK"
    except SyntaxError as e:
        return False, f"SyntaxError: {e.filename}:{e.lineno} {e.msg}"
    except Exception as e:
        return False, f"Error: {e}"


def validate_shell(file_path: str) -> tuple[bool, str]:
    """检查 Shell 脚本语法 (bash -n)"""
    try:
        result = subprocess.run(
            ['bash', '-n', file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, "OK"
        else:
            return False, result.stderr
    except FileNotFoundError:
        return False, "bash not found"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def validate_typescript(file_path: str) -> tuple[bool, str]:
    """检查 TypeScript 文件语法 (需要 tsc)"""
    # 提取单个文件进行快速检查
    try:
        # 简单检查: 不允许 Markdown 代码块标记
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if content.strip().startswith('```'):
            return False, "File starts with Markdown code block - not pure code"

        # 检查明显的语法问题
        lines = content.split('\n')
        brace_count = 0
        paren_count = 0

        for line in lines:
            # 跳过注释
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                continue

            for char in line:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1

        if brace_count != 0:
            return False, f"Unbalanced braces: {brace_count}"
        if paren_count != 0:
            return False, f"Unbalanced parentheses: {paren_count}"

        return True, "OK"
    except Exception as e:
        return False, str(e)


def validate_file(file_path: str) -> tuple[bool, str]:
    """根据文件扩展名选择验证方法"""
    if not os.path.exists(file_path):
        return False, "File not found"

    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.py':
        return validate_python(file_path)
    elif ext in ['.sh', '.bash']:
        return validate_shell(file_path)
    elif ext in ['.ts', '.tsx', '.js', '.jsx']:
        return validate_typescript(file_path)
    else:
        return True, "Unsupported file type (no validation)"


def main():
    if len(sys.argv) < 2:
        print("用法: dry_run_validation.py <文件路径>")
        sys.exit(1)

    file_path = sys.argv[1]
    success, message = validate_file(file_path)

    if success:
        print(f"OK: {file_path}")
        sys.exit(0)
    else:
        print(f"FAILED: {file_path}")
        print(f"Reason: {message}")
        sys.exit(1)


if __name__ == '__main__':
    main()