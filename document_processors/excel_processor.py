"""
Excel文档处理器
处理XLSX和XLS格式文档的文本提取和元数据提取
"""

import logging
from typing import List, Dict, Any
import os

from .base_processor import BaseDocumentProcessor

# 日志配置
logger = logging.getLogger(__name__)

class ExcelProcessor(BaseDocumentProcessor):
    """Excel文档处理器"""
    
    def __init__(self):
        """初始化Excel处理器"""
        super().__init__()
    
    def can_process(self, file_path: str) -> bool:
        """判断是否可以处理Excel文件"""
        return file_path.lower().endswith(('.xlsx', '.xls'))
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['.xlsx', '.xls']
    
    def extract_text(self, file_path: str) -> str:
        """
        从Excel文件中提取文本
        
        Args:
            file_path: Excel文件路径
        
        Returns:
            提取的文本内容
        """
        try:
            return self._extract_from_excel(file_path)
                
        except Exception as e:
            logger.error(f"从Excel文档提取文本失败: {file_path} - {e}")
            return ""
    
    def _extract_from_excel(self, file_path: str) -> str:
        """从Excel文件提取文本"""
        try:
            import pandas as pd
            
            content = []
            content.append(f"Excel工作簿：{os.path.basename(file_path)}")
            content.append("=" * 60)
            
            # 读取Excel文件
            try:
                xl_file = pd.ExcelFile(file_path)
                sheet_names = xl_file.sheet_names
                
                content.append(f"工作表总数：{len(sheet_names)}")
                content.append(f"工作表列表：{', '.join(sheet_names)}")
                content.append("")
                
            except Exception as e:
                logger.error(f"无法读取Excel文件结构: {file_path} - {e}")
                return f"错误：无法读取Excel文件 - {str(e)}"
            
            # 处理每个工作表
            for sheet_name in sheet_names:
                try:
                    # 读取工作表数据
                    df = pd.read_excel(file_path, sheet_name=sheet_name, na_values=[''], keep_default_na=False)
                    
                    content.append(f"\n=== 工作表: {sheet_name} ===")
                    
                    if df.empty:
                        content.append("（此工作表为空）")
                        continue
                    
                    # 显示工作表基本信息
                    content.append(f"行数：{len(df)}")
                    content.append(f"列数：{len(df.columns)}")
                    content.append(f"列名：{', '.join(str(col) for col in df.columns)}")
                    content.append("")
                    
                    # 智能处理数据内容
                    if len(df) <= 100:  # 小表格：显示全部内容
                        content.append("【完整数据】")
                        content.append(self._format_dataframe(df))
                    else:  # 大表格：显示概要和前几行
                        content.append("【数据概要】")
                        content.append(f"总行数：{len(df)}")
                        
                        # 显示数据类型统计
                        dtype_counts = df.dtypes.value_counts()
                        content.append(f"数据类型分布：{dict(dtype_counts)}")
                        
                        # 显示前10行
                        content.append("\n【前10行数据】")
                        content.append(self._format_dataframe(df.head(10)))
                        
                        # 如果有数值列，显示统计信息
                        numeric_cols = df.select_dtypes(include=['number']).columns
                        if len(numeric_cols) > 0:
                            content.append(f"\n【数值列统计】")
                            stats = df[numeric_cols].describe()
                            content.append(self._format_dataframe(stats))
                    
                    content.append("")
                    
                except Exception as e:
                    logger.warning(f"处理工作表 {sheet_name} 失败: {e}")
                    content.append(f"=== 工作表: {sheet_name} ===")
                    content.append(f"错误：无法处理此工作表 - {str(e)}")
                    content.append("")
            
            return "\n".join(content)
            
        except Exception as e:
            logger.error(f"从Excel文件提取文本失败: {file_path} - {e}")
            return f"错误：无法处理Excel文件 - {str(e)}"
    
    def _format_dataframe(self, df) -> str:
        """格式化DataFrame为文本"""
        try:
            # 将DataFrame转换为字符串，保持良好的格式
            return df.to_string(index=True, max_cols=10, max_colwidth=50)
        except Exception as e:
            logger.warning(f"格式化DataFrame失败: {e}")
            return f"数据格式化失败: {str(e)}"
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取Excel文档元数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Excel元数据字典
        """
        try:
            import pandas as pd
            
            metadata_dict = {
                'document_type': 'Excel',
                'file_extension': os.path.splitext(file_path)[1].lower()
            }
            
            try:
                # 读取Excel文件基本信息
                xl_file = pd.ExcelFile(file_path)
                sheet_names = xl_file.sheet_names
                
                metadata_dict.update({
                    'sheet_count': len(sheet_names),
                    'sheet_names': sheet_names
                })
                
                # 分析每个工作表
                sheet_stats = {}
                total_rows = 0
                total_cols = 0
                total_cells_with_data = 0
                
                for sheet_name in sheet_names:
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, na_values=[''], keep_default_na=False)
                        
                        # 计算有数据的单元格数量
                        cells_with_data = df.count().sum()  # 非空单元格数
                        
                        sheet_stat = {
                            'rows': len(df),
                            'columns': len(df.columns),
                            'cells_with_data': int(cells_with_data),
                            'column_names': list(df.columns),
                            'data_types': df.dtypes.apply(str).to_dict()
                        }
                        
                        # 数值列统计
                        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                        text_cols = df.select_dtypes(include=['object']).columns.tolist()
                        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
                        
                        sheet_stat.update({
                            'numeric_columns': len(numeric_cols),
                            'text_columns': len(text_cols),
                            'date_columns': len(date_cols),
                            'numeric_column_names': numeric_cols,
                            'text_column_names': text_cols,
                            'date_column_names': date_cols
                        })
                        
                        sheet_stats[sheet_name] = sheet_stat
                        total_rows += len(df)
                        total_cols += len(df.columns)
                        total_cells_with_data += cells_with_data
                        
                    except Exception as e:
                        logger.warning(f"分析工作表 {sheet_name} 失败: {e}")
                        sheet_stats[sheet_name] = {'error': str(e)}
                
                metadata_dict.update({
                    'sheet_statistics': sheet_stats,
                    'total_rows': total_rows,
                    'total_columns': total_cols,
                    'total_cells_with_data': int(total_cells_with_data),
                    'data_density': total_cells_with_data / max(total_rows * total_cols, 1) if total_rows > 0 else 0
                })
                
                # 尝试提取Excel文件属性（如果有的话）
                try:
                    # 注意：pandas无法直接提取Excel文件的元数据属性
                    # 这里只能提供基本的文件分析结果
                    pass
                except Exception as e:
                    logger.debug(f"提取Excel文件属性失败: {e}")
                
            except Exception as e:
                logger.error(f"分析Excel文件结构失败: {file_path} - {e}")
                metadata_dict['error'] = str(e)
            
            return metadata_dict
            
        except Exception as e:
            logger.error(f"提取Excel元数据失败: {file_path} - {e}")
            return {
                'document_type': 'Excel',
                'error': str(e)
            } 