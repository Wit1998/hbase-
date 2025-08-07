#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HBase数据迁移验证系统启动脚本
"""

import os
import sys
import subprocess
import argparse


def check_dependencies():
    """检查依赖库"""
    try:
        import streamlit
        import happybase
        import pandas
        import plotly
        import yaml
        print("✅ 所有依赖库已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("请运行: pip install -r requirements.txt")
        return False


def install_dependencies():
    """安装依赖库"""
    print("正在安装依赖库...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖库安装完成")
        return True
    except subprocess.CalledProcessError:
        print("❌ 依赖库安装失败")
        return False


def create_reports_dir():
    """创建报告目录"""
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        print(f"✅ 创建报告目录: {reports_dir}")


def run_streamlit(port=8501, host="localhost"):
    """运行Streamlit应用"""
    print(f"🚀 启动HBase数据迁移验证系统")
    print(f"📱 访问地址: http://{host}:{port}")
    print("🔗 按 Ctrl+C 停止应用")
    print("-" * 50)
    
    try:
        subprocess.run([
            "streamlit", "run", "streamlit_app.py",
            "--server.port", str(port),
            "--server.address", host,
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except FileNotFoundError:
        print("❌ 找不到streamlit命令，请确保已正确安装streamlit")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="HBase数据迁移验证系统")
    parser.add_argument("--port", type=int, default=8501, help="端口号 (默认: 8501)")
    parser.add_argument("--host", default="localhost", help="主机地址 (默认: localhost)")
    parser.add_argument("--install", action="store_true", help="安装依赖库")
    parser.add_argument("--check", action="store_true", help="检查依赖库")
    
    args = parser.parse_args()
    
    # 检查依赖
    if args.check:
        check_dependencies()
        return
    
    # 安装依赖
    if args.install:
        install_dependencies()
        return
    
    # 检查并安装依赖
    if not check_dependencies():
        choice = input("是否自动安装依赖库? (y/n): ").lower()
        if choice == 'y':
            if not install_dependencies():
                sys.exit(1)
        else:
            print("请手动安装依赖库后重试")
            sys.exit(1)
    
    # 创建必要目录
    create_reports_dir()
    
    # 启动应用
    run_streamlit(args.port, args.host)


if __name__ == "__main__":
    main()
