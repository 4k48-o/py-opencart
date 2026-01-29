#!/usr/bin/env python3
"""
Basic usage example for py-opencart library
"""

from opencart_api import OpenCartClient


def main():
    # Initialize the OpenCart client
    # Replace with your actual OpenCart URL and API credentials
    client = OpenCartClient(
        base_url='https://your-opencart-site.com',
        api_key='your-api-key',
        api_secret='your-api-secret'  # if required
    )
    
    # Test authentication
    authenticated = client.authenticate()
    if authenticated:
        print("Successfully authenticated with OpenCart API")
    else:
        print("Failed to authenticate with OpenCart API")
        return
    
    # Example: Get all products
    print("\nFetching products...")
    products = client.get_products()
    print(f"Found {len(products)} products")
    
    # Example: Get specific product (replace with actual product ID)
    # product = client.get_product(1)
    # if product:
    #     print(f"Product details: {product}")
    
    # Example: Create a new product (uncomment to use)
    # new_product = {
    #     'name': 'Sample Product',
    #     'model': 'SAMPLE-001',
    #     'price': 19.99,
    #     'quantity': 100,
    #     'description': 'This is a sample product'
    # }
    # created_product = client.create_product(new_product)
    # if created_product:
    #     print(f"Created product: {created_product}")
    
    # Example: Get orders
    print("\nFetching orders...")
    orders = client.get_orders()
    print(f"Found {len(orders)} orders")
    
    # Example: Get customers
    print("\nFetching customers...")
    customers = client.get_customers()
    print(f"Found {len(customers)} customers")


if __name__ == "__main__":
    main()