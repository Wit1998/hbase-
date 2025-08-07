# 🐳 Docker部署指南

## 🚀 快速开始

### 1. 安装Docker

**macOS:**
```bash
# 使用Homebrew安装
brew install --cask docker

# 或下载Docker Desktop
# https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu/Debian):**
```bash
# 更新包索引
sudo apt-get update

# 安装Docker
sudo apt-get install docker.io

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 将用户添加到docker组
sudo usermod -aG docker $USER
```

### 2. 构建镜像

```bash
# 自动构建脚本（推荐）
./build-and-push.sh --test-only

# 或手动构建
docker build -t hbase-validator:v1.0.0 .
```

### 3. 本地运行测试

```bash
# 使用docker-compose（推荐）
docker-compose up -d

# 或直接运行Docker容器
docker run -d \
  --name hbase-validator \
  -p 8501:8501 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/reports:/app/reports \
  hbase-validator:latest
```

访问: http://localhost:8501

### 4. 停止服务

```bash
# docker-compose方式
docker-compose down

# 直接运行方式
docker stop hbase-validator
docker rm hbase-validator
```

## 🌐 腾讯云容器服务部署

### 1. 推送镜像到腾讯云容器镜像服务

```bash
# 登录腾讯云容器镜像服务
docker login ccr.ccs.tencentyun.com --username=您的用户名

# 构建并推送镜像
./build-and-push.sh -r ccr.ccs.tencentyun.com/your-namespace
```

### 2. 在腾讯云容器服务(TKE)部署

1. **创建集群**
   - 登录腾讯云控制台
   - 选择"容器服务TKE"
   - 创建标准集群

2. **部署应用**
   ```bash
   # 更新k8s/deployment.yaml中的镜像地址
   # 将your-registry替换为: ccr.ccs.tencentyun.com/your-namespace
   
   # 应用部署配置
   kubectl apply -f k8s/deployment.yaml
   ```

3. **获取外网访问地址**
   ```bash
   kubectl get svc hbase-validator-service
   ```

### 3. 弹性容器实例(EKS)部署

```bash
# 使用EKS Serverless部署
kubectl apply -f k8s/deployment.yaml --server-dry-run=client -o yaml | \
kubectl annotate -f - eks.tke.cloud.tencent.com/cpu=0.5 \
eks.tke.cloud.tencent.com/memory=1Gi --dry-run=client -o yaml | \
kubectl apply -f -
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `STREAMLIT_SERVER_PORT` | Streamlit服务端口 | 8501 |
| `STREAMLIT_SERVER_ADDRESS` | 服务绑定地址 | 0.0.0.0 |
| `STREAMLIT_SERVER_HEADLESS` | 无头模式运行 | true |

### 存储挂载

- `/app/config.yaml` - 配置文件
- `/app/reports` - 报告输出目录
- `/app/logs` - 日志目录

## 🔧 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看容器日志
   docker logs hbase-validator
   
   # 进入容器调试
   docker exec -it hbase-validator /bin/bash
   ```

2. **健康检查失败**
   ```bash
   # 手动检查健康状态
   curl http://localhost:8501/_stcore/health
   ```

3. **端口访问问题**
   ```bash
   # 检查端口绑定
   docker port hbase-validator
   
   # 检查防火墙设置
   sudo ufw allow 8501
   ```

### 日志查看

```bash
# Docker容器日志
docker logs -f hbase-validator

# Kubernetes Pod日志
kubectl logs -f deployment/hbase-validator

# 应用内日志
docker exec hbase-validator tail -f /app/logs/hbase_validation.log
```

## 📊 监控和维护

### 资源监控

```bash
# 查看容器资源使用
docker stats hbase-validator

# Kubernetes资源监控
kubectl top pods
kubectl describe pod -l app=hbase-validator
```

### 自动扩缩容 (TKE)

在 `k8s/deployment.yaml` 中添加HPA配置:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hbase-validator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hbase-validator
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🚀 高级配置

### 1. 生产环境优化

```dockerfile
# 多阶段构建优化镜像大小
FROM python:3.11-alpine as builder
# ... 构建步骤

FROM python:3.11-alpine
# ... 运行时步骤
```

### 2. 安全加固

```bash
# 使用非root用户运行
RUN adduser -D -s /bin/sh appuser
USER appuser
```

### 3. 性能优化

```yaml
# Kubernetes资源限制
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

## 📝 更新部署

```bash
# 构建新版本
./build-and-push.sh -r ccr.ccs.tencentyun.com/your-namespace -v v1.1.0

# 滚动更新
kubectl set image deployment/hbase-validator hbase-validator=ccr.ccs.tencentyun.com/your-namespace/hbase-validator:v1.1.0

# 检查更新状态
kubectl rollout status deployment/hbase-validator
```

## 🆘 技术支持

如遇到问题，请提供以下信息：
1. 容器/Pod日志
2. 环境信息 (操作系统、Docker版本、Kubernetes版本)
3. 错误截图或错误信息
4. 配置文件内容
