#!/bin/bash

# HBase数据验证系统 - 腾讯云Coding构建推送脚本
# 使用方法: ./build-and-push-coding.sh

set -e

# 腾讯云Coding配置
CODING_REGISTRY="tencentpartner-docker.pkg.coding.net"
CODING_USER="rorokey-1754558094217"
CODING_PASSWORD="fe4fb2ca7457e5db758227015c78e8fab3f52fb0"
CODING_NAMESPACE="rorokey"  # 请根据实际项目修改
IMAGE_NAME="hbase-validator"
VERSION="latest"

# 完整镜像地址
FULL_IMAGE_NAME="${CODING_REGISTRY}/${CODING_NAMESPACE}/${IMAGE_NAME}:${VERSION}"

# 颜色输出
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查Docker是否运行
check_docker() {
    log_step "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker Desktop"
        log_info "Mac安装: https://docs.docker.com/desktop/mac/install/"
        log_info "或使用Homebrew: brew install --cask docker"
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker未运行，请启动Docker Desktop"
        exit 1
    fi
    
    log_info "Docker环境检查通过"
}

# 登录腾讯云Coding
login_coding() {
    log_step "登录腾讯云Coding Docker仓库..."
    
    echo "${CODING_PASSWORD}" | docker login \
        --username ${CODING_USER} \
        --password-stdin \
        ${CODING_REGISTRY}
    
    if [ $? -eq 0 ]; then
        log_info "登录成功: ${CODING_REGISTRY}"
    else
        log_error "登录失败"
        exit 1
    fi
}

# 构建Docker镜像
build_image() {
    log_step "构建Docker镜像..."
    
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile不存在，请确保在项目根目录"
        exit 1
    fi
    
    # 构建镜像
    docker build -t ${IMAGE_NAME}:${VERSION} .
    
    # 打标签
    docker tag ${IMAGE_NAME}:${VERSION} ${FULL_IMAGE_NAME}
    
    log_info "镜像构建完成: ${FULL_IMAGE_NAME}"
}

# 推送镜像
push_image() {
    log_step "推送镜像到腾讯云Coding..."
    
    docker push ${FULL_IMAGE_NAME}
    
    if [ $? -eq 0 ]; then
        log_info "镜像推送成功: ${FULL_IMAGE_NAME}"
    else
        log_error "镜像推送失败"
        exit 1
    fi
}

# 清理本地镜像 (可选)
cleanup_local() {
    log_step "清理本地临时镜像..."
    
    docker rmi ${IMAGE_NAME}:${VERSION} || true
    
    log_info "本地清理完成"
}

# 显示镜像信息
show_image_info() {
    log_step "显示镜像信息..."
    
    echo ""
    echo "=== 构建完成 ==="
    echo "镜像地址: ${FULL_IMAGE_NAME}"
    echo "镜像大小: $(docker images ${FULL_IMAGE_NAME} --format 'table {{.Size}}' | tail -n 1)"
    echo "构建时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "=== 使用方法 ==="
    echo "在Kubernetes中使用此镜像:"
    echo "image: ${FULL_IMAGE_NAME}"
    echo ""
}

# 更新部署文件中的镜像地址
update_deploy_files() {
    log_step "更新部署文件中的镜像地址..."
    
    # 备份原文件
    if [ -f "simple-deploy.yaml" ]; then
        cp simple-deploy.yaml simple-deploy.yaml.backup
        
        # 更新镜像地址
        sed -i.tmp "s|ccr.ccs.tencentyun.com/your-namespace/hbase-validator:latest|${FULL_IMAGE_NAME}|g" simple-deploy.yaml
        rm simple-deploy.yaml.tmp
        
        log_info "已更新 simple-deploy.yaml 中的镜像地址"
    fi
    
    if [ -f "hbase-validator-deploy.yaml" ]; then
        cp hbase-validator-deploy.yaml hbase-validator-deploy.yaml.backup
        
        # 更新镜像地址
        sed -i.tmp "s|ccr.ccs.tencentyun.com/your-namespace/hbase-validator:latest|${FULL_IMAGE_NAME}|g" hbase-validator-deploy.yaml
        rm hbase-validator-deploy.yaml.tmp
        
        log_info "已更新 hbase-validator-deploy.yaml 中的镜像地址"
    fi
}

# 主函数
main() {
    echo "========================================="
    echo "  HBase数据验证系统 - 镜像构建推送工具"
    echo "========================================="
    echo ""
    
    # 显示配置信息
    log_info "配置信息:"
    echo "  仓库地址: ${CODING_REGISTRY}"
    echo "  用户名: ${CODING_USER}"
    echo "  项目: ${CODING_NAMESPACE}"
    echo "  镜像名: ${IMAGE_NAME}:${VERSION}"
    echo "  完整地址: ${FULL_IMAGE_NAME}"
    echo ""
    
    # 确认继续
    read -p "确认以上配置正确? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "操作已取消"
        exit 0
    fi
    
    # 执行构建推送流程
    check_docker
    login_coding
    build_image
    push_image
    update_deploy_files
    show_image_info
    
    # 询问是否清理本地镜像
    read -p "是否清理本地临时镜像? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_local
    fi
    
    echo ""
    log_info "🎉 所有操作完成！"
    log_info "您现在可以使用更新后的YAML文件部署到Kubernetes集群"
}

# 错误处理
trap 'log_error "脚本执行失败，退出码: $?"' ERR

# 执行主函数
main "$@"
