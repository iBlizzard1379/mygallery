#!/bin/bash

# 画廊系统内网部署脚本
# 适用于内网多用户并发访问

set -e  # 遇到错误立即退出

echo "🎨 画廊系统内网部署脚本"
echo "=========================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 配置参数
PROJECT_DIR=$(pwd)
PYTHON_VERSION="3.9"
SERVER_PORT=${SERVER_PORT:-8000}
SERVER_HOST=${SERVER_HOST:-0.0.0.0}

# 内网优化配置
export MAX_SESSIONS=${MAX_SESSIONS:-50}
export SESSION_TIMEOUT_MINUTES=${SESSION_TIMEOUT_MINUTES:-60}
export CLEANUP_INTERVAL_SECONDS=${CLEANUP_INTERVAL_SECONDS:-300}

# 性能优化配置
export PYTHON_GC_THRESHOLD="700,10,10"
export MALLOC_TRIM_THRESHOLD=100000
export PYTHONOPTIMIZE=2
export PYTHONDONTWRITEBYTECODE=1

log_info "项目目录: $PROJECT_DIR"
log_info "服务器配置: $SERVER_HOST:$SERVER_PORT"
log_info "最大会话数: $MAX_SESSIONS"
log_info "会话超时: $SESSION_TIMEOUT_MINUTES 分钟"

# 检查系统要求
check_system_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        log_info "Python版本: $PYTHON_VER"
        
        # 版本比较
        if [[ $(echo "$PYTHON_VER >= 3.8" | bc -l) -eq 0 ]]; then
            log_error "需要Python 3.8或更高版本，当前版本: $PYTHON_VER"
            exit 1
        fi
    else
        log_error "未找到Python3"
        exit 1
    fi
    
    # 检查uv工具
    if ! command -v uv &> /dev/null; then
        log_error "未找到uv工具，请先安装uv"
        echo "安装方法: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    log_info "uv版本: $(uv --version)"
    
    # 检查系统资源
    if command -v free &> /dev/null; then
        TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
        log_info "系统内存: ${TOTAL_MEM}GB"
        
        if [ "$TOTAL_MEM" -lt 4 ]; then
            log_warn "内存不足4GB，建议增加内存以获得更好的性能"
        fi
    fi
    
    # 检查磁盘空间
    DISK_AVAIL=$(df -h . | awk 'NR==2 {print $4}')
    log_info "可用磁盘空间: $DISK_AVAIL"
}

# 设置虚拟环境
setup_environment() {
    log_info "设置Python虚拟环境..."
    
    # 检查是否已存在虚拟环境
    if [ ! -d ".venv" ]; then
        log_info "创建新的虚拟环境..."
        uv venv --python $PYTHON_VERSION
    else
        log_info "使用现有虚拟环境"
    fi
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 验证虚拟环境
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        log_info "虚拟环境已激活: $VIRTUAL_ENV"
    else
        log_error "虚拟环境激活失败"
        exit 1
    fi
}

# 安装依赖
install_dependencies() {
    log_info "安装项目依赖..."
    
    # 使用uv安装依赖
    if [ -f "requirements.txt" ]; then
        log_info "从requirements.txt安装依赖..."
        uv pip install -r requirements.txt
    else
        log_error "未找到requirements.txt文件"
        exit 1
    fi
    
    # 安装监控依赖
    log_info "安装监控依赖..."
    uv pip install psutil requests
    
    # 验证核心依赖
    log_info "验证核心依赖..."
    python3 -c "
import langchain
import langchain_openai
import faiss
print('✓ 核心依赖验证通过')
" || {
        log_error "核心依赖验证失败"
        exit 1
    }
}

# 配置环境变量
setup_config() {
    log_info "配置环境变量..."
    
    # 检查.env文件
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            log_info "从env.example创建.env文件..."
            cp env.example .env
        else
            log_error "未找到env.example文件"
            exit 1
        fi
    fi
    
    # 更新配置
    log_info "更新多用户并发配置..."
    
    # 备份原配置
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    
    # 添加或更新多用户配置
    {
        echo ""
        echo "# 多用户并发配置"
        echo "MAX_SESSIONS=$MAX_SESSIONS"
        echo "SESSION_TIMEOUT_MINUTES=$SESSION_TIMEOUT_MINUTES"
        echo "CLEANUP_INTERVAL_SECONDS=$CLEANUP_INTERVAL_SECONDS"
        echo ""
        echo "# 服务器配置"
        echo "PORT=$SERVER_PORT"
        echo "HOST=$SERVER_HOST"
        echo ""
        echo "# 性能优化配置"
        echo "PYTHON_GC_THRESHOLD=$PYTHON_GC_THRESHOLD"
        echo "MALLOC_TRIM_THRESHOLD=$MALLOC_TRIM_THRESHOLD"
    } >> .env
    
    log_info "配置文件已更新"
}

# 系统优化
optimize_system() {
    log_info "应用系统优化..."
    
    # 调整文件描述符限制
    if command -v ulimit &> /dev/null; then
        ulimit -n 65536 2>/dev/null || log_warn "无法调整文件描述符限制"
        log_info "文件描述符限制: $(ulimit -n)"
    fi
    
    # 设置内存优化
    export PYTHONMALLOC=malloc
    
    # 设置垃圾回收优化
    export PYTHONGC=$PYTHON_GC_THRESHOLD
    
    log_info "系统优化配置完成"
}

# 预热系统
warmup_system() {
    log_info "预热系统组件..."
    
    # 预加载Python模块
    python3 -c "
import sys
sys.path.insert(0, '.')

try:
    from session_manager import get_session_manager
    print('✓ 会话管理器预加载成功')
except Exception as e:
    print(f'⚠ 会话管理器预加载失败: {e}')

try:
    from resource_manager import get_resource_manager
    print('✓ 资源管理器预加载成功')
except Exception as e:
    print(f'⚠ 资源管理器预加载失败: {e}')

try:
    import rag_chain
    print('✓ RAG链模块预加载成功')
except Exception as e:
    print(f'⚠ RAG链模块预加载失败: {e}')
"

    # 检查向量数据库
    if [ -d "vector_db" ]; then
        log_info "向量数据库目录存在"
    else
        log_warn "向量数据库目录不存在，首次运行时将自动创建"
    fi
    
    # 检查文档目录
    if [ -d "images" ]; then
        DOC_COUNT=$(find images -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" -o -name "*.xlsx" \) | wc -l)
        log_info "文档目录中有 $DOC_COUNT 个文档文件"
    else
        log_warn "文档目录不存在"
        mkdir -p images
    fi
}

# 启动监控
start_monitoring() {
    if [ "$1" = "--no-monitor" ]; then
        log_info "跳过监控启动"
        return
    fi
    
    log_info "启动系统监控..."
    
    # 检查监控脚本
    if [ -f "monitor.py" ]; then
        # 后台启动监控
        nohup python3 monitor.py > monitor.log 2>&1 &
        MONITOR_PID=$!
        echo $MONITOR_PID > monitor.pid
        log_info "监控进程已启动，PID: $MONITOR_PID"
    else
        log_warn "未找到监控脚本monitor.py"
    fi
}

# 启动服务器
start_server() {
    log_info "启动画廊服务器..."
    log_info "服务器地址: http://$SERVER_HOST:$SERVER_PORT"
    log_info "管理面板: http://$SERVER_HOST:$SERVER_PORT/admin"
    
    # 检查端口是否被占用
    if command -v netstat &> /dev/null; then
        if netstat -tlnp | grep ":$SERVER_PORT " > /dev/null; then
            log_error "端口 $SERVER_PORT 已被占用"
            exit 1
        fi
    fi
    
    # 启动服务器
    export PYTHONPATH="$PYTHONPATH:$(pwd)"
    export KMP_DUPLICATE_LIB_OK=TRUE
    
    # 使用优化参数启动
    exec python3 -X dev -O server.py
}

# 清理函数
cleanup() {
    log_info "清理进程..."
    
    # 停止监控
    if [ -f "monitor.pid" ]; then
        MONITOR_PID=$(cat monitor.pid)
        if kill -0 $MONITOR_PID 2>/dev/null; then
            kill $MONITOR_PID
            log_info "监控进程已停止"
        fi
        rm -f monitor.pid
    fi
}

# 信号处理
trap cleanup EXIT INT TERM

# 显示帮助
show_help() {
    echo "画廊系统内网部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help              显示此帮助信息"
    echo "  --check-only        仅检查系统要求"
    echo "  --no-monitor        不启动监控"
    echo "  --port PORT         指定服务器端口 (默认: 8000)"
    echo "  --host HOST         指定服务器主机 (默认: 0.0.0.0)"
    echo "  --max-sessions N    最大会话数 (默认: 50)"
    echo ""
    echo "环境变量:"
    echo "  SERVER_PORT               服务器端口"
    echo "  SERVER_HOST               服务器主机"
    echo "  MAX_SESSIONS              最大会话数"
    echo "  SESSION_TIMEOUT_MINUTES   会话超时分钟数"
    echo "  CLEANUP_INTERVAL_SECONDS  清理间隔秒数"
    echo ""
    echo "示例:"
    echo "  $0                          # 标准部署"
    echo "  $0 --port 9000             # 使用端口9000"
    echo "  $0 --max-sessions 100      # 支持100个并发会话"
    echo "  $0 --no-monitor            # 不启动监控"
}

# 主函数
main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_help
                exit 0
                ;;
            --check-only)
                check_system_requirements
                log_info "系统检查完成"
                exit 0
                ;;
            --no-monitor)
                NO_MONITOR=true
                ;;
            --port)
                SERVER_PORT="$2"
                shift
                ;;
            --host)
                SERVER_HOST="$2"
                shift
                ;;
            --max-sessions)
                MAX_SESSIONS="$2"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done
    
    # 执行部署步骤
    log_info "开始内网部署..."
    
    check_system_requirements
    setup_environment
    install_dependencies
    setup_config
    optimize_system
    warmup_system
    
    if [ "$NO_MONITOR" != "true" ]; then
        start_monitoring
    fi
    
    log_info "系统准备完成，启动服务器..."
    start_server
}

# 运行主函数
main "$@" 