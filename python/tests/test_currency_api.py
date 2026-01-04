"""
Unit tests for Currency API
"""
import pytest
from datetime import datetime
from httpx import AsyncClient
from app.main import app
from app.models.localisation.currency import Currency




@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_list_currencies_without_auth(async_client):
    """Test GET /api/v1/currencies/ without authentication"""
    response = await async_client.get("/api/v1/currencies/")
    assert response.status_code == 401  # Unauthorized without auth (FastAPI认证流程：先检查认证401，再检查权限403)


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_list_currencies(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/currencies/ endpoint"""
    headers = auth_headers
    # Create test currencies
    curr1 = Currency(
        title="US Dollar",
        code="USD",
        symbol_left="$",
        symbol_right="",
        decimal_place=2,
        value=1.0,
        status=1
    )
    await curr1.save()
    
    curr2 = Currency(
        title="Chinese Yuan",
        code="CNY",
        symbol_left="¥",
        symbol_right="",
        decimal_place=2,
        value=7.2,
        status=1
    )
    await curr2.save()
    
    response = await async_client.get("/api/v1/currencies/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_list_currencies_with_status_filter(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/currencies/ with status filter"""
    headers = auth_headers
    # Create test currencies
    curr1 = Currency(title="USD", code="USD", value=1.0, status=1)
    await curr1.save()
    
    curr2 = Currency(title="Disabled", code="DIS", value=1.0, status=0)
    await curr2.save()
    
    # Filter by status=1
    response = await async_client.get("/api/v1/currencies/?status=1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == 1 for item in data)


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_get_currency_by_id(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/currencies/{currency_id} endpoint"""
    headers = auth_headers
    # Create test currency
    curr = Currency(
        title="US Dollar",
        code="USD",
        symbol_left="$",
        symbol_right="",
        decimal_place=2,
        value=1.0,
        status=1
    )
    await curr.save()
    
    response = await async_client.get(f"/api/v1/currencies/{curr.currency_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["currency_id"] == curr.currency_id
    assert data["title"] == "US Dollar"
    assert data["code"] == "USD"
    assert data["value"] == 1.0


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_currency_by_id_not_found(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/currencies/{currency_id} with non-existent ID"""
    headers = auth_headers
    response = await async_client.get("/api/v1/currencies/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_currency_by_code(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/currencies/by-code/{code} endpoint"""
    headers = auth_headers
    # Create test currency
    curr = Currency(
        title="US Dollar",
        code="USD",
        value=1.0,
        status=1
    )
    await curr.save()
    
    response = await async_client.get("/api/v1/currencies/by-code/USD", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "USD"
    assert data["title"] == "US Dollar"


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_currency_by_code_not_found(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/currencies/by-code/{code} with non-existent code"""
    headers = auth_headers
    response = await async_client.get("/api/v1/currencies/by-code/XXX", headers=headers)
    assert response.status_code == 404


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_create_currency(db_transaction, auth_headers, async_client):
    """Test POST /api/v1/currencies/ endpoint"""
    headers = auth_headers
    import random
    import string
    # 生成符合ISO 4217标准的3字符唯一代码
    # 使用随机3个大写字母确保唯一性
    unique_code = ''.join(random.choices(string.ascii_uppercase, k=3))
    data = {
        "title": "Euro",
        "code": unique_code,
        "symbol_left": "€",
        "symbol_right": "",
        "decimal_place": 2,
        "value": 0.85,
        "status": 1
    }
    
    response = await async_client.post("/api/v1/currencies/", json=data, headers=headers)
    assert response.status_code == 201
    result = response.json()
    assert result["title"] == "Euro"
    assert result["code"] == unique_code
    assert result["value"] == 0.85
    assert "currency_id" in result


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_currency_duplicate_code(db_transaction, auth_headers, async_client):
    """Test POST /api/v1/currencies/ with duplicate code"""
    headers = auth_headers
    # Create first currency
    curr = Currency(title="USD", code="USD", value=1.0, status=1)
    await curr.save()
    
    # Try to create duplicate
    data = {
        "title": "US Dollar 2",
        "code": "USD",
        "value": 1.0,
        "status": 1
    }
    
    response = await async_client.post("/api/v1/currencies/", json=data, headers=headers)
    assert response.status_code == 400


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_update_currency(db_transaction, auth_headers, async_client):
    """Test PUT /api/v1/currencies/{currency_id} endpoint"""
    headers = auth_headers
    # Create test currency
    curr = Currency(
        title="US Dollar",
        code="USD",
        value=1.0,
        status=1
    )
    await curr.save()
    
    # Update currency
    data = {
        "title": "US Dollar Updated",
        "value": 1.1
    }
    
    response = await async_client.put(f"/api/v1/currencies/{curr.currency_id}", json=data, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["title"] == "US Dollar Updated"
    assert result["value"] == 1.1
    assert "date_modified" in result
    
    # Verify in database
    updated_curr = await Currency.get(currency_id=curr.currency_id)
    assert updated_curr.title == "US Dollar Updated"
    assert updated_curr.value == 1.1
    assert updated_curr.date_modified is not None


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_update_currency_rate(db_transaction, auth_headers, async_client):
    """Test PUT /api/v1/currencies/{currency_id}/rate endpoint"""
    headers = auth_headers
    # Create test currency
    curr = Currency(
        title="US Dollar",
        code="USD",
        value=1.0,
        status=1
    )
    await curr.save()
    
    # Update rate
    response = await async_client.put(f"/api/v1/currencies/{curr.currency_id}/rate?value=1.05", headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["value"] == 1.05
    
    # Verify in database
    updated_curr = await Currency.get(currency_id=curr.currency_id)
    assert updated_curr.value == 1.05
    assert updated_curr.date_modified is not None


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_delete_currency(db_transaction, auth_headers, async_client):
    """Test DELETE /api/v1/currencies/{currency_id} endpoint"""
    headers = auth_headers
    # Create test currency
    curr = Currency(
        title="Test Currency",
        code="TST",
        value=1.0,
        status=1
    )
    await curr.save()
    currency_id = curr.currency_id
    
    # Delete currency
    response = await async_client.delete(f"/api/v1/currencies/{currency_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify deleted
    deleted_curr = await Currency.get_or_none(currency_id=currency_id)
    assert deleted_curr is None


@pytest.mark.currency
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_delete_currency_not_found(db_transaction, auth_headers, async_client):
    """Test DELETE /api/v1/currencies/{currency_id} with non-existent ID"""
    headers = auth_headers
    response = await async_client.delete("/api/v1/currencies/99999", headers=headers)
    assert response.status_code == 404

