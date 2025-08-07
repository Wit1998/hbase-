#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HBase数据迁移验证核心类
用于验证原端和目标端HBase数据的一致性
"""

import hashlib
import time
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

try:
    import happybase
except ImportError:
    print("请安装happybase库: pip install happybase")
    exit(1)


@dataclass
class HBaseConnection:
    """HBase连接配置"""
    host: str
    port: int = 9090
    table_name: str = ""
    timeout: int = 30000


@dataclass
class ValidationResult:
    """验证结果数据类"""
    total_rows: int = 0
    matched_rows: int = 0
    missing_in_target: int = 0
    missing_in_source: int = 0
    data_mismatch: int = 0
    error_rows: int = 0
    validation_time: float = 0.0
    details: List[Dict] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_rows == 0:
            return 0.0
        return (self.matched_rows / self.total_rows) * 100


class HBaseDataValidator:
    """HBase数据验证器"""
    
    def __init__(self, source_config: HBaseConnection, target_config: HBaseConnection):
        """
        初始化验证器
        
        Args:
            source_config: 源端HBase连接配置
            target_config: 目标端HBase连接配置
        """
        self.source_config = source_config
        self.target_config = target_config
        self.source_conn = None
        self.target_conn = None
        self.source_table = None
        self.target_table = None
        
        # 统计计数器
        self.lock = threading.Lock()
        self.result = ValidationResult()
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
    
    def setup_logging(self):
        """配置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hbase_validation.log'),
                logging.StreamHandler()
            ]
        )
    
    def connect_source(self) -> bool:
        """连接源端HBase"""
        try:
            self.logger.info(f"连接源端HBase: {self.source_config.host}:{self.source_config.port}")
            self.source_conn = happybase.Connection(
                host=self.source_config.host,
                port=self.source_config.port,
                timeout=self.source_config.timeout
            )
            
            # 测试连接
            tables = self.source_conn.tables()
            table_bytes = self.source_config.table_name.encode('utf-8')
            
            if table_bytes not in tables:
                self.logger.error(f"源端表不存在: {self.source_config.table_name}")
                return False
            
            self.source_table = self.source_conn.table(self.source_config.table_name)
            self.logger.info("源端连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"连接源端失败: {e}")
            return False
    
    def connect_target(self) -> bool:
        """连接目标端HBase"""
        try:
            self.logger.info(f"连接目标端HBase: {self.target_config.host}:{self.target_config.port}")
            self.target_conn = happybase.Connection(
                host=self.target_config.host,
                port=self.target_config.port,
                timeout=self.target_config.timeout
            )
            
            # 测试连接
            tables = self.target_conn.tables()
            table_bytes = self.target_config.table_name.encode('utf-8')
            
            if table_bytes not in tables:
                self.logger.error(f"目标端表不存在: {self.target_config.table_name}")
                return False
            
            self.target_table = self.target_conn.table(self.target_config.table_name)
            self.logger.info("目标端连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"连接目标端失败: {e}")
            return False
    
    def disconnect(self):
        """断开所有连接"""
        if self.source_conn:
            self.source_conn.close()
            self.logger.info("源端连接已断开")
        
        if self.target_conn:
            self.target_conn.close()
            self.logger.info("目标端连接已断开")
    
    def get_row_data(self, table, rowkey: str) -> Optional[Dict]:
        """获取行数据"""
        try:
            return table.row(rowkey.encode('utf-8'))
        except Exception as e:
            self.logger.warning(f"获取行数据失败 {rowkey}: {e}")
            return None
    
    def calculate_data_hash(self, data: Dict) -> str:
        """计算数据哈希值"""
        if not data:
            return ""
        
        # 将数据转换为排序后的字符串并计算MD5
        sorted_data = sorted(data.items())
        data_str = json.dumps(sorted_data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    def validate_single_row(self, rowkey: str) -> Dict:
        """验证单行数据"""
        result = {
            'rowkey': rowkey,
            'status': 'unknown',
            'details': {},
            'timestamp': time.time()
        }
        
        try:
            # 获取源端数据
            source_data = self.get_row_data(self.source_table, rowkey)
            target_data = self.get_row_data(self.target_table, rowkey)
            
            # 检查数据存在性
            if source_data is None and target_data is None:
                result['status'] = 'both_missing'
                result['details'] = {'message': '源端和目标端都没有此行数据'}
                
            elif source_data is None:
                result['status'] = 'missing_in_source'
                result['details'] = {
                    'message': '源端缺失此行数据',
                    'target_columns': len(target_data) if target_data else 0
                }
                with self.lock:
                    self.result.missing_in_source += 1
                    
            elif target_data is None:
                result['status'] = 'missing_in_target'
                result['details'] = {
                    'message': '目标端缺失此行数据',
                    'source_columns': len(source_data) if source_data else 0
                }
                with self.lock:
                    self.result.missing_in_target += 1
                    
            else:
                # 两端都有数据，进行详细对比
                source_hash = self.calculate_data_hash(source_data)
                target_hash = self.calculate_data_hash(target_data)
                
                if source_hash == target_hash:
                    result['status'] = 'matched'
                    result['details'] = {
                        'message': '数据完全一致',
                        'columns_count': len(source_data),
                        'data_hash': source_hash
                    }
                    with self.lock:
                        self.result.matched_rows += 1
                else:
                    result['status'] = 'data_mismatch'
                    mismatch_details = self.compare_row_details(source_data, target_data)
                    result['details'] = {
                        'message': '数据不一致',
                        'source_hash': source_hash,
                        'target_hash': target_hash,
                        'mismatches': mismatch_details
                    }
                    with self.lock:
                        self.result.data_mismatch += 1
            
            with self.lock:
                self.result.total_rows += 1
                
        except Exception as e:
            result['status'] = 'error'
            result['details'] = {'message': f'验证出错: {str(e)}'}
            with self.lock:
                self.result.error_rows += 1
                self.result.total_rows += 1
            
        return result
    
    def compare_row_details(self, source_data: Dict, target_data: Dict) -> Dict:
        """详细对比行数据差异"""
        mismatches = {
            'missing_columns_in_target': [],
            'missing_columns_in_source': [],
            'value_differences': []
        }
        
        source_columns = set(source_data.keys())
        target_columns = set(target_data.keys())
        
        # 找出缺失的列
        mismatches['missing_columns_in_target'] = list(source_columns - target_columns)
        mismatches['missing_columns_in_source'] = list(target_columns - source_columns)
        
        # 对比相同列的值
        common_columns = source_columns & target_columns
        for col in common_columns:
            if source_data[col] != target_data[col]:
                mismatches['value_differences'].append({
                    'column': col.decode('utf-8') if isinstance(col, bytes) else str(col),
                    'source_value': str(source_data[col]),
                    'target_value': str(target_data[col])
                })
        
        return mismatches
    
    def get_all_rowkeys(self, table, max_rows: Optional[int] = None) -> List[str]:
        """获取表中所有行键"""
        rowkeys = []
        try:
            scan_kwargs = {'columns': []}
            if max_rows:
                scan_kwargs['limit'] = max_rows
                
            for key, _ in table.scan(**scan_kwargs):
                rowkeys.append(key.decode('utf-8'))
                
        except Exception as e:
            self.logger.error(f"获取行键列表失败: {e}")
            
        return rowkeys
    
    def validate_by_rowkeys_list(self, rowkeys: List[str], max_workers: int = 10, 
                                progress_callback=None) -> ValidationResult:
        """根据行键列表进行验证"""
        self.logger.info(f"开始验证 {len(rowkeys)} 行数据")
        start_time = time.time()
        
        # 重置结果
        self.result = ValidationResult()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_rowkey = {
                executor.submit(self.validate_single_row, rowkey): rowkey 
                for rowkey in rowkeys
            }
            
            completed = 0
            for future in as_completed(future_to_rowkey):
                rowkey = future_to_rowkey[future]
                try:
                    result = future.result()
                    self.result.details.append(result)
                    
                    completed += 1
                    if progress_callback and completed % 100 == 0:
                        progress_callback(completed, len(rowkeys))
                        
                except Exception as e:
                    self.logger.error(f"处理行键 {rowkey} 时出错: {e}")
        
        self.result.validation_time = time.time() - start_time
        self.logger.info(f"验证完成，耗时 {self.result.validation_time:.2f} 秒")
        
        return self.result
    
    def validate_all_data(self, max_rows: Optional[int] = None, max_workers: int = 10,
                         progress_callback=None) -> ValidationResult:
        """验证所有数据"""
        # 获取源端所有行键
        self.logger.info("获取源端行键列表...")
        source_rowkeys = self.get_all_rowkeys(self.source_table, max_rows)
        
        if not source_rowkeys:
            self.logger.warning("源端没有数据")
            return ValidationResult()
        
        return self.validate_by_rowkeys_list(source_rowkeys, max_workers, progress_callback)
    
    def generate_report(self) -> Dict:
        """生成验证报告"""
        report = {
            'summary': {
                'total_rows': self.result.total_rows,
                'matched_rows': self.result.matched_rows,
                'missing_in_target': self.result.missing_in_target,
                'missing_in_source': self.result.missing_in_source,
                'data_mismatch': self.result.data_mismatch,
                'error_rows': self.result.error_rows,
                'success_rate': f"{self.result.success_rate:.2f}%",
                'validation_time': f"{self.result.validation_time:.2f}秒"
            },
            'configuration': {
                'source': {
                    'host': self.source_config.host,
                    'port': self.source_config.port,
                    'table': self.source_config.table_name
                },
                'target': {
                    'host': self.target_config.host,
                    'port': self.target_config.port,
                    'table': self.target_config.table_name
                }
            },
            'details': self.result.details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return report
    
    def save_report(self, filename: str = None):
        """保存验证报告到文件"""
        if filename is None:
            filename = f"hbase_validation_report_{int(time.time())}.json"
            
        report = self.generate_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"验证报告已保存到: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            return None
