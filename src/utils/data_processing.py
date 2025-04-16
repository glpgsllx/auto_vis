import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Any, Union
import os
import traceback

def load_data_file(file_path: str) -> Tuple[pd.DataFrame, Union[str, None]]:
    """加载数据文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        Tuple[pd.DataFrame, str]: (DataFrame, 错误信息)
    """
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            # 尝试不同的编码和分隔符
            encodings = ['utf-8', 'gbk', 'latin1']
            separators = [',', '\t', ';']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                        # 如果读取成功且列数大于1，则返回
                        if df.shape[1] > 1:
                            return df, None
                    except Exception:
                        continue
            
            # 如果上面的组合都失败了，尝试最基本的读取
            df = pd.read_csv(file_path)
            return df, None
            
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
            return df, None
        else:
            return None, f"不支持的文件格式: {file_ext}"
    except Exception as e:
        error_info = f"加载文件失败: {str(e)}\n{traceback.format_exc()}"
        return None, error_info

def infer_column_descriptions(df: pd.DataFrame) -> Dict[str, str]:
    """基于数据自动推断列描述
    
    Args:
        df: 待分析的DataFrame
        
    Returns:
        Dict[str, str]: 列名到描述的映射
    """
    descriptions = {}
    
    for col in df.columns:
        # 获取列的数据类型
        col_type = df[col].dtype
        
        # 获取基本数据样本
        if df.shape[0] > 0:
            sample = df[col].iloc[0]
            sample_type = type(sample).__name__
        else:
            sample = None
            sample_type = "未知"
        
        # 推断列的用途
        col_lower = col.lower()
        description = ""
        
        # 时间相关列
        if 'date' in col_lower or 'time' in col_lower or 'year' in col_lower or 'month' in col_lower:
            if pd.api.types.is_datetime64_any_dtype(col_type):
                description = "时间/日期"
            else:
                description = "可能是时间/日期"
        
        # ID列
        elif 'id' in col_lower or col_lower.endswith('_id'):
            description = "ID/标识符"
        
        # 名称列
        elif 'name' in col_lower or 'title' in col_lower:
            description = "名称/标题"
        
        # 金额/价格列
        elif any(kw in col_lower for kw in ['price', 'cost', 'amount', 'salary', 'income', 'revenue', 'sale', '价格', '金额', '成本']):
            description = "金额/价格"
        
        # 数量列
        elif any(kw in col_lower for kw in ['count', 'quantity', 'number', 'num', 'qty', '数量']):
            description = "数量/计数"
        
        # 百分比/比率列
        elif any(kw in col_lower for kw in ['rate', 'ratio', 'percent', 'proportion', '比率', '百分比']):
            description = "比率/百分比"
        
        # 性别列
        elif 'gender' in col_lower or 'sex' in col_lower or '性别' in col_lower:
            description = "性别"
        
        # 年龄列
        elif 'age' in col_lower or '年龄' in col_lower:
            description = "年龄"
        
        # 类别/分类列
        elif any(kw in col_lower for kw in ['category', 'type', 'class', 'group', 'status', '类别', '类型', '分类']):
            description = "类别/分类"
        
        # 基于数据类型的默认描述
        else:
            if pd.api.types.is_numeric_dtype(col_type):
                # 检查是否可能是分类数据
                if df[col].nunique() < 10 and df.shape[0] > 20:
                    description = "可能是分类数值"
                else:
                    description = "数值"
            elif pd.api.types.is_string_dtype(col_type):
                # 检查文本长度
                if df[col].str.len().mean() > 100:
                    description = "长文本"
                else:
                    description = "文本"
            elif pd.api.types.is_bool_dtype(col_type):
                description = "布尔值/标志"
            else:
                description = f"{col_type}"
        
        descriptions[col] = description
    
    return descriptions

def process_data(df: pd.DataFrame) -> Dict[str, Any]:
    """处理数据并生成基本分析报告
    
    Args:
        df: 待分析的DataFrame
        
    Returns:
        Dict: 数据分析报告
    """
    report = {}
    
    # 基本信息
    report["行数"] = df.shape[0]
    report["列数"] = df.shape[1]
    report["内存使用"] = f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
    
    # 缺失值信息
    missing_values = df.isna().sum()
    report["缺失值"] = {}
    for col in df.columns:
        if missing_values[col] > 0:
            report["缺失值"][col] = f"{missing_values[col]} ({missing_values[col]/df.shape[0]:.1%})"
    
    # 数值列统计
    numeric_cols = df.select_dtypes(include=['number']).columns
    report["数值列统计"] = {}
    for col in numeric_cols:
        report["数值列统计"][col] = {
            "最小值": float(df[col].min()) if not pd.isna(df[col].min()) else None,
            "最大值": float(df[col].max()) if not pd.isna(df[col].max()) else None,
            "平均值": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
            "中位数": float(df[col].median()) if not pd.isna(df[col].median()) else None,
            "标准差": float(df[col].std()) if not pd.isna(df[col].std()) else None
        }
    
    # 分类列统计
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    report["分类列统计"] = {}
    for col in categorical_cols:
        if df[col].nunique() < 20:  # 只处理基数不太高的分类列
            value_counts = df[col].value_counts().to_dict()
            # 将计数转换为字符串表示
            formatted_counts = {str(k): f"{v} ({v/df.shape[0]:.1%})" for k, v in value_counts.items()}
            report["分类列统计"][col] = formatted_counts
    
    # 时间列分析
    date_cols = df.select_dtypes(include=['datetime']).columns
    report["时间列分析"] = {}
    for col in date_cols:
        report["时间列分析"][col] = {
            "最早": str(df[col].min()) if not pd.isna(df[col].min()) else None,
            "最晚": str(df[col].max()) if not pd.isna(df[col].max()) else None,
            "时间跨度(天)": (df[col].max() - df[col].min()).days if not pd.isna(df[col].min()) and not pd.isna(df[col].max()) else None
        }
    
    return report 