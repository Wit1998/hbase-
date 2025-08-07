#!/bin/bash

# HBase数据迁移验证系统 - 腾讯云TKE部署脚本
# 使用说明：chmod +x deploy.sh && ./deploy.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
NAMESPACE=${NAMESPACE:-default}
IMAGE_REGISTRY=${IMAGE_REGISTRY:-"your-registry.tencentcloudcr.com"}
IMAGE_REPOSITORY=${IMAGE_REPOSITORY:-"hbase-validator"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
FULL_IMAGE_NAME="${IMAGE_REGISTRY}/${IMAGE_REPOSITORY}:${IMAGE_TAG}"

echo -e "${BLUE}=== HBase数据迁移验证系统部署脚本 ===${NC}"
echo -e "${YELLOW}目标命名空间: ${NAMESPACE}${NC}"
echo -e "${YELLOW}镜像地址: ${FULL_IMAGE_NAME}${NC}"

# 检查kubectl是否可用
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}错误: kubectl 命令未找到，请先安装kubectl${NC}"
    exit 1
fi

# 检查集群连接
echo -e "${BLUE}检查Kubernetes集群连接...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}错误: 无法连接到Kubernetes集群${NC}"
    exit 1
fi

# 创建命名空间（如果不存在）
echo -e "${BLUE}检查命名空间...${NC}"
if ! kubectl get namespace ${NAMESPACE} &> /dev/null; then
    echo -e "${YELLOW}创建命名空间: ${NAMESPACE}${NC}"
    kubectl create namespace ${NAMESPACE}
else
    echo -e "${GREEN}命名空间 ${NAMESPACE} 已存在${NC}"
fi

# 更新Deployment中的镜像地址
echo -e "${BLUE}更新部署配置中的镜像地址...${NC}"
sed -i.bak "s|image: hbase-validator:latest|image: ${FULL_IMAGE_NAME}|g" deployment.yaml

# 部署ConfigMap
echo -e "${BLUE}部署ConfigMap...${NC}"
kubectl apply -f configmap.yaml -n ${NAMESPACE}

# 部署Deployment
echo -e "${BLUE}部署应用...${NC}"
kubectl apply -f deployment.yaml -n ${NAMESPACE}

# 部署Service
echo -e "${BLUE}部署Service...${NC}"
kubectl apply -f service.yaml -n ${NAMESPACE}

# 可选：部署Ingress
read -p "是否部署Ingress? (y/n): " deploy_ingress
if [[ $deploy_ingress == "y" || $deploy_ingress == "Y" ]]; then
    echo -e "${BLUE}部署Ingress...${NC}"
    kubectl apply -f ingress.yaml -n ${NAMESPACE}
fi

# 等待部署完成
echo -e "${BLUE}等待Pod启动...${NC}"
kubectl rollout status deployment/hbase-validator -n ${NAMESPACE} --timeout=300s

# 检查部署状态
echo -e "${BLUE}检查部署状态...${NC}"
kubectl get pods -l app=hbase-validator -n ${NAMESPACE}
kubectl get services -l app=hbase-validator -n ${NAMESPACE}

# 获取访问地址
echo -e "${GREEN}=== 部署完成 ===${NC}"
echo -e "${YELLOW}Pod状态:${NC}"
kubectl get pods -l app=hbase-validator -n ${NAMESPACE}

echo -e "${YELLOW}Service信息:${NC}"
kubectl get services -l app=hbase-validator -n ${NAMESPACE}

# 获取NodePort访问地址
NODEPORT=$(kubectl get service hbase-validator-nodeport -n ${NAMESPACE} -o jsonpath='{.spec.ports[0].nodePort}')
if [ ! -z "$NODEPORT" ]; then
    echo -e "${GREEN}NodePort访问地址: http://<任意节点IP>:${NODEPORT}${NC}"
fi

# 获取Ingress访问地址
if kubectl get ingress hbase-validator-ingress -n ${NAMESPACE} &> /dev/null; then
    INGRESS_HOST=$(kubectl get ingress hbase-validator-ingress -n ${NAMESPACE} -o jsonpath='{.spec.rules[0].host}')
    echo -e "${GREEN}Ingress访问地址: http://${INGRESS_HOST}${NC}"
fi

echo -e "${GREEN}部署完成！${NC}"

# 恢复原始配置文件
mv deployment.yaml.bak deployment.yaml
