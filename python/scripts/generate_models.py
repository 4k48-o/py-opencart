#!/usr/bin/env python3
"""
Generate Tortoise ORM models from OpenCart PHP database schema
"""
import re
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Business domain classification rules
BUSINESS_DOMAINS = {
    'system': [
        r'^api', r'^setting$', r'^store$', r'^cron$', r'^event$',
        r'^extension$', r'^modification$', r'^session$', r'^user',
        r'^seo_url$', r'^translation$'
    ],
    'localisation': [
        r'^country', r'^zone', r'^currency$', r'^language$', r'^geo_zone',
        r'^tax_', r'^weight_class$', r'^length_class$', r'^address_format',
        r'^location$', r'_status$', r'^return_', r'^subscription_status$'
    ],
    'customer': [
        r'^customer', r'^address$'
    ],
    'catalog': [
        r'^product', r'^category', r'^manufacturer', r'^attribute',
        r'^option', r'^filter', r'^download', r'^review', r'^subscription_plan',
        r'^identifier$'
    ],
    'order': [
        r'^order', r'^cart$', r'^returns', r'^coupon', r'^voucher'
    ],
    'marketing': [
        r'^marketing', r'^affiliate'
    ],
    'cms': [
        r'^article', r'^topic', r'^information', r'^antispam$'
    ],
    'design': [
        r'^banner', r'^layout', r'^theme$'
    ],
    'report': [
        r'^statistics$', r'^product_viewed$'
    ]
}


def classify_table(table_name: str) -> str:
    """Classify table into business domain"""
    for domain, patterns in BUSINESS_DOMAINS.items():
        for pattern in patterns:
            if re.match(pattern, table_name):
                return domain
    # Default to system if no match
    return 'system'


# Type mapping from MySQL to Tortoise ORM
TYPE_MAPPING = {
    'int': 'IntField',
    'tinyint': 'SmallIntField',
    'smallint': 'SmallIntField',
    'mediumint': 'IntField',
    'bigint': 'BigIntField',
    'varchar': 'CharField',
    'char': 'CharField',
    'text': 'TextField',
    'mediumtext': 'TextField',
    'longtext': 'TextField',
    'datetime': 'DatetimeField',
    'date': 'DateField',
    'time': 'TimeField',
    'timestamp': 'DatetimeField',
    'decimal': 'DecimalField',
    'float': 'FloatField',
    'double': 'FloatField',
    'json': 'JSONField',
    'blob': 'BinaryField',
    'longblob': 'BinaryField',
}


def parse_mysql_type(mysql_type: str) -> Tuple[str, Dict]:
    """Parse MySQL type to Tortoise ORM field type and parameters"""
    mysql_type_orig = mysql_type
    mysql_type = mysql_type.lower().strip()
    
    # Handle enum type specially
    if mysql_type.startswith('enum'):
        # Extract enum values
        if '(' in mysql_type:
            enum_content = mysql_type.split('(', 1)[1].rstrip(')')
            # enum values are like 'day','week','semi_month','month','year'
            # Unescape and extract values
            enum_values = []
            for v in enum_content.split(','):
                v = v.strip().strip("'\"")
                # Handle escaped quotes
                v = v.replace("\\'", "'")
                enum_values.append(v)
            max_length = max(len(v) for v in enum_values) if enum_values else 32
            # Add some buffer for safety
            max_length = max(max_length, 32)
            return 'CharField', {'max_length': max_length}
    
    # Extract base type and parameters
    if '(' in mysql_type:
        base_type, params = mysql_type.split('(', 1)
        params = params.rstrip(')')
    else:
        base_type = mysql_type
        params = ''
    
    # Map to Tortoise type
    tortoise_type = TYPE_MAPPING.get(base_type, 'CharField')
    
    field_params = {}
    
    if base_type in ['varchar', 'char']:
        if params:
            field_params['max_length'] = int(params)
        else:
            field_params['max_length'] = 255
    
    elif base_type in ['int', 'tinyint', 'smallint', 'mediumint', 'bigint']:
        if params:
            # Extract size if present (e.g., int(11))
            pass  # Size is usually not needed in Tortoise
    
    elif base_type == 'decimal':
        if params:
            parts = params.split(',')
            if len(parts) == 2:
                field_params['max_digits'] = int(parts[0])
                field_params['decimal_places'] = int(parts[1])
    
    return tortoise_type, field_params


def python_name(name: str) -> str:
    """Convert database name to Python identifier"""
    # Handle Python keywords
    python_keywords = {
        'default': 'is_default',
        'return': 'return_obj',
        'class': 'class_obj',
        'import': 'import_obj',
        'from': 'from_obj',
        'as': 'as_obj',
        'if': 'if_obj',
        'else': 'else_obj',
        'elif': 'elif_obj',
        'for': 'for_obj',
        'while': 'while_obj',
        'def': 'def_obj',
        'lambda': 'lambda_obj',
        'try': 'try_obj',
        'except': 'except_obj',
        'finally': 'finally_obj',
        'with': 'with_obj',
        'pass': 'pass_obj',
        'break': 'break_obj',
        'continue': 'continue_obj',
        'and': 'and_obj',
        'or': 'or_obj',
        'not': 'not_obj',
        'is': 'is_obj',
        'in': 'in_obj',
        'del': 'del_obj',
        'global': 'global_obj',
        'nonlocal': 'nonlocal_obj',
        'assert': 'assert_obj',
        'yield': 'yield_obj',
        'raise': 'raise_obj',
    }
    return python_keywords.get(name, name)


def pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase"""
    parts = name.split('_')
    return ''.join(word.capitalize() for word in parts)


def parse_php_schema(php_file: Path) -> List[Dict]:
    """Parse PHP schema file and extract table definitions"""
    with open(php_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tables = []
    
    # Find all table definitions
    # Pattern: $tables[] = [ ... ];
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
        field_pattern = r"\[\s*'name'\s*=>\s*'([^']+)',\s*'type'\s*=>\s*'([^']+)'[^\]]*\]"
        
        for field_match in re.finditer(field_pattern, table_def):
            field_name = field_match.group(1)
            field_type = field_match.group(2)
            
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
        
        # Extract foreign keys
        foreign_keys = []
        foreign_pattern = r"\[\s*'key'\s*=>\s*'([^']+)',\s*'table'\s*=>\s*'([^']+)',\s*'field'\s*=>\s*'([^']+)'[^\]]*\]"
        for fk_match in re.finditer(foreign_pattern, table_def):
            foreign_keys.append({
                'key': fk_match.group(1),
                'table': fk_match.group(2),
                'field': fk_match.group(3)
            })
        
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
            'foreign': foreign_keys,
            'indexes': indexes
        })
    
    return tables


def generate_model_code(table: Dict, db_prefix: str = 'oc_') -> str:
    """Generate Tortoise ORM model code for a table"""
    table_name = table['name']
    class_name = pascal_case(table_name)
    domain = classify_table(table_name)
    
    # Generate imports
    imports = [
        "from tortoise.models import Model",
        "from tortoise import fields",
    ]
    
    # Check for cross-domain relationships
    foreign_tables = {fk['table']: classify_table(fk['table']) for fk in table['foreign']}
    cross_domain_imports = {}
    for fk_table, fk_domain in foreign_tables.items():
        if fk_domain != domain:
            if fk_domain not in cross_domain_imports:
                cross_domain_imports[fk_domain] = []
            cross_domain_imports[fk_domain].append(pascal_case(fk_table))
    
    # Generate field definitions
    field_definitions = []
    primary_key_field = None
    
    for field in table['fields']:
        field_name = python_name(field['name'])
        mysql_type = field['type']
        tortoise_type, field_params = parse_mysql_type(mysql_type)
        
        # Handle primary key
        if field['auto_increment'] or field['name'] in table['primary']:
            if len(table['primary']) == 1:
                field_params['pk'] = True
                primary_key_field = field['name']
        
        # Handle null
        if not field['not_null'] and not field_params.get('pk'):
            field_params['null'] = True
        
        # Handle default
        if field['default'] is not None and not field_params.get('pk'):
            default_val = field['default']
            if default_val == '':
                field_params['default'] = "''"
            elif default_val.isdigit():
                field_params['default'] = default_val
            elif default_val.replace('.', '').isdigit():
                field_params['default'] = default_val
            else:
                field_params['default'] = f"'{default_val}'"
        
        # Build field definition
        params_str = ', '.join(f"{k}={v}" if not isinstance(v, str) or v.startswith("'") or v.isdigit() else f"{k}='{v}'" for k, v in field_params.items())
        
        field_def = f"    {field_name} = fields.{tortoise_type}({params_str})"
        field_definitions.append(field_def)
    
    # Generate relationship methods
    relationship_methods = []
    for fk in table['foreign']:
        fk_field = python_name(fk['key'])
        fk_table = fk['table']
        fk_class = pascal_case(fk_table)
        fk_domain = classify_table(fk_table)
        fk_pk_field = fk['field']  # The primary key field name in the foreign table
        
        # Skip self-references
        if fk_table == table_name:
            method_name = f"get_{fk_table}"
            method_code = f"""    async def {method_name}(self):
        \"\"\"Get related {fk_class}\"\"\"
        if self.{fk_field}:
            # Self-reference: import locally to avoid circular import
            from .{fk_table} import {fk_class}
            return await {fk_class}.get({fk_pk_field}=self.{fk_field})
        return None"""
            relationship_methods.append(method_code)
            continue
        
        # Generate get method
        # Handle Python keywords in table names for imports
        # For Python keywords, we need to use importlib or __import__
        python_keywords = ['return', 'class', 'import', 'from', 'as', 'if', 'else', 'elif', 'for', 'while', 'def', 'lambda', 'try', 'except', 'finally', 'with', 'pass', 'break', 'continue', 'and', 'or', 'not', 'is', 'in', 'del', 'global', 'nonlocal', 'assert', 'yield', 'raise']
        
        if fk_table in python_keywords:
            # Use importlib for Python keywords - import in method instead
            # Don't add to imports, will import in method
            import_path = None
        else:
            if fk_domain == domain:
                import_path = f"from .{fk_table} import {fk_class}"
            else:
                import_path = f"from ..{fk_domain}.{fk_table} import {fk_class}"
        
        if import_path and import_path not in imports:
            imports.append(import_path)
        
        method_name = f"get_{fk_table}"
        
        # Handle Python keywords - import in method
        if fk_table in python_keywords:
            if fk_domain == domain:
                import_lines = [
                    "            from importlib import import_module",
                    f"            _module = import_module('app.models.{domain}.{fk_table}')",
                    f"            {fk_class} = getattr(_module, '{fk_class}')"
                ]
            else:
                import_lines = [
                    "            from importlib import import_module",
                    f"            _module = import_module('app.models.{fk_domain}.{fk_table}')",
                    f"            {fk_class} = getattr(_module, '{fk_class}')"
                ]
            import_block = "\n".join(import_lines)
            method_code = f"""    async def {method_name}(self):
        \"\"\"Get related {fk_class}\"\"\"
        if self.{fk_field}:
{import_block}
            return await {fk_class}.get({fk_pk_field}=self.{fk_field})
        return None"""
        else:
            method_code = f"""    async def {method_name}(self):
        \"\"\"Get related {fk_class}\"\"\"
        if self.{fk_field}:
            return await {fk_class}.get({fk_pk_field}=self.{fk_field})
        return None"""
        relationship_methods.append(method_code)
    
    # Generate Meta class
    meta_fields = [f"        table = \"{db_prefix}{table_name}\""]
    
    # Add indexes
    if table['indexes']:
        index_tuples = []
        for idx in table['indexes']:
            if len(idx['keys']) == 1:
                index_tuples.append(f"(\"{idx['keys'][0]}\",)")
            else:
                keys_str = ', '.join(f'"{k}"' for k in idx['keys'])
                index_tuples.append(f"({keys_str},)")
        meta_fields.append(f"        indexes = [{', '.join(index_tuples)}]")
    
    # Handle composite primary keys
    if len(table['primary']) > 1:
        pk_tuple = ', '.join(f'"{pk}"' for pk in table['primary'])
        meta_fields.append(f"        unique_together = (({pk_tuple}),)")
    
    # Generate enhanced docstring with field descriptions
    field_docs = []
    for field in table['fields']:
        field_name = python_name(field['name'])
        field_type = field['type']
        is_pk = field['auto_increment'] or field['name'] in table['primary']
        is_nullable = not field['not_null'] and not is_pk
        default_val = field.get('default')
        
        field_desc = f"        {field_name} ({field_type})"
        if is_pk:
            field_desc += " - Primary key"
        if is_nullable:
            field_desc += ", nullable"
        if default_val is not None:
            field_desc += f", default: {default_val}"
        field_docs.append(field_desc)
    
    # Generate class docstring
    class_docstring = [
        '    """',
        f'    {class_name} model',
        '    ',
        f'    Represents the {table_name} table in the OpenCart database.',
        '    ',
        '    Attributes:',
    ] + field_docs + [
        '    """',
    ]
    
    # Combine all parts
    code_parts = [
        '"""',
        f'Tortoise ORM model for {table_name} table',
        '"""',
        '',
    ] + imports + [
        '',
        '',
        f'class {class_name}(Model):',
    ] + class_docstring + [
        '',
    ] + field_definitions + [
        '',
        '    class Meta:',
    ] + meta_fields + [
        '',
    ] + relationship_methods + [
        '',
    ]
    
    return '\n'.join(code_parts)


def generate_init_file(models: List[str], domain: str) -> str:
    """Generate __init__.py file for a domain"""
    imports = [f"from .{model} import {pascal_case(model)}" for model in models]
    imports.append('')
    imports.append('__all__ = [')
    imports.extend([f"    '{pascal_case(model)}'," for model in models])
    imports.append(']')
    
    return '\n'.join(imports)


def main():
    """Main function"""
    # Paths
    project_root = Path(__file__).parent.parent
    php_schema = project_root.parent / 'php' / 'upload' / 'system' / 'helper' / 'db_schema.php'
    models_dir = project_root / 'app' / 'models'
    
    print(f"Reading schema from: {php_schema}")
    
    # Parse schema
    tables = parse_php_schema(php_schema)
    print(f"Found {len(tables)} tables")
    
    # Group tables by domain
    tables_by_domain: Dict[str, List[Dict]] = {}
    for table in tables:
        domain = classify_table(table['name'])
        if domain not in tables_by_domain:
            tables_by_domain[domain] = []
        tables_by_domain[domain].append(table)
    
    # Create domain directories
    for domain in tables_by_domain.keys():
        domain_dir = models_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        (domain_dir / '__init__.py').touch()
    
    # Generate models
    db_prefix = 'oc_'
    for domain, domain_tables in tables_by_domain.items():
        print(f"\nGenerating models for domain: {domain} ({len(domain_tables)} tables)")
        domain_dir = models_dir / domain
        model_names = []
        
        for table in domain_tables:
            model_code = generate_model_code(table, db_prefix)
            model_name = table['name']
            model_file = domain_dir / f"{model_name}.py"
            
            with open(model_file, 'w', encoding='utf-8') as f:
                f.write(model_code)
            
            model_names.append(model_name)
            print(f"  Generated: {model_name}.py")
        
        # Generate __init__.py for domain
        init_content = generate_init_file(model_names, domain)
        with open(domain_dir / '__init__.py', 'w', encoding='utf-8') as f:
            f.write(init_content)
    
    # Generate root __init__.py
    root_init = [
        '"""',
        'Models package - all business domain models',
        '"""',
        '',
    ]
    for domain in sorted(tables_by_domain.keys()):
        root_init.append(f"from .{domain} import *")
    
    with open(models_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(root_init))
    
    print(f"\n✓ Generated {len(tables)} models across {len(tables_by_domain)} domains")
    print(f"✓ Models directory: {models_dir}")


if __name__ == '__main__':
    main()

