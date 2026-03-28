from django.db import models


class Sender(models.Model):
    """差出人（1アプリにつき1レコード）"""

    names = models.JSONField()  # ["山田 太郎", "山田 花子"]
    zipcode = models.CharField(max_length=8)  # NNN-NNNN
    address = models.CharField(max_length=400)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "差出人"

    def __str__(self):
        return " / ".join(self.names)


class Guest(models.Model):
    """出席者（0件以上）"""

    names = models.JSONField()  # 1〜5名のリスト
    zipcode = models.CharField(max_length=8, blank=True, null=True)
    address = models.CharField(max_length=400, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "出席者"
        ordering = ["id"]

    def __str__(self):
        return " / ".join(self.names)
