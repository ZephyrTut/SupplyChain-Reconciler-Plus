"""
比对引擎 - 核心数据比对逻辑
"""
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional, Any
from config import COMPARE_STATUS


class CompareEngine:
    """Excel 数据比对引擎"""
    
    # 操作符映射：UI显示名 -> 内部代码
    OPERATOR_MAP = {
        "等于": "EQUALS",
        "不等于": "NOT_EQUALS",
        "包含": "CONTAINS",
        "不包含": "NOT_CONTAINS",
        "包含于": "IN_LIST",
        "大于": "GREATER",
        "小于": "LESS"
    }
    
    @staticmethod
    def convert_operator(operator: str) -> str:
        """转换UI操作符为内部代码"""
        return CompareEngine.OPERATOR_MAP.get(operator, operator)

    @staticmethod
    def clean_column(df: pd.DataFrame, clean_rules: List[Dict]) -> pd.DataFrame:
        """
        清洗列数据
        
        Args:
            df: DataFrame
            clean_rules: 清洗规则列表，每项包含:
                - column: 要清洗的列名
                - mode: "删除匹配" | "保留匹配" | "替换为"
                - regex: 正则表达式
                - replace: 替换值（仅"替换为"模式使用）
                
        Returns:
            清洗后的 DataFrame
        """
        if not clean_rules:
            return df
            
        df = df.copy()
        
        for rule in clean_rules:
            column = rule.get("column", "")
            mode = rule.get("mode", "删除匹配")
            regex = rule.get("regex", "")
            replace_val = rule.get("replace", "")
            
            if not column or column not in df.columns or not regex:
                continue
                
            try:
                if mode == "删除匹配":
                    # 删除匹配的内容，保留其他内容
                    df[column] = df[column].astype(str).str.replace(regex, "", regex=True).str.strip()
                elif mode == "保留匹配":
                    # 只保留匹配的内容
                    df[column] = df[column].astype(str).str.extract(f"({regex})", expand=False).fillna("")
                elif mode == "替换为":
                    # 将匹配的内容替换为指定值
                    df[column] = df[column].astype(str).str.replace(regex, replace_val, regex=True)
            except Exception as e:
                print(f"清洗列 {column} 时出错: {e}")
                
        return df

    @staticmethod
    def aggregate_manual_with_pivot(
        df: pd.DataFrame,
        key_col: str,
        value_col: str,
        pivot_config: Dict,
        filters: Optional[List[Tuple[str, str, str]]] = None
    ) -> Tuple[pd.DataFrame, List[str], List[str]]:
        """
        手工表透视聚合（区分出库/入库）
        
        Args:
            df: 手工表 DataFrame
            key_col: 主键列名
            value_col: 数值列名
            pivot_config: 透视配置，包含:
                - pivot_column: 透视列名
                - out_values: 出库值列表（如["发货", "退货"]）
                - in_values: 入库值列表（如["退仓"]）
            filters: 筛选条件列表
            
        Returns:
            (聚合后的 DataFrame, 出库列名列表, 入库列名列表)
            DataFrame 包含: key_col, 各透视列, 手工数量(=出库-入库)
        """
        if not pivot_config:
            return df, [], []
            
        pivot_column = pivot_config.get("pivot_column", "")
        out_values = pivot_config.get("out_values", [])
        in_values = pivot_config.get("in_values", [])
        
        if not pivot_column or pivot_column not in df.columns:
            return df, [], []
            
        df = df.copy()
        
        # 应用筛选条件
        if filters:
            for col, op, val in filters:
                if col not in df.columns:
                    continue
                col_data = df[col].astype(str)
                if op == "EQUALS":
                    df = df[col_data == val]
                elif op == "NOT_EQUALS":
                    df = df[col_data != val]
                elif op == "CONTAINS":
                    if isinstance(val, str):
                        values = [v.strip() for v in val.replace('；', ';').replace('，', ',').replace(';', ',').split(',') if v.strip()]
                    else:
                        values = [str(val)]
                    if values:
                        mask = col_data.str.contains(values[0], na=False, regex=False)
                        for v in values[1:]:
                            mask = mask | col_data.str.contains(v, na=False, regex=False)
                        df = df[mask]
                elif op == "IN_LIST":
                    if isinstance(val, str):
                        values = [v.strip() for v in val.replace('；', ';').replace('，', ',').replace(';', ',').split(',') if v.strip()]
                    else:
                        values = [str(val)]
                    df = df[col_data.isin(values)]
        
        # 转换数值列
        if value_col in df.columns:
            df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0)
        else:
            return df, [], []
        
        # 获取所有透视值（出库+入库）
        all_pivot_values = out_values + in_values
        if not all_pivot_values:
            # 没有指定出入库，按普通透视处理
            return df, [], []
        
        # 筛选只包含指定透视值的行
        df = df[df[pivot_column].astype(str).isin(all_pivot_values)]
        
        if df.empty:
            return df, out_values, in_values
        
        # 透视操作
        pivot_df = df.pivot_table(
            index=key_col,
            columns=pivot_column,
            values=value_col,
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # 确保所有指定的透视列都存在
        for pv in all_pivot_values:
            if pv not in pivot_df.columns:
                pivot_df[pv] = 0
        
        # 计算手工数量 = Σ出库 - Σ入库
        out_sum = pivot_df[[c for c in out_values if c in pivot_df.columns]].sum(axis=1) if out_values else 0
        in_sum = pivot_df[[c for c in in_values if c in pivot_df.columns]].sum(axis=1) if in_values else 0
        pivot_df["手工数量"] = out_sum - in_sum
        
        return pivot_df, out_values, in_values

    @staticmethod
    def make_key(df: pd.DataFrame, key_cols: List[str], keyname: str = "__KEY__") -> pd.DataFrame:
        """
        生成复合主键
        
        Args:
            df: DataFrame
            key_cols: 主键列名列表
            keyname: 生成的 Key 列名
            
        Returns:
            添加了主键列的 DataFrame
        """
        df = df.copy()
        key_parts = []
        for col in key_cols:
            if col in df.columns:
                key_parts.append(df[col].astype(str).str.strip().fillna(""))
            else:
                key_parts.append(pd.Series([""] * len(df)))
        
        df[keyname] = key_parts[0]
        for part in key_parts[1:]:
            df[keyname] = df[keyname] + " | " + part
        
        return df

    @staticmethod
    def aggregate_data(
        df: pd.DataFrame,
        key_col: str,
        value_cols: List[str],
        pivot_col: Optional[str] = None,
        filters: Optional[List[Tuple[str, str, str]]] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        聚合数据，支持透视
        
        Args:
            df: DataFrame
            key_col: 主键列名
            value_cols: 数值列名列表
            pivot_col: 透视列名 (可选)
            filters: 筛选条件列表 [(column, operator, value), ...]
            
        Returns:
            (聚合后的 DataFrame, 透视值列表)
        """
        df = df.copy()
        
        # 应用筛选条件
        if filters:
            for col, op, val in filters:
                if col not in df.columns:
                    continue
                col_data = df[col].astype(str)
                if op == "EQUALS":
                    df = df[col_data == val]
                elif op == "NOT_EQUALS":
                    df = df[col_data != val]
                elif op == "CONTAINS":
                    # 支持多值筛选（逗号或分号分隔，满足任一即可）
                    if isinstance(val, str):
                        values = [v.strip() for v in val.replace('；', ';').replace('，', ',').replace(';', ',').split(',') if v.strip()]
                    else:
                        values = [str(val)]
                    if values:
                        mask = col_data.str.contains(values[0], na=False, regex=False)
                        for v in values[1:]:
                            mask = mask | col_data.str.contains(v, na=False, regex=False)
                        df = df[mask]
                elif op == "NOT_CONTAINS":
                    # 支持多值筛选（不包含任何一个值）
                    if isinstance(val, str):
                        values = [v.strip() for v in val.replace('；', ';').replace('，', ',').replace(';', ',').split(',') if v.strip()]
                    else:
                        values = [str(val)]
                    if values:
                        mask = ~col_data.str.contains(values[0], na=False, regex=False)
                        for v in values[1:]:
                            mask = mask & ~col_data.str.contains(v, na=False, regex=False)
                        df = df[mask]
                elif op == "IN_LIST":
                    # 支持多值筛选（逗号或分号分隔）
                    if isinstance(val, str):
                        # 统一处理中英文逗号和分号
                        values = [v.strip() for v in val.replace('；', ';').replace('，', ',').replace(';', ',').split(',') if v.strip()]
                    else:
                        values = [str(val)]
                    df = df[col_data.isin(values)]
                elif op == "NOT_IN_LIST":
                    # 不包含于：不在列表中的记录
                    if isinstance(val, str):
                        values = [v.strip() for v in val.replace('；', ';').replace('，', ',').replace(';', ',').split(',') if v.strip()]
                    else:
                        values = [str(val)]
                    df = df[~col_data.isin(values)]
                elif op == "GREATER":
                    try:
                        df = df[pd.to_numeric(df[col], errors='coerce') > float(val)]
                    except:
                        pass
                elif op == "LESS":
                    try:
                        df = df[pd.to_numeric(df[col], errors='coerce') < float(val)]
                    except:
                        pass
        
        # 转换数值列
        for col in value_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        pivot_values = []
        
        if pivot_col and pivot_col in df.columns:
            # 获取透视值
            pivot_values = df[pivot_col].dropna().astype(str).unique().tolist()
            pivot_values = sorted([v for v in pivot_values if v.strip()])
            
            # 透视操作
            if value_cols:
                val_col = value_cols[0]
                pivot_df = df.pivot_table(
                    index=key_col,
                    columns=pivot_col,
                    values=val_col,
                    aggfunc='sum',
                    fill_value=0
                ).reset_index()
                
                # 重命名透视列（移除MultiIndex）
                if isinstance(pivot_df.columns, pd.MultiIndex):
                    pivot_df.columns = [f"{c1}_{c2}" if c2 else c1 for c1, c2 in pivot_df.columns]
                
                # 透视列就是除了key_col的其他列
                status_cols = [c for c in pivot_df.columns if c != key_col]
                
                # 计算总计
                numeric_cols = [c for c in status_cols if pd.api.types.is_numeric_dtype(pivot_df[c])]
                if numeric_cols:
                    pivot_df["系统总计"] = pivot_df[numeric_cols].sum(axis=1)
                else:
                    pivot_df["系统总计"] = 0
                
                return pivot_df, pivot_values
        
        # 普通聚合
        if value_cols:
            agg_dict = {col: 'sum' for col in value_cols if col in df.columns}
            if agg_dict:
                result = df.groupby(key_col, as_index=False).agg(agg_dict)
                return result, pivot_values
        
        # 只返回唯一键
        result = df[[key_col]].drop_duplicates()
        return result, pivot_values

    @staticmethod
    def merge_and_compare(
        manual_df: pd.DataFrame,
        system_df: pd.DataFrame,
        key_col: str,
        manual_val_col: str,
        system_val_col: str,
        diff_formula: Optional[str] = None,
        pivot_values: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        合并并比对两个表
        
        Args:
            manual_df: 手工表聚合结果
            system_df: 系统表聚合结果
            key_col: 主键列名
            manual_val_col: 手工表数值列名
            system_val_col: 系统表数值列名
            diff_formula: 差值计算公式 (可选)
            pivot_values: 透视值列表 (用于公式变量)
            
        Returns:
            比对结果 DataFrame
        """
        # 准备干净的数据副本，避免列名冲突
        manual_clean = manual_df.copy()
        system_clean = system_df.copy()
        
        # 重命名为标准列名
        if manual_val_col in manual_clean.columns:
            manual_clean = manual_clean.rename(columns={manual_val_col: "手工数量"})
        
        if system_val_col in system_clean.columns and system_val_col != "系统总计":
            system_clean = system_clean.rename(columns={system_val_col: "系统总计"})
        
        # 只保留需要的列进行merge
        manual_cols = [key_col, "手工数量"]
        system_cols = [key_col] + [c for c in system_clean.columns if c != key_col]
        
        manual_merge = manual_clean[manual_cols] if all(c in manual_clean.columns for c in manual_cols) else manual_clean
        system_merge = system_clean[system_cols] if len(system_cols) > 1 else system_clean
        
        # 合并数据（不会有列名冲突）
        result = manual_merge.merge(system_merge, on=key_col, how='outer')
        
        # 确保必要列存在
        if "手工数量" not in result.columns:
            result["手工数量"] = 0
        if "系统总计" not in result.columns:
            result["系统总计"] = 0
        
        # 转换为数值类型
        result["手工数量"] = pd.to_numeric(result["手工数量"], errors='coerce').fillna(0)
        result["系统总计"] = pd.to_numeric(result["系统总计"], errors='coerce').fillna(0)
        
        # 计算差值
        result["差值"] = CompareEngine._calc_diff(result, diff_formula, pivot_values)
        
        # 标记状态
        result["比对状态"] = result.apply(CompareEngine._label_row, axis=1)
        
        return result

    @staticmethod
    def _calc_diff(df: pd.DataFrame, formula: Optional[str], pivot_values: Optional[List[str]]) -> pd.Series:
        """
        根据公式计算差值
        
        Args:
            df: DataFrame
            formula: 差值公式，如 "手工数量 - (系统总计 - 已关闭)"
            pivot_values: 可用的透视变量列表
            
        Returns:
            差值 Series
        """
        if not formula or formula.strip() == "":
            # 默认公式
            return df["手工数量"] - df["系统总计"]
        
        def eval_formula(row):
            try:
                expr = formula
                
                # 替换变量
                variables = {
                    "手工数量": row.get("手工数量", 0) or 0,
                    "系统总计": row.get("系统总计", 0) or 0,
                }
                
                # 添加透视列变量
                if pivot_values:
                    for pv in pivot_values:
                        variables[pv] = row.get(pv, 0) or 0
                
                # 按变量名长度降序排序替换，避免部分匹配
                for var_name in sorted(variables.keys(), key=len, reverse=True):
                    expr = expr.replace(var_name, str(float(variables[var_name])))
                
                # 安全计算
                if re.match(r'^[\d\s+\-*/().]+$', expr):
                    return eval(expr)
                return row["手工数量"] - row["系统总计"]
            except Exception:
                return row["手工数量"] - row["系统总计"]
        
        return df.apply(eval_formula, axis=1)

    @staticmethod
    def _label_row(row) -> str:
        """标记单行的比对状态"""
        manual = row.get("手工数量", 0) or 0
        system = row.get("系统总计", 0) or 0
        diff = row.get("差值", 0) or 0
        
        manual_nan = pd.isna(row.get("手工数量"))
        system_nan = pd.isna(row.get("系统总计"))
        
        # 系统有但手工无
        if system > 0 and (manual_nan or manual == 0):
            return COMPARE_STATUS["system_only"]
        
        # 手工有但系统无
        if manual > 0 and (system_nan or system == 0):
            return COMPARE_STATUS["manual_only"]
        
        # 都为0或都不存在
        if manual == 0 and system == 0:
            return COMPARE_STATUS["match"]
        
        # 数值比较
        if abs(diff) < 0.001:
            return COMPARE_STATUS["match"]
        
        return COMPARE_STATUS["diff"]

    @staticmethod
    def get_preview_matches(
        manual_df: pd.DataFrame,
        system_df: pd.DataFrame,
        manual_key_cols: List[str],
        system_key_cols: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取匹配预览数据
        
        Args:
            manual_df: 手工表数据
            system_df: 系统表数据
            manual_key_cols: 手工表主键列
            system_key_cols: 系统表主键列
            limit: 预览行数
            
        Returns:
            匹配预览列表
        """
        def build_key(row, cols):
            parts = [str(row.get(c, '')).strip() for c in cols]
            return ' | '.join(parts)
        
        # 构建系统表键映射
        system_keys = {}
        for _, row in system_df.head(limit * 5).iterrows():
            key = build_key(row, system_key_cols)
            if key and key not in system_keys:
                system_keys[key] = row.to_dict()
        
        # 构建手工表键映射
        manual_keys = {}
        for _, row in manual_df.head(limit * 5).iterrows():
            key = build_key(row, manual_key_cols)
            if key and key not in manual_keys:
                manual_keys[key] = row.to_dict()
        
        # 生成预览
        preview = []
        seen = set()
        
        # 先从手工表取样
        for _, row in manual_df.head(limit).iterrows():
            key = build_key(row, manual_key_cols)
            if not key or key in seen:
                continue
            seen.add(key)
            
            sys_row = system_keys.get(key)
            status = "match" if sys_row else "manual_only"
            preview.append({
                "key": key,
                "manual": row.to_dict(),
                "system": sys_row,
                "status": status
            })
        
        # 再从系统表补充
        for _, row in system_df.head(limit).iterrows():
            key = build_key(row, system_key_cols)
            if not key or key in seen:
                continue
            seen.add(key)
            
            man_row = manual_keys.get(key)
            status = "match" if man_row else "system_only"
            preview.append({
                "key": key,
                "manual": man_row,
                "system": row.to_dict(),
                "status": status
            })
            
            if len(preview) >= limit:
                break
        
        return preview[:limit]
