# 🚀 快速部署指南

## 📋 部署文件说明

### 1. `simple-deploy.yaml` - 简化版 (推荐新手)
- ✅ 基本功能齐全
- ✅ 配置简单
- ✅ 快速部署
- 包含：ConfigMap, Deployment, Service, Ingress

### 2. `hbase-validator-deploy.yaml` - 完整版 (推荐生产环境)
- ✅ 生产环境就绪
- ✅ 包含所有高级功能
- ✅ 安全性配置
- 包含：Namespace, ConfigMap, Secret, Deployment, Service, Ingress, HPA, PDB

## 🛠️ 部署步骤

### 方式1: 简化版部署

1. **修改配置**
```bash
# 编辑simple-deploy.yaml，修改以下内容：
# 1. HBase连接地址
# 2. 腾讯云镜像地址
# 3. 域名配置
```

2. **部署应用**
```bash
kubectl apply -f simple-deploy.yaml
```

3. **验证部署**
```bash
# 检查Pod状态
kubectl get pods -l app=hbase-validator

# 检查Service
kubectl get svc hbase-validator-service

# 检查Ingress
kubectl get ingress hbase-validator-ingress
```

### 方式2: 完整版部署

1. **修改配置**
```bash
# 编辑hbase-validator-deploy.yaml，修改：
# 1. namespace名称 (可选)
# 2. HBase连接地址
# 3. 腾讯云镜像地址
# 4. 域名配置
# 5. 资源配置
```

2. **部署应用**
```bash
kubectl apply -f hbase-validator-deploy.yaml
```

3. **验证部署**
```bash
# 检查namespace资源
kubectl get all -n hbase-validator

# 检查HPA状态
kubectl get hpa -n hbase-validator

# 查看详细信息
kubectl describe deployment hbase-validator -n hbase-validator
```

## ⚙️ 必须修改的配置项

### 🔧 1. 镜像地址
```yaml
# 在Deployment中找到以下行并修改
image: ccr.ccs.tencentyun.com/your-namespace/hbase-validator:latest
# 改为:
image: ccr.ccs.tencentyun.com/实际命名空间/hbase-validator:latest
```

### 🔧 2. HBase连接配置
```yaml
# 在ConfigMap中修改
source:
  host: "your-source-hbase-host"  # 改为实际源端HBase地址
  port: 9090
target:
  host: "your-target-hbase-host"  # 改为实际目标端HBase地址  
  port: 9090
```

### 🔧 3. 域名配置
```yaml
# 在Ingress中修改
rules:
- host: hbase-validator.your-domain.com  # 改为您的实际域名
```

## 🌐 访问应用

### 通过域名访问
```
http://hbase-validator.your-domain.com
```

### 通过端口转发访问 (测试用)
```bash
kubectl port-forward svc/hbase-validator-service 8501:80
# 然后访问: http://localhost:8501
```

### 通过NodePort访问 (如果修改Service类型)
```yaml
# 修改Service类型为NodePort
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 8501
    nodePort: 30080  # 30000-32767范围内
```

## 🔍 常用管理命令

### 查看状态
```bash
# 查看Pod日志
kubectl logs -l app=hbase-validator -f

# 查看Pod详细信息
kubectl describe pod -l app=hbase-validator

# 查看Service端点
kubectl get endpoints hbase-validator-service
```

### 扩缩容
```bash
# 手动扩容到5个副本
kubectl scale deployment hbase-validator --replicas=5

# 查看HPA状态 (完整版才有)
kubectl get hpa hbase-validator-hpa -n hbase-validator
```

### 更新应用
```bash
# 更新镜像
kubectl set image deployment/hbase-validator hbase-validator=ccr.ccs.tencentyun.com/your-namespace/hbase-validator:v1.1

# 查看滚动更新状态
kubectl rollout status deployment/hbase-validator
```

### 清理资源
```bash
# 删除简化版资源
kubectl delete -f simple-deploy.yaml

# 删除完整版资源
kubectl delete -f hbase-validator-deploy.yaml
```

## 🚨 故障排查

### Pod启动失败
```bash
# 查看Pod事件
kubectl get events --sort-by=.metadata.creationTimestamp

# 查看Pod详细状态
kubectl describe pod <pod-name>

# 查看容器日志
kubectl logs <pod-name> -c hbase-validator
```

### 服务访问失败
```bash
# 检查Service端点
kubectl get endpoints hbase-validator-service

# 检查Ingress状态
kubectl describe ingress hbase-validator-ingress

# 测试Pod内部服务
kubectl exec -it <pod-name> -- curl http://localhost:8501/_stcore/health
```

### 配置问题
```bash
# 查看ConfigMap内容
kubectl get configmap hbase-validator-config -o yaml

# 重新加载配置 (重启Pod)
kubectl rollout restart deployment/hbase-validator
```

## 📊 监控和日志

### 查看资源使用
```bash
# 查看Pod资源使用
kubectl top pods -l app=hbase-validator

# 查看Node资源使用
kubectl top nodes
```

### 实时日志
```bash
# 查看所有Pod日志
kubectl logs -l app=hbase-validator -f --tail=100

# 查看特定Pod日志
kubectl logs <pod-name> -f
```

## 🎯 快速检查清单

部署前检查：
- [ ] 修改了镜像地址
- [ ] 配置了HBase连接信息
- [ ] 设置了正确的域名
- [ ] 确认kubectl可以连接集群
- [ ] 确认有足够的集群资源

部署后检查：
- [ ] Pod状态为Running
- [ ] Service有正确的端点
- [ ] Ingress配置正确
- [ ] 应用可以通过域名访问
- [ ] HBase连接正常
