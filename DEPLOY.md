# 🚀 HBase数据验证系统 - 腾讯云容器部署指南

## 📋 部署架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   用户访问       │────│  腾讯云TKE集群     │────│  HBase集群      │
│                │    │                  │    │                │
│  Web Browser   │    │  ┌─────────────┐  │    │  Source HBase  │
│  Mobile App    │────│  │   Ingress   │  │────│  Target HBase  │
│                │    │  └─────────────┘  │    │                │
└─────────────────┘    │  ┌─────────────┐  │    └─────────────────┘
                       │  │   Service   │  │
                       │  └─────────────┘  │
                       │  ┌─────────────┐  │
                       │  │ Deployment  │  │
                       │  │  (2 Pods)   │  │
                       │  └─────────────┘  │
                       │  ┌─────────────┐  │
                       │  │ ConfigMap   │  │
                       │  └─────────────┘  │
                       └──────────────────┘
```

## 🔧 前置条件

### 1. 腾讯云环境准备
- **TKE集群**: 已创建并运行的腾讯云容器服务集群
- **容器镜像服务**: 开通TCR个人版或企业版
- **kubectl**: 已安装并配置连接到TKE集群

### 2. 本地开发环境
- **Docker**: 用于构建镜像
- **kubectl**: 用于部署到Kubernetes
- **Git**: 代码管理

### 3. 网络要求
- 容器能访问HBase集群（源端和目标端）
- Ingress能对外提供访问

## 🏗️ 快速部署步骤

### Step 1: 克隆代码并配置
```bash
git clone git@github.com:Wit1998/hbase-.git
cd hbase-
```

### Step 2: 修改配置文件
编辑 `build-and-deploy.sh` 中的配置：
```bash
# 修改这些变量为您的腾讯云配置
NAMESPACE="your-namespace"      # 替换为您的TCR命名空间
```

编辑 `k8s/configmap.yaml` 中的HBase连接信息：
```yaml
source:
  host: "your-source-hbase-host"    # 源端HBase地址
  port: 9090
target:  
  host: "your-target-hbase-host"    # 目标端HBase地址
  port: 9090
```

### Step 3: 登录腾讯云容器镜像服务
```bash
# 登录TCR
docker login ccr.ccs.tencentyun.com
# 输入您的腾讯云账号和密码
```

### Step 4: 一键部署
```bash
# 执行完整部署流程
./build-and-deploy.sh all
```

## 📝 详细操作说明

### 🔨 构建镜像
```bash
# 仅构建Docker镜像
./build-and-deploy.sh build
```

### 📤 推送镜像
```bash
# 推送镜像到腾讯云TCR
./build-and-deploy.sh push
```

### 🚀 部署服务
```bash
# 部署到Kubernetes集群
./build-and-deploy.sh deploy
```

### 🧹 清理资源
```bash
# 删除所有Kubernetes资源
./build-and-deploy.sh cleanup
```

## 🔍 部署验证

### 检查Pod状态
```bash
kubectl get pods -l app=hbase-validator
```
预期输出：
```
NAME                              READY   STATUS    RESTARTS   AGE
hbase-validator-xxxxxxxxx-xxxxx   1/1     Running   0          2m
hbase-validator-xxxxxxxxx-xxxxx   1/1     Running   0          2m
```

### 检查Service
```bash
kubectl get svc hbase-validator-service
```

### 检查Ingress
```bash
kubectl get ingress hbase-validator-ingress
```

### 查看日志
```bash
kubectl logs -l app=hbase-validator -f
```

## 🌐 访问应用

### 通过Ingress访问
1. 配置域名解析指向Ingress IP
2. 访问: `http://hbase-validator.your-domain.com`

### 通过端口转发访问（测试用）
```bash
kubectl port-forward svc/hbase-validator-service 8501:80
```
然后访问: `http://localhost:8501`

## ⚙️ 配置说明

### 环境变量配置
在 `k8s/deployment.yaml` 中可以配置：
- `STREAMLIT_SERVER_PORT`: Streamlit服务端口
- `STREAMLIT_SERVER_ADDRESS`: 服务监听地址

### 资源配置
默认资源配置：
- **CPU**: 请求500m，限制1000m
- **内存**: 请求1Gi，限制2Gi
- **副本数**: 2个Pod

### 存储配置
- **配置文件**: 通过ConfigMap挂载
- **报告输出**: 使用EmptyDir存储（Pod重启会丢失）

## 🔧 故障排查

### Pod启动失败
```bash
# 查看Pod详细信息
kubectl describe pod -l app=hbase-validator

# 查看Pod日志
kubectl logs -l app=hbase-validator
```

### 健康检查失败
检查以下配置：
- Streamlit服务是否正常启动
- 端口8501是否正确监听
- 健康检查路径 `/_stcore/health` 是否可访问

### 网络连接问题
1. 检查HBase服务器网络连通性
2. 验证防火墙配置
3. 确认Service和Pod的网络策略

### 性能调优
根据实际负载调整：
1. **CPU/内存资源**
2. **Pod副本数量**
3. **HBase连接池配置**
4. **并发处理线程数**

## 📊 监控和日志

### 应用日志
```bash
# 实时查看所有Pod日志
kubectl logs -l app=hbase-validator -f

# 查看特定Pod日志
kubectl logs <pod-name>
```

### 系统监控
- **CPU/内存使用**: 通过Kubernetes Dashboard或监控系统
- **网络流量**: 监控Pod网络指标
- **应用性能**: 通过Streamlit内置监控

## 🔐 安全配置

### 网络安全
- 配置NetworkPolicy限制Pod网络访问
- 使用HTTPS/TLS加密传输
- 限制Ingress访问IP白名单

### 访问控制
- 配置RBAC权限控制
- 使用ServiceAccount管理Pod权限
- 敏感配置使用Secret而非ConfigMap

## 📈 扩展和优化

### 水平扩展
```bash
# 扩展Pod副本数
kubectl scale deployment hbase-validator --replicas=5
```

### 自动扩展
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
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 📞 技术支持

如遇问题，请提供以下信息：
1. 错误日志和截图
2. Pod和Service状态信息
3. 网络和HBase连接配置
4. 部署环境和版本信息

---
**HBase数据迁移验证系统** - 让数据迁移验证在容器环境中更加高效！
