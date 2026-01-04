"""
Tortoise ORM model for session table
"""

from tortoise.models import Model
from tortoise import fields


class Session(Model):
    """
    Session model
    
    Represents the session table in the OpenCart database.
    
    Attributes:
        session_id (varchar(32)) - Primary key
        data (text), nullable
        expire (datetime), nullable
    """

    session_id = fields.CharField(max_length=32, pk=True)
    data = fields.TextField(null=True)
    expire = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_session"
        indexes = [("expire",)]

