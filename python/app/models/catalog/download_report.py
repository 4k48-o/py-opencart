"""
Tortoise ORM model for download_report table
"""

from tortoise.models import Model
from tortoise import fields
from .download import Download
from ..system.store import Store


class DownloadReport(Model):
    """
    DownloadReport model
    
    Represents the download_report table in the OpenCart database.
    
    Attributes:
        download_report_id (int(11)) - Primary key
        download_id (int(11)), nullable
        store_id (int(11)), nullable, default: 0
        ip (varchar(40)), nullable
        country (varchar(2)), nullable
        date_added (datetime), nullable
    """

    download_report_id = fields.IntField(pk=True)
    download_id = fields.IntField(null=True)
    store_id = fields.IntField(null=True, default=0)
    ip = fields.CharField(max_length=40, null=True)
    country = fields.CharField(max_length=2, null=True)
    date_added = fields.DatetimeField(null=True)

    class Meta:
        table = "oc_download_report"

    async def get_download(self):
        """Get related Download"""
        if self.download_id:
            return await Download.get(download_id=self.download_id)
        return None
    async def get_store(self):
        """Get related Store"""
        if self.store_id:
            return await Store.get(store_id=self.store_id)
        return None
