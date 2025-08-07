#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HBase数据迁移验证系统 - 命令行版本
提供命令行接口进行数据验证
"""

import argparse
import json
import sys
import time
from typing import List

from hbase_data_validator import HBaseDataValidator, HBaseConnection
from config_manager import ConfigManager


class ProgressBar:
    """简单的进度条显示"""
    
    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0
    
    def update(self, current: int):
        """更新进度"""
        self.current = current
        percent = current / self.total if self.total > 0 else 0
        filled = int(self.width * percent)
        bar = '█' * filled + '░' * (self.width - filled)
        
        print(f'\r验证进度: |{bar}| {percent:.1%} ({current}/{self.total})', end='', flush=True)
    
    def finish(self):
        """完成进度条"""
        print()


class CLIValidator:
    """命令行验证器"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.validator = None
        self.progress_bar = None
    
    def progress_callback(self, completed: int, total: int):
        """进度回调"""
        if self.progress_bar is None:
            self.progress_bar = ProgressBar(total)
        self.progress_bar.update(completed)
    
    def create_validator_from_config(self) -> HBaseDataValidator:
        """从配置创建验证器"""
        source_config = self.config_manager.get_source_config()
        target_config = self.config_manager.get_target_config()
        
        source_conn = HBaseConnection(
            host=source_config.get('host', 'localhost'),
            port=source_config.get('port', 9090),
            table_name=source_config.get('table_name', ''),
            timeout=source_config.get('timeout', 30000)
        )
        
        target_conn = HBaseConnection(
            host=target_config.get('host', 'localhost'),
            port=target_config.get('port', 9090),
            table_name=target_config.get('table_name', ''),
            timeout=target_config.get('timeout', 30000)
        )
        
        return HBaseDataValidator(source_conn, target_conn)
    
    def create_validator_from_args(self, args) -> HBaseDataValidator:
        """从命令行参数创建验证器"""
        source_conn = HBaseConnection(
            host=args.source_host,
            port=args.source_port,
            table_name=args.source_table,
            timeout=30000
        )
        
        target_conn = HBaseConnection(
            host=args.target_host,
            port=args.target_port,
            table_name=args.target_table,
            timeout=30000
        )
        
        return HBaseDataValidator(source_conn, target_conn)
    
    def test_connections(self, validator: HBaseDataValidator) -> bool:
        """测试连接"""
        print("🔍 测试HBase连接...")
        
        # 测试源端
        print("  - 测试源端连接...", end='')
        if validator.connect_source():
            print(" ✅")
        else:
            print(" ❌")
            return False
        
        # 测试目标端
        print("  - 测试目标端连接...", end='')
        if validator.connect_target():
            print(" ✅")
        else:
            print(" ❌")
            return False
        
        print("✅ 连接测试通过")
        return True
    
    def load_rowkeys_from_file(self, filename: str) -> List[str]:
        """从文件加载行键"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                rowkeys = [line.strip() for line in f if line.strip()]
            print(f"📄 从文件加载了 {len(rowkeys)} 个行键")
            return rowkeys
        except Exception as e:
            print(f"❌ 加载行键文件失败: {e}")
            return []
    
    def validate_data(self, args):
        """执行数据验证"""
        # 创建验证器
        if args.use_config:
            validator = self.create_validator_from_config()
        else:
            validator = self.create_validator_from_args(args)
        
        self.validator = validator
        
        # 测试连接
        if not self.test_connections(validator):
            return False
        
        print(f"\n🚀 开始数据验证")
        print(f"📊 配置信息:")
        print(f"  - 源端: {validator.source_config.host}:{validator.source_config.port}")
        print(f"  - 目标端: {validator.target_config.host}:{validator.target_config.port}")
        print(f"  - 表名: {validator.source_config.table_name}")
        print(f"  - 最大行数: {args.max_rows or '不限制'}")
        print(f"  - 并发数: {args.max_workers}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            if args.rowkeys_file:
                # 使用行键文件验证
                rowkeys = self.load_rowkeys_from_file(args.rowkeys_file)
                if not rowkeys:
                    return False
                
                result = validator.validate_by_rowkeys_list(
                    rowkeys, args.max_workers, self.progress_callback
                )
            else:
                # 全量验证
                result = validator.validate_all_data(
                    args.max_rows, args.max_workers, self.progress_callback
                )
            
            if self.progress_bar:
                self.progress_bar.finish()
            
            # 显示结果
            self.display_results(result)
            
            # 保存报告
            if args.output:
                report_file = validator.save_report(args.output)
                if report_file:
                    print(f"📄 验证报告已保存: {report_file}")
            
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断验证")
            return False
        except Exception as e:
            print(f"\n❌ 验证失败: {e}")
            return False
        finally:
            validator.disconnect()
    
    def display_results(self, result):
        """显示验证结果"""
        print("\n" + "=" * 50)
        print("📊 验证结果汇总")
        print("=" * 50)
        
        print(f"总行数:     {result.total_rows:,}")
        print(f"匹配行数:   {result.matched_rows:,}")
        print(f"目标端缺失: {result.missing_in_target:,}")
        print(f"源端缺失:   {result.missing_in_source:,}")
        print(f"数据不一致: {result.data_mismatch:,}")
        print(f"错误行数:   {result.error_rows:,}")
        print(f"成功率:     {result.success_rate:.2f}%")
        print(f"耗时:       {result.validation_time:.2f}秒")
        
        # 状态图标
        if result.success_rate == 100.0:
            print("\n🎉 数据完全一致！")
        elif result.success_rate >= 95.0:
            print(f"\n✅ 数据基本一致 ({result.success_rate:.1f}%)")
        elif result.success_rate >= 80.0:
            print(f"\n⚠️ 数据存在差异 ({result.success_rate:.1f}%)")
        else:
            print(f"\n❌ 数据差异较大 ({result.success_rate:.1f}%)")
        
        print("=" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="HBase数据迁移验证系统 - 命令行版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用配置文件验证
  python cli_validator.py --use-config
  
  # 指定连接参数验证
  python cli_validator.py \\
    --source-host source-host --source-table table1 \\
    --target-host target-host --target-table table1
  
  # 使用行键文件验证
  python cli_validator.py --use-config --rowkeys-file rowkeys.txt
  
  # 限制验证行数和并发
  python cli_validator.py --use-config --max-rows 1000 --max-workers 5
        """
    )
    
    # 连接配置
    parser.add_argument("--use-config", action="store_true", 
                       help="使用config.yaml配置文件")
    
    parser.add_argument("--source-host", default="localhost",
                       help="源端HBase主机 (默认: localhost)")
    parser.add_argument("--source-port", type=int, default=9090,
                       help="源端HBase端口 (默认: 9090)")
    parser.add_argument("--source-table", 
                       help="源端表名")
    
    parser.add_argument("--target-host", default="localhost",
                       help="目标端HBase主机 (默认: localhost)")
    parser.add_argument("--target-port", type=int, default=9090,
                       help="目标端HBase端口 (默认: 9090)")
    parser.add_argument("--target-table",
                       help="目标端表名")
    
    # 验证配置
    parser.add_argument("--max-rows", type=int,
                       help="最大验证行数 (默认: 不限制)")
    parser.add_argument("--max-workers", type=int, default=10,
                       help="并发线程数 (默认: 10)")
    parser.add_argument("--rowkeys-file",
                       help="行键文件路径")
    
    # 输出配置
    parser.add_argument("--output", "-o",
                       help="输出报告文件名")
    
    args = parser.parse_args()
    
    # 参数验证
    if not args.use_config:
        if not args.source_table or not args.target_table:
            print("❌ 请指定源端和目标端表名，或使用 --use-config")
            sys.exit(1)
    
    # 创建验证器并运行
    cli_validator = CLIValidator()
    
    print("🔍 HBase数据迁移验证系统 - 命令行版本")
    print("-" * 50)
    
    if cli_validator.validate_data(args):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
