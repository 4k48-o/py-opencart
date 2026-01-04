"""
Unit tests for Store model
"""
import pytest
from app.models.system.store import Store


@pytest.mark.asyncio
async def test_store_model_creation(db_transaction):
    """Test creating a Store instance"""
    store = Store(
        name="Test Store",
        url="https://test.example.com"
    )
    
    assert store.name == "Test Store"
    assert store.url == "https://test.example.com"
    assert store.store_id is None  # Not saved yet


@pytest.mark.asyncio
async def test_store_model_save(db_transaction):
    """Test saving a Store to database"""
    store = Store(
        name="Test Store 2",
        url="https://test2.example.com"
    )
    await store.save()
    
    assert store.store_id is not None
    assert store.store_id > 0


@pytest.mark.asyncio
async def test_store_model_retrieve(db_transaction):
    """Test retrieving a Store from database"""
    # Create and save
    store = Store(
        name="Test Store 3",
        url="https://test3.example.com"
    )
    await store.save()
    store_id = store.store_id
    
    # Retrieve
    retrieved = await Store.get(store_id=store_id)
    
    assert retrieved.store_id == store_id
    assert retrieved.name == "Test Store 3"
    assert retrieved.url == "https://test3.example.com"


@pytest.mark.asyncio
async def test_store_model_update(db_transaction):
    """Test updating a Store"""
    store = Store(
        name="Original Name",
        url="https://original.example.com"
    )
    await store.save()
    
    # Update
    store.name = "Updated Name"
    store.url = "https://updated.example.com"
    await store.save()
    
    # Verify
    updated = await Store.get(store_id=store.store_id)
    assert updated.name == "Updated Name"
    assert updated.url == "https://updated.example.com"


@pytest.mark.asyncio
async def test_store_model_delete(db_transaction):
    """Test deleting a Store"""
    store = Store(
        name="To Delete",
        url="https://delete.example.com"
    )
    await store.save()
    store_id = store.store_id
    
    # Delete
    await store.delete()
    
    # Verify deletion
    with pytest.raises(Exception):  # Should raise DoesNotExist
        await Store.get(store_id=store_id)


@pytest.mark.asyncio
async def test_store_model_list(db_transaction):
    """Test listing all stores"""
    # Create multiple stores
    for i in range(3):
        store = Store(
            name=f"Store {i}",
            url=f"https://store{i}.example.com"
        )
        await store.save()
    
    # List all
    stores = await Store.all()
    assert len(stores) >= 3


@pytest.mark.asyncio
async def test_store_model_meta(db_transaction):
    """Test Store model Meta configuration"""
    assert Store._meta.db_table == "oc_store"
    assert Store._meta.pk_attr == "store_id"

