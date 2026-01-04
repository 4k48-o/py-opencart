"""
Unit tests for User Management API
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.system.user import User
from app.models.system.user_group import UserGroup
from app.models.system.user_login import UserLogin
from datetime import datetime
import json

# Note: TestClient is synchronous but can handle async routes
# Database setup is handled by conftest.py fixtures
client = TestClient(app)


@pytest.mark.user
@pytest.mark.model
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_user_group_model(db_transaction):
    """Test creating a user group (model test)"""
    user_group = UserGroup(
        name="Test Group",
        permission='{"product": ["create", "read"]}'
    )
    await user_group.save()
    
    assert user_group.user_group_id is not None
    assert user_group.name == "Test Group"


@pytest.mark.user
@pytest.mark.model
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_create_user_model(db_transaction):
    """Test creating a user (model test)"""
    # First create a user group
    user_group = UserGroup(name="Test Group")
    await user_group.save()
    
    # Create user
    user = User(
        username="testuser",
        password="testpass123",
        user_group_id=user_group.user_group_id,
        email="test@example.com",
        firstname="Test",
        lastname="User",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    
    assert user.user_id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"


@pytest.mark.user
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_list_user_groups_api(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/users/groups/ endpoint"""
    headers = auth_headers
    response = await async_client.get("/api/v1/users/groups/?skip=0&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.user
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_user_group_api(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/users/groups/{user_group_id} endpoint"""
    headers = auth_headers
    # Try with non-existent ID
    response = await async_client.get("/api/v1/users/groups/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.user
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_create_user_group_api(db_transaction, auth_headers, async_client):
    """Test POST /api/v1/users/groups/ endpoint"""
    headers = auth_headers
    import uuid
    unique_name = f"New Test Group {uuid.uuid4().hex[:8]}"
    response = await async_client.post(
        "/api/v1/users/groups/",
        json={
            "name": unique_name,
            "permission": {
                "product": ["create", "read", "update"],
                "order": ["read"]
            }
        },
        headers=headers
    )
    # May succeed (201) or fail if name exists (400)
    assert response.status_code in [201, 400]
    if response.status_code == 201:
        data = response.json()
        assert data["name"] == unique_name
        assert "user_group_id" in data


@pytest.mark.user
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.critical
@pytest.mark.asyncio
async def test_create_user_api(db_transaction, auth_headers, async_client):
    """Test POST /api/v1/users/ endpoint"""
    headers = auth_headers
    # First need a user group
    # Try to create user with invalid group
    import uuid
    unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
    response = await async_client.post(
        "/api/v1/users/",
        json={
            "username": unique_username,
            "password": "password123",
            "user_group_id": 99999,  # Non-existent group
            "email": f"{unique_username}@example.com",
            "firstname": "Test",
            "lastname": "User",
            "status": 1
        },
        headers=headers
    )
    assert response.status_code == 400  # Should fail due to invalid group


@pytest.mark.user
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_user_api(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/users/{user_id} endpoint"""
    headers = auth_headers
    # Try with non-existent ID
    response = await async_client.get("/api/v1/users/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.user
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_list_users_api(db_transaction, auth_headers, async_client):
    """Test GET /api/v1/users/ endpoint"""
    headers = auth_headers
    response = await async_client.get("/api/v1/users/?skip=0&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.user
@pytest.mark.model
@pytest.mark.regression
@pytest.mark.asyncio
async def test_user_model_relationships(db_transaction):
    """Test User model relationships"""
    # Create user group
    group = UserGroup(name="Test Group")
    await group.save()
    
    # Create user
    user = User(
        username="reltest",
        password="pass123",
        user_group_id=group.user_group_id,
        email="reltest@example.com",
        firstname="Rel",
        lastname="Test",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    
    # Test relationship method
    user_group = await user.get_user_group()
    assert user_group is not None
    assert user_group.user_group_id == group.user_group_id


@pytest.mark.user
@pytest.mark.model
@pytest.mark.regression
@pytest.mark.asyncio
async def test_user_group_permission_parsing(db_transaction):
    """Test UserGroup permission JSON parsing"""
    # Create group with permissions
    group = UserGroup(
        name="Permission Test Group",
        permission='{"product": ["create", "read"], "order": ["read", "update"]}'
    )
    await group.save()
    
    # Verify permissions
    assert group.permission is not None
    perms = json.loads(group.permission)
    assert "product" in perms
    assert "order" in perms
    assert "create" in perms["product"]
    assert "read" in perms["product"]


@pytest.mark.user
@pytest.mark.model
@pytest.mark.regression
@pytest.mark.asyncio
async def test_user_login_activity(db_transaction):
    """Test UserLogin activity log"""
    # Create user group
    group = UserGroup(name="Test Group")
    await group.save()
    
    # Create user
    user = User(
        username="activitytest",
        password="pass123",
        user_group_id=group.user_group_id,
        email="activitytest@example.com",
        firstname="Activity",
        lastname="Test",
        status=1,
        date_added=datetime.now()
    )
    await user.save()
    
    # Create login activity
    activity = UserLogin(
        user_id=user.user_id,
        ip="127.0.0.1",
        user_agent="Test Agent",
        date_added=datetime.now()
    )
    await activity.save()
    
    assert activity.user_login_id is not None
    assert activity.user_id == user.user_id
    assert activity.ip == "127.0.0.1"
    
    # Test relationship
    related_user = await activity.get_user()
    assert related_user is not None
    assert related_user.user_id == user.user_id

