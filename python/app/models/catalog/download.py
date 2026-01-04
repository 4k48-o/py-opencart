"""
Tortoise ORM model for download table
"""

from tortoise.models import Model
from tortoise import fields


class Download(Model):
    """
    Download model
    
    Represents the download table in the OpenCart database.
    
    Attributes:
        download_id (int(11)) - Primary key
        filename (varchar(160)), nullable
        mask (varchar(128)), nullable
        date_added (datetime), nullable
    """

    download_id = fields.IntField(pk=True)
    filename = fields.CharField(max_length=160, null=True)
    mask = fields.CharField(max_length=128, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_download"

