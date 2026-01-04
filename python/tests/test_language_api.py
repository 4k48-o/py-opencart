"""
Unit tests for Language API
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.localisation.language import Language




@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_list_languages_without_auth(async_client):
    """Test GET /api/v1/languages/ without authentication"""
    response = await async_client.get("/api/v1/languages/")
    assert response.status_code == 401  # Unauthorized without auth (FastAPI认证流程：先检查认证401，再检查权限403)


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_list_languages(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/languages/ endpoint"""
    headers = auth_headers
    # Create test languages
    lang1 = Language(
        name="English",
        code="en",
        locale="en-US",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    await lang1.save()
    
    lang2 = Language(
        name="中文",
        code="zh-CN",
        locale="zh-CN",
        extension="zh-cn",
        sort_order=2,
        status=1
    )
    await lang2.save()
    
    response = await async_client.get("/api/v1/languages/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_list_languages_with_status_filter(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/languages/ with status filter"""
    headers = auth_headers
    # Create test languages
    lang1 = Language(name="English", code="en", status=1, sort_order=1)
    await lang1.save()
    
    lang2 = Language(name="Disabled", code="dis", status=0, sort_order=2)
    await lang2.save()
    
    # Filter by status=1
    response = await async_client.get("/api/v1/languages/?status=1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == 1 for item in data)


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_get_language_by_id(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/languages/{language_id} endpoint"""
    headers = auth_headers
    # Create test language
    lang = Language(
        name="English",
        code="en",
        locale="en-US",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    await lang.save()
    
    response = await async_client.get(f"/api/v1/languages/{lang.language_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["language_id"] == lang.language_id
    assert data["name"] == "English"
    assert data["code"] == "en"


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_language_by_id_not_found(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/languages/{language_id} with non-existent ID"""
    headers = auth_headers
    response = await async_client.get("/api/v1/languages/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_language_by_code(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/languages/by-code/{code} endpoint"""
    headers = auth_headers
    # Create test language
    lang = Language(
        name="English",
        code="en",
        locale="en-US",
        extension="en-gb",
        sort_order=1,
        status=1
    )
    await lang.save()
    
    response = await async_client.get("/api/v1/languages/by-code/en", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "en"
    assert data["name"] == "English"


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_language_by_code_not_found(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/languages/by-code/{code} with non-existent code"""
    headers = auth_headers
    # 使用符合规范的语言代码（2-5字符）来测试404场景
    response = await async_client.get("/api/v1/languages/by-code/xx", headers=headers)
    assert response.status_code == 404


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_language_by_code_invalid_format(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/languages/by-code/{code} with invalid code format"""
    headers = auth_headers
    # 测试不符合规范的语言代码（长度超过5）
    response = await async_client.get("/api/v1/languages/by-code/nonexistent", headers=headers)
    # 应该返回422（参数验证失败），而不是500（服务器错误）
    assert response.status_code == 422


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_create_language(db_transaction, auth_headers, async_client):
    """Test POST /api/v1/languages/ endpoint"""
    headers = auth_headers
    import uuid
    # 生成符合规范的语言代码（2-5字符）
    # 使用fr前缀（2字符）加上随机字符确保唯一性，总长度不超过5字符
    unique_suffix = uuid.uuid4().hex[:3]  # 3个字符
    unique_code = f"fr{unique_suffix}"  # 总共5个字符，符合规范
    data = {
        "name": "French",
        "code": unique_code,
        "locale": "fr-FR",
        "extension": "fr-fr",
        "sort_order": 3,
        "status": 1
    }
    
    response = await async_client.post("/api/v1/languages/", json=data, headers=headers)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "French"
    assert result["code"] == unique_code
    assert "language_id" in result


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_language_duplicate_code(db_transaction, auth_headers, async_client):
    """Test POST /api/v1/languages/ with duplicate code"""
    headers = auth_headers
    # Create first language
    lang = Language(name="English", code="en", status=1, sort_order=1)
    await lang.save()
    
    # Try to create duplicate
    data = {
        "name": "English 2",
        "code": "en",
        "status": 1,
        "sort_order": 2
    }
    
    response = await async_client.post("/api/v1/languages/", json=data, headers=headers)
    assert response.status_code == 400


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_update_language(db_transaction, auth_headers, async_client):
    """Test PUT /api/v1/languages/{language_id} endpoint"""
    headers = auth_headers
    # Create test language
    lang = Language(
        name="English",
        code="en",
        status=1,
        sort_order=1
    )
    await lang.save()
    
    # Update language
    data = {
        "name": "English Updated",
        "status": 0
    }
    
    response = await async_client.put(f"/api/v1/languages/{lang.language_id}", json=data, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "English Updated"
    assert result["status"] == 0
    
    # Verify in database
    updated_lang = await Language.get(language_id=lang.language_id)
    assert updated_lang.name == "English Updated"
    assert updated_lang.status == 0


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_delete_language(db_transaction, auth_headers, async_client):
    """Test DELETE /api/v1/languages/{language_id} endpoint"""
    headers = auth_headers
    # Create test language
    lang = Language(
        name="Test Language",
        code="test",
        status=1,
        sort_order=1
    )
    await lang.save()
    language_id = lang.language_id
    
    # Delete language
    response = await async_client.delete(f"/api/v1/languages/{language_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify deleted
    deleted_lang = await Language.get_or_none(language_id=language_id)
    assert deleted_lang is None


@pytest.mark.language
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_delete_language_not_found(db_transaction, auth_headers, async_client):
    """Test DELETE /api/v1/languages/{language_id} with non-existent ID"""
    headers = auth_headers
    response = await async_client.delete("/api/v1/languages/99999", headers=headers)
    assert response.status_code == 404

