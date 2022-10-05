from django.urls import path, include
from .views import *

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("timeseries/symbol=<str:symbol>&period=<str:period>&interval=<str:interval>", timeseriesAPI),
    path("companyinfo/symbol=<str:symbol>", companyDetailAPI),
    path("currentStock/symbol=<str:symbol>", currentStockAPI),
    path("dailyStock/symbol=<str:symbol>", dailyStockAPI),
    path("stocktransaction/owner=<str:owner>&action=<str:action>&symbol=<str:symbol>&price=<str:price>&quantity=<str:quantity>", stockTransactionAPI),
    path("stocktransaction/owner=<str:owner>", stockListAPI),
    path("stockInfo/symbol=<str:symbol>", stockInfoAPI),
    path("userInfo/id=<str:id>&email=<str:email>", userRegisterAPI),
    path("userInfo/id=<str:id>", userFindAPI),
    path("stocktransaction/buy/owner=<str:owner>&symbol=<str:symbol>&price=<str:price>&quantity=<str:quantity>", stockBuyAPI),
    path("stocktransaction/sell/owner=<str:owner>&symbol=<str:symbol>&price=<str:price>&quantity=<str:quantity>", stockSellAPI),
    path("stocktransaction/own/owner=<str:owner>", ownStockAPI),
    path("imageupload/name=<str:name>&userid=<str:userid>", profileImageAPI),
    path("assetDaily", myAssetUpdateAPI), # Uploading myasset test
    path("myasset/id=<str:id>", myAssetViewAPI),
    path("myStockCurrentPrice/owner=<str:owner>", myStockCurrentPrice),
    path("indices", indices),
    path("futures", futures),
    path("indicesUS", indicesChosen),
    path("indices/symbol=<str:symbol>", singleIndex)
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
