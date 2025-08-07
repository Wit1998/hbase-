#!/bin/bash

# HBase数据验证系统 - 构建和部署脚本
# 使用方法: ./build-and-deploy.sh [命令]
# 命令: build, push, deploy, all

set -e

# 配置变量 - 请根据您的腾讯云配置修改
REGISTRY="ccr.ccs.tencentyun.com"
NAMESPACE="your-namespace"  # 替换为您的命名空间
IMAGE_NAME="hbase-validator"
VERSION="latest"
FULL_IMAGE_NAME="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:${VERSION}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 检查Docker是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker未运行或无法访问"
        exit 1
    fi
}

# 构建Docker镜像
build_image() {
    log_info "开始构建Docker镜像..."
    
    docker build -t ${IMAGE_NAME}:${VERSION} .
    docker tag ${IMAGE_NAME}:${VERSION} ${FULL_IMAGE_NAME}
    
    log_info "镜像构建完成: ${FULL_IMAGE_NAME}"
}

# 推送镜像到腾讯云
push_image() {
    log_info "开始推送镜像到腾讯云容器镜像服务..."
    
    # 检查是否已登录
    if ! docker info | grep -q "Registry: ${REGISTRY}"; then
        log_warn "请先登录腾讯云容器镜像服务:"
        log_warn "docker login ${REGISTRY}"
        log_warn "使用您的腾讯云账号和密码"
        exit 1
    fi
    
    docker push ${FULL_IMAGE_NAME}
    log_info "镜像推送完成: ${FULL_IMAGE_NAME}"
}

# 部署到Kubernetes
deploy_k8s() {
    log_info "开始部署到Kubernetes集群..."
    
    # 检查kubectl是否可用
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl命令未找到，请确保已安装并配置kubectl"
        exit 1
    fi
    
    # 更新部署文件中的镜像地址
    sed -i.bak "s|ccr.ccs.tencentyun.com/your-namespace/hbase-validator:latest|${FULL_IMAGE_NAME}|g" k8s/deployment.yaml
    
    # 应用Kubernetes配置
    log_info "创建ConfigMap..."
    kubectl apply -f k8s/configmap.yaml
    
    log_info "创建Deployment和Service..."
    kubectl apply -f k8s/deployment.yaml
    
    log_info "创建Ingress..."
    kubectl apply -f k8s/ingress.yaml
    
    # 恢复原始配置文件
    mv k8s/deployment.yaml.bak k8s/deployment.yaml
    
    log_info "部署完成！"
    
    # 显示部署状态
    log_info "检查部署状态..."
    kubectl get pods -l app=hbase-validator
    kubectl get svc hbase-validator-service
    kubectl get ingress hbase-validator-ingress
}

# 清理资源
cleanup() {
    log_info "清理Kubernetes资源..."
    kubectl delete -f k8s/ingress.yaml --ignore-not-found=true
    kubectl delete -f k8s/deployment.yaml --ignore-not-found=true
    kubectl delete -f k8s/configmap.yaml --ignore-not-found=true
    log_info "清理完成"
}

# 显示帮助信息
show_help() {
    echo "HBase数据验证系统 - 构建和部署脚本"
    echo ""
    echo "使用方法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  build     - 构建Docker镜像"
    echo "  push      - 推送镜像到腾讯云"
    echo "  deploy    - 部署到Kubernetes"
    echo "  all       - 执行完整流程 (build + push + deploy)"
    echo "  cleanup   - 清理Kubernetes资源"
    echo "  help      - 显示帮助信息"
    echo ""
    echo "环境变量配置:"
    echo "  REGISTRY=${REGISTRY}"
    echo "  NAMESPACE=${NAMESPACE}"
    echo "  IMAGE_NAME=${IMAGE_NAME}"
    echo "  VERSION=${VERSION}"
}

# 主程序
main() {
    case "${1:-help}" in
        build)
            check_docker
            build_image
            ;;
        push)
            check_docker
            push_image
            ;;
        deploy)
            deploy_k8s
            ;;
        all)
            check_docker
            build_image
            push_image
            deploy_k8s
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
