from django.db import models
from uuid import uuid4
# Create your models here.

class TimeSeries(models.Model):
    id = models.UUIDField(
        default= uuid4,
        unique=True,
        primary_key=True,
        editable=False
    )
    date = models.DateField()
    open = models.DecimalField(max_digits=30, decimal_places=30)
    high = models.DecimalField(max_digits=30, decimal_places=30)
    low = models.DecimalField(max_digits=30, decimal_places=30)
    close = models.DecimalField(max_digits=30, decimal_places=30)
    volume = models.DecimalField(max_digits=30, decimal_places=30)

class currentStock(models.Model):
    date = models.DateField()
    open = models.DecimalField(max_digits=30, decimal_places=30)
    high = models.DecimalField(max_digits=30, decimal_places=30)
    low = models.DecimalField(max_digits=30, decimal_places=30)
    close = models.DecimalField(max_digits=30, decimal_places=30)
    adjclose = models.DecimalField(max_digits=30, decimal_places=30)
    volume = models.DecimalField(max_digits=30, decimal_places=30)

class dailyStock(models.Model):
    id = models.UUIDField(
        default= uuid4,
        unique=True,
        primary_key=True,
        editable=False
    )
    date = models.DateField()
    open = models.DecimalField(max_digits=30, decimal_places=30)
    high = models.DecimalField(max_digits=30, decimal_places=30)
    low = models.DecimalField(max_digits=30, decimal_places=30)
    close = models.DecimalField(max_digits=30, decimal_places=30)
    adjclose = models.DecimalField(max_digits=30, decimal_places=30)
    volume = models.DecimalField(max_digits=30, decimal_places=30)

class stockTransaction(models.Model):
    id = models.UUIDField(
        default= uuid4,
        unique=True,
        primary_key=True,
        editable=False
    )
    date = models.DateField()
    owner = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)
    price = models.CharField(max_length=100)
    quantity = models.CharField(max_length=100)

# class transactionHistory(models.Model):
#     id = models.UUIDField(
#         default= uuid4,
#         unique=True,
#         primary_key=True,
#         editable=False
#     )
#     date = models.DateField()


class userInfo(models.Model):
    id = models.UUIDField(
        default= uuid4,
        unique=True,
        primary_key=True,
        editable=False
    )
    email = models.EmailField()
    createdAt = models.DateField()
    nickname = models.CharField(max_length=100)
    cash = models.DecimalField(max_digits=100, decimal_places=30)
    imageURL = models.CharField(max_length=200)

class ownStock(models.Model):
    owner = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)
    price = models.CharField(max_length=100)
    quantity = models.CharField(max_length=100)

class ProfileImage(models.Model):
    image = models.ImageField(upload_to="images/")

    def __str__(self):
        return str(self.title)
