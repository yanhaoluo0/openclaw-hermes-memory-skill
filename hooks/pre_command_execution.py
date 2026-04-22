#!/usr/bin/env python3
"""
pre_command_execution.py - 命令白名单前置拦截

在 Agent 调用系统命令前，校验命令是否在白名单内。
基于 role 的权限控制，阻止危险操作。

Usage:
    python3 pre_command_execution.py <role> <command>
"""

import sys
import re
import subprocess


# 角色白名单配置
WHITELIST = {
    'frontend': [
        r'^npm$', r'^npx$', r'^yarn$', r'^pnpm$',
        r'^git$', r'^node$', r'^python3$', r'^node_modules/\.bin/',
        r'^git\s+status$', r'^git\s+diff$', r'^git\s+add$', r'^git\s+commit',
        r'^git\s+checkout', r'^git\s+branch'
    ],
    'backend': [
        r'^npm$', r'^npx$', r'^yarn$', r'^pnpm$',
        r'^git$', r'^node$', r'^python3$', r'^python$',
        r'^docker$', r'^docker-compose$', r'^kubectl$',
        r'^curl$', r'^wget$', r'^ps$', r'^grep$', r'^find$',
        r'^chmod$', r'^chown$', r'^mkdir$', r'^rm$', r'^touch$', r'^cat$', r'^echo$', r'^tee$',
        r'^node_modules/\.bin/'
    ],
    'test': [
        r'^npm$', r'^npx$', r'^yarn$', r'^pnpm$',
        r'^git$', r'^node$', r'^python3$', r'^pytest$',
        r'^playwright$', r'^curl$', r'^wget$',
        r'^jest$', r'^vitest$', r'^mocha$', r'^rspec$',
        r'^node_modules/\.bin/'
    ],
    'devops': [
        r'^npm$', r'^npx$', r'^yarn$', r'^pnpm$',
        r'^git$', r'^node$', r'^python3$', r'^docker$',
        r'^docker-compose$', r'^kubectl$', r'^ssh$',
        r'^systemctl$', r'^ps$', r'^grep$', r'^find$',
        r'^chmod$', r'^chown$', r'^mkdir$', r'^rm$', r'^cat$', r'^echo$', r'^tee$',
        r'^journalctl$', r'^service$', r'^htop$', r'^top$', r'^df$', r'^du$'
    ],
    'pm': [
        # PM 角色通常不执行命令，但允许查看
        r'^git$', r'^ls$', r'^cat$', r'^find$', r'^grep$'
    ]
}

# 危险命令模式（绝对拦截）
DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s+/',
    r'mkfs',
    r'fdisk',
    r'dd\s+if=',
    r':\(\)\s*\{\s*:\|:&\s*\}\s*;',
    r'>\s*/dev/sd',
    r'shutdown',
    r'reboot',
    r'init\s+6',
]


def is_dangerous(command: str) -> bool:
    """检查是否为危险命令"""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            return True
    return False


def is_allowed(role: str, command: str) -> tuple[bool, str]:
    """检查命令是否在白名单内"""
    if role not in WHITELIST:
        return False, f"未知角色: {role}"

    for pattern in WHITELIST[role]:
        if re.match(pattern, command.strip()):
            return True, f"OK (matched: {pattern})"

    return False, f"不在白名单内"


def main():
    if len(sys.argv) < 3:
        print("用法: pre_command_execution.py <role> <command>")
        print(f"可用角色: {', '.join(WHITELIST.keys())}")
        sys.exit(1)

    role = sys.argv[1]
    command = sys.argv[2]

    # 1. 首先检查危险命令
    if is_dangerous(command):
        print("REJECTED: 危险命令模式 detected")
        print(f"命令: {command}")
        print("操作: 已拦截，不消耗 LLM token")
        sys.exit(1)

    # 2. 检查白名单
    allowed, reason = is_allowed(role, command)

    if allowed:
        print(f"APPROVED: {command}")
        print(f"Role: {role}")
        print(f"Reason: {reason}")
        sys.exit(0)
    else:
        print("REJECTED: 命令不在白名单中")
        print(f"命令: {command}")
        print(f"角色: {role}")
        print(f"原因: {reason}")
        print(f"允许的命令: {', '.join(WHITELIST.get(role, []))}")
        sys.exit(1)


if __name__ == '__main__':
    main()