# 🚀 HBase数据迁移验证系统 - 腾讯云TKE部署指南

本指南将帮助您将HBase数据迁移验证系统部署到腾讯云容器服务TKE（Tencent Kubernetes Engine）。

## 📋 前提条件

### 1. 环境要求
- ✅ 腾讯云账号和访问权限
- ✅ 已创建TKE集群
- ✅ 本地安装kubectl命令行工具
- ✅ 本地安装Docker
- ✅ 配置好kubectl访问TKE集群

### 2. 腾讯云资源
- **TKE集群**: 至少2个节点，每个节点2核4GB以上
- **TCR容器镜像仓库**: 用于存储镜像
- **CLB负载均衡器**: 用于外部访问（可选）

## 🔧 部署步骤

### 步骤1: 构建和推送Docker镜像

#### 1.1 登录腾讯云容器镜像仓库
```bash
# 替换为您的TCR实例域名
docker login your-registry.tencentcloudcr.com
```

#### 1.2 构建镜像
```bash
# 在项目根目录执行
docker build -t hbase-validator:latest .
```

#### 1.3 标记和推送镜像
```bash
# 替换为您的TCR仓库地址
docker tag hbase-validator:latest your-registry.tencentcloudcr.com/namespace/hbase-validator:latest
docker push your-registry.tencentcloudcr.com/namespace/hbase-validator:latest
```

### 步骤2: 配置kubectl连接TKE集群

#### 2.1 下载集群访问凭证
1. 登录腾讯云控制台
2. 进入容器服务TKE > 集群管理
3. 选择目标集群，点击"基本信息"
4. 下载kubeconfig文件

#### 2.2 配置kubectl
```bash
# 方式1: 设置KUBECONFIG环境变量
export KUBECONFIG=/path/to/your/kubeconfig

# 方式2: 复制到默认位置
cp /path/to/your/kubeconfig ~/.kube/config

# 验证连接
kubectl cluster-info
kubectl get nodes
```

### 步骤3: 修改配置文件

#### 3.1 更新镜像地址
编辑 `k8s/deployment.yaml`，将镜像地址替换为您的TCR地址：
```yaml
spec:
  containers:
  - name: hbase-validator
    image: your-registry.tencentcloudcr.com/namespace/hbase-validator:latest
```

#### 3.2 配置HBase连接信息
编辑 `k8s/configmap.yaml`，更新HBase连接配置：
```yaml
data:
  config.yaml: |
    source:
      host: "your-source-hbase-host"
      port: 9090
      table_name: "your_table_name"
    target:
      host: "your-target-hbase-host"
      port: 9090
      table_name: "your_table_name"
```

### 步骤4: 部署应用

#### 4.1 使用自动化脚本部署（推荐）
```bash
cd k8s
export IMAGE_REGISTRY="your-registry.tencentcloudcr.com"
export IMAGE_REPOSITORY="namespace/hbase-validator"
export IMAGE_TAG="latest"
export NAMESPACE="default"

./deploy.sh
```

#### 4.2 手动部署
```bash
cd k8s

# 创建命名空间（可选）
kubectl create namespace hbase-validator

# 部署ConfigMap
kubectl apply -f configmap.yaml

# 部署应用
kubectl apply -f deployment.yaml

# 部署Service
kubectl apply -f service.yaml

# 部署Ingress（可选）
kubectl apply -f ingress.yaml
```

### 步骤5: 验证部署

#### 5.1 检查Pod状态
```bash
kubectl get pods -l app=hbase-validator
kubectl logs -l app=hbase-validator
```

#### 5.2 检查Service
```bash
kubectl get services -l app=hbase-validator
```

#### 5.3 获取访问地址
```bash
# NodePort方式
kubectl get service hbase-validator-nodeport
# 访问地址: http://<任意节点IP>:30851

# Ingress方式
kubectl get ingress hbase-validator-ingress
```

## 🌐 访问配置

### 方式1: NodePort访问
- **端口**: 30851
- **访问地址**: `http://<TKE节点公网IP>:30851`

### 方式2: Ingress访问
1. 配置域名解析指向CLB
2. 访问地址: `http://hbase-validator.yourdomain.com`

### 方式3: LoadBalancer（推荐生产环境）
```yaml
# 修改 service.yaml
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8501
    protocol: TCP
```

## 🔧 高级配置

### 1. 资源限制调整
```yaml
# 在 deployment.yaml 中调整
resources:
  requests:
    memory: "1Gi"
    cpu: "1000m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### 2. 水平伸缩配置
```bash
# 创建HPA
kubectl autoscale deployment hbase-validator --cpu-percent=70 --min=2 --max=10
```

### 3. 持久化存储
```yaml
# 添加PVC配置到 deployment.yaml
volumeMounts:
- name: data-volume
  mountPath: /app/data
volumes:
- name: data-volume
  persistentVolumeClaim:
    claimName: hbase-validator-pvc
```

## 🔒 安全配置

### 1. 网络策略
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: hbase-validator-netpol
spec:
  podSelector:
    matchLabels:
      app: hbase-validator
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 8501
```

### 2. RBAC配置
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: hbase-validator-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: hbase-validator-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
```

## 📊 监控和日志

### 1. 查看日志
```bash
# 实时查看日志
kubectl logs -f deployment/hbase-validator

# 查看特定Pod日志
kubectl logs -f <pod-name>
```

### 2. 监控指标
```bash
# 查看资源使用情况
kubectl top pods -l app=hbase-validator
kubectl top nodes
```

## 🔧 故障排除

### 常见问题

#### 1. Pod启动失败
```bash
# 查看Pod状态和事件
kubectl describe pod <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp
```

#### 2. 镜像拉取失败
- 检查TCR镜像仓库权限
- 验证镜像地址是否正确
- 确认集群可以访问TCR

#### 3. 服务无法访问
- 检查Service配置
- 验证防火墙和安全组设置
- 确认负载均衡器配置

#### 4. HBase连接失败
- 验证HBase服务可达性
- 检查网络连接和端口
- 确认配置文件中的连接参数

## 📱 本地开发测试

### 使用Docker Compose
```bash
# 本地开发环境
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🔄 CI/CD集成

### GitHub Actions示例
```yaml
name: Deploy to TKE
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build and push
      run: |
        docker build -t ${{ secrets.TCR_REGISTRY }}/hbase-validator:${{ github.sha }} .
        docker push ${{ secrets.TCR_REGISTRY }}/hbase-validator:${{ github.sha }}
    - name: Deploy to TKE
      run: |
        kubectl set image deployment/hbase-validator hbase-validator=${{ secrets.TCR_REGISTRY }}/hbase-validator:${{ github.sha }}
```

## 📞 技术支持

如有问题，请：
1. 检查Pod和Service状态
2. 查看详细日志信息
3. 参考腾讯云TKE官方文档
4. 提交Issue到项目仓库

---

**部署愉快！** 🎉
