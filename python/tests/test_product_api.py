"""
Unit tests for Product API and Service
包含基础校验测试、逻辑校验测试、权限测试和API具体业务测试
"""
import pytest
import uuid
import json
from decimal import Decimal
from datetime import datetime, date
from httpx import AsyncClient
from app.main import app
from app.models.catalog.product import Product
from app.models.catalog.product_description import ProductDescription
from app.models.catalog.manufacturer import Manufacturer
from app.models.system.stock_status import StockStatus
from app.models.localisation.tax_class import TaxClass
from app.models.localisation.weight_class import WeightClass
from app.models.localisation.length_class import LengthClass
from app.models.system.weight_class_description import WeightClassDescription
from app.models.system.length_class_description import LengthClassDescription
from app.models.catalog.category import Category
from app.models.catalog.category_description import CategoryDescription
from app.models.catalog.attribute_group import AttributeGroup
from app.models.catalog.attribute_group_description import AttributeGroupDescription
from app.models.catalog.attribute import Attribute
from app.models.catalog.attribute_description import AttributeDescription
from app.models.catalog.option import Option
from app.models.catalog.option_description import OptionDescription
from app.models.catalog.option_value import OptionValue
from app.models.catalog.option_value_description import OptionValueDescription
from app.models.localisation.language import Language
from app.services.product_service import ProductService
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductDescriptionCreate
)
from app.exceptions import NotFoundException, ConflictException, ValidationException
from pydantic import ValidationError


# ==================== 用户角色权限梳理 ====================
"""
测试用户角色权限设计：

1. 管理员用户（admin_user）：
   - 权限：product:read, product:create, product:update, product:delete
   - 用途：测试正常业务流程

2. 只读用户（readonly_user）：
   - 权限：product:read
   - 用途：测试只读权限限制

3. 创建用户（create_user）：
   - 权限：product:read, product:create
   - 用途：测试创建权限，验证无法更新/删除

4. 更新用户（update_user）：
   - 权限：product:read, product:update
   - 用途：测试更新权限，验证无法创建/删除

5. 删除用户（delete_user）：
   - 权限：product:read, product:delete
   - 用途：测试删除权限，验证无法创建/更新

6. 无权限用户（no_permission_user）：
   - 权限：无
   - 用途：测试无权限访问
"""


# ==================== Fixtures: 测试用户和权限 ====================

@pytest.fixture
async def admin_user_group(db_transaction):
    """创建管理员用户组（完整权限）"""
    permissions = {
        "store": ["read", "create", "update", "delete"],
        "setting": ["read", "create", "update", "delete"],
        "language": ["read", "create", "update", "delete"],
        "currency": ["read", "create", "update", "delete"],
        "user": ["read", "create", "update", "delete"],
        "attribute_group": ["read", "create", "update", "delete"],
        "option": ["read", "create", "update", "delete"],
        "option_value": ["read", "create", "update", "delete"],
        "category": ["read", "create", "update", "delete"],
        "product": ["read", "create", "update", "delete"],
    }
    
    from app.models.system.user_group import UserGroup
    user_group = UserGroup(
        name=f"Admin Group_{uuid.uuid4().hex[:8]}",
        permission=json.dumps(permissions)
    )
    await user_group.save()
    return user_group


@pytest.fixture
async def readonly_user_group(db_transaction):
    """创建只读用户组"""
    permissions = {
        "product": ["read"],
    }
    
    from app.models.system.user_group import UserGroup
    user_group = UserGroup(
        name=f"Readonly Group_{uuid.uuid4().hex[:8]}",
        permission=json.dumps(permissions)
    )
    await user_group.save()
    return user_group


@pytest.fixture
async def create_user_group(db_transaction):
    """创建仅创建权限的用户组"""
    permissions = {
        "product": ["read", "create"],
    }
    
    from app.models.system.user_group import UserGroup
    user_group = UserGroup(
        name=f"Create Group_{uuid.uuid4().hex[:8]}",
        permission=json.dumps(permissions)
    )
    await user_group.save()
    return user_group


@pytest.fixture
async def update_user_group(db_transaction):
    """创建仅更新权限的用户组"""
    permissions = {
        "product": ["read", "update"],
    }
    
    from app.models.system.user_group import UserGroup
    user_group = UserGroup(
        name=f"Update Group_{uuid.uuid4().hex[:8]}",
        permission=json.dumps(permissions)
    )
    await user_group.save()
    return user_group


@pytest.fixture
async def delete_user_group(db_transaction):
    """创建仅删除权限的用户组"""
    permissions = {
        "product": ["read", "delete"],
    }
    
    from app.models.system.user_group import UserGroup
    user_group = UserGroup(
        name=f"Delete Group_{uuid.uuid4().hex[:8]}",
        permission=json.dumps(permissions)
    )
    await user_group.save()
    return user_group


@pytest.fixture
async def no_permission_user_group(db_transaction):
    """创建无权限用户组"""
    permissions = {}
    
    from app.models.system.user_group import UserGroup
    user_group = UserGroup(
        name=f"No Permission Group_{uuid.uuid4().hex[:8]}",
        permission=json.dumps(permissions)
    )
    await user_group.save()
    return user_group


@pytest.fixture
async def admin_user(db_transaction, admin_user_group):
    """创建管理员用户"""
    from app.models.system.user import User
    from app.core.security import get_password_hash
    
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        username=f"admin_{unique_id}",
        password=get_password_hash("testpass123"),
        user_group_id=admin_user_group.user_group_id,
        email=f"admin_{unique_id}@example.com",
        firstname="Admin",
        lastname="User",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    return user


@pytest.fixture
async def readonly_user(db_transaction, readonly_user_group):
    """创建只读用户"""
    from app.models.system.user import User
    from app.core.security import get_password_hash
    
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        username=f"readonly_{unique_id}",
        password=get_password_hash("testpass123"),
        user_group_id=readonly_user_group.user_group_id,
        email=f"readonly_{unique_id}@example.com",
        firstname="Readonly",
        lastname="User",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    return user


@pytest.fixture
async def create_user(db_transaction, create_user_group):
    """创建仅创建权限的用户"""
    from app.models.system.user import User
    from app.core.security import get_password_hash
    
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        username=f"create_{unique_id}",
        password=get_password_hash("testpass123"),
        user_group_id=create_user_group.user_group_id,
        email=f"create_{unique_id}@example.com",
        firstname="Create",
        lastname="User",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    return user


@pytest.fixture
async def update_user(db_transaction, update_user_group):
    """创建仅更新权限的用户"""
    from app.models.system.user import User
    from app.core.security import get_password_hash
    
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        username=f"update_{unique_id}",
        password=get_password_hash("testpass123"),
        user_group_id=update_user_group.user_group_id,
        email=f"update_{unique_id}@example.com",
        firstname="Update",
        lastname="User",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    return user


@pytest.fixture
async def delete_user(db_transaction, delete_user_group):
    """创建仅删除权限的用户"""
    from app.models.system.user import User
    from app.core.security import get_password_hash
    
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        username=f"delete_{unique_id}",
        password=get_password_hash("testpass123"),
        user_group_id=delete_user_group.user_group_id,
        email=f"delete_{unique_id}@example.com",
        firstname="Delete",
        lastname="User",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    return user


@pytest.fixture
async def no_permission_user(db_transaction, no_permission_user_group):
    """创建无权限用户"""
    from app.models.system.user import User
    from app.core.security import get_password_hash
    
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        username=f"noperm_{unique_id}",
        password=get_password_hash("testpass123"),
        user_group_id=no_permission_user_group.user_group_id,
        email=f"noperm_{unique_id}@example.com",
        firstname="No",
        lastname="Permission",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    return user


@pytest.fixture
async def auth_headers_admin(admin_user):
    """管理员用户的认证头"""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"sub": str(admin_user.user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_readonly(readonly_user):
    """只读用户的认证头"""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"sub": str(readonly_user.user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_create(create_user):
    """创建用户的认证头"""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"sub": str(create_user.user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_update(update_user):
    """更新用户的认证头"""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"sub": str(update_user.user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_delete(delete_user):
    """删除用户的认证头"""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"sub": str(delete_user.user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_no_permission(no_permission_user):
    """无权限用户的认证头"""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"sub": str(no_permission_user.user_id)})
    return {"Authorization": f"Bearer {token}"}


# ==================== Fixtures: 基础测试数据 ====================

@pytest.fixture
async def test_languages(db_transaction):
    """创建测试语言"""
    languages = []
    for i, (name, code, locale) in enumerate([
        ("English", "en", "en-GB"),
        ("中文", "zh", "zh-CN"),
        ("Français", "fr", "fr-FR"),
    ], start=1):
        language = await Language.create(
            name=name,
            code=code,
            locale=locale,
            extension=code.lower(),
            sort_order=i,
            status=1
        )
        languages.append(language)
    return languages


@pytest.fixture
async def test_categories(db_transaction, test_languages):
    """创建测试分类（至少2个，包含父子关系）"""
    # 创建父分类
    parent_category = await Category.create(
        parent_id=0,
        image=None,
        sort_order=10,
        status=1
    )
    
    for language in test_languages:
        await CategoryDescription.create(
            category_id=parent_category.category_id,
            language_id=language.language_id,
            name=f"Parent Category {language.code}",
            description=f"Parent Category Description {language.code}"
        )
    
    # 创建子分类
    child_category = await Category.create(
        parent_id=parent_category.category_id,
        image=None,
        sort_order=20,
        status=1
    )
    
    for language in test_languages:
        await CategoryDescription.create(
            category_id=child_category.category_id,
            language_id=language.language_id,
            name=f"Child Category {language.code}",
            description=f"Child Category Description {language.code}"
        )
    
    return {
        "parent": parent_category,
        "child": child_category
    }


@pytest.fixture
async def test_manufacturer(db_transaction):
    """创建测试制造商"""
    unique_id = uuid.uuid4().hex[:8]
    manufacturer = await Manufacturer.create(
        name=f"Test Manufacturer {unique_id}",
        image="manufacturer.jpg",
        sort_order=10
    )
    return manufacturer


@pytest.fixture
async def test_stock_status(db_transaction, test_languages):
    """创建测试库存状态"""
    # 创建库存状态（使用第一个语言作为基础）
    stock_status_id = 1
    for language in test_languages:
        await StockStatus.create(
            stock_status_id=stock_status_id,
            language_id=language.language_id,
            name=f"In Stock {language.code}"
        )
    return stock_status_id


@pytest.fixture
async def test_tax_class(db_transaction):
    """创建测试税类"""
    unique_id = uuid.uuid4().hex[:8]
    tax_class = await TaxClass.create(
        title=f"Test Tax Class {unique_id}",
        description=f"Test Tax Class Description {unique_id}"
    )
    return tax_class


@pytest.fixture
async def test_weight_class(db_transaction, test_languages):
    """创建测试重量单位"""
    unique_id = uuid.uuid4().hex[:8]
    weight_class = await WeightClass.create(
        value=Decimal("1.00000000")
    )
    
    # 创建多语言描述
    for language in test_languages:
        await WeightClassDescription.create(
            weight_class_id=weight_class.weight_class_id,
            language_id=language.language_id,
            title=f"Kilogram {language.code}",
            unit="kg"
        )
    
    return weight_class


@pytest.fixture
async def test_length_class(db_transaction, test_languages):
    """创建测试长度单位"""
    unique_id = uuid.uuid4().hex[:8]
    length_class = await LengthClass.create(
        value=Decimal("1.00000000")
    )
    
    # 创建多语言描述
    for language in test_languages:
        await LengthClassDescription.create(
            length_class_id=length_class.length_class_id,
            language_id=language.language_id,
            title=f"Centimeter {language.code}",
            unit="cm"
        )
    
    return length_class


@pytest.fixture
async def test_attribute_group(db_transaction, test_languages):
    """创建测试属性组"""
    unique_id = uuid.uuid4().hex[:8]
    attribute_group = await AttributeGroup.create(
        sort_order=10
    )
    
    # 创建多语言描述
    for language in test_languages:
        await AttributeGroupDescription.create(
            attribute_group_id=attribute_group.attribute_group_id,
            language_id=language.language_id,
            name=f"Test Attribute Group {language.code} {unique_id}"
        )
    
    return attribute_group


@pytest.fixture
async def test_attributes(db_transaction, test_attribute_group, test_languages):
    """创建测试属性（至少2个，不同属性组）"""
    unique_id = uuid.uuid4().hex[:8]
    
    # 创建第一个属性
    attribute1 = await Attribute.create(
        attribute_group_id=test_attribute_group.attribute_group_id,
        sort_order=10
    )
    
    for language in test_languages:
        await AttributeDescription.create(
            attribute_id=attribute1.attribute_id,
            language_id=language.language_id,
            name=f"Color {language.code} {unique_id}"
        )
    
    # 创建第二个属性组和属性
    attribute_group2 = await AttributeGroup.create(sort_order=20)
    for language in test_languages:
        await AttributeGroupDescription.create(
            attribute_group_id=attribute_group2.attribute_group_id,
            language_id=language.language_id,
            name=f"Test Attribute Group 2 {language.code} {unique_id}"
        )
    
    attribute2 = await Attribute.create(
        attribute_group_id=attribute_group2.attribute_group_id,
        sort_order=20
    )
    
    for language in test_languages:
        await AttributeDescription.create(
            attribute_id=attribute2.attribute_id,
            language_id=language.language_id,
            name=f"Size {language.code} {unique_id}"
        )
    
    return [attribute1, attribute2]


@pytest.fixture
async def test_options(db_transaction, test_languages):
    """创建测试选项（至少2个，不同类型）"""
    unique_id = uuid.uuid4().hex[:8]
    
    # 创建select类型选项
    option1 = await Option.create(
        type="select",
        sort_order=10
    )
    
    for language in test_languages:
        await OptionDescription.create(
            option_id=option1.option_id,
            language_id=language.language_id,
            name=f"Select Option {language.code} {unique_id}"
        )
    
    # 创建radio类型选项
    option2 = await Option.create(
        type="radio",
        sort_order=20
    )
    
    for language in test_languages:
        await OptionDescription.create(
            option_id=option2.option_id,
            language_id=language.language_id,
            name=f"Radio Option {language.code} {unique_id}"
        )
    
    return [option1, option2]


@pytest.fixture
async def test_option_values(db_transaction, test_options, test_languages):
    """创建测试选项值（每个选项至少2个值）"""
    values = []
    
    for option in test_options:
        # 为每个选项创建2个选项值
        for i in range(2):
            unique_id = uuid.uuid4().hex[:8]
            option_value = await OptionValue.create(
                option_id=option.option_id,
                image=f"value_{i}.jpg",
                sort_order=i * 10
            )
            
            for language in test_languages:
                await OptionValueDescription.create(
                    option_value_id=option_value.option_value_id,
                    language_id=language.language_id,
                    option_id=option.option_id,
                    name=f"Value {i+1} {language.code} {unique_id}"
                )
            
            values.append(option_value)
    
    return values


# ==================== Fixtures: 测试商品 ====================

@pytest.fixture
async def test_product(db_transaction, test_languages, test_manufacturer, test_stock_status, 
                       test_tax_class, test_weight_class, test_length_class):
    """创建测试商品"""
    unique_id = uuid.uuid4().hex[:8]
    product = await Product.create(
        master_id=0,
        model=f"MODEL-{unique_id}",
        sku=f"SKU-{unique_id}",
        price=Decimal("99.99"),
        quantity=100,
        stock_status_id=test_stock_status,
        manufacturer_id=test_manufacturer.manufacturer_id,
        tax_class_id=test_tax_class.tax_class_id,
        weight=Decimal("1.5"),
        weight_class_id=test_weight_class.weight_class_id,
        length=Decimal("10.0"),
        width=Decimal("5.0"),
        height=Decimal("3.0"),
        length_class_id=test_length_class.length_class_id,
        sort_order=10,
        status=1,
        date_added=datetime.now()
    )
    
    # 创建多语言描述
    for language in test_languages:
        await ProductDescription.create(
            product_id=product.product_id,
            language_id=language.language_id,
            name=f"Test Product {language.code} {unique_id}",
            description=f"Test Product Description {language.code}",
            meta_title=f"Test Product Meta Title {language.code}",
            meta_description=f"Test Product Meta Description {language.code}",
            meta_keyword=f"test,product,{language.code}"
        )
    
    return product


# ==================== 测试用例：商品核心CRUD接口 ====================

# ==================== 3.1.1 获取商品列表 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_products_success(async_client, auth_headers_admin, test_product):
    """测试API：成功获取商品列表"""
    response = await async_client.get("/api/v1/products/", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # 验证返回的商品包含必要字段
    product_item = data[0]
    assert "product_id" in product_item
    assert "name" in product_item
    assert "model" in product_item
    assert "price" in product_item


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_products_with_pagination(async_client, auth_headers_admin, test_product):
    """测试API：分页功能测试"""
    # 测试第一页
    response = await async_client.get(
        "/api/v1/products/?skip=0&limit=1",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1
    
    # 测试第二页
    response = await async_client.get(
        "/api/v1/products/?skip=1&limit=1",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_products_with_sorting(async_client, auth_headers_admin, test_product):
    """测试API：排序功能测试"""
    # 按价格排序
    response = await async_client.get(
        "/api/v1/products/?sort=price&order=asc",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    if len(data) > 1:
        prices = [item["price"] for item in data]
        assert prices == sorted(prices)
    
    # 按名称排序
    response = await async_client.get(
        "/api/v1/products/?sort=name&order=desc",
        headers=auth_headers_admin
    )
    assert response.status_code == 200


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_products_with_filters(async_client, auth_headers_admin, test_product):
    """测试API：筛选功能测试"""
    # 按名称筛选
    response = await async_client.get(
        f"/api/v1/products/?filter[name]=Test",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    
    # 按型号筛选
    response = await async_client.get(
        f"/api/v1/products/?filter[model]={test_product.model}",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    if len(data) > 0:
        assert data[0]["model"] == test_product.model
    
    # 按制造商筛选
    response = await async_client.get(
        f"/api/v1/products/?filter[manufacturer_id]={test_product.manufacturer_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    
    # 按价格范围筛选
    response = await async_client.get(
        "/api/v1/products/?filter[price_from]=0&filter[price_to]=1000",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    
    # 按状态筛选
    response = await async_client.get(
        "/api/v1/products/?filter[status]=1",
        headers=auth_headers_admin
    )
    assert response.status_code == 200


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_products_with_language(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：多语言名称返回测试"""
    # 指定语言ID
    response = await async_client.get(
        f"/api/v1/products/?language_id={test_languages[0].language_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    if len(data) > 0:
        assert "name" in data[0]


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_list_products_without_auth(async_client):
    """测试API：未认证访问（期望401）"""
    response = await async_client.get("/api/v1/products/")
    assert response.status_code == 401


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_list_products_with_readonly_permission(async_client, auth_headers_readonly, test_product):
    """测试API：只读权限访问（期望200）"""
    response = await async_client.get("/api/v1/products/", headers=auth_headers_readonly)
    assert response.status_code == 200


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_list_products_without_permission(async_client, auth_headers_no_permission):
    """测试API：无权限访问（期望403）"""
    response = await async_client.get("/api/v1/products/", headers=auth_headers_no_permission)
    assert response.status_code == 403


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_products_empty_result(async_client, auth_headers_admin):
    """测试API：空结果集"""
    # 使用一个不存在的筛选条件
    response = await async_client.get(
        "/api/v1/products/?filter[name]=NonexistentProduct12345",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_products_invalid_pagination(async_client, auth_headers_admin):
    """测试API：无效分页参数"""
    # 负数skip
    response = await async_client.get(
        "/api/v1/products/?skip=-1&limit=10",
        headers=auth_headers_admin
    )
    assert response.status_code == 422
    
    # 负数limit
    response = await async_client.get(
        "/api/v1/products/?skip=0&limit=-1",
        headers=auth_headers_admin
    )
    assert response.status_code == 422
    
    # 超大limit
    response = await async_client.get(
        "/api/v1/products/?skip=0&limit=1000",
        headers=auth_headers_admin
    )
    assert response.status_code == 422


# ==================== 3.1.2 获取商品详情 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_success(async_client, auth_headers_admin, test_product):
    """测试API：成功获取商品详情"""
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == test_product.product_id
    assert data["model"] == test_product.model
    assert "name" in data
    assert "price" in data


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_with_language(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：多语言描述返回测试"""
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}?language_id={test_languages[0].language_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "descriptions" in data or "name" in data


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_with_attributes(async_client, auth_headers_admin, test_product, test_attributes, test_languages):
    """测试API：包含属性信息（include=attributes）"""
    # 先为商品添加属性（ProductAttribute使用复合主键：product_id, attribute_id, language_id）
    from app.models.catalog.product_attribute import ProductAttribute
    
    for lang in test_languages:
        await ProductAttribute.create(
            product_id=test_product.product_id,
            attribute_id=test_attributes[0].attribute_id,
            language_id=lang.language_id,
            text=f"Attribute Value {lang.code}"
        )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}?include=attributes",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "attributes" in data
    assert data["attributes"] is not None
    assert isinstance(data["attributes"], list)
    assert len(data["attributes"]) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_with_options(async_client, auth_headers_admin, test_product, test_options, test_option_values):
    """测试API：包含选项信息（include=options）"""
    # 先为商品添加选项
    from app.models.catalog.product_option import ProductOption
    
    product_option = await ProductOption.create(
        product_id=test_product.product_id,
        option_id=test_options[0].option_id,
        value="",
        required=1
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}?include=options",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "options" in data
    assert data["options"] is not None
    assert isinstance(data["options"], list)
    assert len(data["options"]) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_with_images(async_client, auth_headers_admin, test_product):
    """测试API：包含图片信息（include=images）"""
    # 先为商品添加图片
    from app.models.catalog.product_image import ProductImage
    await ProductImage.create(
        product_id=test_product.product_id,
        image="test_image.jpg",
        sort_order=10
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}?include=images",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "images" in data
    assert data["images"] is not None
    assert isinstance(data["images"], list)
    assert len(data["images"]) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_with_categories(async_client, auth_headers_admin, test_product, test_categories):
    """测试API：包含分类信息（include=categories）"""
    # 先为商品添加分类
    from app.models.catalog.product_to_category import ProductToCategory
    await ProductToCategory.create(
        product_id=test_product.product_id,
        category_id=test_categories["parent"].category_id
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}?include=categories",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert data["categories"] is not None
    assert isinstance(data["categories"], list)
    assert len(data["categories"]) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_with_related(async_client, auth_headers_admin, test_product, test_languages, test_manufacturer, test_stock_status, test_tax_class, test_weight_class, test_length_class):
    """测试API：包含相关商品信息（include=related）"""
    # 先创建另一个商品作为相关商品
    unique_id = uuid.uuid4().hex[:8]
    related_product = await Product.create(
        master_id=0,
        model=f"RELATED-{unique_id}",
        sku=f"SKU-REL-{unique_id}",
        price=Decimal("199.99"),
        quantity=50,
        stock_status_id=test_stock_status,
        manufacturer_id=test_manufacturer.manufacturer_id,
        tax_class_id=test_tax_class.tax_class_id,
        weight=Decimal("2.0"),
        weight_class_id=test_weight_class.weight_class_id,
        length=Decimal("15.0"),
        width=Decimal("8.0"),
        height=Decimal("5.0"),
        length_class_id=test_length_class.length_class_id,
        sort_order=20,
        status=1,
        date_added=datetime.now()
    )
    
    # 创建相关商品描述
    from app.models.catalog.product_description import ProductDescription
    for lang in test_languages:
        await ProductDescription.create(
            product_id=related_product.product_id,
            language_id=lang.language_id,
            name=f"Related Product {lang.code} {unique_id}"
        )
    
    # 添加相关商品关联
    from app.models.catalog.product_related import ProductRelated
    await ProductRelated.create(
        product_id=test_product.product_id,
        related_id=related_product.product_id
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}?include=related",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "related_products" in data
    assert data["related_products"] is not None
    assert isinstance(data["related_products"], list)
    assert len(data["related_products"]) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_with_all_includes(async_client, auth_headers_admin, test_product, test_attributes, test_options, test_categories, test_languages, test_manufacturer, test_stock_status, test_tax_class, test_weight_class, test_length_class):
    """测试API：包含所有关联数据（include=attributes,options,images,categories,related）"""
    # 准备测试数据
    from app.models.catalog.product_attribute import ProductAttribute
    from app.models.catalog.product_option import ProductOption
    from app.models.catalog.product_image import ProductImage
    from app.models.catalog.product_to_category import ProductToCategory
    from app.models.catalog.product_related import ProductRelated
    from app.models.catalog.product_description import ProductDescription
    
    # 添加属性（ProductAttribute使用复合主键：product_id, attribute_id, language_id）
    for lang in test_languages:
        await ProductAttribute.create(
            product_id=test_product.product_id,
            attribute_id=test_attributes[0].attribute_id,
            language_id=lang.language_id,
            text=f"Attribute Value {lang.code}"
        )
    
    # 添加选项
    product_option = await ProductOption.create(
        product_id=test_product.product_id,
        option_id=test_options[0].option_id,
        value="",
        required=1
    )
    
    # 添加图片
    await ProductImage.create(
        product_id=test_product.product_id,
        image="test_image.jpg",
        sort_order=10
    )
    
    # 添加分类
    await ProductToCategory.create(
        product_id=test_product.product_id,
        category_id=test_categories["parent"].category_id
    )
    
    # 创建并添加相关商品
    unique_id = uuid.uuid4().hex[:8]
    related_product = await Product.create(
        master_id=0,
        model=f"RELATED-{unique_id}",
        sku=f"SKU-REL-{unique_id}",
        price=Decimal("199.99"),
        quantity=50,
        stock_status_id=test_stock_status,
        manufacturer_id=test_manufacturer.manufacturer_id,
        tax_class_id=test_tax_class.tax_class_id,
        weight=Decimal("2.0"),
        weight_class_id=test_weight_class.weight_class_id,
        length=Decimal("15.0"),
        width=Decimal("8.0"),
        height=Decimal("5.0"),
        length_class_id=test_length_class.length_class_id,
        sort_order=20,
        status=1,
        date_added=datetime.now()
    )
    for lang in test_languages:
        await ProductDescription.create(
            product_id=related_product.product_id,
            language_id=lang.language_id,
            name=f"Related Product {lang.code} {unique_id}"
        )
    await ProductRelated.create(
        product_id=test_product.product_id,
        related_id=related_product.product_id
    )
    
    # 测试包含所有关联数据
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}?include=attributes,options,images,categories,related",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    
    # 验证所有关联字段都存在
    assert "attributes" in data
    assert data["attributes"] is not None
    assert isinstance(data["attributes"], list)
    
    assert "options" in data
    assert data["options"] is not None
    assert isinstance(data["options"], list)
    
    assert "images" in data
    assert data["images"] is not None
    assert isinstance(data["images"], list)
    
    assert "categories" in data
    assert data["categories"] is not None
    assert isinstance(data["categories"], list)
    
    assert "related_products" in data
    assert data["related_products"] is not None
    assert isinstance(data["related_products"], list)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_not_found(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    response = await async_client.get(
        "/api/v1/products/999999",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_product_invalid_id(async_client, auth_headers_admin):
    """测试API：无效商品ID"""
    # 非数字ID
    response = await async_client.get(
        "/api/v1/products/invalid",
        headers=auth_headers_admin
    )
    assert response.status_code == 422
    
    # 负数ID
    response = await async_client.get(
        "/api/v1/products/-1",
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_get_product_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    response = await async_client.get(f"/api/v1/products/{test_product.product_id}")
    assert response.status_code == 401


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_get_product_with_readonly_permission(async_client, auth_headers_readonly, test_product):
    """测试API：只读权限访问（期望200）"""
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}",
        headers=auth_headers_readonly
    )
    assert response.status_code == 200


# ==================== 3.1.3 创建商品 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_success(async_client, auth_headers_admin, test_languages, 
                                          test_manufacturer, test_stock_status, test_tax_class,
                                          test_weight_class, test_length_class):
    """测试API：成功创建基础商品"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "sku": f"SKU-{unique_id}",
        "price": "99.99",
        "quantity": 100,
        "stock_status_id": test_stock_status,
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "status": 1,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code} {unique_id}",
                "description": f"Test Product Description {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["model"] == product_data["model"]
    assert data["product_id"] > 0
    assert len(data.get("descriptions", [])) >= len(test_languages)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_manufacturer(async_client, auth_headers_admin, test_languages, test_stock_status, test_tax_class, test_weight_class, test_length_class):
    """测试API：制造商不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "manufacturer_id": 999999,  # 不存在的制造商ID
        "stock_status_id": test_stock_status,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_stock_status(async_client, auth_headers_admin, test_languages, test_manufacturer, test_tax_class, test_weight_class, test_length_class):
    """测试API：库存状态不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": 999999,  # 不存在的库存状态ID
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_tax_class(async_client, auth_headers_admin, test_languages, test_manufacturer, test_stock_status, test_weight_class, test_length_class):
    """测试API：税类不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": test_stock_status,
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": 999999,  # 不存在的税类ID
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_weight_class(async_client, auth_headers_admin, test_languages, test_manufacturer, test_stock_status, test_tax_class, test_length_class):
    """测试API：重量单位不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": test_stock_status,
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": 999999,  # 不存在的重量单位ID
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_length_class(async_client, auth_headers_admin, test_languages, test_manufacturer, test_stock_status, test_tax_class, test_weight_class):
    """测试API：长度单位不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": test_stock_status,
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": 999999,  # 不存在的长度单位ID
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_category(async_client, auth_headers_admin, test_languages, test_manufacturer, test_stock_status, test_tax_class, test_weight_class, test_length_class):
    """测试API：分类不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": test_stock_status,
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "category_ids": [999999],  # 不存在的分类ID
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_related_product(async_client, auth_headers_admin, test_languages, test_manufacturer, test_stock_status, test_tax_class, test_weight_class, test_length_class):
    """测试API：相关商品不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": test_stock_status,
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "related_product_ids": [999999],  # 不存在的相关商品ID
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_with_descriptions(async_client, auth_headers_admin, test_languages,
                                                     test_manufacturer, test_stock_status, test_tax_class,
                                                     test_weight_class, test_length_class):
    """测试API：创建商品（含多语言描述）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Product {lang.code} {unique_id}",
                "description": f"Description {lang.code}",
                "meta_title": f"Meta Title {lang.code}",
                "meta_description": f"Meta Description {lang.code}",
                "meta_keyword": f"keyword,{lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data.get("descriptions", [])) == len(test_languages)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_variant_product(async_client, auth_headers_admin, test_product, test_languages,
                                          test_manufacturer, test_stock_status, test_tax_class,
                                          test_weight_class, test_length_class):
    """测试API：创建变体商品（master_id > 0）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "master_id": test_product.product_id,
        "model": f"VARIANT-{unique_id}",
        "price": "89.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Variant Product {lang.code} {unique_id}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["master_id"] == test_product.product_id


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_empty_model(async_client, auth_headers_admin, test_languages):
    """测试API：商品型号为空（期望422）"""
    product_data = {
        "model": "",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_model_too_long(async_client, auth_headers_admin, test_languages):
    """测试API：商品型号超长（期望422）"""
    product_data = {
        "model": "A" * 65,  # 超过64字符
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_duplicate_model(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：商品型号重复（期望409）"""
    product_data = {
        "model": test_product.model,  # 使用已存在的型号
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 409


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_duplicate_sku(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：SKU重复验证（期望409）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "sku": test_product.sku,  # 使用已存在的SKU
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_negative_price(async_client, auth_headers_admin, test_languages):
    """测试API：价格为负数（期望422）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "-10.00",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_negative_quantity(async_client, auth_headers_admin, test_languages):
    """测试API：库存为负数（期望422）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "quantity": -1,
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_empty_descriptions(async_client, auth_headers_admin):
    """测试API：描述为空（期望422）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": []
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_empty_name(async_client, auth_headers_admin, test_languages):
    """测试API：商品名称为空（期望422）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": ""  # 空名称
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_name_too_long(async_client, auth_headers_admin, test_languages):
    """测试API：商品名称超长（期望422）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "A" * 256  # 超过255字符
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_duplicate_language(async_client, auth_headers_admin, test_languages):
    """测试API：描述语言ID重复（期望422）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product 1"
            },
            {
                "language_id": test_languages[0].language_id,  # 重复的语言ID
                "name": "Test Product 2"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_name_too_long(async_client, auth_headers_admin, test_languages):
    """测试API：商品名称超长（期望422）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "A" * 256  # 超过255字符
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_manufacturer(async_client, auth_headers_admin, test_languages, test_stock_status, test_tax_class, test_weight_class, test_length_class):
    """测试API：制造商不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "manufacturer_id": 999999,  # 不存在的制造商ID
        "stock_status_id": test_stock_status,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_stock_status(async_client, auth_headers_admin, test_languages, test_manufacturer, test_tax_class, test_weight_class, test_length_class):
    """测试API：库存状态不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": 999999,  # 不存在的库存状态ID
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_tax_class(async_client, auth_headers_admin, test_languages, test_manufacturer, test_stock_status, test_weight_class, test_length_class):
    """测试API：税类不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": test_stock_status,
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": 999999,  # 不存在的税类ID
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_weight_class(async_client, auth_headers_admin, test_languages, test_manufacturer, test_stock_status, test_tax_class, test_length_class):
    """测试API：重量单位不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": test_stock_status,
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": 999999,  # 不存在的重量单位ID
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": test_length_class.length_class_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_invalid_length_class(async_client, auth_headers_admin, test_languages, test_manufacturer, test_stock_status, test_tax_class, test_weight_class):
    """测试API：长度单位不存在（期望422）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "stock_status_id": test_stock_status,
        "manufacturer_id": test_manufacturer.manufacturer_id,
        "tax_class_id": test_tax_class.tax_class_id,
        "weight": "1.5",
        "weight_class_id": test_weight_class.weight_class_id,
        "length": "10.0",
        "width": "5.0",
        "height": "3.0",
        "length_class_id": 999999,  # 不存在的长度单位ID
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_create_product_without_auth(async_client, test_languages):
    """测试API：未认证访问（期望401）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 401


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_create_product_with_readonly_permission(async_client, auth_headers_readonly, test_languages):
    """测试API：只读权限访问（期望403）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_readonly
    )
    assert response.status_code == 403


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_create_product_with_create_permission(async_client, auth_headers_create, test_languages,
                                                          test_manufacturer, test_stock_status, test_tax_class,
                                                          test_weight_class, test_length_class):
    """测试API：创建权限访问（期望201）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": f"Test Product {unique_id}"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_create
    )
    assert response.status_code == 201


# ==================== 3.1.4 更新商品 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_product_success(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：成功更新商品"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"UPDATED-{unique_id}",
        "price": "199.99",
        "quantity": 200,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Updated Product {lang.code} {unique_id}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == product_data["model"]
    # 价格格式：Decimal序列化可能包含尾随零，比较数值而非字符串
    assert float(data["price"]) == float(product_data["price"])


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_product_not_found(async_client, auth_headers_admin, test_languages):
    """测试API：商品不存在（期望404）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.put(
        "/api/v1/products/999999",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_update_product_without_auth(async_client, test_product, test_languages):
    """测试API：未认证访问（期望401）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data
    )
    assert response.status_code == 401


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_update_product_with_readonly_permission(async_client, auth_headers_readonly, test_product, test_languages):
    """测试API：只读权限访问（期望403）"""
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_readonly
    )
    assert response.status_code == 403


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_update_product_with_update_permission(async_client, auth_headers_update, test_product, test_languages):
    """测试API：更新权限访问（期望200）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"UPDATED-{unique_id}",
        "price": "199.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": f"Updated Product {unique_id}"
            }
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_update
    )
    assert response.status_code == 200


# ==================== 3.1.5 部分更新商品 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_patch_product_success(async_client, auth_headers_admin, test_product):
    """测试API：成功部分更新商品"""
    product_data = {
        "price": "299.99"
    }
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    # 价格格式：Decimal序列化可能包含尾随零，比较数值而非字符串
    assert float(data["price"]) == float(product_data["price"])


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_patch_product_price_only(async_client, auth_headers_admin, test_product):
    """测试API：仅更新价格"""
    product_data = {
        "price": "399.99"
    }
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    # 价格格式：Decimal序列化可能包含尾随零，比较数值而非字符串
    assert float(data["price"]) == float(product_data["price"])


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_patch_product_quantity_only(async_client, auth_headers_admin, test_product):
    """测试API：仅更新库存"""
    product_data = {
        "quantity": 500
    }
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == product_data["quantity"]


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_patch_product_status_only(async_client, auth_headers_admin, test_product):
    """测试API：仅更新状态"""
    product_data = {
        "status": 0  # 禁用
    }
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == product_data["status"]


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_patch_product_not_found(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    product_data = {
        "price": "99.99"
    }
    
    response = await async_client.patch(
        "/api/v1/products/999999",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_patch_product_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    product_data = {
        "price": "99.99"
    }
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data
    )
    assert response.status_code == 401


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_patch_product_with_update_permission(async_client, auth_headers_update, test_product):
    """测试API：更新权限访问（期望200）"""
    product_data = {
        "price": "499.99"
    }
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_update
    )
    assert response.status_code == 200


# ==================== 3.1.6 删除商品 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_success(async_client, auth_headers_admin, test_languages,
                                          test_manufacturer, test_stock_status, test_tax_class,
                                          test_weight_class, test_length_class):
    """测试API：成功删除商品"""
    # 创建一个新商品用于删除
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"DELETE-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": f"Delete Test Product {unique_id}"
            }
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["product_id"]
    
    # 删除商品
    delete_response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=auth_headers_admin
    )
    assert delete_response.status_code == 204
    
    # 验证商品已删除
    get_response = await async_client.get(
        f"/api/v1/products/{product_id}",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_not_found(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    response = await async_client.delete(
        "/api/v1/products/999999",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_delete_product_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    response = await async_client.delete(f"/api/v1/products/{test_product.product_id}")
    assert response.status_code == 401


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_delete_product_with_readonly_permission(async_client, auth_headers_readonly, test_product):
    """测试API：只读权限访问（期望403）"""
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}",
        headers=auth_headers_readonly
    )
    assert response.status_code == 403


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_delete_product_with_delete_permission(async_client, auth_headers_delete, test_languages,
                                                          test_manufacturer, test_stock_status, test_tax_class,
                                                          test_weight_class, test_length_class):
    """测试API：删除权限访问（期望204）"""
    # 创建一个新商品用于删除
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"DELETE-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": f"Delete Test Product {unique_id}"
            }
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_delete
    )
    # 删除权限用户可能没有创建权限，所以这里可能返回403
    # 如果返回403，我们需要使用admin用户创建，然后用delete用户删除
    if create_response.status_code == 403:
        # 使用admin用户创建（需要从conftest获取admin用户）
        from app.models.system.user_group import UserGroup
        from app.models.system.user import User
        from app.core.security import get_password_hash, create_access_token
        
        admin_group = await UserGroup.create(
            name=f"Temp Admin {uuid.uuid4().hex[:8]}",
            permission=json.dumps({"product": ["read", "create", "update", "delete"]})
        )
        admin_user = await User.create(
            username=f"temp_admin_{uuid.uuid4().hex[:8]}",
            password=get_password_hash("testpass123"),
            user_group_id=admin_group.user_group_id,
            email=f"temp_admin_{uuid.uuid4().hex[:8]}@example.com",
            firstname="Temp",
            lastname="Admin",
            status=1,
            date_added=datetime.now()
        )
        admin_token = create_access_token(data={"sub": str(admin_user.user_id)})
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        create_response = await async_client.post(
            "/api/v1/products/",
            json=product_data,
            headers=admin_headers
        )
        assert create_response.status_code == 201
    
    product_id = create_response.json()["product_id"]
    
    # 使用delete权限用户删除
    delete_response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=auth_headers_delete
    )
    assert delete_response.status_code == 204


# ==================== 3.1.7 复制商品 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_copy_product_success(async_client, auth_headers_admin, test_product):
    """测试API：成功复制商品"""
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/copy",
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] != test_product.product_id
    assert data["model"] != test_product.model  # 型号应该不同（或清除）


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_copy_product_not_found(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    response = await async_client.post(
        "/api/v1/products/999999/copy",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_copy_product_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    response = await async_client.post(f"/api/v1/products/{test_product.product_id}/copy")
    assert response.status_code == 401


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_copy_product_with_create_permission(async_client, auth_headers_create, test_product):
    """测试API：创建权限访问（期望201）"""
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/copy",
        headers=auth_headers_create
    )
    assert response.status_code == 201


# ==================== 测试用例：商品属性关联接口 ====================

# ==================== 3.2.1 获取商品属性列表 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_attributes_success(async_client, auth_headers_admin, test_product, test_attributes, test_languages):
    """测试API：成功获取商品属性列表"""
    # 先添加一个属性
    from app.models.catalog.product_attribute import ProductAttribute
    await ProductAttribute.create(
        product_id=test_product.product_id,
        attribute_id=test_attributes[0].attribute_id,
        language_id=test_languages[0].language_id,
        text="Test Attribute Text"
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/attributes",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_attributes_empty(async_client, auth_headers_admin, test_product):
    """测试API：商品无属性（空列表）"""
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/attributes",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_attributes_not_found(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    response = await async_client.get(
        "/api/v1/products/999999/attributes",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_list_product_attributes_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    response = await async_client.get(f"/api/v1/products/{test_product.product_id}/attributes")
    assert response.status_code == 401


# ==================== 3.2.2 添加商品属性 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_attribute_success(async_client, auth_headers_admin, test_product, test_attributes, test_languages):
    """测试API：成功添加商品属性"""
    attribute_data = {
        "attribute_id": test_attributes[0].attribute_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "text": f"Attribute Text {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/attributes",
        json=attribute_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_attribute_validation_invalid_product(async_client, auth_headers_admin, test_attributes, test_languages):
    """测试API：商品不存在（期望404）"""
    attribute_data = {
        "attribute_id": test_attributes[0].attribute_id,
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "text": "Test Text"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/999999/attributes",
        json=attribute_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_attribute_validation_invalid_attribute(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：属性不存在（期望422）"""
    attribute_data = {
        "attribute_id": 999999,
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "text": "Test Text"
            }
        ]
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/attributes",
        json=attribute_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_add_product_attribute_without_auth(async_client, test_product, test_attributes, test_languages):
    """测试API：未认证访问（期望401）"""
    attribute_data = {
        "attribute_id": test_attributes[0].attribute_id,
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "text": "Test Text"
            }
        ]
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/attributes",
        json=attribute_data
    )
    assert response.status_code == 401


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_add_product_attribute_without_permission(async_client, auth_headers_readonly, test_product, test_attributes, test_languages):
    """测试API：无更新权限（期望403）"""
    attribute_data = {
        "attribute_id": test_attributes[0].attribute_id,
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "text": "Test Text"
            }
        ]
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/attributes",
        json=attribute_data,
        headers=auth_headers_readonly
    )
    assert response.status_code == 403


# ==================== 3.2.3 更新商品属性 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_product_attribute_success(async_client, auth_headers_admin, test_product, test_attributes, test_languages):
    """测试API：成功更新商品属性"""
    # 先添加一个属性
    from app.models.catalog.product_attribute import ProductAttribute
    await ProductAttribute.create(
        product_id=test_product.product_id,
        attribute_id=test_attributes[0].attribute_id,
        language_id=test_languages[0].language_id,
        text="Original Text"
    )
    
    attribute_data = {
        "attribute_id": test_attributes[0].attribute_id,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "text": f"Updated Text {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}/attributes/{test_attributes[0].attribute_id}",
        json=attribute_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_product_attribute_not_found(async_client, auth_headers_admin, test_product, test_attributes, test_languages):
    """测试API：商品属性不存在（期望404）"""
    attribute_data = {
        "attribute_id": test_attributes[0].attribute_id,
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "text": "Test Text"
            }
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}/attributes/{test_attributes[0].attribute_id}",
        json=attribute_data,
        headers=auth_headers_admin
    )
    # 如果属性不存在，可能返回404或422，取决于实现
    assert response.status_code in [404, 422]


# ==================== 3.2.4 删除商品属性 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_attribute_success(async_client, auth_headers_admin, test_product, test_attributes, test_languages):
    """测试API：成功删除商品属性"""
    # 先添加一个属性
    from app.models.catalog.product_attribute import ProductAttribute
    await ProductAttribute.create(
        product_id=test_product.product_id,
        attribute_id=test_attributes[0].attribute_id,
        language_id=test_languages[0].language_id,
        text="Test Text"
    )
    
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/attributes/{test_attributes[0].attribute_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 204


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_attribute_not_found(async_client, auth_headers_admin, test_product, test_attributes):
    """测试API：商品属性不存在（期望404）"""
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/attributes/{test_attributes[0].attribute_id}",
        headers=auth_headers_admin
    )
    # 如果属性不存在，可能返回404或204（幂等性），取决于实现
    assert response.status_code in [404, 204]


# ==================== 3.2.5 批量更新商品属性 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_batch_update_product_attributes_success(async_client, auth_headers_admin, test_product, test_attributes, test_languages):
    """测试API：成功批量更新商品属性"""
    attributes_data = [
        {
            "attribute_id": test_attributes[0].attribute_id,
            "descriptions": [
                {
                    "language_id": lang.language_id,
                    "text": f"Batch Text 1 {lang.code}"
                }
                for lang in test_languages
            ]
        },
        {
            "attribute_id": test_attributes[1].attribute_id,
            "descriptions": [
                {
                    "language_id": lang.language_id,
                    "text": f"Batch Text 2 {lang.code}"
                }
                for lang in test_languages
            ]
        }
    ]
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}/attributes",
        json=attributes_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_batch_update_product_attributes_not_found(async_client, auth_headers_admin, test_attributes, test_languages):
    """测试API：商品不存在（期望404）"""
    attributes_data = [
        {
            "attribute_id": test_attributes[0].attribute_id,
            "descriptions": [
                {
                    "language_id": test_languages[0].language_id,
                    "text": "Test Text"
                }
            ]
        }
    ]
    
    response = await async_client.patch(
        "/api/v1/products/999999/attributes",
        json=attributes_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404


# ==================== 测试用例：商品选项关联接口 ====================

# ==================== 3.3.1 获取商品选项列表 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_options_success(async_client, auth_headers_admin, test_product, test_options):
    """测试API：成功获取商品选项列表"""
    # 先添加一个选项
    from app.models.catalog.product_option import ProductOption
    product_option = await ProductOption.create(
        product_id=test_product.product_id,
        option_id=test_options[0].option_id,
        value="",
        required=1
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/options",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_options_empty(async_client, auth_headers_admin, test_product):
    """测试API：商品无选项（空列表）"""
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/options",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_options_not_found(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    response = await async_client.get(
        "/api/v1/products/999999/options",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_list_product_options_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    response = await async_client.get(f"/api/v1/products/{test_product.product_id}/options")
    assert response.status_code == 401


# ==================== 3.3.2 添加商品选项 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_option_success(async_client, auth_headers_admin, test_product, test_options, test_option_values):
    """测试API：成功添加商品选项"""
    # select/radio/checkbox类型的选项必须提供product_option_values
    # test_options[0]是select类型，需要提供选项值
    option_data = {
        "option_id": test_options[0].option_id,
        "value": "",
        "required": 1,
        "product_option_values": [
            {
                "option_value_id": test_option_values[0].option_value_id,
                "quantity": 10,
                "subtract": 1,
                "price": "10.00",
                "price_prefix": "+"
            }
        ]
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/options",
        json=option_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert "product_option_id" in data


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_option_validation_invalid_product(async_client, auth_headers_admin, test_options):
    """测试API：商品不存在（期望404）"""
    option_data = {
        "option_id": test_options[0].option_id,
        "value": "",
        "required": 1
    }
    
    response = await async_client.post(
        "/api/v1/products/999999/options",
        json=option_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_option_validation_invalid_option(async_client, auth_headers_admin, test_product):
    """测试API：选项不存在（期望422）"""
    option_data = {
        "option_id": 999999,
        "value": "",
        "required": 1
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/options",
        json=option_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_add_product_option_without_auth(async_client, test_product, test_options):
    """测试API：未认证访问（期望401）"""
    option_data = {
        "option_id": test_options[0].option_id,
        "value": "",
        "required": 1
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/options",
        json=option_data
    )
    assert response.status_code == 401


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_add_product_option_without_permission(async_client, auth_headers_readonly, test_product, test_options):
    """测试API：无更新权限（期望403）"""
    option_data = {
        "option_id": test_options[0].option_id,
        "value": "",
        "required": 1
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/options",
        json=option_data,
        headers=auth_headers_readonly
    )
    assert response.status_code == 403


# ==================== 3.3.3 删除商品选项 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_option_success(async_client, auth_headers_admin, test_product, test_options):
    """测试API：成功删除商品选项"""
    # 先添加一个选项
    from app.models.catalog.product_option import ProductOption
    product_option = await ProductOption.create(
        product_id=test_product.product_id,
        option_id=test_options[0].option_id,
        value="",
        required=1
    )
    
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/options/{product_option.product_option_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 204


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_option_not_found(async_client, auth_headers_admin, test_product):
    """测试API：商品选项不存在（期望404）"""
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/options/999999",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


# ==================== 3.3.4 获取选项值列表 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_option_values_success(async_client, auth_headers_admin, test_product, test_options, test_option_values):
    """测试API：成功获取选项值列表"""
    # 先添加一个商品选项
    from app.models.catalog.product_option import ProductOption
    product_option = await ProductOption.create(
        product_id=test_product.product_id,
        option_id=test_options[0].option_id,
        value="",
        required=1
    )
    
    # 添加选项值
    from app.models.catalog.product_option_value import ProductOptionValue
    await ProductOptionValue.create(
        product_option_id=product_option.product_option_id,
        product_id=test_product.product_id,
        option_id=test_options[0].option_id,
        option_value_id=test_option_values[0].option_value_id,
        quantity=10,
        price=Decimal("10.00")
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/options/{product_option.product_option_id}/values",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_option_values_empty(async_client, auth_headers_admin, test_product, test_options):
    """测试API：选项无值（空列表）"""
    # 先添加一个商品选项
    from app.models.catalog.product_option import ProductOption
    product_option = await ProductOption.create(
        product_id=test_product.product_id,
        option_id=test_options[0].option_id,
        value="",
        required=1
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/options/{product_option.product_option_id}/values",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_option_values_not_found(async_client, auth_headers_admin, test_product):
    """测试API：商品选项不存在（期望404）"""
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/options/999999/values",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


# ==================== 3.3.5 添加选项值 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_option_value_success(async_client, auth_headers_admin, test_product, test_options, test_option_values):
    """测试API：成功添加选项值"""
    # 先添加一个商品选项
    from app.models.catalog.product_option import ProductOption
    product_option = await ProductOption.create(
        product_id=test_product.product_id,
        option_id=test_options[0].option_id,
        value="",
        required=1
    )
    
    option_value_data = {
        "option_value_id": test_option_values[0].option_value_id,
        "quantity": 10,
        "subtract": 1,
        "price": "10.00",
        "price_prefix": "+",
        "points": 0,
        "points_prefix": "+",
        "weight": "0.5",
        "weight_prefix": "+"
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/options/{product_option.product_option_id}/values",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert "product_option_value_id" in data


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_option_value_validation_invalid_option(async_client, auth_headers_admin, test_product, test_option_values):
    """测试API：商品选项不存在（期望404）"""
    option_value_data = {
        "option_value_id": test_option_values[0].option_value_id,
        "quantity": 10,
        "price": "10.00"
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/options/999999/values",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_add_product_option_value_without_auth(async_client, test_product, test_options, test_option_values):
    """测试API：未认证访问（期望401）"""
    # 先添加一个商品选项
    from app.models.catalog.product_option import ProductOption
    product_option = await ProductOption.create(
        product_id=test_product.product_id,
        option_id=test_options[0].option_id,
        value="",
        required=1
    )
    
    option_value_data = {
        "option_value_id": test_option_values[0].option_value_id,
        "quantity": 10,
        "price": "10.00"
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/options/{product_option.product_option_id}/values",
        json=option_value_data
    )
    assert response.status_code == 401


# ==================== 测试用例：商品图片管理接口 ====================

# ==================== 3.4.1 获取商品图片列表 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_images_success(async_client, auth_headers_admin, test_product):
    """测试API：成功获取商品图片列表"""
    # 先添加一个图片
    from app.models.catalog.product_image import ProductImage
    await ProductImage.create(
        product_id=test_product.product_id,
        image="test_image.jpg",
        sort_order=10
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/images",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_images_sorted(async_client, auth_headers_admin, test_product):
    """测试API：图片排序测试（按sort_order排序）"""
    from app.models.catalog.product_image import ProductImage
    # 创建多张图片，使用不同的sort_order
    images = [
        {"image": "image3.jpg", "sort_order": 30},
        {"image": "image1.jpg", "sort_order": 10},
        {"image": "image2.jpg", "sort_order": 20},
    ]
    for img_data in images:
        await ProductImage.create(
            product_id=test_product.product_id,
            image=img_data["image"],
            sort_order=img_data["sort_order"]
        )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/images",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    
    # 验证图片按sort_order升序排序
    sort_orders = [img["sort_order"] for img in data]
    assert sort_orders == sorted(sort_orders), "图片列表应按sort_order升序排序"


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_images_empty(async_client, auth_headers_admin, test_product):
    """测试API：商品无图片（空列表）"""
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/images",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_images_not_found(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    response = await async_client.get(
        "/api/v1/products/999999/images",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_list_product_images_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    response = await async_client.get(f"/api/v1/products/{test_product.product_id}/images")
    assert response.status_code == 401


# ==================== 3.4.2 添加商品图片 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_image_success(async_client, auth_headers_admin, test_product):
    """测试API：成功添加商品图片"""
    image_data = {
        "image": "new_image.jpg",
        "sort_order": 10
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/images",
        json=image_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert "product_image_id" in data


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_image_auto_primary(async_client, auth_headers_admin, test_product):
    """测试API：自动设置主图（商品image为空时）"""
    # 确保商品image字段为空
    test_product.image = None
    await test_product.save()
    
    image_data = {
        "image": "auto_primary_image.jpg",
        "sort_order": 10
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/images",
        json=image_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    
    # 验证商品image字段被自动更新
    await test_product.refresh_from_db()
    assert test_product.image == image_data["image"], "商品image字段应被自动设置为第一张图片"


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_image_not_found(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    image_data = {
        "image": "test_image.jpg",
        "sort_order": 10
    }
    
    response = await async_client.post(
        "/api/v1/products/999999/images",
        json=image_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_image_validation_invalid_product(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    image_data = {
        "image": "test_image.jpg",
        "sort_order": 10
    }
    
    response = await async_client.post(
        "/api/v1/products/999999/images",
        json=image_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_add_product_image_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    image_data = {
        "image": "test_image.jpg",
        "sort_order": 10
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/images",
        json=image_data
    )
    assert response.status_code == 401


# ==================== 3.4.3 删除商品图片 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_image_success(async_client, auth_headers_admin, test_product):
    """测试API：成功删除商品图片"""
    # 先添加一个图片
    from app.models.catalog.product_image import ProductImage
    product_image = await ProductImage.create(
        product_id=test_product.product_id,
        image="test_image.jpg",
        sort_order=10
    )
    
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/images/{product_image.product_image_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 204


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_image_primary_handling(async_client, auth_headers_admin, test_product):
    """测试API：删除主图处理（应自动设置新的主图）"""
    from app.models.catalog.product_image import ProductImage
    
    # 创建多张图片
    image1 = await ProductImage.create(
        product_id=test_product.product_id,
        image="primary_image.jpg",
        sort_order=10
    )
    image2 = await ProductImage.create(
        product_id=test_product.product_id,
        image="secondary_image.jpg",
        sort_order=20
    )
    
    # 设置第一张图片为主图
    test_product.image = image1.image
    await test_product.save()
    
    # 删除主图
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/images/{image1.product_image_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 204
    
    # 验证商品image字段被更新为新的主图（按sort_order排序的第一张）
    await test_product.refresh_from_db()
    assert test_product.image == image2.image, "删除主图后应自动设置新的主图"


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_image_last_image(async_client, auth_headers_admin, test_product):
    """测试API：删除最后一张图片（应清空商品image字段）"""
    from app.models.catalog.product_image import ProductImage
    
    # 创建一张图片并设置为主图
    product_image = await ProductImage.create(
        product_id=test_product.product_id,
        image="last_image.jpg",
        sort_order=10
    )
    test_product.image = product_image.image
    await test_product.save()
    
    # 删除最后一张图片
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/images/{product_image.product_image_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 204
    
    # 验证商品image字段被清空
    await test_product.refresh_from_db()
    assert test_product.image is None or test_product.image == '', "删除最后一张图片后应清空商品image字段"


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_image_not_found(async_client, auth_headers_admin, test_product):
    """测试API：商品图片不存在（期望404）"""
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/images/999999",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_delete_product_image_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    from app.models.catalog.product_image import ProductImage
    product_image = await ProductImage.create(
        product_id=test_product.product_id,
        image="test_image.jpg",
        sort_order=10
    )
    
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/images/{product_image.product_image_id}"
    )
    assert response.status_code == 401


# ==================== 3.4.4 设置主图 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_set_primary_image_success(async_client, auth_headers_admin, test_product):
    """测试API：成功设置主图"""
    from app.models.catalog.product_image import ProductImage
    product_image = await ProductImage.create(
        product_id=test_product.product_id,
        image="primary_image.jpg",
        sort_order=10
    )
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/images/{product_image.product_image_id}/primary",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_set_primary_image_updates_product_image(async_client, auth_headers_admin, test_product):
    """测试API：设置主图应同步更新商品image字段"""
    from app.models.catalog.product_image import ProductImage
    product_image = await ProductImage.create(
        product_id=test_product.product_id,
        image="new_primary_image.jpg",
        sort_order=10
    )
    
    # 确保商品image字段为空或不同
    test_product.image = "old_image.jpg"
    await test_product.save()
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/images/{product_image.product_image_id}/primary",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    
    # 验证商品image字段被同步更新
    await test_product.refresh_from_db()
    assert test_product.image == product_image.image, "设置主图时应同步更新商品image字段"


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_set_primary_image_not_found(async_client, auth_headers_admin, test_product):
    """测试API：商品图片不存在（期望404）"""
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/images/999999/primary",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_set_primary_image_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    from app.models.catalog.product_image import ProductImage
    product_image = await ProductImage.create(
        product_id=test_product.product_id,
        image="test_image.jpg",
        sort_order=10
    )
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/images/{product_image.product_image_id}/primary"
    )
    assert response.status_code == 401


# ==================== 3.4.5 更新图片排序 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_image_sort_success(async_client, auth_headers_admin, test_product):
    """测试API：成功更新图片排序"""
    from app.models.catalog.product_image import ProductImage
    product_image = await ProductImage.create(
        product_id=test_product.product_id,
        image="test_image.jpg",
        sort_order=10
    )
    
    new_sort_order = 50
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}/images/{product_image.product_image_id}/sort?sort_order={new_sort_order}",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    
    # 验证排序值已更新
    await product_image.refresh_from_db()
    assert product_image.sort_order == new_sort_order, "图片排序值应被更新"


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_image_sort_not_found(async_client, auth_headers_admin, test_product):
    """测试API：商品图片不存在（期望404）"""
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}/images/999999/sort?sort_order=10",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_update_image_sort_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    from app.models.catalog.product_image import ProductImage
    product_image = await ProductImage.create(
        product_id=test_product.product_id,
        image="test_image.jpg",
        sort_order=10
    )
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}/images/{product_image.product_image_id}/sort?sort_order=20"
    )
    assert response.status_code == 401


# ==================== 测试用例：商品分类关联接口 ====================

# ==================== 3.5.1 获取商品分类列表 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_categories_success(async_client, auth_headers_admin, test_product, test_categories):
    """测试API：成功获取商品分类列表"""
    # 先添加一个分类
    from app.models.catalog.product_to_category import ProductToCategory
    await ProductToCategory.create(
        product_id=test_product.product_id,
        category_id=test_categories["parent"].category_id
    )
    
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/categories",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_categories_empty(async_client, auth_headers_admin, test_product):
    """测试API：商品无分类（空列表）"""
    response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/categories",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_product_categories_not_found(async_client, auth_headers_admin):
    """测试API：商品不存在（期望404）"""
    response = await async_client.get(
        "/api/v1/products/999999/categories",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_list_product_categories_without_auth(async_client, test_product):
    """测试API：未认证访问（期望401）"""
    response = await async_client.get(f"/api/v1/products/{test_product.product_id}/categories")
    assert response.status_code == 401


# ==================== 3.5.2 添加商品分类 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_category_success(async_client, auth_headers_admin, test_product, test_categories):
    """测试API：成功添加商品分类"""
    category_data = {
        "category_id": test_categories["parent"].category_id
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/categories",
        json=category_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_category_validation_invalid_product(async_client, auth_headers_admin, test_categories):
    """测试API：商品不存在（期望404）"""
    category_data = {
        "category_id": test_categories["parent"].category_id
    }
    
    response = await async_client.post(
        "/api/v1/products/999999/categories",
        json=category_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_add_product_category_validation_invalid_category(async_client, auth_headers_admin, test_product):
    """测试API：分类不存在（期望404，因为ProductCategoryService抛出NotFoundException）"""
    category_data = {
        "category_id": 999999
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/categories",
        json=category_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 404  # ProductCategoryService抛出NotFoundException，路由转换为404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_add_product_category_without_auth(async_client, test_product, test_categories):
    """测试API：未认证访问（期望401）"""
    category_data = {
        "category_id": test_categories["parent"].category_id
    }
    
    response = await async_client.post(
        f"/api/v1/products/{test_product.product_id}/categories",
        json=category_data
    )
    assert response.status_code == 401


# ==================== 3.5.3 删除商品分类 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_category_success(async_client, auth_headers_admin, test_product, test_categories):
    """测试API：成功删除商品分类"""
    # 先添加一个分类
    from app.models.catalog.product_to_category import ProductToCategory
    await ProductToCategory.create(
        product_id=test_product.product_id,
        category_id=test_categories["parent"].category_id
    )
    
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/categories/{test_categories['parent'].category_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 204


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_product_category_not_found(async_client, auth_headers_admin, test_product):
    """测试API：商品分类不存在（期望404）"""
    response = await async_client.delete(
        f"/api/v1/products/{test_product.product_id}/categories/999999",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


# ==================== 3.5.4 批量更新商品分类 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_batch_update_product_categories_success(async_client, auth_headers_admin, test_product, test_categories):
    """测试API：成功批量更新商品分类"""
    # 先添加一个分类
    from app.models.catalog.product_to_category import ProductToCategory
    await ProductToCategory.create(
        product_id=test_product.product_id,
        category_id=test_categories["parent"].category_id
    )
    
    # 批量更新为新的分类列表（包含父分类和子分类）
    category_ids = [
        test_categories["parent"].category_id,
        test_categories["child"].category_id
    ]
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}/categories",
        json=category_ids,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    
    # 验证分类已更新（应该包含两个分类）
    list_response = await async_client.get(
        f"/api/v1/products/{test_product.product_id}/categories",
        headers=auth_headers_admin
    )
    assert list_response.status_code == 200
    categories = list_response.json()
    assert len(categories) == 2
    category_ids_returned = [cat["category_id"] for cat in categories]
    assert test_categories["parent"].category_id in category_ids_returned
    assert test_categories["child"].category_id in category_ids_returned


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_batch_update_product_categories_validation_invalid_categories(async_client, auth_headers_admin, test_product, test_categories):
    """测试API：无效分类ID（期望404）"""
    # 使用不存在的分类ID
    invalid_category_ids = [
        test_categories["parent"].category_id,
        999999  # 不存在的分类ID
    ]
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}/categories",
        json=invalid_category_ids,
        headers=auth_headers_admin
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_batch_update_product_categories_validation_duplicate(async_client, auth_headers_admin, test_product, test_categories):
    """测试API：重复分类ID（期望422）"""
    # 使用重复的分类ID
    duplicate_category_ids = [
        test_categories["parent"].category_id,
        test_categories["parent"].category_id  # 重复的分类ID
    ]
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}/categories",
        json=duplicate_category_ids,
        headers=auth_headers_admin
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.product
@pytest.mark.api
@pytest.mark.permission
@pytest.mark.asyncio
async def test_api_batch_update_product_categories_without_auth(async_client, test_product, test_categories):
    """测试API：未认证访问（期望401）"""
    category_ids = [
        test_categories["parent"].category_id
    ]
    
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}/categories",
        json=category_ids
    )
    assert response.status_code == 401


# ==================== 测试用例：完整业务流程 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.business
@pytest.mark.asyncio
async def test_product_lifecycle(async_client, auth_headers_admin, test_languages, test_manufacturer, 
                                  test_stock_status, test_tax_class, test_weight_class, test_length_class):
    """测试API：商品完整生命周期（创建→更新→删除）"""
    unique_id = uuid.uuid4().hex[:8]
    
    # 1. 创建商品
    product_data = {
        "model": f"LIFECYCLE-{unique_id}",
        "price": "99.99",
        "quantity": 100,
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Lifecycle Product {lang.code} {unique_id}"
            }
            for lang in test_languages
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    product_id = create_response.json()["product_id"]
    
    # 2. 更新商品
    update_data = {
        "price": "199.99",
        "quantity": 200
    }
    
    update_response = await async_client.patch(
        f"/api/v1/products/{product_id}",
        json=update_data,
        headers=auth_headers_admin
    )
    assert update_response.status_code == 200
    # 价格格式：Decimal序列化可能包含尾随零，比较数值而非字符串
    assert float(update_response.json()["price"]) == float(update_data["price"])
    
    # 3. 删除商品
    delete_response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=auth_headers_admin
    )
    assert delete_response.status_code == 204
    
    # 4. 验证商品已删除
    get_response = await async_client.get(
        f"/api/v1/products/{product_id}",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 404


@pytest.mark.product
@pytest.mark.api
@pytest.mark.business
@pytest.mark.asyncio
async def test_variant_product_flow(async_client, auth_headers_admin, test_languages, test_manufacturer,
                                     test_stock_status, test_tax_class, test_weight_class, test_length_class):
    """测试API：变体商品业务流程"""
    unique_id = uuid.uuid4().hex[:8]
    
    # 1. 创建主商品
    master_product_data = {
        "model": f"MASTER-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": f"Master Product {unique_id}"
            }
        ]
    }
    
    master_response = await async_client.post(
        "/api/v1/products/",
        json=master_product_data,
        headers=auth_headers_admin
    )
    assert master_response.status_code == 201
    master_id = master_response.json()["product_id"]
    
    # 2. 创建变体商品
    variant_product_data = {
        "master_id": master_id,
        "model": f"VARIANT-{unique_id}",
        "price": "89.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": f"Variant Product {unique_id}"
            }
        ]
    }
    
    variant_response = await async_client.post(
        "/api/v1/products/",
        json=variant_product_data,
        headers=auth_headers_admin
    )
    assert variant_response.status_code == 201
    variant_id = variant_response.json()["product_id"]
    assert variant_response.json()["master_id"] == master_id
    
    # 3. 查询变体商品列表
    list_response = await async_client.get(
        f"/api/v1/products/?filter[master_id]={master_id}",
        headers=auth_headers_admin
    )
    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data) >= 1


# ==================== 阶段2（P1）：创建商品验证测试（补充） ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_with_attributes(async_client, auth_headers_admin, test_languages, test_attributes):
    """测试API：创建商品（含属性）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Product with Attributes {lang.code} {unique_id}"
            }
            for lang in test_languages
        ],
        "attributes": [
            {
                "attribute_id": test_attributes[0].attribute_id,
                "descriptions": [
                    {
                        "language_id": lang.language_id,
                        "text": f"Attribute Value {lang.code}"
                    }
                    for lang in test_languages
                ]
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] > 0
    
    # 验证属性已创建
    # ProductAttribute是复合主键表(product_id, attribute_id, language_id)
    # 每个语言的描述会创建一条记录，所以应该有多条记录
    from app.models.catalog.product_attribute import ProductAttribute
    attributes = await ProductAttribute.filter(product_id=data["product_id"]).values('attribute_id', 'language_id')
    assert len(attributes) == len(test_languages)  # 应该为每个语言创建一条记录
    # 验证所有记录的attribute_id都相同
    attribute_ids = {attr['attribute_id'] for attr in attributes}
    assert len(attribute_ids) == 1  # 应该只有一个唯一的attribute_id
    assert test_attributes[0].attribute_id in attribute_ids


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_with_options(async_client, auth_headers_admin, test_languages, test_options, test_option_values):
    """测试API：创建商品（含选项）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Product with Options {lang.code} {unique_id}"
            }
            for lang in test_languages
        ],
        "options": [
            {
                "option_id": test_options[0].option_id,
                "value": "",
                "required": 1,
                "product_option_values": [
                    {
                        "option_value_id": test_option_values[0].option_value_id,
                        "quantity": 10,
                        "subtract": 1,
                        "price": "10.00",
                        "price_prefix": "+"
                    }
                ]
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] > 0
    
    # 验证选项已创建
    from app.models.catalog.product_option import ProductOption
    options = await ProductOption.filter(product_id=data["product_id"]).values('option_id')
    assert len(options) == 1
    assert options[0]["option_id"] == test_options[0].option_id


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_with_images(async_client, auth_headers_admin, test_languages):
    """测试API：创建商品（含图片）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Product with Images {lang.code} {unique_id}"
            }
            for lang in test_languages
        ],
        "images": [
            {
                "image": "image1.jpg",
                "sort_order": 10
            },
            {
                "image": "image2.jpg",
                "sort_order": 20
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] > 0
    
    # 验证图片已创建
    from app.models.catalog.product_image import ProductImage
    images = await ProductImage.filter(product_id=data["product_id"]).values('image', 'sort_order')
    assert len(images) == 2
    assert images[0]["image"] == "image1.jpg"
    assert images[1]["image"] == "image2.jpg"


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_with_categories(async_client, auth_headers_admin, test_languages, test_categories):
    """测试API：创建商品（含分类）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Product with Categories {lang.code} {unique_id}"
            }
            for lang in test_languages
        ],
        "category_ids": [
            test_categories["parent"].category_id,
            test_categories["child"].category_id
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] > 0
    
    # 验证分类已创建
    from app.models.catalog.product_to_category import ProductToCategory
    categories = await ProductToCategory.filter(product_id=data["product_id"]).values('category_id')
    assert len(categories) == 2
    category_ids = {c["category_id"] for c in categories}
    assert test_categories["parent"].category_id in category_ids
    assert test_categories["child"].category_id in category_ids


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_with_related(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：创建商品（含相关商品）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Product with Related {lang.code} {unique_id}"
            }
            for lang in test_languages
        ],
        "related_product_ids": [test_product.product_id]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] > 0
    
    # 验证相关商品已创建
    from app.models.catalog.product_related import ProductRelated
    related = await ProductRelated.filter(product_id=data["product_id"]).values('related_id')
    assert len(related) == 1
    assert related[0]["related_id"] == test_product.product_id


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_with_all_associations(async_client, auth_headers_admin, test_languages, test_attributes, test_options, test_option_values, test_categories, test_product):
    """测试API：创建商品（含所有关联数据）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Product with All {lang.code} {unique_id}"
            }
            for lang in test_languages
        ],
        "attributes": [
            {
                "attribute_id": test_attributes[0].attribute_id,
                "descriptions": [
                    {
                        "language_id": lang.language_id,
                        "text": f"Attribute Value {lang.code}"
                    }
                    for lang in test_languages
                ]
            }
        ],
        "options": [
            {
                "option_id": test_options[0].option_id,
                "value": "",
                "required": 1,
                "product_option_values": [
                    {
                        "option_value_id": test_option_values[0].option_value_id,
                        "quantity": 10,
                        "subtract": 1,
                        "price": "10.00",
                        "price_prefix": "+"
                    }
                ]
            }
        ],
        "images": [
            {
                "image": "all_image1.jpg",
                "sort_order": 10
            }
        ],
        "category_ids": [test_categories["parent"].category_id],
        "related_product_ids": [test_product.product_id]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] > 0
    
    # 验证所有关联数据都已创建
    from app.models.catalog.product_attribute import ProductAttribute
    from app.models.catalog.product_option import ProductOption
    from app.models.catalog.product_image import ProductImage
    from app.models.catalog.product_to_category import ProductToCategory
    from app.models.catalog.product_related import ProductRelated
    
    # ProductAttribute是复合主键表，每个语言的描述会创建一条记录
    attributes = await ProductAttribute.filter(product_id=data["product_id"]).values('attribute_id', 'language_id')
    assert len(attributes) >= len(test_languages)  # 至少为每个语言创建一条记录
    # 验证attribute_id的唯一性
    attribute_ids = {attr['attribute_id'] for attr in attributes}
    assert len(attribute_ids) >= 1  # 至少有一个唯一的attribute_id
    
    options = await ProductOption.filter(product_id=data["product_id"]).values('option_id')
    assert len(options) == 1
    
    images = await ProductImage.filter(product_id=data["product_id"]).values('image')
    assert len(images) == 1
    
    categories = await ProductToCategory.filter(product_id=data["product_id"]).values('category_id')
    assert len(categories) == 1
    
    related = await ProductRelated.filter(product_id=data["product_id"]).values('related_id')
    assert len(related) == 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_product_validation_self_related(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：商品关联自己（期望422）"""
    # 创建商品后，尝试更新时关联自己
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"MODEL-{unique_id}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Test Product {lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    product_id = response.json()["product_id"]
    
    # 尝试更新时关联自己（应该失败）
    update_data = {
        "related_product_ids": [product_id]  # 关联自己
    }
    update_response = await async_client.put(
        f"/api/v1/products/{product_id}",
        json=update_data,
        headers=auth_headers_admin
    )
    # 更新时关联自己应该返回422
    assert update_response.status_code == 422


# ==================== 阶段2（P1）：更新商品验证测试 ====================

@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_product_with_descriptions(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：更新商品（含多语言描述）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"UPDATED-{unique_id}",
        "price": "199.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Updated Product {lang.code} {unique_id}",
                "description": f"Updated Description {lang.code}",
                "meta_title": f"Updated Meta Title {lang.code}",
                "meta_description": f"Updated Meta Description {lang.code}",
                "meta_keyword": f"updated,keyword,{lang.code}"
            }
            for lang in test_languages
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data.get("descriptions", [])) == len(test_languages)
    
    # 验证描述已更新
    for desc in data["descriptions"]:
        assert "Updated" in desc["name"]


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_product_with_associations(async_client, auth_headers_admin, test_product, test_languages, test_attributes, test_options, test_option_values, test_categories):
    """测试API：更新商品（含关联数据）"""
    unique_id = uuid.uuid4().hex[:8]
    product_data = {
        "model": f"UPDATED-{unique_id}",
        "price": "199.99",
        "descriptions": [
            {
                "language_id": lang.language_id,
                "name": f"Updated Product {lang.code} {unique_id}"
            }
            for lang in test_languages
        ],
        "attributes": [
            {
                "attribute_id": test_attributes[0].attribute_id,
                "descriptions": [
                    {
                        "language_id": lang.language_id,
                        "text": f"Updated Attribute Value {lang.code}"
                    }
                    for lang in test_languages
                ]
            }
        ],
        "options": [
            {
                "option_id": test_options[0].option_id,
                "value": "",
                "required": 1,
                "product_option_values": [
                    {
                        "option_value_id": test_option_values[0].option_value_id,
                        "quantity": 20,
                        "subtract": 1,
                        "price": "20.00",
                        "price_prefix": "+"
                    }
                ]
            }
        ],
        "category_ids": [test_categories["parent"].category_id]
    }
    
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == test_product.product_id
    
    # 验证关联数据已更新
    from app.models.catalog.product_attribute import ProductAttribute
    from app.models.catalog.product_option import ProductOption
    from app.models.catalog.product_to_category import ProductToCategory
    
    attributes = await ProductAttribute.filter(product_id=test_product.product_id).values('attribute_id')
    assert len(attributes) >= 1
    
    options = await ProductOption.filter(product_id=test_product.product_id).values('option_id')
    assert len(options) >= 1
    
    categories = await ProductToCategory.filter(product_id=test_product.product_id).values('category_id')
    assert len(categories) >= 1


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_product_validation_errors(async_client, auth_headers_admin, test_product, test_languages):
    """测试API：更新商品验证错误"""
    # 测试1：型号为空
    product_data = {
        "model": "",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422
    
    # 测试2：名称为空
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "99.99",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": ""  # 空名称
            }
        ]
    }
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422
    
    # 测试3：价格为负数
    product_data = {
        "model": f"MODEL-{uuid.uuid4().hex[:8]}",
        "price": "-10.00",
        "descriptions": [
            {
                "language_id": test_languages[0].language_id,
                "name": "Test Product"
            }
        ]
    }
    response = await async_client.put(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422


@pytest.mark.product
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_patch_product_validation_errors(async_client, auth_headers_admin, test_product):
    """测试API：部分更新商品验证错误"""
    # 测试1：价格为负数
    product_data = {
        "price": "-10.00"
    }
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422
    
    # 测试2：库存为负数
    product_data = {
        "quantity": -1
    }
    response = await async_client.patch(
        f"/api/v1/products/{test_product.product_id}",
        json=product_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422

