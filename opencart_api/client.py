import requests
from typing import Dict, List, Optional, Any
import json


class OpenCartClient:
    """
    A client for interacting with OpenCart API
    """
    
    def __init__(self, base_url: str, api_key: str, api_secret: Optional[str] = None):
        """
        Initialize the OpenCart client
        
        Args:
            base_url: The base URL of the OpenCart installation
            api_key: API key for authentication
            api_secret: Optional API secret if required by the OpenCart installation
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        
        # Set up headers for API requests
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'py-opencart/0.1.0'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to the OpenCart API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint to call
            data: Optional data to send with the request
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/index.php?route=api/{endpoint}"
        
        params = {
            'key': self.api_key
        }
        
        if method.upper() == 'GET':
            response = self.session.get(url, params=params)
        elif method.upper() == 'POST':
            response = self.session.post(url, params=params, json=data)
        elif method.upper() == 'PUT':
            response = self.session.put(url, params=params, json=data)
        elif method.upper() == 'DELETE':
            response = self.session.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        response.raise_for_status()
        return response.json()
    
    def authenticate(self) -> bool:
        """
        Authenticate with the OpenCart API
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Try to make a simple API call to test authentication
            response = self._make_request('GET', 'login')
            return 'success' in response or response.get('key') == self.api_key
        except Exception:
            return False
    
    def get_products(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get a list of products
        
        Args:
            filters: Optional filters to apply to the product query
            
        Returns:
            List of product dictionaries
        """
        # Note: Actual OpenCart API endpoints may vary depending on the version and extensions
        # This is a simplified example
        endpoint = 'product'
        if filters:
            # Apply filters as needed
            pass
        
        try:
            # Attempt to call the products API endpoint
            return self._make_request('GET', endpoint)
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """
        Get a specific product by ID
        
        Args:
            product_id: ID of the product to retrieve
            
        Returns:
            Product dictionary or None if not found
        """
        try:
            # This is a hypothetical endpoint - actual implementation may vary
            response = self._make_request('GET', f'product/{product_id}')
            return response
        except Exception as e:
            print(f"Error fetching product {product_id}: {e}")
            return None
    
    def create_product(self, product_data: Dict) -> Optional[Dict]:
        """
        Create a new product
        
        Args:
            product_data: Dictionary containing product information
            
        Returns:
            Created product data or error information
        """
        try:
            response = self._make_request('POST', 'product', data=product_data)
            return response
        except Exception as e:
            print(f"Error creating product: {e}")
            return None
    
    def update_product(self, product_id: int, product_data: Dict) -> Optional[Dict]:
        """
        Update an existing product
        
        Args:
            product_id: ID of the product to update
            product_data: Dictionary containing updated product information
            
        Returns:
            Updated product data or error information
        """
        try:
            response = self._make_request('PUT', f'product/{product_id}', data=product_data)
            return response
        except Exception as e:
            print(f"Error updating product {product_id}: {e}")
            return None
    
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product
        
        Args:
            product_id: ID of the product to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            response = self._make_request('DELETE', f'product/{product_id}')
            return 'success' in response
        except Exception as e:
            print(f"Error deleting product {product_id}: {e}")
            return False
    
    def get_orders(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get a list of orders
        
        Args:
            filters: Optional filters to apply to the order query
            
        Returns:
            List of order dictionaries
        """
        try:
            return self._make_request('GET', 'order')
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return []
    
    def get_customers(self) -> List[Dict]:
        """
        Get a list of customers
        
        Returns:
            List of customer dictionaries
        """
        try:
            return self._make_request('GET', 'customer')
        except Exception as e:
            print(f"Error fetching customers: {e}")
            return []