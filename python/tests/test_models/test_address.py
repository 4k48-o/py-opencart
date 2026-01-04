"""
Unit tests for Address model
"""
import pytest
from app.models.customer.address import Address
from app.models.customer.customer import Customer


@pytest.mark.asyncio
async def test_address_model_creation(db_transaction):
    """Test creating an Address instance"""
    address = Address(
        firstname="John",
        lastname="Doe",
        address_1="123 Main St",
        city="New York",
        postcode="10001",
        country_id=1,
        zone_id=1
    )
    
    assert address.firstname == "John"
    assert address.lastname == "Doe"
    assert address.address_1 == "123 Main St"
    assert address.city == "New York"
    assert address.postcode == "10001"


@pytest.mark.asyncio
async def test_address_model_save(db_transaction):
    """Test saving an Address to database"""
    address = Address(
        firstname="Jane",
        lastname="Smith",
        address_1="456 Oak Ave",
        city="Los Angeles",
        postcode="90001"
    )
    await address.save()
    
    assert address.address_id is not None
    assert address.address_id > 0


@pytest.mark.asyncio
async def test_address_relationship_method(db_transaction):
    """Test Address.get_customer() relationship method"""
    # Create a customer first
    customer = Customer(
        firstname="Test",
        lastname="Customer",
        email="test@example.com",
        telephone="1234567890"
    )
    await customer.save()
    
    # Create address with customer_id
    address = Address(
        customer_id=customer.customer_id,
        firstname="Test",
        lastname="Address",
        address_1="789 Test St",
        city="Test City"
    )
    await address.save()
    
    # Test relationship method
    related_customer = await address.get_customer()
    assert related_customer is not None
    assert related_customer.customer_id == customer.customer_id
    assert related_customer.email == "test@example.com"


@pytest.mark.asyncio
async def test_address_model_indexes(db_transaction):
    """Test that Address model has correct indexes"""
    # Verify Meta class has indexes
    meta = Address._meta
    assert hasattr(meta, 'indexes') or hasattr(meta, '_indexes')
    
    # Verify table name
    assert meta.db_table == "oc_address"

