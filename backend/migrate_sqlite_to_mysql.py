#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 到 MySQL 数据迁移脚本

使用方法:
    # 导出 SQLite 数据
    python migrate_sqlite_to_mysql.py --export --sqlite ../debate_arena1.db

    # 导入数据到 MySQL（确保 .env 中 DATABASE_URL 已配置为 MySQL）
    python migrate_sqlite_to_mysql.py --import
"""

import sqlite3
import json
import os
import sys
from datetime import datetime


def export_sqlite_data(sqlite_path: str, output_dir: str = "migration_data"):
    """导出 SQLite 数据到 JSON 文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    tables = ['competitors', 'debate_topics', 'users', 'matches']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
            
            # 处理 JSON 字段
            for row in data:
                for key, value in row.items():
                    if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                        try:
                            row[key] = json.loads(value)
                        except:
                            pass
            
            output_file = os.path.join(output_dir, f"{table}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✓ 导出 {table}: {len(data)} 条记录")
        except Exception as e:
            print(f"✗ 导出 {table} 失败: {e}")
    
    conn.close()
    print(f"\n数据已导出到 {output_dir}/ 目录")


def import_to_mysql(data_dir: str = "migration_data"):
    """导入数据到 MySQL"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # 从环境变量读取 MySQL 连接
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url or 'mysql' not in database_url:
        print("错误: DATABASE_URL 未配置或不是 MySQL 连接")
        print("请在 .env 文件中配置:")
        print("DATABASE_URL=mysql+pymysql://user:password@host:3306/debate_arena?charset=utf8mb4")
        sys.exit(1)
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 导入 models 创建表
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from models import Base, CompetitorModel, DebateTopicModel, UserModel, MatchModel
    
    # 创建表结构
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表结构已创建")
    
    # 导入数据
    table_model_map = {
        'competitors': CompetitorModel,
        'debate_topics': DebateTopicModel,
        'users': UserModel,
        'matches': MatchModel
    }
    
    for table, Model in table_model_map.items():
        json_file = os.path.join(data_dir, f"{table}.json")
        if not os.path.exists(json_file):
            print(f"⚠ 跳过 {table}: 文件不存在")
            continue
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for row in data:
            # 移除 id 字段让 MySQL 自动生成
            row_copy = row.copy()
            if 'id' in row_copy:
                del row_copy['id']
            
            # 处理日期字段
            for key in ['created_at', 'last_match_at', 'last_login', 'finished_at']:
                if key in row_copy and row_copy[key]:
                    if isinstance(row_copy[key], str):
                        try:
                            row_copy[key] = datetime.fromisoformat(row_copy[key].replace('Z', '+00:00'))
                        except:
                            row_copy[key] = None
            
            try:
                obj = Model(**row_copy)
                session.add(obj)
                count += 1
            except Exception as e:
                print(f"⚠ 导入 {table} 记录失败: {e}")
        
        session.commit()
        print(f"✓ 导入 {table}: {count} 条记录")
    
    session.close()
    print("\n✓ 数据迁移完成！")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SQLite 到 MySQL 数据迁移")
    parser.add_argument('--export', action='store_true', help='导出 SQLite 数据')
    parser.add_argument('--import', dest='do_import', action='store_true', help='导入数据到 MySQL')
    parser.add_argument('--sqlite', default='debate_arena.db', help='SQLite 数据库文件路径')
    parser.add_argument('--data-dir', default='migration_data', help='数据目录')
    
    args = parser.parse_args()
    
    if args.export:
        # 查找 SQLite 文件
        sqlite_paths = [
            args.sqlite,
            f"./{args.sqlite}",
            f"../{args.sqlite}",
            "../debate_arena1.db",
        ]
        sqlite_path = None
        for path in sqlite_paths:
            if os.path.exists(path):
                sqlite_path = path
                break
        
        if not sqlite_path:
            print(f"错误: 找不到 SQLite 数据库文件")
            print(f"尝试过的路径: {sqlite_paths}")
            sys.exit(1)
        
        print(f"使用 SQLite 文件: {sqlite_path}")
        export_sqlite_data(sqlite_path, args.data_dir)
    
    elif args.do_import:
        import_to_mysql(args.data_dir)
    
    else:
        parser.print_help()
        print("\n示例:")
        print("  # 导出 SQLite 数据")
        print("  python migrate_sqlite_to_mysql.py --export --sqlite ../debate_arena1.db")
        print("")
        print("  # 导入数据到 MySQL")
        print("  python migrate_sqlite_to_mysql.py --import")
