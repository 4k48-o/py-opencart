# py-opencart

A Python library for interacting with OpenCart e-commerce platform APIs.

## Overview
This library provides a Python interface to interact with OpenCart's API, allowing developers to programmatically manage products, orders, customers, and other e-commerce data.

## Features
- Product management
- Order processing
- Customer management
- Category handling
- Image uploads
- Inventory tracking

## Installation
```bash
pip install py-opencart
```

## Usage
```python
from opencart_api import OpenCartClient

client = OpenCartClient('https://yourstore.com', 'your_api_key')
products = client.get_products()
```

## Contributing
Feel free to submit issues and enhancement requests!