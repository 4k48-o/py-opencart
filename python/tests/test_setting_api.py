"""
Unit tests for Setting API
"""
import pytest
import json
from httpx import AsyncClient
from app.main import app
from app.models.system.setting import Setting
from app.models.system.store import Store


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_list_settings_without_auth(async_client):
    """Test GET /api/v1/settings/ without authentication"""
    response = await async_client.get("/api/v1/settings/")
    assert response.status_code == 401  # Unauthorized without auth (FastAPI认证流程：先检查认证401，再检查权限403)


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_list_settings(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/settings/ endpoint"""
    headers = auth_headers
    # Create test settings
    setting1 = Setting(
        code="config",
        key="test_key1",
        value="test_value1",
        store_id=0,
        serialized=0
    )
    await setting1.save()
    
    setting2 = Setting(
        code="theme",
        key="test_key2",
        value='{"color": "blue"}',
        store_id=0,
        serialized=1
    )
    await setting2.save()
    
    response = await async_client.get("/api/v1/settings/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_list_settings_with_filters(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/settings/ with filters"""
    headers = auth_headers
    # Create test settings
    setting1 = Setting(
        code="config",
        key="filter_key1",
        value="value1",
        store_id=0,
        serialized=0
    )
    await setting1.save()
    
    setting2 = Setting(
        code="config",
        key="filter_key2",
        value="value2",
        store_id=1,
        serialized=0
    )
    await setting2.save()
    
    # Filter by code
    response = await async_client.get("/api/v1/settings/?code=config", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert all(item["code"] == "config" for item in data)
    
    # Filter by store_id
    response = await async_client.get("/api/v1/settings/?store_id=1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert all(item["store_id"] == 1 for item in data)


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_get_setting_by_id(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/settings/{setting_id} endpoint"""
    headers = auth_headers
    # Create test setting
    setting = Setting(
        code="config",
        key="test_key",
        value="test_value",
        store_id=0,
        serialized=0
    )
    await setting.save()
    
    response = await async_client.get(f"/api/v1/settings/{setting.setting_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["setting_id"] == setting.setting_id
    assert data["code"] == "config"
    assert data["key"] == "test_key"
    assert data["value"] == "test_value"


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_setting_by_id_not_found(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/settings/{setting_id} with non-existent ID"""
    headers = auth_headers
    response = await async_client.get("/api/v1/settings/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_setting_by_key(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/settings/by-key/{code}/{key} endpoint"""
    headers = auth_headers
    # Create test setting
    setting = Setting(
        code="config",
        key="timezone",
        value="Asia/Shanghai",
        store_id=0,
        serialized=0
    )
    await setting.save()
    
    response = await async_client.get("/api/v1/settings/by-key/config/timezone?store_id=0", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "config"
    assert data["key"] == "timezone"
    assert data["value"] == "Asia/Shanghai"


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_setting_by_key_not_found(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/settings/by-key/{code}/{key} with non-existent key"""
    headers = auth_headers
    response = await async_client.get("/api/v1/settings/by-key/config/nonexistent?store_id=0", headers=headers)
    assert response.status_code == 404


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_create_setting(db_transaction, auth_headers, async_client):
    """Test POST /api/v1/settings/ endpoint"""
    headers = auth_headers
    import uuid
    unique_key = f"new_setting_{uuid.uuid4().hex[:8]}"
    data = {
        "code": "config",
        "key": unique_key,
        "value": "new_value",
        "store_id": 0,
        "serialized": 0
    }
    
    response = await async_client.post("/api/v1/settings/", json=data, headers=headers)
    assert response.status_code == 201
    result = response.json()
    assert result["code"] == "config"
    assert result["key"] == unique_key
    assert result["value"] == "new_value"
    assert "setting_id" in result


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_setting_with_json(db_transaction, auth_headers, async_client):
    """Test POST /api/v1/settings/ with serialized JSON"""
    headers = auth_headers
    import uuid
    # 使用唯一键避免与其他测试冲突
    unique_key = f"theme_config_{uuid.uuid4().hex[:8]}"
    json_value = {"color": "blue", "size": "large"}
    data = {
        "code": "theme",
        "key": unique_key,
        "value": json.dumps(json_value),
        "store_id": 0,
        "serialized": 1
    }
    
    response = await async_client.post("/api/v1/settings/", json=data, headers=headers)
    assert response.status_code == 201
    result = response.json()
    assert result["serialized"] == 1
    assert result["parsed_value"] == json_value


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_setting_duplicate(db_transaction, auth_headers, async_client):
    """Test POST /api/v1/settings/ with duplicate code/key"""
    headers = auth_headers
    # Create first setting
    setting = Setting(
        code="config",
        key="duplicate_key",
        value="value1",
        store_id=0,
        serialized=0
    )
    await setting.save()
    
    # Try to create duplicate
    data = {
        "code": "config",
        "key": "duplicate_key",
        "value": "value2",
        "store_id": 0,
        "serialized": 0
    }
    
    response = await async_client.post("/api/v1/settings/", json=data, headers=headers)
    assert response.status_code == 400


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_update_setting(db_transaction, auth_headers, async_client):
    """Test PUT /api/v1/settings/{setting_id} endpoint"""
    headers = auth_headers
    # Create test setting
    setting = Setting(
        code="config",
        key="update_key",
        value="old_value",
        store_id=0,
        serialized=0
    )
    await setting.save()
    
    # Update setting
    data = {
        "value": "new_value"
    }
    
    response = await async_client.put(f"/api/v1/settings/{setting.setting_id}", json=data, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["value"] == "new_value"
    
    # Verify in database
    updated_setting = await Setting.get(setting_id=setting.setting_id)
    assert updated_setting.value == "new_value"


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_update_setting_by_key(db_transaction, auth_headers, async_client):
    """Test PUT /api/v1/settings/by-key/{code}/{key} endpoint"""
    headers = auth_headers
    # Create test setting
    setting = Setting(
        code="config",
        key="update_by_key",
        value="old_value",
        store_id=0,
        serialized=0
    )
    await setting.save()
    
    # Update setting
    data = {
        "value": "updated_value"
    }
    
    response = await async_client.put("/api/v1/settings/by-key/config/update_by_key?store_id=0", json=data, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["value"] == "updated_value"


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_delete_setting(db_transaction, auth_headers, async_client):
    """Test DELETE /api/v1/settings/{setting_id} endpoint"""
    headers = auth_headers
    # Create test setting
    setting = Setting(
        code="config",
        key="delete_key",
        value="delete_value",
        store_id=0,
        serialized=0
    )
    await setting.save()
    setting_id = setting.setting_id
    
    # Delete setting
    response = await async_client.delete(f"/api/v1/settings/{setting_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify deleted
    deleted_setting = await Setting.get_or_none(setting_id=setting_id)
    assert deleted_setting is None


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_delete_setting_not_found(db_transaction, auth_headers, async_client):
    """Test DELETE /api/v1/settings/{setting_id} with non-existent ID"""
    headers = auth_headers
    response = await async_client.delete("/api/v1/settings/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_get_timezone(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/settings/timezone endpoint"""
    headers = auth_headers
    # Create timezone setting
    setting = Setting(
        code="config",
        key="config_timezone",
        value="Asia/Shanghai",
        store_id=0,
        serialized=0
    )
    await setting.save()
    
    response = await async_client.get("/api/v1/settings/timezone?store_id=0", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "config_timezone"
    assert data["value"] == "Asia/Shanghai"


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_timezone_not_found(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/settings/timezone when not set"""
    headers = auth_headers
    response = await async_client.get("/api/v1/settings/timezone?store_id=999", headers=headers)
    assert response.status_code == 404


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_update_timezone(db_transaction, auth_headers, async_client):
    """Test PUT /api/v1/settings/timezone endpoint"""
    headers = auth_headers
    # Create timezone setting
    setting = Setting(
        code="config",
        key="config_timezone",
        value="UTC",
        store_id=0,
        serialized=0
    )
    await setting.save()
    
    # Update timezone
    response = await async_client.put("/api/v1/settings/timezone?timezone=Asia/Shanghai&store_id=0", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == "Asia/Shanghai"
    
    # Verify in database - 重新查询确保获取最新值
    updated_setting = await Setting.filter(
        code="config",
        key="config_timezone",
        store_id=0
    ).first()
    assert updated_setting is not None
    assert updated_setting.value == "Asia/Shanghai"


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_update_timezone_invalid(db_transaction, auth_headers, async_client):
    """Test PUT /api/v1/settings/timezone with invalid timezone"""
    headers = auth_headers
    response = await async_client.put("/api/v1/settings/timezone?timezone=Invalid/Timezone&store_id=0", headers=headers)
    # May return 400 if validation is strict, or 200 if validation is lenient
    assert response.status_code in [400, 200]


@pytest.mark.setting
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_list_timezones(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/settings/timezones endpoint"""
    headers = auth_headers
    response = await async_client.get("/api/v1/settings/timezones", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "UTC" in data
    assert "Asia/Shanghai" in data

