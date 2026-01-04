"""
Unit tests for Option API and Service
包含基础校验测试、逻辑校验测试、权限测试和API具体业务测试
"""
import pytest
import uuid
import json
from httpx import AsyncClient
from app.main import app
from app.models.catalog.option import Option
from app.models.catalog.option_description import OptionDescription
from app.models.catalog.option_value import OptionValue
from app.models.catalog.option_value_description import OptionValueDescription
from app.models.catalog.product_option import ProductOption
from app.models.localisation.language import Language
from app.services.option_service import OptionService
from app.schemas.option import (
    OptionCreate, OptionUpdate, OptionDescriptionCreate
)
from app.exceptions import NotFoundException, ConflictException, ValidationException


# ==================== 用户角色权限梳理 ====================
"""
测试用户角色权限设计：

1. 管理员用户（admin_user）：
   - 权限：option:read, option:create, option:update, option:delete
   - 用途：测试正常业务流程

2. 只读用户（readonly_user）：
   - 权限：option:read
   - 用途：测试只读权限限制

3. 创建用户（create_user）：
   - 权限：option:read, option:create
   - 用途：测试创建权限，验证无法更新/删除

4. 更新用户（update_user）：
   - 权限：option:read, option:update
   - 用途：测试更新权限，验证无法创建/删除

5. 无权限用户（no_permission_user）：
   - 权限：无
   - 用途：测试无权限访问

6. 部分权限用户（partial_user）：
   - 权限：option:read, option:create（无update/delete）
   - 用途：测试部分权限场景
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
        "option": ["read"],
        "option_value": ["read"],
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
        "option": ["read", "create"],
        "option_value": ["read", "create"],
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
        "option": ["read", "update"],
        "option_value": ["read", "update"],
    }
    
    from app.models.system.user_group import UserGroup
    user_group = UserGroup(
        name=f"Update Group_{uuid.uuid4().hex[:8]}",
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
    from datetime import datetime
    
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
    from datetime import datetime
    
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
    from datetime import datetime
    
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
    from datetime import datetime
    
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
async def no_permission_user(db_transaction, no_permission_user_group):
    """创建无权限用户"""
    from app.models.system.user import User
    from app.core.security import get_password_hash
    from datetime import datetime
    
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
async def auth_headers_no_permission(no_permission_user):
    """无权限用户的认证头"""
    from app.core.security import create_access_token
    
    token = create_access_token(data={"sub": str(no_permission_user.user_id)})
    return {"Authorization": f"Bearer {token}"}


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
async def test_option(db_transaction, test_languages):
    """创建测试选项（select类型，带选项值）"""
    # 创建选项
    option = await Option.create(
        type="select",
        validation=None,
        sort_order=10
    )
    
    # 创建描述
    for language in test_languages:
        await OptionDescription.create(
            option_id=option.option_id,
            language_id=language.language_id,
            name=f"Test Option {language.code}"
        )
    
    return option


@pytest.fixture
async def test_option_with_values(db_transaction, test_languages, test_option):
    """创建带选项值的测试选项"""
    # 创建选项值
    values = []
    for i, sort_order in enumerate([10, 20, 30], start=1):
        value = await OptionValue.create(
            option_id=test_option.option_id,
            image=None,
            sort_order=sort_order
        )
        
        # 创建选项值描述
        for language in test_languages:
            await OptionValueDescription.create(
                option_value_id=value.option_value_id,
                language_id=language.language_id,
                option_id=test_option.option_id,
                name=f"Value {i} {language.code}"
            )
        values.append(value)
    
    return test_option, values


# ==================== 权限测试 ====================

@pytest.mark.option
@pytest.mark.permission
@pytest.mark.asyncio
async def test_list_options_without_auth(async_client):
    """测试未认证用户访问选项列表"""
    response = await async_client.get("/api/v1/options/")
    assert response.status_code == 401  # Unauthorized


@pytest.mark.option
@pytest.mark.permission
@pytest.mark.asyncio
async def test_list_options_with_readonly_permission(async_client, auth_headers_readonly, test_option):
    """测试只读用户访问选项列表"""
    response = await async_client.get("/api/v1/options/", headers=auth_headers_readonly)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.option
@pytest.mark.permission
@pytest.mark.asyncio
async def test_list_options_without_permission(async_client, auth_headers_no_permission):
    """测试无权限用户访问选项列表"""
    response = await async_client.get("/api/v1/options/", headers=auth_headers_no_permission)
    assert response.status_code == 403  # Forbidden


@pytest.mark.option
@pytest.mark.permission
@pytest.mark.asyncio
async def test_create_option_without_permission(async_client, auth_headers_readonly):
    """测试只读用户尝试创建选项"""
    option_data = {
        "type": "text",
        "sort_order": 0,
        "descriptions": [
            {"language_id": 1, "name": "Test Option"}
        ]
    }
    response = await async_client.post("/api/v1/options/", json=option_data, headers=auth_headers_readonly)
    assert response.status_code == 403  # Forbidden


@pytest.mark.option
@pytest.mark.permission
@pytest.mark.asyncio
async def test_create_option_with_create_permission(async_client, auth_headers_create, test_languages):
    """测试创建权限用户创建选项"""
    option_data = {
        "type": "text",
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Test Option {lang.code}"}
            for lang in test_languages
        ]
    }
    response = await async_client.post("/api/v1/options/", json=option_data, headers=auth_headers_create)
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "text"
    assert len(data["descriptions"]) == len(test_languages)


@pytest.mark.option
@pytest.mark.permission
@pytest.mark.asyncio
async def test_update_option_without_permission(async_client, auth_headers_create, test_option, test_languages):
    """测试创建权限用户尝试更新选项"""
    option_data = {
        "type": "text",
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Updated Option {lang.code}"}
            for lang in test_languages
        ]
    }
    response = await async_client.put(
        f"/api/v1/options/{test_option.option_id}",
        json=option_data,
        headers=auth_headers_create
    )
    assert response.status_code == 403  # Forbidden


@pytest.mark.option
@pytest.mark.permission
@pytest.mark.asyncio
async def test_delete_option_without_permission(async_client, auth_headers_update, test_option):
    """测试更新权限用户尝试删除选项"""
    response = await async_client.delete(
        f"/api/v1/options/{test_option.option_id}",
        headers=auth_headers_update
    )
    assert response.status_code == 403  # Forbidden


# ==================== 基础校验测试（数据验证） ====================

@pytest.mark.option
@pytest.mark.model
@pytest.mark.asyncio
async def test_option_model_creation(db_transaction):
    """测试选项模型创建（基础校验）"""
    option = Option(type="text", sort_order=10)
    await option.save()
    
    assert option.option_id is not None
    assert option.type == "text"
    assert option.sort_order == 10


@pytest.mark.option
@pytest.mark.model
@pytest.mark.asyncio
async def test_option_description_model_creation(db_transaction, test_languages):
    """测试选项描述模型创建（基础校验）"""
    option = await Option.create(type="text", sort_order=5)
    
    desc = await OptionDescription.create(
        option_id=option.option_id,
        language_id=test_languages[0].language_id,
        name="Test Option"
    )
    
    assert desc.option_id == option.option_id
    assert desc.language_id == test_languages[0].language_id
    assert desc.name == "Test Option"


@pytest.mark.option
@pytest.mark.model
@pytest.mark.asyncio
async def test_option_schema_validation(db_transaction):
    """测试选项Schema验证（基础校验）"""
    # 测试无效类型
    with pytest.raises(Exception):  # ValidationError
        OptionCreate(
            type="invalid_type",
            sort_order=0,
            descriptions=[{"language_id": 1, "name": "Test"}]
        )
    
    # 测试空描述数组
    with pytest.raises(Exception):  # ValidationError
        OptionCreate(
            type="text",
            sort_order=0,
            descriptions=[]
        )
    
    # 测试描述名称长度验证
    with pytest.raises(Exception):  # ValidationError
        OptionDescriptionCreate(
            language_id=1,
            name=""  # 空名称应该失败
        )


# ==================== 逻辑校验测试（业务逻辑） ====================

@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_list_options(db_transaction, test_languages):
    """测试服务层：获取选项列表（逻辑校验）"""
    service = OptionService()
    
    # 创建测试数据
    option1 = await Option.create(type="text", sort_order=10)
    option2 = await Option.create(type="select", sort_order=5)
    
    await OptionDescription.create(
        option_id=option1.option_id,
        language_id=test_languages[0].language_id,
        name="Option 1"
    )
    
    await OptionDescription.create(
        option_id=option2.option_id,
        language_id=test_languages[0].language_id,
        name="Option 2"
    )
    
    # 测试列表获取
    result = await service.list_options(skip=0, limit=20)
    assert len(result) >= 2
    
    # 测试排序
    result = await service.list_options(skip=0, limit=20, sort="sort_order", order="asc")
    assert result[0].sort_order <= result[1].sort_order
    
    # 测试类型筛选
    result = await service.list_options(skip=0, limit=20, filter_type="text")
    assert all(opt.type == "text" for opt in result)
    
    # 测试名称筛选
    result = await service.list_options(skip=0, limit=20, filter_name="Option 1")
    assert len(result) >= 1
    assert any("Option 1" in desc.name for opt in result for desc in opt.descriptions)


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_get_option(db_transaction, test_option):
    """测试服务层：获取选项详情（逻辑校验）"""
    service = OptionService()
    
    result = await service.get_option(option_id=test_option.option_id)
    assert result.option_id == test_option.option_id
    assert result.type == "select"
    assert len(result.descriptions) > 0


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_get_option_not_found(db_transaction):
    """测试服务层：获取不存在的选项（逻辑校验）"""
    service = OptionService()
    
    with pytest.raises(NotFoundException):
        await service.get_option(option_id=99999)


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_create_option(db_transaction, test_languages):
    """测试服务层：创建选项（逻辑校验）"""
    service = OptionService()
    
    option_data = OptionCreate(
        type="text",
        validation=None,
        sort_order=5,
        descriptions=[
            OptionDescriptionCreate(language_id=lang.language_id, name=f"Test Option {lang.code}")
            for lang in test_languages
        ]
    )
    
    result = await service.create_option(option_data)
    assert result.type == "text"
    assert result.sort_order == 5
    assert len(result.descriptions) == len(test_languages)


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_create_option_duplicate_language(db_transaction, test_languages):
    """测试服务层：创建选项时语言ID重复（逻辑校验）"""
    service = OptionService()
    
    option_data = OptionCreate(
        type="text",
        sort_order=5,
        descriptions=[
            OptionDescriptionCreate(language_id=test_languages[0].language_id, name="Test 1"),
            OptionDescriptionCreate(language_id=test_languages[0].language_id, name="Test 2"),  # 重复
        ]
    )
    
    with pytest.raises(ValidationException):
        await service.create_option(option_data)


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_create_option_empty_name(db_transaction, test_languages):
    """测试服务层：创建选项时名称为空（逻辑校验）"""
    service = OptionService()
    
    # 使用 model_construct 绕过 Schema 验证，直接测试服务层验证逻辑
    desc = OptionDescriptionCreate.model_construct(
        language_id=test_languages[0].language_id,
        name=""  # 空名称
    )
    
    option_data = OptionCreate.model_construct(
        type="text",
        sort_order=5,
        descriptions=[desc]
    )
    
    with pytest.raises(ValidationException):
        await service.create_option(option_data)


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_create_option_name_too_long(db_transaction, test_languages):
    """测试服务层：创建选项时名称过长（逻辑校验）"""
    service = OptionService()
    
    # 使用 model_construct 绕过 Schema 验证，直接测试服务层验证逻辑
    long_name = "a" * 129  # 超过128字符
    desc = OptionDescriptionCreate.model_construct(
        language_id=test_languages[0].language_id,
        name=long_name
    )
    
    option_data = OptionCreate.model_construct(
        type="text",
        sort_order=5,
        descriptions=[desc]
    )
    
    with pytest.raises(ValidationException):
        await service.create_option(option_data)


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_update_option(db_transaction, test_option_with_values, test_languages):
    """测试服务层：更新选项（逻辑校验）"""
    service = OptionService()
    
    # test_option_with_values 返回 (option, values) 元组
    test_option, _ = test_option_with_values
    
    # 使用 test_option_with_values，确保选项已有选项值（满足radio类型的要求）
    option_data = OptionCreate(
        type="radio",
        validation="required",
        sort_order=20,
        descriptions=[
            OptionDescriptionCreate(language_id=lang.language_id, name=f"Updated Option {lang.code}")
            for lang in test_languages
        ]
    )
    
    result = await service.update_option(test_option.option_id, option_data)
    assert result.type == "radio"
    assert result.validation == "required"
    assert result.sort_order == 20
    assert len(result.descriptions) == len(test_languages)


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_update_option_type_requires_values(db_transaction, test_languages):
    """测试服务层：更新选项类型为select/radio/checkbox时必须已有选项值（逻辑校验）"""
    service = OptionService()
    
    # 创建一个text类型的选项（不需要选项值）
    option = await Option.create(type="text", sort_order=0)
    for lang in test_languages:
        await OptionDescription.create(
            option_id=option.option_id,
            language_id=lang.language_id,
            name=f"Test {lang.code}"
        )
    
    # 尝试更新为select类型（但没有选项值）
    option_data = OptionCreate(
        type="select",
        sort_order=0,
        descriptions=[
            OptionDescriptionCreate(language_id=lang.language_id, name=f"Test {lang.code}")
            for lang in test_languages
        ]
    )
    
    with pytest.raises(ValidationException):
        await service.update_option(option.option_id, option_data)


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_delete_option(db_transaction, test_option):
    """测试服务层：删除选项（逻辑校验）"""
    service = OptionService()
    
    await service.delete_option(test_option.option_id)
    
    # 验证选项已删除
    with pytest.raises(NotFoundException):
        await service.get_option(test_option.option_id)


@pytest.mark.option
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_delete_option_used_by_product(db_transaction, test_option):
    """测试服务层：删除被商品使用的选项（逻辑校验）"""
    service = OptionService()
    
    # 创建商品选项关联
    product_option = await ProductOption.create(
        product_id=1,
        option_id=test_option.option_id,
        value="",
        required=1
    )
    
    # 尝试删除应该失败
    with pytest.raises(ConflictException):
        await service.delete_option(test_option.option_id)


# ==================== API测试（完整业务流程） ====================

@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_options(async_client, auth_headers_admin, test_option):
    """测试API：获取选项列表"""
    response = await async_client.get("/api/v1/options/", headers=auth_headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_list_options_with_filters(async_client, auth_headers_admin, test_option):
    """测试API：带筛选条件的选项列表"""
    # 测试类型筛选
    response = await async_client.get(
        "/api/v1/options/",
        params={"filter[type]": "select"},
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert all(opt["type"] == "select" for opt in data)
    
    # 测试分页
    response = await async_client.get(
        "/api/v1/options/",
        params={"skip": 0, "limit": 1},
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_option(async_client, auth_headers_admin, test_option):
    """测试API：获取选项详情"""
    response = await async_client.get(
        f"/api/v1/options/{test_option.option_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["option_id"] == test_option.option_id
    assert data["type"] == "select"
    assert "descriptions" in data


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_option_not_found(async_client, auth_headers_admin):
    """测试API：获取不存在的选项"""
    response = await async_client.get(
        "/api/v1/options/99999",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_option(async_client, auth_headers_admin, test_languages):
    """测试API：创建选项"""
    option_data = {
        "type": "text",
        "validation": None,
        "sort_order": 5,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"New Option {lang.code}"}
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/options/",
        json=option_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "text"
    assert len(data["descriptions"]) == len(test_languages)
    assert "option_id" in data


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_option_all_types(async_client, auth_headers_admin, test_languages):
    """测试API：创建所有类型的选项"""
    option_types = ["select", "radio", "checkbox", "text", "textarea", "file", "date", "datetime", "time", "image"]
    
    for opt_type in option_types:
        option_data = {
            "type": opt_type,
            "sort_order": 0,
            "descriptions": [
                {"language_id": lang.language_id, "name": f"{opt_type} Option {lang.code}"}
                for lang in test_languages
            ]
        }
        
        response = await async_client.post(
            "/api/v1/options/",
            json=option_data,
            headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == opt_type


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_option_validation_error(async_client, auth_headers_admin, test_languages):
    """测试API：创建选项时验证错误"""
    # 测试空描述（Pydantic验证在路由层拦截，返回422）
    option_data = {
        "type": "text",
        "sort_order": 0,
        "descriptions": []
    }
    
    response = await async_client.post(
        "/api/v1/options/",
        json=option_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422  # Pydantic验证返回422
    
    # 测试无效类型
    option_data = {
        "type": "invalid_type",
        "sort_order": 0,
        "descriptions": [
            {"language_id": test_languages[0].language_id, "name": "Test"}
        ]
    }
    
    response = await async_client.post(
        "/api/v1/options/",
        json=option_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_option(async_client, auth_headers_admin, test_option, test_languages):
    """测试API：更新选项"""
    # 先为select类型选项创建选项值（因为要更新为radio类型，需要已有选项值）
    from app.models.catalog.option_value import OptionValue
    from app.models.catalog.option_value_description import OptionValueDescription
    
    value = await OptionValue.create(
        option_id=test_option.option_id,
        sort_order=0
    )
    for lang in test_languages:
        await OptionValueDescription.create(
            option_value_id=value.option_value_id,
            language_id=lang.language_id,
            option_id=test_option.option_id,
            name=f"Value {lang.code}"
        )
    
    # 现在可以更新为radio类型
    option_data = {
        "type": "radio",
        "validation": "required",
        "sort_order": 15,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Updated Option {lang.code}"}
            for lang in test_languages
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/options/{test_option.option_id}",
        json=option_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "radio"
    assert data["validation"] == "required"
    assert data["sort_order"] == 15


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_patch_option(async_client, auth_headers_admin, test_option, test_languages):
    """测试API：部分更新选项"""
    # 只更新sort_order
    option_data = {
        "sort_order": 25
    }
    
    response = await async_client.patch(
        f"/api/v1/options/{test_option.option_id}",
        json=option_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sort_order"] == 25
    # 其他字段应该保持不变
    assert data["type"] == "select"
    
    # 只更新描述
    option_data = {
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Patched Option {lang.code}"}
            for lang in test_languages
        ]
    }
    
    response = await async_client.patch(
        f"/api/v1/options/{test_option.option_id}",
        json=option_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["descriptions"]) == len(test_languages)


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_option(async_client, auth_headers_admin, test_languages):
    """测试API：删除选项"""
    # 先创建一个选项
    option_data = {
        "type": "text",
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"To Delete {lang.code}"}
            for lang in test_languages
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/options/",
        json=option_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    option_id = create_response.json()["option_id"]
    
    # 删除选项
    response = await async_client.delete(
        f"/api/v1/options/{option_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 204
    
    # 验证选项已删除
    get_response = await async_client.get(
        f"/api/v1/options/{option_id}",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 404


@pytest.mark.option
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_option_used_by_product(async_client, auth_headers_admin, test_option):
    """测试API：删除被商品使用的选项"""
    # 创建商品选项关联
    await ProductOption.create(
        product_id=1,
        option_id=test_option.option_id,
        value="",
        required=1
    )
    
    # 尝试删除应该失败
    response = await async_client.delete(
        f"/api/v1/options/{test_option.option_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 400
    assert "已被商品使用" in response.json()["detail"]


# ==================== 业务场景测试（完整业务流程） ====================

@pytest.mark.option
@pytest.mark.business
@pytest.mark.asyncio
async def test_option_lifecycle(async_client, auth_headers_admin, test_languages):
    """测试选项完整生命周期：创建 -> 更新 -> 删除"""
    # 1. 创建选项
    option_data = {
        "type": "text",
        "sort_order": 10,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Lifecycle Option {lang.code}"}
            for lang in test_languages
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/options/",
        json=option_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    option_id = create_response.json()["option_id"]
    
    # 2. 获取选项
    get_response = await async_client.get(
        f"/api/v1/options/{option_id}",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 200
    assert get_response.json()["type"] == "text"
    
    # 3. 更新选项
    update_data = {
        "type": "textarea",
        "sort_order": 20,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Updated Lifecycle Option {lang.code}"}
            for lang in test_languages
        ]
    }
    
    update_response = await async_client.put(
        f"/api/v1/options/{option_id}",
        json=update_data,
        headers=auth_headers_admin
    )
    assert update_response.status_code == 200
    assert update_response.json()["type"] == "textarea"
    
    # 4. 部分更新
    patch_data = {"sort_order": 30}
    patch_response = await async_client.patch(
        f"/api/v1/options/{option_id}",
        json=patch_data,
        headers=auth_headers_admin
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["sort_order"] == 30
    
    # 5. 删除选项
    delete_response = await async_client.delete(
        f"/api/v1/options/{option_id}",
        headers=auth_headers_admin
    )
    assert delete_response.status_code == 204
    
    # 6. 验证已删除
    final_get_response = await async_client.get(
        f"/api/v1/options/{option_id}",
        headers=auth_headers_admin
    )
    assert final_get_response.status_code == 404


@pytest.mark.option
@pytest.mark.business
@pytest.mark.asyncio
async def test_option_with_multiple_languages(async_client, auth_headers_admin, test_languages):
    """测试多语言选项管理"""
    # 创建多语言选项
    option_data = {
        "type": "select",
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Multi-language Option {lang.code}"}
            for lang in test_languages
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/options/",
        json=option_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    option_id = create_response.json()["option_id"]
    
    # 验证所有语言描述都存在
    get_response = await async_client.get(
        f"/api/v1/options/{option_id}",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 200
    descriptions = get_response.json()["descriptions"]
    assert len(descriptions) == len(test_languages)
    
    # 验证每个语言都有对应的描述
    language_ids = {desc["language_id"] for desc in descriptions}
    assert language_ids == {lang.language_id for lang in test_languages}


@pytest.mark.option
@pytest.mark.business
@pytest.mark.asyncio
async def test_option_type_validation_rules(async_client, auth_headers_admin, test_languages):
    """测试不同选项类型的验证规则"""
    # 测试需要选项值的类型（select, radio, checkbox）
    # 这些类型在更新时必须已有选项值
    
    # 先创建一个text类型的选项
    option_data = {
        "type": "text",
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Text Option {lang.code}"}
            for lang in test_languages
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/options/",
        json=option_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    option_id = create_response.json()["option_id"]
    
    # 尝试更新为select类型（但没有选项值）应该失败
    update_data = {
        "type": "select",
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Select Option {lang.code}"}
            for lang in test_languages
        ]
    }
    
    update_response = await async_client.put(
        f"/api/v1/options/{option_id}",
        json=update_data,
        headers=auth_headers_admin
    )
    assert update_response.status_code == 400
    assert "必须至少有一个选项值" in update_response.json()["detail"]

