"""
Unit tests for OptionValue API and Service
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
from app.models.catalog.product_option_value import ProductOptionValue
from app.models.localisation.language import Language
from app.services.option_value_service import OptionValueService
from app.schemas.option_value import (
    OptionValueCreate, OptionValueUpdate, OptionValueDescriptionCreate, OptionValueSortUpdate
)
from app.exceptions import NotFoundException, ConflictException, ValidationException


# ==================== Fixtures: 复用Option测试的fixtures ====================

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
    """创建测试选项（select类型）"""
    option = await Option.create(
        type="select",
        validation=None,
        sort_order=10
    )
    
    for language in test_languages:
        await OptionDescription.create(
            option_id=option.option_id,
            language_id=language.language_id,
            name=f"Test Option {language.code}"
        )
    
    return option


@pytest.fixture
async def test_option_value(db_transaction, test_option, test_languages):
    """创建测试选项值"""
    value = await OptionValue.create(
        option_id=test_option.option_id,
        image="test_image.jpg",
        sort_order=10
    )
    
    for language in test_languages:
        await OptionValueDescription.create(
            option_value_id=value.option_value_id,
            language_id=language.language_id,
            option_id=test_option.option_id,
            name=f"Test Value {language.code}"
        )
    
    return value


@pytest.fixture
async def test_option_with_multiple_values(db_transaction, test_option, test_languages):
    """创建带多个选项值的测试选项"""
    values = []
    for i, sort_order in enumerate([10, 20, 30], start=1):
        value = await OptionValue.create(
            option_id=test_option.option_id,
            image=None,
            sort_order=sort_order
        )
        
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

@pytest.mark.option_value
@pytest.mark.permission
@pytest.mark.asyncio
async def test_get_option_value_without_auth(async_client):
    """测试未认证用户访问选项值"""
    response = await async_client.get("/api/v1/option-values/1")
    assert response.status_code == 401  # Unauthorized


@pytest.mark.option_value
@pytest.mark.permission
@pytest.mark.asyncio
async def test_get_option_value_with_readonly_permission(async_client, auth_headers_readonly, test_option_value):
    """测试只读用户访问选项值"""
    response = await async_client.get(
        f"/api/v1/option-values/{test_option_value.option_value_id}",
        headers=auth_headers_readonly
    )
    assert response.status_code == 200
    data = response.json()
    assert data["option_value_id"] == test_option_value.option_value_id


@pytest.mark.option_value
@pytest.mark.permission
@pytest.mark.asyncio
async def test_get_option_value_without_permission(async_client, auth_headers_no_permission):
    """测试无权限用户访问选项值"""
    response = await async_client.get(
        "/api/v1/option-values/1",
        headers=auth_headers_no_permission
    )
    assert response.status_code == 403  # Forbidden


@pytest.mark.option_value
@pytest.mark.permission
@pytest.mark.asyncio
async def test_create_option_value_without_permission(async_client, auth_headers_readonly, test_option, test_languages):
    """测试只读用户尝试创建选项值"""
    option_value_data = {
        "option_id": test_option.option_id,
        "image": None,
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Test Value {lang.code}"}
            for lang in test_languages
        ]
    }
    response = await async_client.post(
        "/api/v1/option-values/",
        json=option_value_data,
        headers=auth_headers_readonly
    )
    assert response.status_code == 403  # Forbidden


@pytest.mark.option_value
@pytest.mark.permission
@pytest.mark.asyncio
async def test_create_option_value_with_create_permission(async_client, auth_headers_create, test_option, test_languages):
    """测试创建权限用户创建选项值"""
    option_value_data = {
        "option_id": test_option.option_id,
        "image": None,
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"New Value {lang.code}"}
            for lang in test_languages
        ]
    }
    response = await async_client.post(
        "/api/v1/option-values/",
        json=option_value_data,
        headers=auth_headers_create
    )
    assert response.status_code == 201
    data = response.json()
    assert data["option_id"] == test_option.option_id
    assert len(data["descriptions"]) == len(test_languages)


# ==================== 基础校验测试（数据验证） ====================

@pytest.mark.option_value
@pytest.mark.model
@pytest.mark.asyncio
async def test_option_value_model_creation(db_transaction, test_option):
    """测试选项值模型创建（基础校验）"""
    value = OptionValue(
        option_id=test_option.option_id,
        image="test.jpg",
        sort_order=5
    )
    await value.save()
    
    assert value.option_value_id is not None
    assert value.option_id == test_option.option_id
    assert value.image == "test.jpg"
    assert value.sort_order == 5


@pytest.mark.option_value
@pytest.mark.model
@pytest.mark.asyncio
async def test_option_value_description_model_creation(db_transaction, test_option, test_languages):
    """测试选项值描述模型创建（基础校验）"""
    value = await OptionValue.create(
        option_id=test_option.option_id,
        image=None,
        sort_order=0
    )
    
    desc = await OptionValueDescription.create(
        option_value_id=value.option_value_id,
        language_id=test_languages[0].language_id,
        option_id=test_option.option_id,
        name="Test Value"
    )
    
    assert desc.option_value_id == value.option_value_id
    assert desc.language_id == test_languages[0].language_id
    assert desc.option_id == test_option.option_id
    assert desc.name == "Test Value"


@pytest.mark.option_value
@pytest.mark.model
@pytest.mark.asyncio
async def test_option_value_schema_validation(db_transaction):
    """测试选项值Schema验证（基础校验）"""
    # 测试空描述数组
    with pytest.raises(Exception):  # ValidationError
        OptionValueCreate(
            option_id=1,
            descriptions=[]
        )
    
    # 测试描述名称长度验证
    with pytest.raises(Exception):  # ValidationError
        OptionValueDescriptionCreate(
            language_id=1,
            name=""  # 空名称应该失败
        )


# ==================== 逻辑校验测试（业务逻辑） ====================

@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_get_option_value(db_transaction, test_option_value):
    """测试服务层：获取选项值详情（逻辑校验）"""
    service = OptionValueService()
    
    result = await service.get_option_value(option_value_id=test_option_value.option_value_id)
    assert result.option_value_id == test_option_value.option_value_id
    assert result.option_id == test_option_value.option_id
    assert len(result.descriptions) > 0


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_get_option_value_not_found(db_transaction):
    """测试服务层：获取不存在的选项值（逻辑校验）"""
    service = OptionValueService()
    
    with pytest.raises(NotFoundException):
        await service.get_option_value(option_value_id=99999)


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_create_option_value(db_transaction, test_option, test_languages):
    """测试服务层：创建选项值（逻辑校验）"""
    service = OptionValueService()
    
    option_value_data = OptionValueCreate(
        option_id=test_option.option_id,
        image="new_image.jpg",
        sort_order=15,
        descriptions=[
            OptionValueDescriptionCreate(language_id=lang.language_id, name=f"New Value {lang.code}")
            for lang in test_languages
        ]
    )
    
    result = await service.create_option_value(option_value_data)
    assert result.option_id == test_option.option_id
    assert result.image == "new_image.jpg"
    assert result.sort_order == 15
    assert len(result.descriptions) == len(test_languages)


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_create_option_value_invalid_option(db_transaction, test_languages):
    """测试服务层：为不存在的选项创建选项值（逻辑校验）"""
    service = OptionValueService()
    
    option_value_data = OptionValueCreate(
        option_id=99999,  # 不存在的选项ID
        descriptions=[
            OptionValueDescriptionCreate(language_id=lang.language_id, name=f"Value {lang.code}")
            for lang in test_languages
        ]
    )
    
    with pytest.raises(NotFoundException):
        await service.create_option_value(option_value_data)


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_create_option_value_duplicate_language(db_transaction, test_option, test_languages):
    """测试服务层：创建选项值时语言ID重复（逻辑校验）"""
    service = OptionValueService()
    
    option_value_data = OptionValueCreate(
        option_id=test_option.option_id,
        descriptions=[
            OptionValueDescriptionCreate(language_id=test_languages[0].language_id, name="Test 1"),
            OptionValueDescriptionCreate(language_id=test_languages[0].language_id, name="Test 2"),  # 重复
        ]
    )
    
    with pytest.raises(ValidationException):
        await service.create_option_value(option_value_data)


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_get_option_values(db_transaction, test_option_with_multiple_values):
    """测试服务层：获取选项下的所有选项值（逻辑校验）"""
    service = OptionValueService()
    option, values = test_option_with_multiple_values
    
    result = await service.get_option_values(option_id=option.option_id)
    assert len(result) == len(values)
    
    # 测试排序
    result = await service.get_option_values(option_id=option.option_id, sort="sort_order", order="asc")
    assert result[0].sort_order <= result[1].sort_order


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_update_option_value(db_transaction, test_option_value, test_languages):
    """测试服务层：更新选项值（逻辑校验）"""
    service = OptionValueService()
    
    option_value_data = OptionValueCreate(
        option_id=test_option_value.option_id,
        image="updated_image.jpg",
        sort_order=25,
        descriptions=[
            OptionValueDescriptionCreate(language_id=lang.language_id, name=f"Updated Value {lang.code}")
            for lang in test_languages
        ]
    )
    
    result = await service.update_option_value(test_option_value.option_value_id, option_value_data)
    assert result.image == "updated_image.jpg"
    assert result.sort_order == 25
    assert len(result.descriptions) == len(test_languages)


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_delete_option_value(db_transaction, test_option_with_multiple_values):
    """测试服务层：删除选项值（逻辑校验）"""
    service = OptionValueService()
    
    # 使用有多个选项值的fixture，删除其中一个（不是最后一个）
    option, values = test_option_with_multiple_values
    # 删除第一个选项值（不是最后一个，所以应该成功）
    option_value_id = values[0].option_value_id
    await service.delete_option_value(option_value_id)
    
    # 验证选项值已删除
    with pytest.raises(NotFoundException):
        await service.get_option_value(option_value_id)
    
    # 验证其他选项值仍然存在
    remaining_values = await service.get_option_values(option_id=option.option_id)
    assert len(remaining_values) == len(values) - 1


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_delete_option_value_used_by_product(db_transaction, test_option_value):
    """测试服务层：删除被商品使用的选项值（逻辑校验）"""
    service = OptionValueService()
    
    # 创建商品选项值关联
    await ProductOptionValue.create(
        product_option_id=1,
        product_id=1,
        option_id=test_option_value.option_id,
        option_value_id=test_option_value.option_value_id,
        quantity=10,
        subtract=1,
        price=0.0,
        price_prefix="+",
        points=0,
        points_prefix="+",
        weight=0.0,
        weight_prefix="+"
    )
    
    # 尝试删除应该失败
    with pytest.raises(ConflictException):
        await service.delete_option_value(test_option_value.option_value_id)


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_delete_last_option_value_for_select_type(db_transaction, test_languages):
    """测试服务层：删除select类型选项的最后一个选项值（逻辑校验）"""
    service = OptionValueService()
    
    # 创建select类型的选项，只有一个选项值
    option = await Option.create(type="select", sort_order=0)
    for lang in test_languages:
        await OptionDescription.create(
            option_id=option.option_id,
            language_id=lang.language_id,
            name=f"Select Option {lang.code}"
        )
    
    value = await OptionValue.create(option_id=option.option_id, sort_order=0)
    for lang in test_languages:
        await OptionValueDescription.create(
            option_value_id=value.option_value_id,
            language_id=lang.language_id,
            option_id=option.option_id,
            name=f"Value {lang.code}"
        )
    
    # 尝试删除最后一个选项值应该失败
    with pytest.raises(ConflictException):
        await service.delete_option_value(value.option_value_id)


@pytest.mark.option_value
@pytest.mark.service
@pytest.mark.asyncio
async def test_service_update_option_values_sort(db_transaction, test_option_with_multiple_values):
    """测试服务层：批量更新选项值排序（逻辑校验）"""
    service = OptionValueService()
    option, values = test_option_with_multiple_values
    
    from app.schemas.option_value import OptionValueSortUpdate
    
    sort_data = OptionValueSortUpdate(
        values=[
            {"option_value_id": values[0].option_value_id, "sort_order": 30},
            {"option_value_id": values[1].option_value_id, "sort_order": 10},
            {"option_value_id": values[2].option_value_id, "sort_order": 20},
        ]
    )
    
    result = await service.update_option_values_sort(option_id=option.option_id, sort_data=sort_data)
    assert result["success"] is True
    
    # 验证排序已更新
    updated_values = await service.get_option_values(option_id=option.option_id, sort="sort_order", order="asc")
    assert updated_values[0].sort_order == 10
    assert updated_values[1].sort_order == 20
    assert updated_values[2].sort_order == 30


# ==================== API测试（完整业务流程） ====================

@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_option_value(async_client, auth_headers_admin, test_option_value):
    """测试API：获取选项值详情"""
    response = await async_client.get(
        f"/api/v1/option-values/{test_option_value.option_value_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["option_value_id"] == test_option_value.option_value_id
    assert "descriptions" in data


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_option_value_not_found(async_client, auth_headers_admin):
    """测试API：获取不存在的选项值"""
    response = await async_client.get(
        "/api/v1/option-values/99999",
        headers=auth_headers_admin
    )
    assert response.status_code == 404


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_option_value(async_client, auth_headers_admin, test_option, test_languages):
    """测试API：创建选项值"""
    option_value_data = {
        "option_id": test_option.option_id,
        "image": "new_image.jpg",
        "sort_order": 5,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"New Value {lang.code}"}
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/option-values/",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["option_id"] == test_option.option_id
    assert data["image"] == "new_image.jpg"
    assert len(data["descriptions"]) == len(test_languages)
    assert "option_value_id" in data


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_option_value_validation_error(async_client, auth_headers_admin, test_option, test_languages):
    """测试API：创建选项值时验证错误"""
    # 测试空描述（Pydantic验证在路由层拦截，返回422）
    option_value_data = {
        "option_id": test_option.option_id,
        "descriptions": []
    }
    
    response = await async_client.post(
        "/api/v1/option-values/",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 422  # Pydantic验证返回422
    
    # 测试不存在的选项ID
    option_value_data = {
        "option_id": 99999,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Value {lang.code}"}
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        "/api/v1/option-values/",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 400


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_option_value(async_client, auth_headers_admin, test_option_value, test_languages):
    """测试API：更新选项值"""
    option_value_data = {
        "option_id": test_option_value.option_id,
        "image": "updated_image.jpg",
        "sort_order": 25,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Updated Value {lang.code}"}
            for lang in test_languages
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/option-values/{test_option_value.option_value_id}",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image"] == "updated_image.jpg"
    assert data["sort_order"] == 25


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_patch_option_value(async_client, auth_headers_admin, test_option_value):
    """测试API：部分更新选项值"""
    # 只更新sort_order
    option_value_data = {
        "sort_order": 50
    }
    
    response = await async_client.patch(
        f"/api/v1/option-values/{test_option_value.option_value_id}",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sort_order"] == 50
    # 其他字段应该保持不变
    assert data["option_id"] == test_option_value.option_id


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_option_value(async_client, auth_headers_admin, test_option_with_multiple_values, test_languages):
    """测试API：删除选项值"""
    # 使用有多个选项值的fixture，删除其中一个（不是最后一个）
    option, values = test_option_with_multiple_values
    
    # 删除第一个选项值（不是最后一个，所以应该成功）
    option_value_id = values[0].option_value_id
    
    # 删除选项值
    response = await async_client.delete(
        f"/api/v1/option-values/{option_value_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 204
    
    # 验证选项值已删除
    get_response = await async_client.get(
        f"/api/v1/option-values/{option_value_id}",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 404
    
    # 验证其他选项值仍然存在
    remaining_response = await async_client.get(
        f"/api/v1/option-values/options/{option.option_id}/values",
        headers=auth_headers_admin
    )
    assert remaining_response.status_code == 200
    remaining_values = remaining_response.json()
    assert len(remaining_values) == len(values) - 1


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_delete_option_value_used_by_product(async_client, auth_headers_admin, test_option_value):
    """测试API：删除被商品使用的选项值"""
    # 创建商品选项值关联
    await ProductOptionValue.create(
        product_option_id=1,
        product_id=1,
        option_id=test_option_value.option_id,
        option_value_id=test_option_value.option_value_id,
        quantity=10,
        subtract=1,
        price=0.0,
        price_prefix="+",
        points=0,
        points_prefix="+",
        weight=0.0,
        weight_prefix="+"
    )
    
    # 尝试删除应该失败
    response = await async_client.delete(
        f"/api/v1/option-values/{test_option_value.option_value_id}",
        headers=auth_headers_admin
    )
    assert response.status_code == 400
    assert "已被商品使用" in response.json()["detail"]


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_get_option_values(async_client, auth_headers_admin, test_option_with_multiple_values):
    """测试API：获取选项下的所有选项值"""
    option, values = test_option_with_multiple_values
    
    response = await async_client.get(
        f"/api/v1/option-values/options/{option.option_id}/values",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(values)
    assert all("option_value_id" in item for item in data)


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_create_option_value_for_option(async_client, auth_headers_admin, test_option, test_languages):
    """测试API：为选项创建选项值"""
    option_value_data = {
        "option_id": test_option.option_id,
        "image": None,
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"New Value {lang.code}"}
            for lang in test_languages
        ]
    }
    
    response = await async_client.post(
        f"/api/v1/option-values/options/{test_option.option_id}/values",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 201
    data = response.json()
    assert data["option_id"] == test_option.option_id


@pytest.mark.option_value
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_update_option_values_sort(async_client, auth_headers_admin, test_option_with_multiple_values):
    """测试API：批量更新选项值排序"""
    option, values = test_option_with_multiple_values
    
    sort_data = {
        "values": [
            {"option_value_id": values[0].option_value_id, "sort_order": 30},
            {"option_value_id": values[1].option_value_id, "sort_order": 10},
            {"option_value_id": values[2].option_value_id, "sort_order": 20},
        ]
    }
    
    response = await async_client.patch(
        f"/api/v1/option-values/options/{option.option_id}/values/sort",
        json=sort_data,
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # 验证排序已更新
    get_response = await async_client.get(
        f"/api/v1/option-values/options/{option.option_id}/values?sort=sort_order&order=asc",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 200
    sorted_values = get_response.json()
    assert sorted_values[0]["sort_order"] == 10
    assert sorted_values[1]["sort_order"] == 20
    assert sorted_values[2]["sort_order"] == 30


# ==================== 业务场景测试（完整业务流程） ====================

@pytest.mark.option_value
@pytest.mark.business
@pytest.mark.asyncio
async def test_option_value_lifecycle(async_client, auth_headers_admin, test_option_with_multiple_values, test_languages):
    """测试选项值完整生命周期：创建 -> 更新 -> 删除"""
    # 使用有多个选项值的fixture，确保删除时不会违反业务规则
    option, existing_values = test_option_with_multiple_values
    
    # 1. 创建新的选项值（现在有多个选项值了）
    option_value_data = {
        "option_id": option.option_id,
        "image": "lifecycle.jpg",
        "sort_order": 10,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Lifecycle Value {lang.code}"}
            for lang in test_languages
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/option-values/",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    option_value_id = create_response.json()["option_value_id"]
    
    # 2. 获取选项值
    get_response = await async_client.get(
        f"/api/v1/option-values/{option_value_id}",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 200
    assert get_response.json()["image"] == "lifecycle.jpg"
    
    # 3. 更新选项值
    update_data = {
        "option_id": option.option_id,
        "image": "updated_lifecycle.jpg",
        "sort_order": 20,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Updated Lifecycle Value {lang.code}"}
            for lang in test_languages
        ]
    }
    
    update_response = await async_client.put(
        f"/api/v1/option-values/{option_value_id}",
        json=update_data,
        headers=auth_headers_admin
    )
    assert update_response.status_code == 200
    assert update_response.json()["image"] == "updated_lifecycle.jpg"
    
    # 4. 部分更新
    patch_data = {"sort_order": 30}
    patch_response = await async_client.patch(
        f"/api/v1/option-values/{option_value_id}",
        json=patch_data,
        headers=auth_headers_admin
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["sort_order"] == 30
    
    # 5. 删除选项值（现在有多个选项值，可以删除）
    delete_response = await async_client.delete(
        f"/api/v1/option-values/{option_value_id}",
        headers=auth_headers_admin
    )
    assert delete_response.status_code == 204
    
    # 6. 验证已删除
    final_get_response = await async_client.get(
        f"/api/v1/option-values/{option_value_id}",
        headers=auth_headers_admin
    )
    assert final_get_response.status_code == 404


@pytest.mark.option_value
@pytest.mark.business
@pytest.mark.asyncio
async def test_option_value_with_multiple_languages(async_client, auth_headers_admin, test_option, test_languages):
    """测试多语言选项值管理"""
    # 创建多语言选项值
    option_value_data = {
        "option_id": test_option.option_id,
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Multi-language Value {lang.code}"}
            for lang in test_languages
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/option-values/",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    option_value_id = create_response.json()["option_value_id"]
    
    # 验证所有语言描述都存在
    get_response = await async_client.get(
        f"/api/v1/option-values/{option_value_id}",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 200
    descriptions = get_response.json()["descriptions"]
    assert len(descriptions) == len(test_languages)
    
    # 验证每个语言都有对应的描述
    language_ids = {desc["language_id"] for desc in descriptions}
    assert language_ids == {lang.language_id for lang in test_languages}


@pytest.mark.option_value
@pytest.mark.business
@pytest.mark.asyncio
async def test_option_value_deletion_prevents_last_value_removal(async_client, auth_headers_admin, test_languages):
    """测试删除选项值时防止删除最后一个选项值（select/radio/checkbox类型）"""
    # 创建select类型的选项，只有一个选项值
    option_data = {
        "type": "select",
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Select Option {lang.code}"}
            for lang in test_languages
        ]
    }
    
    create_option_response = await async_client.post(
        "/api/v1/options/",
        json=option_data,
        headers=auth_headers_admin
    )
    assert create_option_response.status_code == 201
    option_id = create_option_response.json()["option_id"]
    
    # 创建一个选项值
    option_value_data = {
        "option_id": option_id,
        "sort_order": 0,
        "descriptions": [
            {"language_id": lang.language_id, "name": f"Value {lang.code}"}
            for lang in test_languages
        ]
    }
    
    create_value_response = await async_client.post(
        "/api/v1/option-values/",
        json=option_value_data,
        headers=auth_headers_admin
    )
    assert create_value_response.status_code == 201
    option_value_id = create_value_response.json()["option_value_id"]
    
    # 尝试删除最后一个选项值应该失败
    delete_response = await async_client.delete(
        f"/api/v1/option-values/{option_value_id}",
        headers=auth_headers_admin
    )
    assert delete_response.status_code == 400
    assert "必须至少保留一个选项值" in delete_response.json()["detail"]


@pytest.mark.option_value
@pytest.mark.business
@pytest.mark.asyncio
async def test_option_value_sort_management(async_client, auth_headers_admin, test_option, test_languages):
    """测试选项值排序管理"""
    # 创建多个选项值
    values = []
    for i in range(3):
        option_value_data = {
            "option_id": test_option.option_id,
            "sort_order": i * 10,
            "descriptions": [
                {"language_id": lang.language_id, "name": f"Value {i+1} {lang.code}"}
                for lang in test_languages
            ]
        }
        
        create_response = await async_client.post(
            "/api/v1/option-values/",
            json=option_value_data,
            headers=auth_headers_admin
        )
        assert create_response.status_code == 201
        values.append(create_response.json())
    
    # 获取选项值列表（按sort_order排序）
    get_response = await async_client.get(
        f"/api/v1/option-values/options/{test_option.option_id}/values?sort=sort_order&order=asc",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 200
    sorted_values = get_response.json()
    assert len(sorted_values) == 3
    assert sorted_values[0]["sort_order"] <= sorted_values[1]["sort_order"]
    assert sorted_values[1]["sort_order"] <= sorted_values[2]["sort_order"]
    
    # 批量更新排序
    sort_data = {
        "values": [
            {"option_value_id": values[2]["option_value_id"], "sort_order": 5},
            {"option_value_id": values[0]["option_value_id"], "sort_order": 15},
            {"option_value_id": values[1]["option_value_id"], "sort_order": 25},
        ]
    }
    
    sort_response = await async_client.patch(
        f"/api/v1/option-values/options/{test_option.option_id}/values/sort",
        json=sort_data,
        headers=auth_headers_admin
    )
    assert sort_response.status_code == 200
    
    # 验证排序已更新
    get_response = await async_client.get(
        f"/api/v1/option-values/options/{test_option.option_id}/values?sort=sort_order&order=asc",
        headers=auth_headers_admin
    )
    assert get_response.status_code == 200
    updated_sorted_values = get_response.json()
    assert updated_sorted_values[0]["sort_order"] == 5
    assert updated_sorted_values[1]["sort_order"] == 15
    assert updated_sorted_values[2]["sort_order"] == 25

