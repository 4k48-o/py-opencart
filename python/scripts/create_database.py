#!/usr/bin/env python3
"""
Create OpenCart database tables from PHP schema
"""
import re
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


def parse_php_schema(php_file: Path) -> list:
    """Parse PHP schema file and extract table definitions"""
    with open(php_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tables = []
    
    # Find all table definitions
    table_pattern = r"\$tables\[\]\s*=\s*\[(.*?)\];"
    
    for match in re.finditer(table_pattern, content, re.DOTALL):
        table_def = match.group(1)
        
        # Extract table name
        name_match = re.search(r"'name'\s*=>\s*'([^']+)'", table_def)
        if not name_match:
            continue
        
        table_name = name_match.group(1)
        
        # Extract fields
        fields = []
        # Pattern to match field definitions, handling escaped quotes in type
        # Match from 'name' to 'type' and capture the type value which may contain escaped quotes
        field_pattern = r"\[\s*'name'\s*=>\s*'([^']+)',\s*'type'\s*=>\s*'((?:[^'\\]|\\.)+)'"
        
        for field_match in re.finditer(field_pattern, table_def):
            field_name = field_match.group(1)
            # Unescape the type string
            field_type = field_match.group(2).replace("\\'", "'").replace("\\\\", "\\")
            
            # Check for auto_increment
            auto_increment = "'auto_increment'" in field_match.group(0)
            
            # Check for default
            default_match = re.search(r"'default'\s*=>\s*'([^']*)'", field_match.group(0))
            default_value = default_match.group(1) if default_match else None
            
            # Check for not_null
            not_null = "'not_null'" in field_match.group(0)
            
            fields.append({
                'name': field_name,
                'type': field_type,
                'auto_increment': auto_increment,
                'default': default_value,
                'not_null': not_null
            })
        
        # Extract primary key
        primary_match = re.search(r"'primary'\s*=>\s*\[(.*?)\]", table_def, re.DOTALL)
        primary_keys = []
        if primary_match:
            primary_content = primary_match.group(1)
            for pk_match in re.finditer(r"'([^']+)'", primary_content):
                primary_keys.append(pk_match.group(1))
        
        # Extract indexes
        indexes = []
        index_pattern = r"\[\s*'name'\s*=>\s*'([^']+)',\s*'key'\s*=>\s*\[(.*?)\][^\]]*\]"
        for idx_match in re.finditer(index_pattern, table_def, re.DOTALL):
            index_name = idx_match.group(1)
            index_keys_content = idx_match.group(2)
            index_keys = []
            for key_match in re.finditer(r"'([^']+)'", index_keys_content):
                index_keys.append(key_match.group(1))
            indexes.append({
                'name': index_name,
                'keys': index_keys
            })
        
        tables.append({
            'name': table_name,
            'fields': fields,
            'primary': primary_keys,
            'indexes': indexes
        })
    
    return tables


def generate_create_table_sql(table: dict, db_prefix: str = 'oc_') -> str:
    """Generate CREATE TABLE SQL statement"""
    table_name = f"{db_prefix}{table['name']}"
    
    sql_parts = [f"CREATE TABLE IF NOT EXISTS `{table_name}` ("]
    
    # Add fields
    field_definitions = []
    for field in table['fields']:
        field_def = f"  `{field['name']}` {field['type']}"
        
        if field['not_null']:
            field_def += " NOT NULL"
        
        # TEXT/BLOB types cannot have default values in MySQL
        text_types = ['text', 'mediumtext', 'longtext', 'blob', 'mediumblob', 'longblob', 'json']
        is_text_type = any(field['type'].lower().startswith(t) for t in text_types)
        
        if field['default'] is not None and not is_text_type:
            if field['default'] == '':
                field_def += " DEFAULT ''"
            else:
                # Escape single quotes in default values
                escaped_default = field['default'].replace("'", "''")
                field_def += f" DEFAULT '{escaped_default}'"
        
        if field['auto_increment']:
            field_def += " AUTO_INCREMENT"
        
        field_definitions.append(field_def)
    
    sql_parts.append(",\n".join(field_definitions))
    
    # Add primary key
    if table['primary']:
        pk_fields = ', '.join(f"`{pk}`" for pk in table['primary'])
        sql_parts.append(f",\n  PRIMARY KEY ({pk_fields})")
    
    # Add indexes
    for index in table['indexes']:
        index_fields = ', '.join(f"`{key}`" for key in index['keys'])
        sql_parts.append(f",\n  KEY `{index['name']}` ({index_fields})")
    
    sql_parts.append("\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;")
    
    return '\n'.join(sql_parts)


def main():
    """Main function"""
    # Database connection settings - 从环境变量读取
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'opencart'),
        'charset': 'utf8mb4'
    }
    
    # Paths
    project_root = Path(__file__).parent.parent
    php_schema = project_root.parent / 'php' / 'upload' / 'system' / 'helper' / 'db_schema.php'
    
    print(f"Reading schema from: {php_schema}")
    
    # Parse schema
    tables = parse_php_schema(php_schema)
    print(f"Found {len(tables)} tables\n")
    
    # Connect to database
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        print("✓ Connected to MySQL database\n")
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        sys.exit(1)
    
    # Create tables
    db_prefix = 'oc_'
    created = 0
    errors = 0
    
    for table in tables:
        try:
            sql = generate_create_table_sql(table, db_prefix)
            cursor.execute(sql)
            created += 1
            print(f"✓ Created table: {db_prefix}{table['name']}")
        except Exception as e:
            errors += 1
            print(f"✗ Error creating table {db_prefix}{table['name']}: {e}")
    
    connection.commit()
    cursor.close()
    connection.close()
    
    print(f"\n{'='*50}")
    print(f"Total tables: {len(tables)}")
    print(f"✓ Created: {created}")
    if errors > 0:
        print(f"✗ Errors: {errors}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()

