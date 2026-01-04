#!/usr/bin/env python3
"""
Create test database opencart_test with the same structure as opencart
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

try:
    import pymysql
except ImportError:
    print("Error: pymysql not installed. Install it with: pip install pymysql")
    sys.exit(1)


def create_test_database():
    """Create test database and copy structure from opencart"""
    # Database connection settings - 从环境变量读取
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'charset': 'utf8mb4'
    }
    
    source_db = 'opencart'
    test_db = 'opencart_test'
    
    print(f"Creating test database: {test_db}")
    print(f"Source database: {source_db}")
    print(f"Host: {db_config['host']}:{db_config['port']}")
    print("-" * 50)
    
    try:
        # Connect to MySQL (without specifying database)
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        print("✓ Connected to MySQL server\n")
        
        # Check if test database exists
        cursor.execute(f"SHOW DATABASES LIKE '{test_db}'")
        if cursor.fetchone():
            print(f"⚠ Database '{test_db}' already exists")
            response = input("Do you want to drop and recreate it? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                cursor.execute(f"DROP DATABASE `{test_db}`")
                print(f"✓ Dropped existing database '{test_db}'")
            else:
                print("Cancelled. Exiting.")
                cursor.close()
                connection.close()
                return
        
        # Check if source database exists
        cursor.execute(f"SHOW DATABASES LIKE '{source_db}'")
        if not cursor.fetchone():
            print(f"✗ Source database '{source_db}' does not exist!")
            print("Please create the source database first.")
            cursor.close()
            connection.close()
            sys.exit(1)
        
        # Create test database
        cursor.execute(f"CREATE DATABASE `{test_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ Created database '{test_db}'\n")
        
        # Get all tables from source database
        cursor.execute(f"USE `{source_db}`")
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(tables)} tables in source database\n")
        
        # Copy table structures
        cursor.execute(f"USE `{test_db}`")
        copied = 0
        errors = 0
        
        for table in tables:
            try:
                # Get CREATE TABLE statement
                cursor.execute(f"USE `{source_db}`")
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_table_sql = cursor.fetchone()[1]
                
                # Execute in test database
                cursor.execute(f"USE `{test_db}`")
                cursor.execute(create_table_sql)
                copied += 1
                print(f"✓ Copied table structure: {table}")
            except Exception as e:
                errors += 1
                print(f"✗ Error copying table {table}: {e}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"\n{'='*50}")
        print(f"Total tables: {len(tables)}")
        print(f"✓ Copied: {copied}")
        if errors > 0:
            print(f"✗ Errors: {errors}")
        print(f"{'='*50}")
        print(f"\n✓ Test database '{test_db}' created successfully!")
        print(f"\nYou can now use this database for testing.")
        password_str = f":{db_config['password']}@" if db_config['password'] else "@"
        print(f"Connection string: mysql://{db_config['user']}{password_str}{db_config['host']}:{db_config['port']}/{test_db}")
        
    except pymysql.Error as e:
        print(f"✗ MySQL Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    create_test_database()

