# 🐳 腾讯云Coding Docker镜像推送指南

## 📋 仓库信息
- **仓库地址**: `tencentpartner-docker.pkg.coding.net`
- **用户名**: `rorokey-1754558094217`
- **项目空间**: `rorokey`
- **镜像名称**: `hbase-validator`
- **完整地址**: `tencentpartner-docker.pkg.coding.net/rorokey/hbase-validator:latest`

## 🚀 方式1: 一键自动化脚本 (推荐)

```bash
# 执行自动化构建推送脚本
./build-and-push-coding.sh
```

脚本会自动完成：
- ✅ Docker环境检查
- ✅ 登录腾讯云Coding仓库
- ✅ 构建Docker镜像
- ✅ 推送镜像到仓库
- ✅ 更新部署YAML文件
- ✅ 清理本地临时镜像

## 🛠️ 方式2: 手动操作步骤

### Step 1: 安装Docker (如果未安装)
```bash
# macOS用户
brew install --cask docker

# 或下载Docker Desktop
# https://docs.docker.com/desktop/mac/install/
```

### Step 2: 启动Docker
确保Docker Desktop已启动并运行。

### Step 3: 登录腾讯云Coding
```bash
docker login -u rorokey-1754558094217 -p fe4fb2ca7457e5db758227015c78e8fab3f52fb0 tencentpartner-docker.pkg.coding.net
```

### Step 4: 构建Docker镜像
```bash
# 在项目根目录执行
docker build -t hbase-validator:latest .
```

### Step 5: 给镜像打标签
```bash
docker tag hbase-validator:latest tencentpartner-docker.pkg.coding.net/rorokey/hbase-validator:latest
```

### Step 6: 推送镜像
```bash
docker push tencentpartner-docker.pkg.coding.net/rorokey/hbase-validator:latest
```

### Step 7: 验证推送成功
```bash
# 查看远程镜像
docker pull tencentpartner-docker.pkg.coding.net/rorokey/hbase-validator:latest
```

## 📂 相关文件说明

### 已更新的部署文件
- ✅ `simple-deploy.yaml` - 镜像地址已更新
- ✅ `hbase-validator-deploy.yaml` - 镜像地址已更新
- ✅ 两个文件都已配置正确的Coding镜像地址

### Dockerfile配置
```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
# ... 其他配置
EXPOSE 8501
CMD ["python", "run_app.py", "--host", "0.0.0.0", "--port", "8501"]
```

## 🎯 Kubernetes部署

镜像推送成功后，可以直接使用更新后的YAML文件部署：

### 简化版部署
```bash
kubectl apply -f simple-deploy.yaml
```

### 完整版部署
```bash
kubectl apply -f hbase-validator-deploy.yaml
```

## 🔍 故障排查

### 登录失败
```bash
# 检查用户名密码是否正确
# 检查网络连接
# 确认仓库地址无误
```

### 构建失败
```bash
# 检查Dockerfile语法
# 确保requirements.txt存在
# 检查项目文件完整性
```

### 推送失败
```bash
# 确认已成功登录
# 检查镜像标签是否正确
# 验证网络连接
```

### 权限问题
```bash
# 确认账号有推送权限
# 检查项目配置
# 联系管理员确认仓库访问权限
```

## 📊 镜像信息查看

### 查看本地镜像
```bash
docker images | grep hbase-validator
```

### 查看镜像详细信息
```bash
docker inspect tencentpartner-docker.pkg.coding.net/rorokey/hbase-validator:latest
```

### 查看镜像历史
```bash
docker history tencentpartner-docker.pkg.coding.net/rorokey/hbase-validator:latest
```

## 🧹 清理操作

### 清理本地镜像
```bash
# 删除本地构建的镜像
docker rmi hbase-validator:latest

# 删除标签镜像
docker rmi tencentpartner-docker.pkg.coding.net/rorokey/hbase-validator:latest

# 清理悬空镜像
docker image prune
```

### 批量清理
```bash
# 清理所有未使用的镜像
docker system prune -a
```

## 🔐 安全注意事项

1. **密码保护**: 不要在脚本中硬编码密码
2. **访问权限**: 确保只有授权人员能访问镜像仓库
3. **镜像扫描**: 定期扫描镜像安全漏洞
4. **版本管理**: 使用语义化版本号管理镜像

## 📈 性能优化

### 多阶段构建优化
```dockerfile
# 使用多阶段构建减小镜像大小
FROM python:3.11-slim as builder
# ... 构建阶段

FROM python:3.11-slim as runtime  
# ... 运行阶段
```

### 缓存优化
```bash
# 利用构建缓存加快构建速度
docker build --cache-from tencentpartner-docker.pkg.coding.net/rorokey/hbase-validator:latest -t hbase-validator:latest .
```

## 📞 技术支持

如遇问题，请提供：
1. 错误信息截图
2. 操作系统和Docker版本
3. 网络环境信息
4. 具体的操作步骤

---
**镜像地址**: `tencentpartner-docker.pkg.coding.net/rorokey/hbase-validator:latest`
