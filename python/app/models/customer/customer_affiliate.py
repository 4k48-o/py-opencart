"""
Tortoise ORM model for customer_affiliate table
"""

from tortoise.models import Model
from tortoise import fields
from .customer import Customer


class CustomerAffiliate(Model):
    """
    CustomerAffiliate model
    
    Represents the customer_affiliate table in the OpenCart database.
    
    Attributes:
        customer_id (int(11)) - Primary key
        company (varchar(60)), nullable
        website (varchar(255)), nullable
        tracking (varchar(64)), nullable
        balance (decimal(15,4)), nullable
        commission (decimal(4,2)), nullable, default: 0.00
        tax (varchar(64)), nullable
        payment_method (varchar(6)), nullable
        cheque (varchar(100)), nullable
        paypal (varchar(64)), nullable
        bank_name (varchar(64)), nullable
        bank_branch_number (varchar(64)), nullable
        bank_swift_code (varchar(64)), nullable
        bank_account_name (varchar(64)), nullable
        bank_account_number (varchar(64)), nullable
        custom_field (text), nullable
        status (tinyint(1)), nullable, default: 0
        date_added (datetime), nullable
    """

    customer_id = fields.IntField(pk=True)
    company = fields.CharField(max_length=60, null=True)
    website = fields.CharField(max_length=255, null=True)
    tracking = fields.CharField(max_length=64, null=True)
    balance = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    commission = fields.DecimalField(max_digits=4, decimal_places=2, null=True, default='0.00')
    tax = fields.CharField(max_length=64, null=True)
    payment_method = fields.CharField(max_length=6, null=True)
    cheque = fields.CharField(max_length=100, null=True)
    paypal = fields.CharField(max_length=64, null=True)
    bank_name = fields.CharField(max_length=64, null=True)
    bank_branch_number = fields.CharField(max_length=64, null=True)
    bank_swift_code = fields.CharField(max_length=64, null=True)
    bank_account_name = fields.CharField(max_length=64, null=True)
    bank_account_number = fields.CharField(max_length=64, null=True)
    custom_field = fields.TextField(null=True)
    status = fields.SmallIntField(null=True, default=0)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_customer_affiliate"

    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
