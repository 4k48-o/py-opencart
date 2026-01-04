"""
Unit tests for AttributeGroup API and Service
包含基础校验测试、逻辑校验测试和API具体业务测试
"""
import pytest
import uuid
from httpx import AsyncClient
from app.main import app
from app.models.catalog.attribute_group import AttributeGroup
from app.models.catalog.attribute_group_description import AttributeGroupDescription
from app.models.catalog.attribute import Attribute
from app.models.localisation.language import Language
from app.services.attribute_group_service import AttributeGroupService
from app.schemas.attribute_group import (
    AttributeGroupCreate, AttributeGroupUpdate, AttributeGroupDescriptionCreate
)
from app.exceptions import NotFoundException, ConflictException, ValidationException
# 使用pytest.mark装饰器，不需要导入markers


# ==================== 基础校验测试（数据验证） ====================

@pytest.mark.attribute_group
@pytest.mark.model
@pytest.mark.asyncio
async def test_attribute_group_model_creation(db_transaction):
    """测试属性组模型创建（基础校验）"""
    group = AttributeGroup(sort_order=10)
    await group.save()
    
    assert group.attribute_group_id is not None
    assert group.sort_order == 10


@pytest.mark.attribute_group
@pytest.mark.model
@pytest.mark.asyncio
async def test_attribute_group_description_model_creation(db_transaction):
    """测试属性组描述模型创建（基础校验）"""
    # 创建属性组
    group = await AttributeGroup.create(sort_order=5)
    
    # 创建语言
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    # 创建描述
    desc = await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id,
        name="Test Attribute Group"
    )
    
    assert desc.attribute_group_id == group.attribute_group_id
    assert desc.language_id == language.language_id
    assert desc.name == "Test Attribute Group"


@pytest.mark.attribute_group
@pytest.mark.model
@pytest.mark.asyncio
async def test_attribute_group_description_unique_constraint(db_transaction):
    """测试属性组描述唯一约束（基础校验）"""
    # 创建属性组
    group = await AttributeGroup.create(sort_order=5)
    
    # 创建语言
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    # 创建第一个描述
    desc1 = await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id,
        name="Test Group"
    )
    
    # 尝试创建重复的描述（应该失败）
    with pytest.raises(Exception):  # IntegrityError
        desc2 = await AttributeGroupDescription.create(
            attribute_group_id=group.attribute_group_id,
            language_id=language.language_id,
            name="Another Name"
        )


@pytest.mark.attribute_group
@pytest.mark.model
@pytest.mark.asyncio
async def test_attribute_group_schema_validation(db_transaction):
    """测试属性组Schema验证（基础校验）"""
    # 测试必填字段验证
    with pytest.raises(Exception):  # ValidationError
        AttributeGroupCreate(
            sort_order=0,
            descriptions=[]  # 空数组应该失败
        )
    
    # 测试描述验证
    with pytest.raises(Exception):  # ValidationError
        AttributeGroupDescriptionCreate(
            language_id=0,  # 无效的语言ID
            name=""  # 空名称应该失败
        )


# ==================== 逻辑校验测试（业务逻辑） ====================

@pytest.mark.attribute_group
@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_list_attribute_groups(db_transaction):
    """测试服务层：获取属性组列表（逻辑校验）"""
    service = AttributeGroupService()
    
    # 创建测试数据
    group1 = await AttributeGroup.create(sort_order=10)
    group2 = await AttributeGroup.create(sort_order=5)
    
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group1.attribute_group_id,
        language_id=language.language_id,
        name="Group 1"
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group2.attribute_group_id,
        language_id=language.language_id,
        name="Group 2"
    )
    
    # 测试列表获取
    result = await service.list_attribute_groups(skip=0, limit=10)
    
    assert len(result) >= 2
    assert all(isinstance(item, type(result[0])) for item in result)
    
    # 测试排序
    result_sorted = await service.list_attribute_groups(sort="sort_order", order="asc")
    if len(result_sorted) >= 2:
        assert result_sorted[0].sort_order <= result_sorted[1].sort_order


@pytest.mark.attribute_group
@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_get_attribute_group(db_transaction):
    """测试服务层：获取属性组详情（逻辑校验）"""
    service = AttributeGroupService()
    
    # 创建测试数据
    group = await AttributeGroup.create(sort_order=15)
    
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id,
        name="Test Group"
    )
    
    # 测试获取详情
    result = await service.get_attribute_group(group.attribute_group_id)
    
    assert result.attribute_group_id == group.attribute_group_id
    assert result.sort_order == 15
    assert len(result.descriptions) == 1
    assert result.descriptions[0].name == "Test Group"
    
    # 测试不存在的ID
    with pytest.raises(NotFoundException):
        await service.get_attribute_group(99999)


@pytest.mark.attribute_group
@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_create_attribute_group(db_transaction):
    """测试服务层：创建属性组（逻辑校验）"""
    service = AttributeGroupService()
    
    # 创建语言
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    # 测试创建
    data = AttributeGroupCreate(
        sort_order=20,
        descriptions=[
            AttributeGroupDescriptionCreate(
                language_id=language.language_id,
                name="New Attribute Group"
            )
        ]
    )
    
    result = await service.create_attribute_group(data)
    
    assert result.attribute_group_id is not None
    assert result.sort_order == 20
    assert len(result.descriptions) == 1
    assert result.descriptions[0].name == "New Attribute Group"
    
    # 验证数据库中的记录
    group = await AttributeGroup.get(attribute_group_id=result.attribute_group_id)
    assert group.sort_order == 20
    
    # 使用 values() 方法避免 Tortoise ORM 尝试选择不存在的 'id' 字段
    desc_data_list = await AttributeGroupDescription.filter(
        attribute_group_id=result.attribute_group_id,
        language_id=language.language_id
    ).values('attribute_group_id', 'language_id', 'name')
    assert len(desc_data_list) > 0
    desc_data = desc_data_list[0]
    assert desc_data['name'] == "New Attribute Group"
    
    # 测试验证：空描述数组（Pydantic schema 验证会在创建对象时失败）
    from pydantic import ValidationError
    with pytest.raises(ValidationError):  # Pydantic 验证错误，不是业务异常
        invalid_data = AttributeGroupCreate(
            sort_order=0,
            descriptions=[]
        )
    
    # 测试验证：重复的语言ID
    with pytest.raises(ValidationException):
        invalid_data = AttributeGroupCreate(
            sort_order=0,
            descriptions=[
                AttributeGroupDescriptionCreate(
                    language_id=language.language_id,
                    name="Name 1"
                ),
                AttributeGroupDescriptionCreate(
                    language_id=language.language_id,  # 重复
                    name="Name 2"
                )
            ]
        )
        await service.create_attribute_group(invalid_data)
    
    # 测试验证：不存在的语言ID
    with pytest.raises(ValidationException):
        invalid_data = AttributeGroupCreate(
            sort_order=0,
            descriptions=[
                AttributeGroupDescriptionCreate(
                    language_id=99999,  # 不存在的语言ID
                    name="Name"
                )
            ]
        )
        await service.create_attribute_group(invalid_data)


@pytest.mark.attribute_group
@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_update_attribute_group(db_transaction):
    """测试服务层：更新属性组（逻辑校验）"""
    service = AttributeGroupService()
    
    # 创建测试数据
    group = await AttributeGroup.create(sort_order=10)
    
    language1 = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    language2 = await Language.create(
        name="Chinese",
        code="zh",
        locale="zh-CN",
        extension="zh-cn",
        sort_order=2,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language1.language_id,
        name="Old Name"
    )
    
    # 测试更新
    data = AttributeGroupCreate(
        sort_order=25,
        descriptions=[
            AttributeGroupDescriptionCreate(
                language_id=language1.language_id,
                name="Updated Name"
            ),
            AttributeGroupDescriptionCreate(
                language_id=language2.language_id,
                name="新名称"
            )
        ]
    )
    
    result = await service.update_attribute_group(group.attribute_group_id, data)
    
    assert result.sort_order == 25
    assert len(result.descriptions) == 2
    
    # 验证旧描述被删除，新描述被创建
    # 使用 values() 方法避免 Tortoise ORM 尝试选择不存在的 'id' 字段
    old_desc_data_list = await AttributeGroupDescription.filter(
        attribute_group_id=group.attribute_group_id,
        language_id=language1.language_id
    ).values('attribute_group_id', 'language_id', 'name')
    assert len(old_desc_data_list) > 0
    old_desc_data = old_desc_data_list[0]
    assert old_desc_data['name'] == "Updated Name"  # 已更新
    
    new_desc_data_list = await AttributeGroupDescription.filter(
        attribute_group_id=group.attribute_group_id,
        language_id=language2.language_id
    ).values('attribute_group_id', 'language_id', 'name')
    assert len(new_desc_data_list) > 0
    new_desc_data = new_desc_data_list[0]
    assert new_desc_data['name'] == "新名称"


@pytest.mark.attribute_group
@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_patch_attribute_group(db_transaction):
    """测试服务层：部分更新属性组（逻辑校验）"""
    service = AttributeGroupService()
    
    # 创建测试数据
    group = await AttributeGroup.create(sort_order=10)
    
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id,
        name="Original Name"
    )
    
    # 测试只更新sort_order
    data = AttributeGroupUpdate(sort_order=30)
    result = await service.patch_attribute_group(group.attribute_group_id, data)
    
    assert result.sort_order == 30
    # 描述应该保持不变
    # 使用 values() 方法避免 Tortoise ORM 尝试选择不存在的 'id' 字段
    desc_data_list = await AttributeGroupDescription.filter(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id
    ).values('attribute_group_id', 'language_id', 'name')
    assert len(desc_data_list) > 0
    desc_data = desc_data_list[0]
    assert desc_data['name'] == "Original Name"
    
    # 测试只更新描述
    data = AttributeGroupUpdate(
        descriptions=[
            AttributeGroupDescriptionCreate(
                language_id=language.language_id,
                name="Patched Name"
            )
        ]
    )
    result = await service.patch_attribute_group(group.attribute_group_id, data)
    
    # 使用 values() 方法避免 Tortoise ORM 尝试选择不存在的 'id' 字段
    desc_data_list = await AttributeGroupDescription.filter(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id
    ).values('attribute_group_id', 'language_id', 'name')
    assert len(desc_data_list) > 0
    desc_data = desc_data_list[0]
    assert desc_data['name'] == "Patched Name"


@pytest.mark.attribute_group
@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_delete_attribute_group(db_transaction):
    """测试服务层：删除属性组（逻辑校验）"""
    service = AttributeGroupService()
    
    # 创建测试数据
    group = await AttributeGroup.create(sort_order=10)
    
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id,
        name="Test Group"
    )
    
    # 测试删除（无属性）
    await service.delete_attribute_group(group.attribute_group_id)
    
    # 验证已删除
    deleted_group = await AttributeGroup.get_or_none(attribute_group_id=group.attribute_group_id)
    assert deleted_group is None
    
    # 验证描述也被删除
    # 使用 values() 方法避免 Tortoise ORM 尝试选择不存在的 'id' 字段
    deleted_desc_data_list = await AttributeGroupDescription.filter(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id
    ).values('attribute_group_id', 'language_id', 'name')
    assert len(deleted_desc_data_list) == 0
    
    # 测试删除不存在的属性组
    with pytest.raises(NotFoundException):
        await service.delete_attribute_group(99999)
    
    # 测试删除有属性的属性组（应该失败）
    group2 = await AttributeGroup.create(sort_order=20)
    await AttributeGroupDescription.create(
        attribute_group_id=group2.attribute_group_id,
        language_id=language.language_id,
        name="Group with Attributes"
    )
    
    # 创建属性
    attribute = await Attribute.create(
        attribute_group_id=group2.attribute_group_id,
        sort_order=0
    )
    
    with pytest.raises(ConflictException):
        await service.delete_attribute_group(group2.attribute_group_id)


# ==================== API具体业务测试（接口测试） ====================

@pytest.mark.attribute_group
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_list_attribute_groups_without_auth(async_client):
    """测试GET /api/v1/attribute-groups/ 无认证（API业务测试）"""
    response = await async_client.get("/api/v1/attribute-groups/")
    assert response.status_code == 401  # Unauthorized without auth (FastAPI认证流程：先检查认证401，再检查权限403)


@pytest.mark.attribute_group
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_list_attribute_groups(db_transaction, auth_headers, async_client):
    """测试GET /api/v1/attribute-groups/ 获取属性组列表（API业务测试）"""
    headers = auth_headers
    
    # 创建测试数据
    group1 = await AttributeGroup.create(sort_order=10)
    group2 = await AttributeGroup.create(sort_order=5)
    
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group1.attribute_group_id,
        language_id=language.language_id,
        name="Group 1"
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group2.attribute_group_id,
        language_id=language.language_id,
        name="Group 2"
    )
    
    # 测试列表获取
    response = await async_client.get("/api/v1/attribute-groups/", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    
    # 测试分页
    response = await async_client.get(
        "/api/v1/attribute-groups/?skip=0&limit=1",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1
    
    # 测试排序
    response = await async_client.get(
        "/api/v1/attribute-groups/?sort=sort_order&order=asc",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    if len(data) >= 2:
        assert data[0]["sort_order"] <= data[1]["sort_order"]
    
    # 测试名称筛选
    response = await async_client.get(
        "/api/v1/attribute-groups/?filter[name]=Group 1",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    # 筛选结果应该包含"Group 1"
    if len(data) > 0:
        names = [desc["name"] for item in data for desc in item.get("descriptions", [])]
        assert any("Group 1" in name for name in names)


@pytest.mark.attribute_group
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_get_attribute_group(db_transaction, auth_headers, async_client):
    """测试GET /api/v1/attribute-groups/{id} 获取属性组详情（API业务测试）"""
    headers = auth_headers
    
    # 创建测试数据
    group = await AttributeGroup.create(sort_order=15)
    
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id,
        name="Test Attribute Group"
    )
    
    # 测试获取详情
    response = await async_client.get(
        f"/api/v1/attribute-groups/{group.attribute_group_id}",
        headers=headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["attribute_group_id"] == group.attribute_group_id
    assert data["sort_order"] == 15
    assert len(data["descriptions"]) == 1
    assert data["descriptions"][0]["name"] == "Test Attribute Group"
    
    # 测试不存在的ID
    response = await async_client.get("/api/v1/attribute-groups/99999", headers=headers)
    assert response.status_code == 404
    
    # 测试带language_id参数
    response = await async_client.get(
        f"/api/v1/attribute-groups/{group.attribute_group_id}?language_id={language.language_id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Attribute Group"  # 应该返回当前语言的名称


@pytest.mark.attribute_group
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_create_attribute_group(db_transaction, auth_headers, async_client):
    """测试POST /api/v1/attribute-groups/ 创建属性组（API业务测试）"""
    headers = auth_headers
    
    # 创建语言
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    # 测试创建
    unique_name = f"New Group {uuid.uuid4().hex[:8]}"
    data = {
        "sort_order": 20,
        "descriptions": [
            {
                "language_id": language.language_id,
                "name": unique_name
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/attribute-groups/",
        json=data,
        headers=headers
    )
    assert response.status_code == 201
    
    result = response.json()
    assert result["attribute_group_id"] is not None
    assert result["sort_order"] == 20
    assert len(result["descriptions"]) == 1
    assert result["descriptions"][0]["name"] == unique_name
    
    # 测试验证：空描述数组
    invalid_data = {
        "sort_order": 0,
        "descriptions": []
    }
    response = await async_client.post(
        "/api/v1/attribute-groups/",
        json=invalid_data,
        headers=headers
    )
    assert response.status_code == 422  # Pydantic schema 验证失败（min_length=1）
    
    # 测试验证：不存在的语言ID
    invalid_data = {
        "sort_order": 0,
        "descriptions": [
            {
                "language_id": 99999,
                "name": "Test"
            }
        ]
    }
    response = await async_client.post(
        "/api/v1/attribute-groups/",
        json=invalid_data,
        headers=headers
    )
    assert response.status_code == 400


@pytest.mark.attribute_group
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.high
@pytest.mark.asyncio
async def test_update_attribute_group(db_transaction, auth_headers, async_client):
    """测试PUT /api/v1/attribute-groups/{id} 更新属性组（API业务测试）"""
    headers = auth_headers
    
    # 创建测试数据
    group = await AttributeGroup.create(sort_order=10)
    
    language1 = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    language2 = await Language.create(
        name="Chinese",
        code="zh",
        locale="zh-CN",
        extension="zh-cn",
        sort_order=2,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language1.language_id,
        name="Original Name"
    )
    
    # 测试更新
    unique_name = f"Updated Group {uuid.uuid4().hex[:8]}"
    data = {
        "sort_order": 25,
        "descriptions": [
            {
                "language_id": language1.language_id,
                "name": unique_name
            },
            {
                "language_id": language2.language_id,
                "name": "更新的名称"
            }
        ]
    }
    
    response = await async_client.put(
        f"/api/v1/attribute-groups/{group.attribute_group_id}",
        json=data,
        headers=headers
    )
    assert response.status_code == 200
    
    result = response.json()
    assert result["sort_order"] == 25
    assert len(result["descriptions"]) == 2
    
    # 测试不存在的ID
    response = await async_client.put(
        "/api/v1/attribute-groups/99999",
        json=data,
        headers=headers
    )
    assert response.status_code == 404


@pytest.mark.attribute_group
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.high
@pytest.mark.asyncio
async def test_patch_attribute_group(db_transaction, auth_headers, async_client):
    """测试PATCH /api/v1/attribute-groups/{id} 部分更新属性组（API业务测试）"""
    headers = auth_headers
    
    # 创建测试数据
    group = await AttributeGroup.create(sort_order=10)
    
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id,
        name="Original Name"
    )
    
    # 测试只更新sort_order
    data = {"sort_order": 30}
    response = await async_client.patch(
        f"/api/v1/attribute-groups/{group.attribute_group_id}",
        json=data,
        headers=headers
    )
    assert response.status_code == 200
    
    result = response.json()
    assert result["sort_order"] == 30
    
    # 验证描述保持不变
    # 使用 values() 方法避免 Tortoise ORM 尝试选择不存在的 'id' 字段
    desc_data_list = await AttributeGroupDescription.filter(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id
    ).values('attribute_group_id', 'language_id', 'name')
    assert len(desc_data_list) > 0
    desc_data = desc_data_list[0]
    assert desc_data['name'] == "Original Name"
    
    # 测试只更新描述
    unique_name = f"Patched Name {uuid.uuid4().hex[:8]}"
    data = {
        "descriptions": [
            {
                "language_id": language.language_id,
                "name": unique_name
            }
        ]
    }
    response = await async_client.patch(
        f"/api/v1/attribute-groups/{group.attribute_group_id}",
        json=data,
        headers=headers
    )
    assert response.status_code == 200
    
    # 验证描述已更新
    # 使用 values() 方法避免 Tortoise ORM 尝试选择不存在的 'id' 字段
    desc_data_list = await AttributeGroupDescription.filter(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id
    ).values('attribute_group_id', 'language_id', 'name')
    assert len(desc_data_list) > 0
    desc_data = desc_data_list[0]
    assert desc_data['name'] == unique_name


@pytest.mark.attribute_group
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_delete_attribute_group(db_transaction, auth_headers, async_client):
    """测试DELETE /api/v1/attribute-groups/{id} 删除属性组（API业务测试）"""
    headers = auth_headers
    
    # 创建测试数据
    group = await AttributeGroup.create(sort_order=10)
    
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id,
        name="Test Group"
    )
    
    # 测试删除（无属性）
    response = await async_client.delete(
        f"/api/v1/attribute-groups/{group.attribute_group_id}",
        headers=headers
    )
    assert response.status_code == 204
    
    # 验证已删除
    response = await async_client.get(
        f"/api/v1/attribute-groups/{group.attribute_group_id}",
        headers=headers
    )
    assert response.status_code == 404
    
    # 测试删除不存在的属性组
    response = await async_client.delete("/api/v1/attribute-groups/99999", headers=headers)
    assert response.status_code == 404
    
    # 测试删除有属性的属性组（应该失败）
    group2 = await AttributeGroup.create(sort_order=20)
    await AttributeGroupDescription.create(
        attribute_group_id=group2.attribute_group_id,
        language_id=language.language_id,
        name="Group with Attributes"
    )
    
    # 创建属性
    await Attribute.create(
        attribute_group_id=group2.attribute_group_id,
        sort_order=0
    )
    
    response = await async_client.delete(
        f"/api/v1/attribute-groups/{group2.attribute_group_id}",
        headers=headers
    )
    assert response.status_code == 409  # Conflict
    
    error_data = response.json()
    assert "CONFLICT" in str(error_data.get("detail", {})).upper() or "属性" in str(error_data.get("detail", ""))


@pytest.mark.attribute_group
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.medium
@pytest.mark.asyncio
async def test_attribute_group_multilingual(db_transaction, auth_headers, async_client):
    """测试属性组多语言支持（API业务测试）"""
    headers = auth_headers
    
    # 创建多个语言
    language_en = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    language_zh = await Language.create(
        name="Chinese",
        code="zh",
        locale="zh-CN",
        extension="zh-cn",
        sort_order=2,
        status=1
    )
    
    # 创建多语言属性组
    data = {
        "sort_order": 5,
        "descriptions": [
            {
                "language_id": language_en.language_id,
                "name": "Color"
            },
            {
                "language_id": language_zh.language_id,
                "name": "颜色"
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/attribute-groups/",
        json=data,
        headers=headers
    )
    assert response.status_code == 201
    
    result = response.json()
    assert len(result["descriptions"]) == 2
    
    # 验证两种语言的名称都存在
    names = [desc["name"] for desc in result["descriptions"]]
    assert "Color" in names
    assert "颜色" in names
    
    # 测试按语言ID获取
    response = await async_client.get(
        f"/api/v1/attribute-groups/{result['attribute_group_id']}?language_id={language_en.language_id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Color"
    
    response = await async_client.get(
        f"/api/v1/attribute-groups/{result['attribute_group_id']}?language_id={language_zh.language_id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "颜色"


@pytest.mark.attribute_group
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.medium
@pytest.mark.asyncio
async def test_attribute_group_attribute_count(db_transaction, auth_headers, async_client):
    """测试属性组属性数量统计（API业务测试）"""
    headers = auth_headers
    
    # 创建属性组
    group = await AttributeGroup.create(sort_order=10)
    
    language = await Language.create(
        name="English",
        code="en",
        locale="en-GB",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    
    await AttributeGroupDescription.create(
        attribute_group_id=group.attribute_group_id,
        language_id=language.language_id,
        name="Test Group"
    )
    
    # 创建3个属性
    for i in range(3):
        await Attribute.create(
            attribute_group_id=group.attribute_group_id,
            sort_order=i
        )
    
    # 获取属性组详情
    response = await async_client.get(
        f"/api/v1/attribute-groups/{group.attribute_group_id}",
        headers=headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["attribute_count"] == 3

