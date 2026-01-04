"""
Tortoise ORM model for product_option_value table
"""

from tortoise.models import Model
from tortoise import fields
from .product_option import ProductOption
from .product import Product
from .option import Option
from .option_value import OptionValue


class ProductOptionValue(Model):
    """
    ProductOptionValue model
    
    Represents the product_option_value table in the OpenCart database.
    
    Attributes:
        product_option_value_id (int(11)) - Primary key
        product_option_id (int(11)), nullable
        product_id (int(11)), nullable
        option_id (int(11)), nullable
        option_value_id (int(11)), nullable, default: 0
        quantity (int(3)), nullable, default: 0
        subtract (tinyint(1)), nullable, default: 0
        price (decimal(15,4)), nullable
        price_prefix (varchar(1)), nullable
        points (int(8)), nullable, default: 0
        points_prefix (varchar(1)), nullable
        weight (decimal(15,8)), nullable
        weight_prefix (varchar(1)), nullable
    """

    product_option_value_id = fields.IntField(pk=True)
    product_option_id = fields.IntField(null=True)
    product_id = fields.IntField(null=True)
    option_id = fields.IntField(null=True)
    option_value_id = fields.IntField(null=True, default=0)
    quantity = fields.IntField(null=True, default=0)
    subtract = fields.SmallIntField(null=True, default=0)
    price = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    price_prefix = fields.CharField(max_length=1, null=True)
    points = fields.IntField(null=True, default=0)
    points_prefix = fields.CharField(max_length=1, null=True)
    weight = fields.DecimalField(max_digits=15, decimal_places=8, null=True)
    weight_prefix = fields.CharField(max_length=1, null=True)

    class Meta:
        table = "oc_product_option_value"

    async def get_product_option(self):
        """Get related ProductOption"""
        if self.product_option_id:
            return await ProductOption.get(product_option_id=self.product_option_id)
        return None
    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_option(self):
        """Get related Option"""
        if self.option_id:
            return await Option.get(option_id=self.option_id)
        return None
    async def get_option_value(self):
        """Get related OptionValue"""
        if self.option_value_id:
            return await OptionValue.get(option_value_id=self.option_value_id)
        return None
