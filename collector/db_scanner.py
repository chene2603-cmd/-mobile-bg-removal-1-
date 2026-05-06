import os
import re
import json
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from common.logger import setup_logger

class DatabaseScanner:
    """数据库扫描器 - 采集层第二单元"""
    
    def __init__(self, output_dir="output"):
        self.logger = setup_logger("DBScanner")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.findings = []  # 标准化事实列表
        
        # 命名规范正则
        self.allowed_table_pattern = re.compile(r'^[a-z][a-z0-9_]*$', re.IGNORECASE)
        # 违规特征：中文、拼音混写、无意义缩写（长度<3且非标准缩写）
        self.bad_name_keywords = ['tmp', 'temp', 'bak', 'test', '旧', '新', '废弃']
        
    def _emit_finding(self, db_type: str, db_path: str, table_name: str, 
                      issue_type: str, details: dict):
        """标准化事实输出"""
        fact = {
            "layer": "collection",
            "scanner": "database",
            "db_type": db_type,
            "db_path": db_path,
            "table_name": table_name,
            "type": issue_type,   # unused_table, naming_violation, no_primary_key, orphan_foreign_key
            "timestamp": datetime.datetime.now().isoformat(),
            "details": details
        }
        self.findings.append(fact)
        self.logger.debug(f"{db_path} -> {table_name}: {issue_type}")
    
    # ---------- SQLite 扫描 ----------
    def scan_sqlite_db(self, db_path: str) -> List[Dict]:
        """扫描单个 SQLite 数据库文件"""
        if not os.path.exists(db_path):
            self.logger.warning(f"SQLite 文件不存在: {db_path}")
            return []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 获取所有用户表（排除 sqlite_ 系统表）
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                # 1. 检查是否为空表
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                row_count = cursor.fetchone()[0]
                if row_count == 0:
                    self._emit_finding("sqlite", db_path, table, "unused_table", {
                        "row_count": 0,
                        "reason": "表中无任何数据"
                    })
                
                # 2. 检查命名规范
                if not self.allowed_table_pattern.match(table):
                    self._emit_finding("sqlite", db_path, table, "naming_violation", {
                        "pattern": "只允许字母数字下划线，不建议中文或大写开头",
                        "actual": table
                    })
                elif any(kw in table.lower() for kw in self.bad_name_keywords):
                    self._emit_finding("sqlite", db_path, table, "naming_violation", {
                        "pattern": "包含临时/测试关键词",
                        "actual": table
                    })
                
                # 3. 检查主键
                cursor.execute(f"PRAGMA table_info(`{table}`)")
                columns = cursor.fetchall()
                has_pk = any(col[5] == 1 for col in columns)  # col[5] is pk flag
                if not has_pk:
                    self._emit_finding("sqlite", db_path, table, "no_primary_key", {
                        "column_count": len(columns),
                        "sample_columns": [col[1] for col in columns[:3]]
                    })
                
                # 4. 检查孤立外键（SQLite 外键约束通常不强制，但可检查定义）
                cursor.execute(f"PRAGMA foreign_key_list(`{table}`)")
                fks = cursor.fetchall()
                for fk in fks:
                    # 简单检查引用表是否存在
                    ref_table = fk[2]
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (ref_table,))
                    if not cursor.fetchone():
                        self._emit_finding("sqlite", db_path, table, "orphan_foreign_key", {
                            "foreign_key": fk,
                            "referenced_table_missing": ref_table
                        })
            conn.close()
        except Exception as e:
            self.logger.error(f"扫描 SQLite {db_path} 失败: {e}")
        return self.findings
    
    def discover_sqlite_files(self, root_path: str) -> List[str]:
        """递归发现所有 .db, .sqlite, .sqlite3 文件"""
        sqlite_files = []
        root = Path(root_path)
        for ext in ['*.db', '*.sqlite', '*.sqlite3', '*.db3']:
            sqlite_files.extend(root.rglob(ext))
        return [str(f) for f in sqlite_files]
    
    # ---------- Microsoft Access (.mdb/.accdb) 扫描 ----------
    def scan_access_db(self, mdb_path: str) -> List[Dict]:
        """
        扫描 Access 数据库（需要 pyodbc 和 Access Database Engine）
        若未安装驱动，则跳过并记录警告
        """
        try:
            import pyodbc
        except ImportError:
            self.logger.warning("未安装 pyodbc，跳过 Access 扫描。如需支持，请安装: pip install pyodbc")
            return []
        
        # 尝试连接 Access
        conn_str = (
            r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            f"DBQ={mdb_path};"
        )
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # 获取所有用户表
            cursor.execute("SELECT Name FROM MSysObjects WHERE Type=1 AND Flags=0")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                # 行数
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                row_count = cursor.fetchone()[0]
                if row_count == 0:
                    self._emit_finding("access", mdb_path, table, "unused_table", {"row_count": 0})
                
                # 命名检查
                if not self.allowed_table_pattern.match(table):
                    self._emit_finding("access", mdb_path, table, "naming_violation", {
                        "actual": table
                    })
                
                # 主键检查
                try:
                    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE TABLE_NAME='{table}' AND CONSTRAINT_NAME LIKE 'PK%'")
                    pk = cursor.fetchone()
                    if not pk:
                        self._emit_finding("access", mdb_path, table, "no_primary_key", {})
                except Exception:
                    pass
            
            conn.close()
        except Exception as e:
            self.logger.error(f"扫描 Access {mdb_path} 失败: {e}")
        return self.findings
    
    def discover_access_files(self, root_path: str) -> List[str]:
        """发现 .mdb, .accdb 文件"""
        access_files = []
        root = Path(root_path)
        for ext in ['*.mdb', '*.accdb']:
            access_files.extend(root.rglob(ext))
        return [str(f) for f in access_files]
    
    # ---------- SQL Server LocalDB 扫描（可选）----------
    def scan_sqlserver_localdb(self, instance_name="(localdb)\\MSSQLLocalDB") -> List[Dict]:
        """
        扫描 SQL Server LocalDB 实例（需要 pyodbc）
        """
        try:
            import pyodbc
        except ImportError:
            self.logger.warning("未安装 pyodbc，跳过 SQL Server LocalDB 扫描")
            return []
        
        conn_str = f"DRIVER={{SQL Server Native Client 11.0}};SERVER={instance_name};Trusted_Connection=yes;"
        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4")  # 排除系统库
            dbs = [row[0] for row in cursor.fetchall()]
            
            for db_name in dbs:
                cursor.execute(f"USE [{db_name}]; SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
                tables = cursor.fetchall()
                for schema, table in tables:
                    full_name = f"{schema}.{table}"
                    # 检查行数
                    cursor.execute(f"USE [{db_name}]; SELECT COUNT(*) FROM [{schema}].[{table}]")
                    row_count = cursor.fetchone()[0]
                    if row_count == 0:
                        self._emit_finding("sqlserver", instance_name, full_name, "unused_table", {
                            "database": db_name,
                            "row_count": 0
                        })
                    # 命名检查等可类似添加
            conn.close()
        except Exception as e:
            self.logger.error(f"SQL Server LocalDB 扫描失败: {e}")
        return self.findings
    
    # ---------- 综合入口 ----------
    def scan_all_databases(self, root_path: str, include_sqlserver_localdb: bool = True) -> List[Dict]:
        """扫描路径下所有发现的数据库"""
        self.logger.info(f"开始扫描数据库，根路径: {root_path}")
        
        # SQLite
        sqlite_files = self.discover_sqlite_files(root_path)
        self.logger.info(f"发现 {len(sqlite_files)} 个 SQLite 数据库文件")
        for db_file in sqlite_files:
            self.scan_sqlite_db(db_file)
        
        # Access
        access_files = self.discover_access_files(root_path)
        self.logger.info(f"发现 {len(access_files)} 个 Access 数据库文件")
        for mdb in access_files:
            self.scan_access_db(mdb)
        
        # SQL Server LocalDB (可选，不依赖文件路径)
        if include_sqlserver_localdb:
            self.scan_sqlserver_localdb()
        
        self.logger.info(f"数据库扫描完成，共发现 {len(self.findings)} 个问题事实")
        return self.findings
    
    def save_findings(self, filename=None):
        if filename is None:
            filename = f"db_scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            for finding in self.findings:
                f.write(json.dumps(finding, ensure_ascii=False) + '\n')
        self.logger.info(f"数据库扫描事实已保存至 {output_path}")
        return str(output_path)
    
    def print_summary(self):
        # 按类型统计
        type_count = {}
        for f in self.findings:
            t = f['type']
            type_count[t] = type_count.get(t, 0) + 1
        print("\n📊 数据库扫描结果汇总")
        for t, cnt in type_count.items():
            print(f"   {t}: {cnt}")
        print(f"   总计问题事实: {len(self.findings)}")

# 独立测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("请输入要扫描的路径: ").strip()
    
    scanner = DatabaseScanner()
    scanner.scan_all_databases(target)
    scanner.print_summary()
    scanner.save_findings()