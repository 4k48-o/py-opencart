"""
Tortoise ORM model for return table
"""

from tortoise.models import Model
from tortoise import fields
from ..order.order import Order
from ..catalog.product import Product
from ..customer.customer import Customer
from ..localisation.return_reason import ReturnReason
from ..localisation.return_action import ReturnAction
from ..localisation.return_status import ReturnStatus


class Return(Model):
    """
    Return model
    
    Represents the return table in the OpenCart database.
    
    Attributes:
        return_id (int(11)) - Primary key
        order_id (int(11)), nullable, default: 0
        customer_id (int(11)), nullable, default: 0
        firstname (varchar(32)), nullable
        lastname (varchar(32)), nullable
        email (varchar(96)), nullable
        telephone (varchar(32)), nullable
        product_id (int(11)), nullable, default: 0
        product (varchar(255)), nullable
        model (varchar(64)), nullable
        quantity (int(4)), nullable, default: 0
        opened (tinyint(1)), nullable, default: 0
        return_reason_id (int(11)), nullable, default: 0
        return_action_id (int(11)), nullable, default: 0
        return_status_id (int(11)), nullable, default: 0
        comment (text), nullable
        date_ordered (date), nullable
        date_added (datetime), nullable
        date_modified (datetime), nullable
    """

    return_id = fields.IntField(pk=True)
    order_id = fields.IntField(null=True, default=0)
    customer_id = fields.IntField(null=True, default=0)
    firstname = fields.CharField(max_length=32, null=True)
    lastname = fields.CharField(max_length=32, null=True)
    email = fields.CharField(max_length=96, null=True)
    telephone = fields.CharField(max_length=32, null=True)
    product_id = fields.IntField(null=True, default=0)
    product = fields.CharField(max_length=255, null=True)
    model = fields.CharField(max_length=64, null=True)
    quantity = fields.IntField(null=True, default=0)
    opened = fields.SmallIntField(null=True, default=0)
    return_reason_id = fields.IntField(null=True, default=0)
    return_action_id = fields.IntField(null=True, default=0)
    return_status_id = fields.IntField(null=True, default=0)
    comment = fields.TextField(null=True)
    date_ordered = fields.DateField(null=True)
    date_added = fields.DatetimeField(null=True)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_return"

    async def get_order(self):
        """Get related Order"""
        if self.order_id:
            return await Order.get(order_id=self.order_id)
        return None
    async def get_product(self):
        """Get related Product"""
        if self.product_id:
            return await Product.get(product_id=self.product_id)
        return None
    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
    async def get_return_reason(self):
        """Get related ReturnReason"""
        if self.return_reason_id:
            return await ReturnReason.get(return_reason_id=self.return_reason_id)
        return None
    async def get_return_action(self):
        """Get related ReturnAction"""
        if self.return_action_id:
            return await ReturnAction.get(return_action_id=self.return_action_id)
        return None
    async def get_return_status(self):
        """Get related ReturnStatus"""
        if self.return_status_id:
            return await ReturnStatus.get(return_status_id=self.return_status_id)
        return None
