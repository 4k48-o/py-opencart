#!/usr/bin/env python3
"""
Test script for Store API
"""
import asyncio
import importlib
from app.database import init_db, close_db
from app.config import settings

# Import Store model using importlib to avoid circular import issues
try:
    from app.models.system.store import Store
except (ImportError, AttributeError):
    # Fallback: import using importlib
    store_module = importlib.import_module('app.models.system.store')
    Store = store_module.Store


async def test_store_crud():
    """Test Store CRUD operations"""
    print("Testing Store CRUD operations...")
    print(f"Database: {settings.db_name}@{settings.db_host}:{settings.db_port}\n")
    
    # Initialize database
    await init_db()
    print("✓ Database connected\n")
    
    try:
        # Test: List all stores
        print("1. Listing all stores:")
        stores = await Store.all()
        print(f"   Found {len(stores)} stores")
        for store in stores:
            print(f"   - Store {store.store_id}: {store.name} ({store.url})")
        print()
        
        # Test: Create a new store
        print("2. Creating a new store:")
        new_store = await Store.create(
            name="Test Store",
            url="https://test.example.com"
        )
        print(f"   ✓ Created store with ID: {new_store.store_id}")
        print(f"   Name: {new_store.name}")
        print(f"   URL: {new_store.url}")
        print()
        
        # Test: Get store by ID
        print("3. Getting store by ID:")
        store = await Store.get(store_id=new_store.store_id)
        print(f"   ✓ Retrieved store: {store.name}")
        print()
        
        # Test: Update store
        print("4. Updating store:")
        store.name = "Updated Test Store"
        store.url = "https://updated.example.com"
        await store.save()
        print(f"   ✓ Updated store: {store.name}")
        print()
        
        # Test: Delete store
        print("5. Deleting store:")
        await store.delete()
        print(f"   ✓ Deleted store with ID: {new_store.store_id}")
        print()
        
        print("✓ All CRUD operations completed successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db()


if __name__ == '__main__':
    asyncio.run(test_store_crud())

