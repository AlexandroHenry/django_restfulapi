from dataclasses import fields
from rest_framework import serializers
from .models import *

class TimeSeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSeries
        fields = ('id','date', 'open', 'high', 'low', 'close', 'volume')

class currentStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = currentStock
        fields = ('date', 'open', 'high', 'low', 'close','adjclose', 'volume')

class dailyStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = currentStock
        fields = ('id', 'date', 'open', 'high', 'low', 'close','adjclose', 'volume')

class stockTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = stockTransaction
        fields = ('id', 'owner','date', 'action', 'symbol', 'price', 'quantity')

class userInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = userInfo
        field = ('id', 'email', 'createdAt', 'nickname', 'cash', 'imageURL')

class ownStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ownStock
        field = ('owner', 'symbol', 'price', 'quantity')