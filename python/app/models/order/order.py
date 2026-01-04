"""
Tortoise ORM model for order table
"""

from tortoise.models import Model
from tortoise import fields
from ..system.store import Store
from ..customer.customer import Customer
from ..customer.customer_group import CustomerGroup
from ..localisation.country import Country
from ..localisation.zone import Zone
from .order_status import OrderStatus
from ..customer.customer_affiliate import CustomerAffiliate
from ..marketing.marketing import Marketing
from ..localisation.language import Language
from ..localisation.currency import Currency


class Order(Model):
    """
    Order model
    
    Represents the order table in the OpenCart database.
    
    Attributes:
        order_id (int(11)) - Primary key
        subscription_id (int(11)), nullable, default: 0
        invoice_no (int(11)), nullable, default: 0
        invoice_prefix (varchar(26)), nullable
        transaction_id (varchar(100)), nullable
        store_id (int(11)), nullable, default: 0
        store_name (varchar(64)), nullable
        store_url (varchar(255)), nullable
        customer_id (int(11)), nullable, default: 0
        customer_group_id (int(11)), nullable, default: 0
        firstname (varchar(32)), nullable
        lastname (varchar(32)), nullable
        email (varchar(96)), nullable
        telephone (varchar(32)), nullable
        custom_field (text), nullable
        payment_address_id (int(11)), nullable, default: 0
        payment_firstname (varchar(32)), nullable
        payment_lastname (varchar(32)), nullable
        payment_company (varchar(60)), nullable
        payment_address_1 (varchar(128)), nullable
        payment_address_2 (varchar(128)), nullable
        payment_city (varchar(128)), nullable
        payment_postcode (varchar(10)), nullable
        payment_country (varchar(128)), nullable
        payment_country_id (int(11)), nullable, default: 0
        payment_zone (varchar(128)), nullable
        payment_zone_id (int(11)), nullable, default: 0
        payment_address_format (text), nullable
        payment_custom_field (text), nullable
        payment_method (text), nullable
        shipping_address_id (int(11)), nullable
        shipping_firstname (varchar(32)), nullable
        shipping_lastname (varchar(32)), nullable
        shipping_company (varchar(60)), nullable
        shipping_address_1 (varchar(128)), nullable
        shipping_address_2 (varchar(128)), nullable
        shipping_city (varchar(128)), nullable
        shipping_postcode (varchar(10)), nullable
        shipping_country (varchar(128)), nullable
        shipping_country_id (int(11)), nullable, default: 0
        shipping_zone (varchar(128)), nullable
        shipping_zone_id (int(11)), nullable, default: 0
        shipping_address_format (text), nullable
        shipping_custom_field (text), nullable
        shipping_method (text), nullable
        comment (text), nullable
        total (decimal(15,4)), nullable, default: 0.0000
        order_status_id (int(11)), nullable, default: 0
        affiliate_id (int(11)), nullable, default: 0
        commission (decimal(15,4)), nullable
        marketing_id (int(11)), nullable, default: 0
        tracking (varchar(64)), nullable
        language_id (int(11)), nullable
        language_code (varchar(5)), nullable
        currency_id (int(11)), nullable
        currency_code (varchar(3)), nullable
        currency_value (decimal(15,8)), nullable, default: 1.00000000
        ip (varchar(40)), nullable
        forwarded_ip (varchar(40)), nullable
        user_agent (varchar(255)), nullable
        accept_language (varchar(255)), nullable
        date_added (datetime), nullable
        date_modified (datetime), nullable
    """

    order_id = fields.IntField(pk=True)
    subscription_id = fields.IntField(null=True, default=0)
    invoice_no = fields.IntField(null=True, default=0)
    invoice_prefix = fields.CharField(max_length=26, null=True)
    transaction_id = fields.CharField(max_length=100, null=True)
    store_id = fields.IntField(null=True, default=0)
    store_name = fields.CharField(max_length=64, null=True)
    store_url = fields.CharField(max_length=255, null=True)
    customer_id = fields.IntField(null=True, default=0)
    customer_group_id = fields.IntField(null=True, default=0)
    firstname = fields.CharField(max_length=32, null=True)
    lastname = fields.CharField(max_length=32, null=True)
    email = fields.CharField(max_length=96, null=True)
    telephone = fields.CharField(max_length=32, null=True)
    custom_field = fields.TextField(null=True)
    payment_address_id = fields.IntField(null=True, default=0)
    payment_firstname = fields.CharField(max_length=32, null=True)
    payment_lastname = fields.CharField(max_length=32, null=True)
    payment_company = fields.CharField(max_length=60, null=True)
    payment_address_1 = fields.CharField(max_length=128, null=True)
    payment_address_2 = fields.CharField(max_length=128, null=True)
    payment_city = fields.CharField(max_length=128, null=True)
    payment_postcode = fields.CharField(max_length=10, null=True)
    payment_country = fields.CharField(max_length=128, null=True)
    payment_country_id = fields.IntField(null=True, default=0)
    payment_zone = fields.CharField(max_length=128, null=True)
    payment_zone_id = fields.IntField(null=True, default=0)
    payment_address_format = fields.TextField(null=True)
    payment_custom_field = fields.TextField(null=True)
    payment_method = fields.TextField(null=True)
    shipping_address_id = fields.IntField(null=True)
    shipping_firstname = fields.CharField(max_length=32, null=True)
    shipping_lastname = fields.CharField(max_length=32, null=True)
    shipping_company = fields.CharField(max_length=60, null=True)
    shipping_address_1 = fields.CharField(max_length=128, null=True)
    shipping_address_2 = fields.CharField(max_length=128, null=True)
    shipping_city = fields.CharField(max_length=128, null=True)
    shipping_postcode = fields.CharField(max_length=10, null=True)
    shipping_country = fields.CharField(max_length=128, null=True)
    shipping_country_id = fields.IntField(null=True, default=0)
    shipping_zone = fields.CharField(max_length=128, null=True)
    shipping_zone_id = fields.IntField(null=True, default=0)
    shipping_address_format = fields.TextField(null=True)
    shipping_custom_field = fields.TextField(null=True)
    shipping_method = fields.TextField(null=True)
    comment = fields.TextField(null=True)
    total = fields.DecimalField(max_digits=15, decimal_places=4, null=True, default='0.0000')
    order_status_id = fields.IntField(null=True, default=0)
    affiliate_id = fields.IntField(null=True, default=0)
    commission = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    marketing_id = fields.IntField(null=True, default=0)
    tracking = fields.CharField(max_length=64, null=True)
    language_id = fields.IntField(null=True)
    language_code = fields.CharField(max_length=5, null=True)
    currency_id = fields.IntField(null=True)
    currency_code = fields.CharField(max_length=3, null=True)
    currency_value = fields.DecimalField(max_digits=15, decimal_places=8, null=True, default='1.00000000')
    ip = fields.CharField(max_length=40, null=True)
    forwarded_ip = fields.CharField(max_length=40, null=True)
    user_agent = fields.CharField(max_length=255, null=True)
    accept_language = fields.CharField(max_length=255, null=True)
    date_added = fields.DatetimeField(null=True)
    date_modified = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_order"
        indexes = [("email",)]

    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
    async def get_customer(self):
        """Get related Customer"""
        if self.customer_id:
            return await Customer.get(customer_id=self.customer_id)
        return None
    async def get_customer_group(self):
        """Get related CustomerGroup"""
        if self.customer_group_id:
            return await CustomerGroup.get(customer_group_id=self.customer_group_id)
        return None
    async def get_country(self):
        """Get related Country"""
        if self.payment_country_id:
            return await Country.get(country_id=self.payment_country_id)
        return None
    async def get_zone(self):
        """Get related Zone"""
        if self.payment_zone_id:
            return await Zone.get(zone_id=self.payment_zone_id)
        return None
    async def get_country(self):
        """Get related Country"""
        if self.shipping_country_id:
            return await Country.get(country_id=self.shipping_country_id)
        return None
    async def get_zone(self):
        """Get related Zone"""
        if self.shipping_zone_id:
            return await Zone.get(zone_id=self.shipping_zone_id)
        return None
    async def get_order_status(self):
        """Get related OrderStatus"""
        if self.order_status_id:
            return await OrderStatus.get(order_status_id=self.order_status_id)
        return None
    async def get_customer_affiliate(self):
        """Get related CustomerAffiliate"""
        if self.affiliate_id:
            return await CustomerAffiliate.get(customer_id=self.affiliate_id)
        return None
    async def get_marketing(self):
        """Get related Marketing"""
        if self.marketing_id:
            return await Marketing.get(marketing_id=self.marketing_id)
        return None
    async def get_language(self):
        """Get related Language"""
        if self.language_id:
            return await Language.get(language_id=self.language_id)
        return None
    async def get_currency(self):
        """Get related Currency"""
        if self.currency_id:
            return await Currency.get(currency_id=self.currency_id)
        return None
