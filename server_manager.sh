#!/bin/bash
# Apple Notes MCP 服务器管理脚本
# 用于启动、停止、重启和管理本地服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="$SCRIPT_DIR/scripts/server_enhanced.py"
PID_FILE="$HOME/.apple-notes-mcp.pid"
LOG_FILE="$HOME/apple-notes-mcp-server.log"
DEFAULT_PORT=8000

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Apple Notes MCP 服务器管理器${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 检查 Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "未找到 Python 3"
        exit 1
    fi
}

# 检查服务器脚本
check_server_script() {
    if [ ! -f "$SERVER_SCRIPT" ]; then
        print_error "服务器脚本不存在: $SERVER_SCRIPT"
        exit 1
    fi
}

# 获取进程 ID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

# 检查服务器是否正在运行
is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        # 清理过期的 PID 文件
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        return 1
    fi
}

# 检查端口是否被占用
check_port() {
    local port=${1:-$DEFAULT_PORT}
    if lsof -i ":$port" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 启动服务器
start_server() {
    print_header

    if is_running; then
        print_warning "服务器已经在运行中"
        print_info "PID: $(get_pid)"
        print_info "使用 '$0 status' 查看详情"
        return 0
    fi

    local port=${1:-$DEFAULT_PORT}
    local mode=${2:-"foreground"}

    # 检查端口
    if check_port "$port"; then
        print_error "端口 $port 已被占用"
        print_info "占用端口的进程:"
        lsof -i ":$port"
        exit 1
    fi

    check_python
    check_server_script

    print_info "启动 Apple Notes MCP 服务器..."
    print_info "端口: $port"
    print_info "模式: $mode"

    if [ "$mode" = "background" ]; then
        # 后台模式
        print_info "以后台模式启动..."
        nohup python3 "$SERVER_SCRIPT" --port "$port" > "$LOG_FILE" 2>&1 &
        local pid=$!
        echo $pid > "$PID_FILE"

        # 等待服务器启动
        sleep 2

        if is_running; then
            print_success "服务器已启动"
            print_info "PID: $pid"
            print_info "日志文件: $LOG_FILE"
            print_info "服务器地址: http://localhost:$port/sse"
            print_info ""
            print_info "使用以下命令:"
            print_info "  查看状态: $0 status"
            print_info "  查看日志: $0 logs"
            print_info "  停止服务: $0 stop"
        else
            print_error "服务器启动失败"
            print_info "查看日志: tail -f $LOG_FILE"
            exit 1
        fi
    else
        # 前台模式
        print_info "以前台模式启动（按 Ctrl+C 停止）..."
        print_info ""
        python3 "$SERVER_SCRIPT" --port "$port"
    fi
}

# 停止服务器
stop_server() {
    print_header

    if ! is_running; then
        print_warning "服务器未在运行"
        return 0
    fi

    local pid=$(get_pid)
    print_info "停止服务器 (PID: $pid)..."

    kill "$pid"

    # 等待进程结束
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done

    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "进程未正常结束，强制终止..."
        kill -9 "$pid"
    fi

    rm -f "$PID_FILE"
    print_success "服务器已停止"
}

# 重启服务器
restart_server() {
    print_header
    print_info "重启服务器..."

    if is_running; then
        stop_server
        sleep 2
    fi

    start_server "$1" "background"
}

# 查看状态
show_status() {
    print_header

    if is_running; then
        local pid=$(get_pid)
        print_success "服务器正在运行"
        echo ""
        print_info "进程信息:"
        echo "  PID: $pid"
        echo "  命令: $(ps -p $pid -o command=)"
        echo ""

        # CPU 和内存使用情况
        print_info "资源使用:"
        ps -p "$pid" -o %cpu,%mem,rss,vsz | tail -n 1 | awk '{
            printf "  CPU: %.1f%%\n", $1
            printf "  内存: %.1f%% (RSS: %.1f MB, VSZ: %.1f MB)\n", $2, $3/1024, $4/1024
        }'
        echo ""

        # 运行时间
        print_info "运行时间:"
        ps -p "$pid" -o etime= | awk '{print "  " $1}'
        echo ""

        # 端口信息
        print_info "监听端口:"
        lsof -p "$pid" -a -i -P -n | grep LISTEN || echo "  未检测到监听端口"
        echo ""

        print_info "服务端点:"
        echo "  MCP SSE:  http://localhost:$DEFAULT_PORT/sse"
        echo "  Web UI:   http://localhost:$DEFAULT_PORT/"
        echo "  日志文件: $LOG_FILE"

    else
        print_warning "服务器未在运行"
        echo ""
        print_info "启动服务器:"
        echo "  前台模式: $0 start"
        echo "  后台模式: $0 start --daemon"
    fi
}

# 查看日志
show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        print_warning "日志文件不存在: $LOG_FILE"
        return 1
    fi

    local lines=${1:-50}

    print_header
    print_info "显示最后 $lines 行日志:"
    echo ""

    tail -n "$lines" "$LOG_FILE"

    echo ""
    print_info "实时查看日志: tail -f $LOG_FILE"
}

# 跟踪日志
follow_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        print_warning "日志文件不存在: $LOG_FILE"
        return 1
    fi

    print_header
    print_info "实时跟踪日志（按 Ctrl+C 退出）:"
    echo ""

    tail -f "$LOG_FILE"
}

# 测试服务器
test_server() {
    print_header
    print_info "测试服务器连接..."

    local port=${1:-$DEFAULT_PORT}
    local url="http://localhost:$port/health"

    if command -v curl &> /dev/null; then
        print_info "使用 curl 测试: $url"
        echo ""
        curl -s "$url" || print_error "连接失败"
        echo ""
    else
        print_warning "curl 未安装，跳过连接测试"
    fi

    if check_port "$port"; then
        print_success "端口 $port 正在监听"
    else
        print_error "端口 $port 未监听"
    fi
}

# 显示帮助
show_help() {
    print_header

    cat << EOF
用法: $0 <命令> [选项]

命令:
  start [--daemon] [--port PORT]  启动服务器
                                  --daemon: 后台运行
                                  --port: 指定端口（默认 $DEFAULT_PORT）

  stop                            停止服务器

  restart [--port PORT]           重启服务器

  status                          查看服务器状态

  logs [LINES]                    查看日志（默认 50 行）

  follow                          实时跟踪日志

  test [PORT]                     测试服务器连接

  help                            显示此帮助信息

示例:
  $0 start                        # 前台启动
  $0 start --daemon               # 后台启动
  $0 start --port 9000            # 指定端口
  $0 stop                         # 停止服务器
  $0 restart                      # 重启服务器
  $0 status                       # 查看状态
  $0 logs 100                     # 查看最后 100 行日志
  $0 follow                       # 实时查看日志

配置:
  服务器脚本: $SERVER_SCRIPT
  PID 文件:   $PID_FILE
  日志文件:   $LOG_FILE
  默认端口:   $DEFAULT_PORT

更多信息:
  GitHub: https://github.com/yinanli1917-cloud/apple-notes-mcp
  文档:   $SCRIPT_DIR/docs/
EOF
}

# 主函数
main() {
    local command=${1:-help}
    shift || true

    case "$command" in
        start)
            local mode="foreground"
            local port=$DEFAULT_PORT

            while [ $# -gt 0 ]; do
                case "$1" in
                    --daemon|-d)
                        mode="background"
                        shift
                        ;;
                    --port|-p)
                        port="$2"
                        shift 2
                        ;;
                    *)
                        print_error "未知选项: $1"
                        show_help
                        exit 1
                        ;;
                esac
            done

            start_server "$port" "$mode"
            ;;

        stop)
            stop_server
            ;;

        restart)
            local port=$DEFAULT_PORT
            if [ "$1" = "--port" ] || [ "$1" = "-p" ]; then
                port="$2"
            fi
            restart_server "$port"
            ;;

        status)
            show_status
            ;;

        logs)
            show_logs "${1:-50}"
            ;;

        follow)
            follow_logs
            ;;

        test)
            test_server "${1:-$DEFAULT_PORT}"
            ;;

        help|--help|-h)
            show_help
            ;;

        *)
            print_error "未知命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
