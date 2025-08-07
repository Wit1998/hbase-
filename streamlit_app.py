#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HBase数据迁移验证 Streamlit Web应用
提供用户友好的界面进行数据一致性验证
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
import threading
from datetime import datetime
import os
import io

from hbase_data_validator import HBaseDataValidator, HBaseConnection, ValidationResult


class ValidationSession:
    """验证会话管理"""
    def __init__(self):
        self.validator = None
        self.is_running = False
        self.progress = 0
        self.current_result = None
        self.error_message = None


def init_session_state():
    """初始化会话状态"""
    if 'validation_session' not in st.session_state:
        st.session_state.validation_session = ValidationSession()
    if 'validation_history' not in st.session_state:
        st.session_state.validation_history = []


def sidebar_config():
    """侧边栏配置"""
    st.sidebar.title("🔧 连接配置")
    
    # 源端配置
    st.sidebar.subheader("📥 源端HBase")
    source_host = st.sidebar.text_input("源端主机", value="localhost", key="source_host")
    source_port = st.sidebar.number_input("源端端口", value=9090, min_value=1, max_value=65535, key="source_port")
    source_table = st.sidebar.text_input("源端表名", value="hope_saas_oms:oms_order_info", key="source_table")
    
    # 目标端配置
    st.sidebar.subheader("📤 目标端HBase")
    target_host = st.sidebar.text_input("目标端主机", value="localhost", key="target_host")
    target_port = st.sidebar.number_input("目标端端口", value=9090, min_value=1, max_value=65535, key="target_port")
    target_table = st.sidebar.text_input("目标端表名", value="hope_saas_oms:oms_order_info", key="target_table")
    
    # 验证配置
    st.sidebar.subheader("⚙️ 验证配置")
    max_rows = st.sidebar.number_input("最大验证行数", value=1000, min_value=1, help="设置为0表示验证所有数据")
    max_workers = st.sidebar.slider("并发线程数", min_value=1, max_value=20, value=10)
    
    # 行键文件上传
    st.sidebar.subheader("📄 行键文件")
    uploaded_file = st.sidebar.file_uploader("上传行键文件 (可选)", type=['txt'])
    
    return {
        'source': HBaseConnection(source_host, source_port, source_table),
        'target': HBaseConnection(target_host, target_port, target_table),
        'max_rows': max_rows if max_rows > 0 else None,
        'max_workers': max_workers,
        'rowkeys_file': uploaded_file
    }


def test_connections(config):
    """测试连接"""
    st.subheader("🔍 连接测试")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("测试源端连接", type="secondary"):
            with st.spinner("测试源端连接中..."):
                try:
                    validator = HBaseDataValidator(config['source'], config['target'])
                    if validator.connect_source():
                        st.success("✅ 源端连接成功")
                        validator.disconnect()
                    else:
                        st.error("❌ 源端连接失败")
                except Exception as e:
                    st.error(f"❌ 源端连接出错: {str(e)}")
    
    with col2:
        if st.button("测试目标端连接", type="secondary"):
            with st.spinner("测试目标端连接中..."):
                try:
                    validator = HBaseDataValidator(config['source'], config['target'])
                    if validator.connect_target():
                        st.success("✅ 目标端连接成功")
                        validator.disconnect()
                    else:
                        st.error("❌ 目标端连接失败")
                except Exception as e:
                    st.error(f"❌ 目标端连接出错: {str(e)}")


def progress_callback(completed, total):
    """进度回调函数"""
    progress = completed / total
    st.session_state.validation_session.progress = progress


def run_validation(config):
    """运行验证"""
    session = st.session_state.validation_session
    
    try:
        # 创建验证器
        session.validator = HBaseDataValidator(config['source'], config['target'])
        
        # 连接数据库
        if not session.validator.connect_source():
            session.error_message = "无法连接源端HBase"
            return
        
        if not session.validator.connect_target():
            session.error_message = "无法连接目标端HBase"
            return
        
        # 开始验证
        if config['rowkeys_file']:
            # 使用上传的行键文件
            rowkeys_content = config['rowkeys_file'].read().decode('utf-8')
            rowkeys = [line.strip() for line in rowkeys_content.split('\n') if line.strip()]
            result = session.validator.validate_by_rowkeys_list(
                rowkeys, 
                config['max_workers'], 
                progress_callback
            )
        else:
            # 验证所有数据
            result = session.validator.validate_all_data(
                config['max_rows'], 
                config['max_workers'], 
                progress_callback
            )
        
        session.current_result = result
        session.validator.disconnect()
        
        # 保存到历史记录
        st.session_state.validation_history.append({
            'timestamp': datetime.now(),
            'result': result,
            'config': config
        })
        
    except Exception as e:
        session.error_message = f"验证过程出错: {str(e)}"
    finally:
        session.is_running = False


def validation_control(config):
    """验证控制面板"""
    st.subheader("🚀 数据验证")
    
    session = st.session_state.validation_session
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if not session.is_running:
            if st.button("开始验证", type="primary", use_container_width=True):
                session.is_running = True
                session.progress = 0
                session.current_result = None
                session.error_message = None
                
                # 在后台线程中运行验证
                thread = threading.Thread(target=run_validation, args=(config,))
                thread.daemon = True
                thread.start()
        else:
            st.button("验证进行中...", disabled=True, use_container_width=True)
    
    with col2:
        if session.current_result:
            if st.button("查看详细报告", use_container_width=True):
                st.session_state.show_detailed_report = True
    
    with col3:
        if session.current_result:
            report = session.validator.generate_report() if session.validator else {}
            if report:
                report_json = json.dumps(report, ensure_ascii=False, indent=2)
                st.download_button(
                    "下载报告",
                    data=report_json,
                    file_name=f"validation_report_{int(time.time())}.json",
                    mime="application/json",
                    use_container_width=True
                )
    
    # 显示进度
    if session.is_running:
        st.progress(session.progress, text=f"验证进度: {session.progress:.1%}")
    
    # 显示错误信息
    if session.error_message:
        st.error(session.error_message)


def display_validation_results():
    """显示验证结果"""
    session = st.session_state.validation_session
    
    if not session.current_result:
        return
    
    result = session.current_result
    
    st.subheader("📊 验证结果")
    
    # 汇总指标
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("总行数", result.total_rows)
    
    with col2:
        st.metric("匹配行数", result.matched_rows)
    
    with col3:
        st.metric("目标端缺失", result.missing_in_target)
    
    with col4:
        st.metric("数据不一致", result.data_mismatch)
    
    with col5:
        st.metric(
            "成功率", 
            f"{result.success_rate:.1f}%",
            delta=f"{result.success_rate - 100:.1f}%" if result.success_rate < 100 else None
        )
    
    # 可视化图表
    create_result_charts(result)


def create_result_charts(result: ValidationResult):
    """创建结果可视化图表"""
    col1, col2 = st.columns(2)
    
    with col1:
        # 饼图 - 数据分布
        labels = ['匹配', '目标端缺失', '源端缺失', '数据不一致', '错误']
        values = [
            result.matched_rows,
            result.missing_in_target,
            result.missing_in_source,
            result.data_mismatch,
            result.error_rows
        ]
        colors = ['#00D4AA', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values,
            marker_colors=colors,
            hole=0.4
        )])
        fig_pie.update_layout(title="数据验证结果分布")
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # 柱状图 - 详细统计
        categories = ['匹配', '目标端缺失', '源端缺失', '数据不一致', '错误']
        counts = [
            result.matched_rows,
            result.missing_in_target,
            result.missing_in_source,
            result.data_mismatch,
            result.error_rows
        ]
        
        fig_bar = px.bar(
            x=categories, 
            y=counts,
            color=counts,
            color_continuous_scale='Viridis',
            title="验证结果详细统计"
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)


def display_detailed_report():
    """显示详细报告"""
    session = st.session_state.validation_session
    
    if not session.current_result or not st.session_state.get('show_detailed_report', False):
        return
    
    st.subheader("📋 详细验证报告")
    
    # 关闭按钮
    if st.button("关闭详细报告"):
        st.session_state.show_detailed_report = False
        st.rerun()
    
    result = session.current_result
    
    # 过滤选项
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "状态过滤",
            options=['全部', 'matched', 'missing_in_target', 'missing_in_source', 'data_mismatch', 'error'],
            index=0
        )
    
    with col2:
        max_display = st.number_input("最大显示行数", value=100, min_value=10, max_value=1000)
    
    # 过滤数据
    details = result.details
    if status_filter != '全部':
        details = [d for d in details if d['status'] == status_filter]
    
    details = details[:max_display]
    
    # 显示详细信息
    if details:
        # 转换为DataFrame便于显示
        df_data = []
        for detail in details:
            row = {
                '行键': detail['rowkey'],
                '状态': detail['status'],
                '时间戳': datetime.fromtimestamp(detail['timestamp']).strftime('%H:%M:%S')
            }
            
            # 添加详细信息
            if 'message' in detail['details']:
                row['消息'] = detail['details']['message']
            
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # 展开详细信息
        if st.checkbox("显示详细错误信息"):
            for i, detail in enumerate(details[:10]):  # 只显示前10个详细信息
                with st.expander(f"行键: {detail['rowkey']} - {detail['status']}"):
                    st.json(detail['details'])
    else:
        st.info("没有符合条件的数据")


def display_validation_history():
    """显示验证历史"""
    if not st.session_state.validation_history:
        return
    
    st.subheader("📈 验证历史")
    
    history_data = []
    for i, record in enumerate(st.session_state.validation_history):
        history_data.append({
            '序号': i + 1,
            '时间': record['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            '总行数': record['result'].total_rows,
            '匹配行数': record['result'].matched_rows,
            '成功率': f"{record['result'].success_rate:.1f}%",
            '耗时': f"{record['result'].validation_time:.1f}s"
        })
    
    df_history = pd.DataFrame(history_data)
    st.dataframe(df_history, use_container_width=True)
    
    # 清空历史按钮
    if st.button("清空历史记录"):
        st.session_state.validation_history = []
        st.rerun()


def main():
    """主函数"""
    st.set_page_config(
        page_title="HBase数据迁移验证系统",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 HBase数据迁移验证系统")
    st.markdown("---")
    
    # 初始化会话状态
    init_session_state()
    
    # 侧边栏配置
    config = sidebar_config()
    
    # 主界面
    tab1, tab2, tab3 = st.tabs(["🔍 数据验证", "📊 结果分析", "📈 历史记录"])
    
    with tab1:
        # 连接测试
        test_connections(config)
        st.markdown("---")
        
        # 验证控制
        validation_control(config)
        st.markdown("---")
        
        # 实时结果显示
        if st.session_state.validation_session.is_running:
            st.info("🔄 验证正在进行中，请稍候...")
            time.sleep(1)
            st.rerun()
        
        # 显示验证结果
        display_validation_results()
    
    with tab2:
        # 详细报告
        display_detailed_report()
    
    with tab3:
        # 验证历史
        display_validation_history()
    
    # 页面底部信息
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>HBase数据迁移验证系统 | 支持大规模数据一致性验证</p>
        </div>
        """, 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
