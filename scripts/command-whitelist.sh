#!/bin/bash
# command-whitelist.sh - 命令白名单校验

set -e

ROLE="${1:-}"
COMMAND="${2:-}"

if [ -z "$ROLE" ] || [ -z "$COMMAND" ]; then
  echo "用法: command-whitelist.sh <角色> <命令>"
  echo "角色: frontend, backend, test, devops"
  exit 1
fi

# 提取命令主体（去除参数）
CMD_BASE=$(echo "$COMMAND" | awk '{print $1}')
CMD_ARGS=$(echo "$COMMAND" | cut -d' ' -f2-)

# 白名单定义
ALLOWED_COMMANDS_frontend="npm|npx|yarn|pnpm|git|node|python3|node_modules/.bin"

ALLOWED_COMMANDS_backend="npm|npx|yarn|pnpm|git|node|python3|node_modules/.bin|docker|docker-compose|kubectl|curl|wget|ps|grep|find|chmod|chown|mkdir|rm|touch|cat|echo|tee"

ALLOWED_COMMANDS_test="npm|npx|yarn|pnpm|git|node|python3|node_modules/.bin|pytest|playwright|curl|wget|jest|vitest|mocha|rspec"

ALLOWED_COMMANDS_devops="npm|npx|yarn|pnpm|git|node|python3|docker|docker-compose|kubectl|ssh|systemctl|ps|grep|find|chmod|chown|mkdir|rm|cat|echo|tee|journalctl|service|htop|top|df|du"

# 角色特有的禁止子命令 (格式: "角色:命令子串")
FORBIDDEN_SUBCOMMANDS="
frontend:git push
frontend:git push origin
frontend:docker run
frontend:docker exec
backend:rm -rf /
backend:mkfs
backend:fdisk"

# 危险命令黑名单 (正则)
DANGEROUS_PATTERNS="rm\s+-rf\s+/|mkfs|fdisk|dd\s+if=|:{.*:.*&.*};:"

# 检查危险模式
if echo "$COMMAND" | grep -E "$DANGEROUS_PATTERNS" > /dev/null 2>&1; then
  echo "REJECTED: 危险命令模式 detected"
  echo "命令: $COMMAND"
  exit 1
fi

# 根据角色检查白名单
case "$ROLE" in
  frontend)
    ALLOWED="$ALLOWED_COMMANDS_frontend"
    ;;
  backend)
    ALLOWED="$ALLOWED_COMMANDS_backend"
    ;;
  test)
    ALLOWED="$ALLOWED_COMMANDS_test"
    ;;
  devops)
    ALLOWED="$ALLOWED_COMMANDS_devops"
    ;;
  pm)
    echo "APPROVED: PM 角色无命令限制"
    exit 0
    ;;
  *)
    echo "REJECTED: 未知角色 $ROLE"
    exit 1
    ;;
esac

# 执行白名单检查
if echo "$CMD_BASE" | grep -E "^($ALLOWED)$" > /dev/null 2>&1; then
  # 检查角色特有的禁止子命令
  while IFS=: read -r forbid_role forbid_pattern; do
    # 跳过空行和注释
    if [ -z "$forbid_role" ] || [[ "$forbid_role" =~ ^# ]]; then
      continue
    fi
    if [ "$forbid_role" = "$ROLE" ]; then
      if echo "$COMMAND" | grep -E "$forbid_pattern" > /dev/null 2>&1; then
        echo "REJECTED: $COMMAND 包含禁止的子命令 ($forbid_pattern)"
        exit 1
      fi
    fi
  done <<< "$FORBIDDEN_SUBCOMMANDS"

  echo "APPROVED: $CMD_BASE (角色: $ROLE)"
  exit 0
else
  echo "REJECTED: $CMD_BASE 不在白名单中"
  echo "角色 $ROLE 允许的命令: $(echo $ALLOWED | tr '|' ' ')"
  exit 1
fi