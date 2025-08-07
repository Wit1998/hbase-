# 🔍 HBase数据迁移验证系统

一个功能完整的HBase数据迁移验证系统，提供Web界面进行原端和目标端数据一致性验证。

## ✨ 主要功能

- 🔗 **双端连接**: 同时连接源端和目标端HBase
- 🔍 **数据验证**: 行级数据一致性对比
- 📊 **可视化报告**: 实时图表展示验证结果
- 🚀 **并发处理**: 多线程提升验证效率
- 💾 **报告导出**: JSON/Excel格式报告下载
- 🎛️ **界面化操作**: Streamlit Web界面，操作简单
- 📈 **历史记录**: 验证历史追踪和对比

## 🏗️ 系统架构

```
HBase数据迁移验证系统/
├── hbase_data_validator.py    # 核心验证逻辑
├── streamlit_app.py          # Web界面应用
├── config_manager.py         # 配置管理器
├── run_app.py               # 启动脚本
├── requirements.txt         # 依赖库列表
├── config.yaml             # 配置文件
└── README.md              # 使用说明
```

## 🚀 快速开始

### 1. 环境准备

确保已安装Python 3.7+和HBase环境。

### 2. 安装依赖

```bash
# 克隆或下载项目
cd hbase-validation-system

# 自动安装依赖
python run_app.py --install

# 或手动安装
pip install -r requirements.txt
```

### 3. 配置系统

编辑 `config.yaml` 文件，配置您的HBase连接信息：

```yaml
# 源端HBase配置
source:
  host: "source-hbase-host"
  port: 9090
  table_name: "hope_saas_oms:oms_order_info"

# 目标端HBase配置  
target:
  host: "target-hbase-host"
  port: 9090
  table_name: "hope_saas_oms:oms_order_info"
```

### 4. 启动应用

```bash
# 使用启动脚本（推荐）
python run_app.py

# 或直接启动Streamlit
streamlit run streamlit_app.py

# 自定义端口和主机
python run_app.py --port 8502 --host 0.0.0.0
```

### 5. 访问界面

打开浏览器访问：`http://localhost:8501`

## 📖 使用指南

### 界面布局

- **侧边栏**: 连接配置和验证参数设置
- **数据验证标签页**: 连接测试、验证控制和结果展示
- **结果分析标签页**: 详细验证报告和数据分析
- **历史记录标签页**: 验证历史记录和趋势分析

### 验证流程

1. **配置连接**: 在侧边栏设置源端和目标端HBase连接参数
2. **测试连接**: 点击"测试连接"按钮确保连接正常
3. **设置参数**: 配置验证参数（最大行数、并发数等）
4. **开始验证**: 点击"开始验证"按钮启动数据验证
5. **查看结果**: 实时查看验证进度和结果统计
6. **下载报告**: 导出详细验证报告

### 验证模式

#### 1. 全量验证
验证表中所有数据的一致性。

#### 2. 采样验证
按比例随机抽样验证，适合大表快速检查。

#### 3. 行键文件验证
上传包含行键的文件，验证指定行的数据。

## 🔧 高级配置

### 配置文件详解

```yaml
validation:
  max_rows: 1000          # 最大验证行数，0表示不限制
  max_workers: 10         # 并发线程数
  batch_size: 100         # 批处理大小
  timeout: 300           # 超时时间（秒）
  sample_rate: 1.0       # 采样比例（1.0=100%）

report:
  output_dir: "./reports"     # 报告输出目录
  formats: ["json", "excel"]  # 报告格式
  include_details: true       # 是否包含详细信息
  max_detail_records: 1000    # 最大详细记录数
```

### 性能优化

1. **调整并发数**: 根据网络和服务器性能调整`max_workers`
2. **批处理**: 使用`batch_size`控制批处理大小
3. **采样验证**: 大表可先用`sample_rate`快速检查
4. **超时设置**: 根据网络延迟调整`timeout`值

## 📊 验证报告

### 报告内容

- **汇总统计**: 总行数、匹配数、缺失数、不一致数
- **成功率**: 数据一致性百分比
- **详细记录**: 每行数据的验证结果
- **错误信息**: 验证过程中的错误详情
- **性能指标**: 验证耗时、吞吐量等

### 报告格式

#### JSON报告
```json
{
  "summary": {
    "total_rows": 1000,
    "matched_rows": 950,
    "success_rate": "95.00%"
  },
  "details": [...]
}
```

#### Excel报告
包含多个工作表：
- `Summary`: 汇总信息
- `Details`: 详细验证结果
- `Errors`: 错误记录

## 🛠️ 命令行工具

### 检查依赖
```bash
python run_app.py --check
```

### 安装依赖
```bash
python run_app.py --install
```

### 自定义启动
```bash
# 指定端口
python run_app.py --port 8502

# 指定主机（允许外部访问）
python run_app.py --host 0.0.0.0

# 组合使用
python run_app.py --host 0.0.0.0 --port 8502
```

## 🔍 验证算法

### 数据对比策略

1. **行键存在性检查**: 检查行键在两端是否都存在
2. **列族完整性验证**: 对比列族和列的完整性
3. **数据值一致性**: 逐列对比数据值
4. **哈希校验**: 使用MD5哈希快速对比行数据

### 结果分类

- **✅ matched**: 数据完全一致
- **❌ missing_in_target**: 目标端缺失数据
- **❌ missing_in_source**: 源端缺失数据  
- **⚠️ data_mismatch**: 数据不一致
- **🔥 error**: 验证过程出错

## 📋 常见问题

### Q: 连接HBase失败怎么办？
A: 检查以下项目：
- HBase Thrift服务是否启动
- 网络连接是否正常
- 主机名和端口是否正确
- 防火墙设置

### Q: 验证速度慢怎么优化？
A: 可以尝试：
- 增加并发线程数
- 使用采样验证
- 调整批处理大小
- 检查网络延迟

### Q: 大表验证内存不足？
A: 建议：
- 分批验证
- 使用行键文件方式
- 增加系统内存
- 调整批处理大小

### Q: 如何自定义验证逻辑？
A: 可以修改 `hbase_data_validator.py` 中的以下方法：
- `validate_single_row()`: 单行验证逻辑
- `compare_row_details()`: 详细对比逻辑
- `calculate_data_hash()`: 哈希计算方法

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进系统！

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt

# 代码格式化
black *.py

# 代码检查
flake8 *.py

# 运行测试
pytest
```

## 📄 许可证

MIT License

## 📞 技术支持

如有问题，请通过以下方式联系：

- 📧 Email: support@example.com
- 💬 Issue: GitHub Issues
- 📚 文档: Wiki

---

**HBase数据迁移验证系统** - 让数据迁移验证变得简单高效！
