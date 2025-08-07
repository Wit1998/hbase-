#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
用于管理HBase验证系统的配置
"""

import yaml
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ValidationConfig:
    """验证配置数据类"""
    max_rows: int = 1000
    max_workers: int = 10
    batch_size: int = 100
    timeout: int = 300
    verbose: bool = True
    sample_rate: float = 1.0


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f) or {}
            else:
                print(f"配置文件 {self.config_file} 不存在，使用默认配置")
                self.config_data = self.get_default_config()
                self.save_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config_data = self.get_default_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'source': {
                'host': 'localhost',
                'port': 9090,
                'table_name': 'hope_saas_oms:oms_order_info',
                'timeout': 30000
            },
            'target': {
                'host': 'localhost',
                'port': 9090,
                'table_name': 'hope_saas_oms:oms_order_info',
                'timeout': 30000
            },
            'validation': {
                'max_rows': 1000,
                'max_workers': 10,
                'batch_size': 100,
                'timeout': 300,
                'verbose': True,
                'sample_rate': 1.0
            },
            'report': {
                'output_dir': './reports',
                'formats': ['json', 'excel'],
                'include_details': True,
                'max_detail_records': 1000
            },
            'logging': {
                'level': 'INFO',
                'file': 'hbase_validation.log',
                'format': '%(asctime)s - %(levelname)s - %(message)s'
            },
            'ui': {
                'title': 'HBase数据迁移验证系统',
                'default_display_rows': 100,
                'refresh_interval': 5
            }
        }
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_source_config(self):
        """获取源端配置"""
        return self.config_data.get('source', {})
    
    def get_target_config(self):
        """获取目标端配置"""
        return self.config_data.get('target', {})
    
    def get_validation_config(self) -> ValidationConfig:
        """获取验证配置"""
        config = self.config_data.get('validation', {})
        return ValidationConfig(
            max_rows=config.get('max_rows', 1000),
            max_workers=config.get('max_workers', 10),
            batch_size=config.get('batch_size', 100),
            timeout=config.get('timeout', 300),
            verbose=config.get('verbose', True),
            sample_rate=config.get('sample_rate', 1.0)
        )
    
    def get_report_config(self):
        """获取报告配置"""
        return self.config_data.get('report', {})
    
    def get_logging_config(self):
        """获取日志配置"""
        return self.config_data.get('logging', {})
    
    def get_ui_config(self):
        """获取UI配置"""
        return self.config_data.get('ui', {})
