#!/bin/bash

# HBase数据迁移验证系统 - 快速部署脚本
# 支持本地Docker和腾讯云TKE部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 默认配置
IMAGE_NAME="hbase-validator"
IMAGE_TAG="latest"
CONTAINER_NAME="hbase-validator"
PORT="8501"

echo -e "${BLUE}=== HBase数据迁移验证系统快速部署 ===${NC}"

# 显示使用说明
show_usage() {
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  local           本地Docker部署"
    echo "  build           构建Docker镜像"
    echo "  tke             腾讯云TKE部署"
    echo "  stop            停止本地服务"
    echo "  clean           清理本地资源"
    echo "  logs            查看日志"
    echo "  help            显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 local        # 本地部署"
    echo "  $0 build        # 构建镜像"
    echo "  $0 tke          # TKE部署"
    echo "  $0 logs         # 查看日志"
}

# 构建Docker镜像
build_image() {
    echo -e "${BLUE}构建Docker镜像...${NC}"
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
}

# 本地Docker部署
deploy_local() {
    echo -e "${BLUE}开始本地Docker部署...${NC}"
    
    # 停止现有容器
    if docker ps -a | grep -q ${CONTAINER_NAME}; then
        echo -e "${YELLOW}停止现有容器...${NC}"
        docker stop ${CONTAINER_NAME} || true
        docker rm ${CONTAINER_NAME} || true
    fi
    
    # 构建镜像
    build_image
    
    # 创建必要目录
    mkdir -p reports logs
    
    # 启动容器
    echo -e "${BLUE}启动应用容器...${NC}"
    docker run -d \
        --name ${CONTAINER_NAME} \
        -p ${PORT}:8501 \
        -v $(pwd)/config.yaml:/app/config.yaml:ro \
        -v $(pwd)/reports:/app/reports \
        -v $(pwd)/logs:/app/logs \
        -e PYTHONUNBUFFERED=1 \
        -e STREAMLIT_SERVER_PORT=8501 \
        -e STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
        -e STREAMLIT_SERVER_HEADLESS=true \
        -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
        --restart unless-stopped \
        ${IMAGE_NAME}:${IMAGE_TAG}
    
    # 等待启动
    echo -e "${BLUE}等待应用启动...${NC}"
    sleep 10
    
    # 检查状态
    if docker ps | grep -q ${CONTAINER_NAME}; then
        echo -e "${GREEN}✅ 部署成功！${NC}"
        echo -e "${GREEN}访问地址: http://localhost:${PORT}${NC}"
        echo -e "${YELLOW}使用 '$0 logs' 查看日志${NC}"
        echo -e "${YELLOW}使用 '$0 stop' 停止服务${NC}"
    else
        echo -e "${RED}❌ 部署失败，请检查日志${NC}"
        docker logs ${CONTAINER_NAME}
        exit 1
    fi
}

# 使用docker-compose部署
deploy_compose() {
    echo -e "${BLUE}使用Docker Compose部署...${NC}"
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: docker-compose 未安装${NC}"
        exit 1
    fi
    
    # 创建必要目录
    mkdir -p reports logs
    
    # 启动服务
    docker-compose up -d --build
    
    echo -e "${GREEN}✅ Docker Compose部署完成${NC}"
    echo -e "${GREEN}访问地址: http://localhost:${PORT}${NC}"
    echo -e "${YELLOW}使用 'docker-compose logs -f' 查看日志${NC}"
    echo -e "${YELLOW}使用 'docker-compose down' 停止服务${NC}"
}

# TKE部署
deploy_tke() {
    echo -e "${BLUE}开始腾讯云TKE部署...${NC}"
    
    # 检查kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}错误: kubectl 命令未找到${NC}"
        echo -e "${YELLOW}请先安装kubectl并配置集群访问${NC}"
        exit 1
    fi
    
    # 检查集群连接
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}错误: 无法连接到Kubernetes集群${NC}"
        echo -e "${YELLOW}请确保kubectl已正确配置${NC}"
        exit 1
    fi
    
    # 检查必要信息
    if [ -z "${IMAGE_REGISTRY}" ]; then
        echo -e "${YELLOW}请设置镜像仓库地址:${NC}"
        echo "export IMAGE_REGISTRY=\"your-registry.tencentcloudcr.com\""
        echo "export IMAGE_REPOSITORY=\"namespace/hbase-validator\""
        echo "export IMAGE_TAG=\"latest\""
        echo ""
        echo "然后重新运行: $0 tke"
        exit 1
    fi
    
    # 执行TKE部署脚本
    cd k8s
    ./deploy.sh
    cd ..
    
    echo -e "${GREEN}✅ TKE部署完成${NC}"
}

# 停止本地服务
stop_local() {
    echo -e "${BLUE}停止本地服务...${NC}"
    
    # 停止Docker容器
    if docker ps | grep -q ${CONTAINER_NAME}; then
        docker stop ${CONTAINER_NAME}
        echo -e "${GREEN}✅ Docker容器已停止${NC}"
    fi
    
    # 停止Docker Compose
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
        echo -e "${GREEN}✅ Docker Compose服务已停止${NC}"
    fi
}

# 清理本地资源
clean_local() {
    echo -e "${BLUE}清理本地资源...${NC}"
    
    # 停止服务
    stop_local
    
    # 删除容器
    if docker ps -a | grep -q ${CONTAINER_NAME}; then
        docker rm ${CONTAINER_NAME}
        echo -e "${GREEN}✅ 容器已删除${NC}"
    fi
    
    # 删除镜像
    if docker images | grep -q ${IMAGE_NAME}; then
        docker rmi ${IMAGE_NAME}:${IMAGE_TAG}
        echo -e "${GREEN}✅ 镜像已删除${NC}"
    fi
    
    # 清理Docker Compose资源
    if [ -f "docker-compose.yml" ]; then
        docker-compose down --rmi all --volumes
        echo -e "${GREEN}✅ Docker Compose资源已清理${NC}"
    fi
}

# 查看日志
show_logs() {
    echo -e "${BLUE}查看应用日志...${NC}"
    
    if docker ps | grep -q ${CONTAINER_NAME}; then
        docker logs -f ${CONTAINER_NAME}
    elif [ -f "docker-compose.yml" ]; then
        docker-compose logs -f
    else
        echo -e "${YELLOW}没有运行中的服务${NC}"
    fi
}

# 主逻辑
case "${1}" in
    "local")
        deploy_local
        ;;
    "compose")
        deploy_compose
        ;;
    "build")
        build_image
        ;;
    "tke")
        deploy_tke
        ;;
    "stop")
        stop_local
        ;;
    "clean")
        clean_local
        ;;
    "logs")
        show_logs
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    "")
        echo -e "${YELLOW}请选择部署方式:${NC}"
        echo "1. 本地Docker部署: $0 local"
        echo "2. Docker Compose部署: $0 compose"
        echo "3. 腾讯云TKE部署: $0 tke"
        echo "4. 查看帮助: $0 help"
        ;;
    *)
        echo -e "${RED}错误: 未知参数 '$1'${NC}"
        show_usage
        exit 1
        ;;
esac
