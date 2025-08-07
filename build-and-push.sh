#!/bin/bash

# HBase数据验证系统Docker镜像构建和推送脚本

set -e

# 配置变量
IMAGE_NAME="hbase-validator"
IMAGE_VERSION="v1.0.0"
REGISTRY=""  # 填入你的容器镜像仓库地址，如：ccr.ccs.tencentyun.com/your-namespace

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否运行
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        error "Docker未运行，请先启动Docker"
        exit 1
    fi
    log "Docker运行正常"
}

# 构建镜像
build_image() {
    log "开始构建Docker镜像..."
    
    if [ -z "$REGISTRY" ]; then
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_VERSION}"
        LATEST_IMAGE_NAME="${IMAGE_NAME}:latest"
    else
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}"
        LATEST_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:latest"
    fi
    
    # 构建镜像
    docker build -t "$FULL_IMAGE_NAME" -t "$LATEST_IMAGE_NAME" .
    
    log "镜像构建完成: $FULL_IMAGE_NAME"
}

# 测试镜像
test_image() {
    log "测试镜像运行..."
    
    if [ -z "$REGISTRY" ]; then
        TEST_IMAGE="${IMAGE_NAME}:latest"
    else
        TEST_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"
    fi
    
    # 启动测试容器
    CONTAINER_ID=$(docker run -d -p 8501:8501 "$TEST_IMAGE")
    
    log "等待容器启动..."
    sleep 10
    
    # 检查容器健康状态
    if docker exec "$CONTAINER_ID" curl -f http://localhost:8501/_stcore/health >/dev/null 2>&1; then
        log "镜像测试通过"
    else
        warn "镜像健康检查失败，但容器可能正在启动中"
    fi
    
    # 清理测试容器
    docker stop "$CONTAINER_ID" >/dev/null
    docker rm "$CONTAINER_ID" >/dev/null
    log "测试容器已清理"
}

# 推送镜像
push_image() {
    if [ -z "$REGISTRY" ]; then
        warn "未设置镜像仓库地址，跳过推送步骤"
        warn "请在脚本中设置REGISTRY变量或手动推送镜像"
        return
    fi
    
    log "推送镜像到仓库: $REGISTRY"
    
    # 推送版本化镜像
    docker push "${REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}"
    log "推送完成: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}"
    
    # 推送latest标签
    docker push "${REGISTRY}/${IMAGE_NAME}:latest"
    log "推送完成: ${REGISTRY}/${IMAGE_NAME}:latest"
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -r, --registry REGISTRY   设置容器镜像仓库地址"
    echo "  -v, --version VERSION     设置镜像版本 (默认: v1.0.0)"
    echo "  -t, --test-only          仅构建和测试，不推送"
    echo "  -h, --help               显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -r ccr.ccs.tencentyun.com/your-namespace"
    echo "  $0 -r ccr.ccs.tencentyun.com/your-namespace -v v1.1.0"
}

# 解析命令行参数
TEST_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -v|--version)
            IMAGE_VERSION="$2"
            shift 2
            ;;
        -t|--test-only)
            TEST_ONLY=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            error "未知参数: $1"
            show_usage
            exit 1
            ;;
    esac
done

# 主程序
main() {
    log "开始构建HBase数据验证系统Docker镜像..."
    log "镜像名称: $IMAGE_NAME"
    log "镜像版本: $IMAGE_VERSION"
    log "镜像仓库: ${REGISTRY:-"未设置"}"
    
    check_docker
    build_image
    test_image
    
    if [ "$TEST_ONLY" = false ]; then
        push_image
    else
        log "仅测试模式，跳过推送步骤"
    fi
    
    log "构建脚本执行完成!"
    
    if [ -z "$REGISTRY" ]; then
        echo ""
        log "后续步骤:"
        echo "1. 设置镜像仓库地址并重新运行脚本推送镜像"
        echo "2. 或手动推送镜像:"
        echo "   docker tag ${IMAGE_NAME}:${IMAGE_VERSION} YOUR_REGISTRY/${IMAGE_NAME}:${IMAGE_VERSION}"
        echo "   docker push YOUR_REGISTRY/${IMAGE_NAME}:${IMAGE_VERSION}"
    else
        echo ""
        log "后续步骤:"
        echo "1. 更新 k8s/deployment.yaml 中的镜像地址为: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_VERSION}"
        echo "2. 根据实际环境修改配置"
        echo "3. 部署到Kubernetes集群:"
        echo "   kubectl apply -f k8s/deployment.yaml"
    fi
}

# 运行主程序
main
