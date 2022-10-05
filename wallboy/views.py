from ast import And
from http import client
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from .models import *

import pandas as pd
import numpy as np
import yfinance as yf
import uuid
import json
import pymongo
from datetime import datetime
from decimal import Decimal

import bson.json_util as json_util

client = pymongo.MongoClient('mongodb+srv://alaxhenry:Tmdcjdahzk123@alaxhenry.3bowh.mongodb.net/?retryWrites=true&w=majority')
db = client['wallboy_db']
stockTransactionCol = db["stockTransaction"]
userInfoCol = db["userInfo"]
ownStockCol = db["ownStock"]
ownAssetCol = db["ownAsset"]
# Create your views here.

def timeseriesAPI(request, symbol, period, interval):

    # period : str
    #     Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max Either Use period parameter or use start and end
    # interval : str
    #     Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo Intraday data cannot extend last 60 days
    # start: str
    #     Download start date string (YYYY-MM-DD) or _datetime. Default is 1900-01-01
    # end: str
    #     Download end date string (YYYY-MM-DD) or _datetime. Default is now
    rawData = yf.Ticker(symbol).history(period=period, interval=interval)

    historyList = []

    for i in range(len(rawData)):
        id = str(uuid.uuid4())
        # date = rawData.index[i].strftime("%Y-%m-%dT%H:%M:%SZ")
        date = rawData.index[i].strftime("%Y-%m-%d")
        open = np.double(rawData['Open'][i])
        high = np.double(rawData['High'][i])
        low = np.double(rawData['Low'][i])
        close = np.double(rawData['Close'][i])
        volume = np.double(rawData['Volume'][i])
        
        data = {'id': id, 'date': date, 'open': open, 'high': high, 'low': low, 'close': close, 'volume': volume}
        historyList.append(data)

    final = json.dumps(historyList)
    return HttpResponse(json.dumps(historyList), content_type="application/json")

def companyDetailAPI(request, symbol):
    rawData = yf.Ticker(symbol).info
    return HttpResponse(json.dumps(rawData), content_type="application/json")

def currentStockAPI(request, symbol):
    ticker = yf.download(symbol, period='1d')

    date = str(ticker.index.strftime("%Y-%m-%d"))
    date = date[8:18]
    open = np.double(ticker['Open'][0])
    high = np.double(ticker['High'][0])
    low = np.double(ticker['Low'][0])
    close = np.double(ticker['Close'][0])
    adj_close = np.double(ticker['Adj Close'][0])
    volume = np.double(ticker['Volume'][0])

    data = {'date': date, 'open': open, 'high': high, 'low': low, 'close': close, 'adjclose': adj_close, 'volume': volume}
    return HttpResponse(json.dumps(data), content_type="application/json")

def dailyStockAPI(request, symbol):
    ticker = yf.download(symbol, period='1d', interval='1m')
    
    dailyList = []
    for i in range(len(ticker)):
        id = str(uuid.uuid4())
        date = ticker.index[i].strftime("%Y-%m-%dT%H:%M:%SZ")
        open = np.double(ticker['Open'][i])
        high = np.double(ticker['High'][i])
        low = np.double(ticker['Low'][i])
        close = np.double(ticker['Close'][i])
        adj_close = np.double(ticker['Adj Close'][i])
        volume = np.double(ticker['Volume'][i])
        
        data = {'id': id, 'date': date, 'open': open, 'high': high, 'low': low, 'close': close, 'adjclose': adj_close, 'volume': volume}
        dailyList.append(data)
    return HttpResponse(json.dumps(dailyList), content_type="application/json")

@csrf_exempt
def stockInfoAPI(request, symbol):
    information = yf.Ticker(symbol).stats()

    return HttpResponse(json.dumps(information), content_type="application/json")

 # Stock History
@api_view(['POST'])
def stockTransactionAPI(request, action, symbol, price, quantity, owner):
    if request.method == 'POST':
        data = {'date': datetime.now(),'owner': owner ,'action': action, 'symbol': symbol, 'price': price, 'quantity': quantity}
        stockTransactionCol.insert_one(data)
        success = "{upload : success}"
        return HttpResponse(json.dumps(success), content_type="application/json")

@api_view(['GET'])
def stockListAPI(request, owner):
    
    if request.method == 'GET':
        
        wallet = []
        
        mystock = stockTransactionCol.find({
            "owner": {"$eq": owner}
        })

        count = stockTransactionCol.count_documents({"owner": {"$eq": owner}})

        for i in range(count):
            
            id = mystock[i]["_id"]
            date = mystock[i]["date"]
            owner = mystock[i]["owner"]
            action = mystock[i]["action"]
            symbol = mystock[i]["symbol"]
            price = mystock[i]["price"]
            quantity = mystock[i]["quantity"]

            data = {"id": str(id), "date": str(date), "owner": owner, "action": action, "symbol": symbol, "price": price, "quantity": quantity}
            wallet.append(data)

        return HttpResponse(json_util.dumps(wallet), content_type="application/json")

# Stock 현재 보유
@api_view(['GET'])
def ownStockAPI(request, owner):
    
    wallet = []
    
    mystock = ownStockCol.find({
            "owner": {"$eq": owner}
        })

    count = ownStockCol.count_documents({"owner": {"$eq": owner}})

    for i in range(count):
        id = mystock[i]["_id"]
        owner = mystock[i]["owner"]
        symbol = mystock[i]["symbol"]
        price = mystock[i]["price"]
        quantity = mystock[i]["quantity"]
        
        data = {'id': id, 'owner': owner, 'symbol': symbol, 'price': price, 'quantity': quantity}

        wallet.append(data)

    return HttpResponse(json_util.dumps(wallet), content_type="application/json")

# Stock Buy
@api_view(['POST'])
def stockBuyAPI(request, owner, symbol, price, quantity):
    search = ownStockCol.find_one({"$and": [{"symbol": symbol}, {"owner": owner}]})
    
    user = userInfoCol.find_one({"id": owner})
    cash = user['cash']
    convertedCash = Decimal(cash)

    changedCash = Decimal(user['cash']) - (Decimal(price) * Decimal(quantity))

    if changedCash >= 0:
        if search == None:
            data = {'owner': owner, 'symbol': symbol, 'price': price, 'quantity': quantity}
            ownStockCol.insert_one(data)

            userData = {"$set": {'id': user['id'], 'createdAt': user['createdAt'], 'email': user['email'], 'nickname': user['nickname'], 'cash': str(changedCash), 'imageURL': user['imageURL']}} 
            userInfoCol.update_one(user, userData)

        else:
            original_quantity = Decimal(search['quantity'])
            original_price = Decimal(search['price'])

            convertedPrice = Decimal(price)
            convertedQuantity = Decimal(quantity)

            totalPrice = (original_quantity * original_price) + (convertedPrice * convertedQuantity)
            totalQuantity = original_quantity + convertedQuantity
            avgPrice = totalPrice / totalQuantity
        
            data = {"$set": {'owner': owner, 'symbol': symbol, 'price': str(avgPrice), 'quantity': str(totalQuantity)}}
            ownStockCol.update_one(search, data)

            userData = {"$set": {'id': user['id'], 'createdAt': user['createdAt'], 'email': user['email'], 'nickname': user['nickname'], 'cash': str(changedCash), 'imageURL': user['imageURL']}} 
            userInfoCol.update_one(user, userData)
        
        success = "{upload : success}"
    else:
        print("구매가격 초과")
        success = "{upload : fail}"

    success = "{upload : success}"
    return HttpResponse(json.dumps(success), content_type="application/json")

# Stock Sell
@api_view(['POST'])
def stockSellAPI(request, owner, symbol, price, quantity):
    search = ownStockCol.find_one({"$and": [{"symbol": symbol}, {"owner": owner}]})
    user = userInfoCol.find_one({"id": owner})

    availableQuantity = Decimal(search['quantity'])
    sellQuantity = Decimal(quantity)
    
    sellAmount = Decimal(price) * Decimal(quantity)

    if search != None:
        
        if availableQuantity >= sellQuantity:
            currentQuantity = availableQuantity - sellQuantity

            data = {"$set": {'owner': owner, 'symbol': symbol, 'price': search['price'], 'quantity': str(currentQuantity)}}
            ownStockCol.update_one(search, data)

            beforeCash = Decimal(user['cash'])
            afterCash = beforeCash + sellAmount

            userData = {"$set": {'id': user['id'], 'createdAt': user['createdAt'], 'email': user['email'], 'nickname': user['nickname'], 'cash': str(afterCash), 'imageURL': user['imageURL']}} 
            userInfoCol.update_one(user, userData)

            success = "{upload : success}"
        else:
            print("보유량보다 초과한 양을 판매할 수 없습니다.")
            success = "{upload : fail}"
    else:
        print("보유한 해당 주식이 없습니다")
        success = "{upload : fail}"

    return HttpResponse(json.dumps(success), content_type="application/json")

@csrf_exempt
def userRegisterAPI(request, id, email):
    
    result = userInfoCol.find_one({"id": id})

    if result == None and request.method == 'POST':
        
        data = {'id': id, 'createdAt': datetime.now(), 'email': email, 'nickname': "Wallboy", 'cash': '10000', 'imageURL': "https://cdn.vectorstock.com/i/preview-1x/22/05/male-profile-picture-vector-1862205.jpg"}
        userInfoCol.insert_one(data)

        success = "{upload : 회원가입 성공!}"
        return HttpResponse(json.dumps(success), content_type="application/json")

def userFindAPI(request, id):
    result = userInfoCol.find_one({"id": id})
    print(result)

    data = {"result": result}
    # account.append(data)
    return HttpResponse(json_util.dumps(data), content_type="application/json")

@csrf_exempt
@api_view(['GET','POST'])
def profileImageAPI(request, name, userid):
    if request.method == "POST":
        
        print("request",request)
        print("request.data: ",request.data)
        print("request.data의 타입: ",type(request.data))
        print("request.FILES: ",request.FILES)
        print("request.FILES의 타입: ",type(request.FILES))
        print("request.method: "+str(request.method))
        print("request.content_type: ",request.content_type)
        print("request.stream: ",request.stream)

        profileImage = ProfileImage()
        profileImage.image = request.FILES['image']
        profileImage.save()
        
        filename = name + ".png"
        imageurl = "http://131.186.28.79/media/images/" + filename
        user = userInfoCol.find_one({"id": userid})
        userData = {"$set": {'id': user['id'], 'createdAt': user['createdAt'], 'email': user['email'], 'nickname': user['nickname'], 'cash': user['cash'], 'imageURL': str(imageurl)}} 
        userInfoCol.update_one(user, userData)

        success = "[{upload : 사진 저장 성공!}]"
        return HttpResponse(json.dumps(success), content_type="application/json")

@csrf_exempt
def myAssetUpdateAPI(request):

    for x in userInfoCol.find():
        total = 0

        for y in ownStockCol.find({'owner': x["id"]}):
            print(y)
            
            sum = float(y["price"]) * float(y["quantity"])
            total += sum

        data = {'id': x["id"], 'cash': x["cash"], 'stockValue': str(total), 'updatedAt': datetime.now()}
        ownAssetCol.insert_one(data)

    data = {"result": "success"}
    return HttpResponse(json_util.dumps(data), content_type="application/json")

@csrf_exempt
def myAssetViewAPI(request, id):
    assetHistory = []
    
    result = ownAssetCol.find({'id': id})
    for i in result:
        data = {'id': i["id"], 'cash': i["cash"], 'stock': i["stockValue"], 'updatedAt': str(i["updatedAt"])[0:10]}
        assetHistory.append(data)

    return HttpResponse(json_util.dumps(assetHistory), content_type="application/json")

@csrf_exempt
def myStockCurrentPrice(request, owner):
    symbols= []
    prices = []
    symbolsText = ""
    stocks = ownStockCol.find({'owner': owner})
    
    for i in stocks:
        symbols.append(i["symbol"])

    for i in symbols:
        symbolsText += f"{i} "

    date = datetime.today().strftime('%Y-%m-%d')
    df = yf.download(symbolsText[0:-1], date).reset_index(drop=True)
    
    for i in symbols:
        data = {'symbol': i, 'adjclose': round(df['Adj Close'][i].iloc[0], 2)}
        prices.append(data)

    return HttpResponse(json_util.dumps(prices), content_type="application/json")

@csrf_exempt
def indices(request):
    indices = []

    indicesUS = ['^DJI', '^IXIC', '^GSPC', '^VIX', '^RUT']
    indicesAsia = ['^KS11', '^KQ11', '^N225']

    indicesUSText = ""
    indicesAsiaText = ""

    for i in indicesUS:
        indicesUSText += f"{i} "

    date = datetime.today().strftime('%Y-%m-%d')
    df_US = yf.download(indicesUSText[0:-1], date).reset_index(drop=True)

    for i in indicesUS:
        if i == "^DJI":
            data = {'name': 'Dow Jones Composite', 'nameKR': '다우존스 종합지수', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        elif i == "^IXIC":
            data = {'name': 'Nasdaq Composite', 'nameKR': '나스닥 종합지수', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        elif i == "^GSPC":
            data = {'name': 'S&P500', 'nameKR': 'S&P500', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        elif i == "^VIX":
            data = {'name': 'CBOE Volatility Index', 'nameKR': 'VIX 지수', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        elif i == "^RUT":
            data = {'name': 'Russell 2000', 'nameKR': 'Russell 2000', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        
        indices.append(data)


    for i in indicesAsia:
        indicesAsiaText += f"{i} "

    date = datetime.today().strftime('%Y-%m-%d')
    df_KR = yf.download(indicesAsiaText[0:-1], date).reset_index(drop=True)

    for i in indicesAsia:
        if i == "^KS11":
            data = {'name': 'KOSPI Composite Index', 'nameKR': '코스피 종합지수', 'symbol': i, 'adjclose': round(df_KR['Adj Close'][i].iloc[0], 2)}
        elif i == "^KQ11":
            data = {'name': 'Kosdaq Composite Index', 'nameKR': '코스닥 종합지수', 'symbol': i, 'adjclose': round(df_KR['Adj Close'][i].iloc[0], 2)}
        elif i == "^KQ11":
            data = {'name': 'Nikkei 225', 'nameKR': '닛케이 225', 'symbol': i, 'adjclose': round(df_KR['Adj Close'][i].iloc[0], 2)}

        indices.append(data)

    csi300 = yf.Ticker("000300.SS").stats()["price"]["regularMarketPrice"]
    data = {'name': 'CSI 300 Index', 'nameKR': '상하이&선전 300', 'symbol': "000300.SS", 'adjclose': round(csi300, 2)}
    indices.append(data)

    hsi = yf.Ticker("^HSI").stats()["price"]["regularMarketPrice"]
    data = {'name': 'HANG SENG INDEX', 'nameKR': '항셍 종합지수', 'symbol': "^HSI", 'adjclose': round(hsi, 2)}
    indices.append(data)

    return HttpResponse(json_util.dumps(indices, ensure_ascii=False), content_type="application/json;  charset=utf-8")

@csrf_exempt
def futures(request):
    futures = []
    futureSymbolText = ""
    futureSymbolText2 = ""

    symbols = ['CL=F', 'BZ=F', 'RB=F', 'NG=F', 'HO=F', 'GC=F', 'SI=F', 'HG=F', 'PL=F', 'PA=F', 'ALI=F', 'ZC=F', 'ZW=F', 'ZO=F', 'ZR=F', 'ZS=F', 'ZM=F', 'ZL=F', 'CC=F', 'KC=F', 'SB=F', 'OJ=F', 'CT=F', 'LBS=F']
    symbols2 = ['CU=F', 'LE=F', 'GF=F', 'HE=F']

    for i in symbols:
        futureSymbolText += f"{i} "

    for i in symbols2:
        futureSymbolText2 += f"{i} "

    date = datetime.today().strftime('%Y-%m-%d')
    df_futures = yf.download(futureSymbolText[0:-1], date).reset_index(drop=True)
    df_futures2 = yf.download(futureSymbolText2[0:-1], date).reset_index(drop=True)

    for i in symbols:
        if i == "CL=F":
            data = {"name": "Crude Oil", "nameKR": "WTI유" , "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "BZ=F":
            data = {"name": "Brent Oil", "nameKR": "브렌트유" ,  "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "RB=F":
            data = {"name": "RBOB Gasoline", "nameKR": "가솔린 RBOB" ,  "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "NG=F":
            data = {"name": "Natuaral Gas", "nameKR": "천연가스" ,  "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "HO=F":
            data = {"name": "Heating oil", "nameKR": "난방유" ,  "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "GC=F":
            data = {"name": "Gold", "nameKR": "금" , "symbol": i, "unit": "USD/t oz.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "SI=F":
            data = {"name": "Silver", "nameKR": "은" ,  "symbol": i, "unit": "USD/t oz.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "HG=F":
            data = {"name": "Copper", "nameKR": "구리" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "PL=F":
            data = {"name": "Platinum", "nameKR": "플래티넘" ,  "symbol": i, "unit": "USD/t oz.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "PA=F":
            data = {"name": "Palladium", "nameKR": "팔라듐" ,  "symbol": i, "unit": "USD/t oz.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "ALI=F":
            data = {"name": "Aluminum", "nameKR": "알루미늄" ,  "symbol": i, "unit": "USD/MT", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "ZC=F":
            data = {"name": "Corn", "nameKR": "옥수수" , "symbol": i, "unit": "USd/bu.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZW=F":
            data = {"name": "Wheat", "nameKR": "밀" ,  "symbol": i, "unit": "USd/bu.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZO=F":
            data = {"name": "Oats", "nameKR": "귀리" ,  "symbol": i, "unit": "USd/bu.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZR=F":
            data = {"name": "Rough Rice", "nameKR": "쌀" ,  "symbol": i, "unit": "USD/cwt", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZS=F":
            data = {"name": "Soybean", "nameKR": "대두" ,  "symbol": i, "unit": "USd/bu.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZM=F":
            data = {"name": "Soybean Meal", "nameKR": "대두박" ,  "symbol": i, "unit": "USD/T.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZL=F":
            data = {"name": "Soybeam Oil", "nameKR": "대두유" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "CC=F":
            data = {"name": "Cocoa", "nameKR": "코코아" , "symbol": i, "unit": "USD/MT", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "KC=F":
            data = {"name": "Coffee", "nameKR": "커피" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "SB=F":
            data = {"name": "Sugar", "nameKR": "설탕" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "OJ=F":
            data = {"name": "Orange Juice", "nameKR": "오렌지쥬스" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "CT=F":
            data = {"name": "Cotton", "nameKR": "면화" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "LBS=F":
            data = {"name": "Lumber", "nameKR": "원목" ,  "symbol": i, "unit": "USD/1000 board feet", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}

        futures.append(data)

    for j in symbols2:
        if j == "CU=F":
            data = {"name": "Ethanol", "nameKR": "에탄올" ,  "symbol": j, "unit": "USD/gal.", "regularMarketPrice": df_futures2['Adj Close'][j].iloc[0], "type": "soft"}
        elif j == "LE=F":
            data = {"name": "Live Cattle", "nameKR": "생우" , "symbol": j, "unit": "USd/lb.", "regularMarketPrice": df_futures2['Adj Close'][j].iloc[0], "type": "livestock"}
        elif j == "GF=F":
            data = {"name": "Feeder Cattle", "nameKR": "육우" ,  "symbol": j, "unit": "USd/lb.", "regularMarketPrice": df_futures2['Adj Close'][j].iloc[0], "type": "livestock"}
        elif j == "HE=F":
            data = {"name": "Lean Hogs", "nameKR": "돈육" ,  "symbol": j, "unit": "USd/lb.", "regularMarketPrice": df_futures2['Adj Close'][j].iloc[0], "type": "livestock"}
        futures.append(data)

    return HttpResponse(json_util.dumps(futures, ensure_ascii=False), content_type="application/json;  charset=utf-8")
        

@csrf_exempt
def indicesChosen(request):
    indices = ['^DJI', '^IXIC', '^GSPC']
    indicesResult = []
    indicesText = ""

    for i in indices:
        indicesText += f"{i} "

    date = datetime.today().strftime('%Y-%m-%d')
    df = yf.download(indicesText[0:-1], date).reset_index(drop=True)

    for i in indices:
        if i == "^DJI":
            data = {'name': 'Dow Jones Composite', 'nameKR': '다우존스 종합지수', 'symbol': i, 'adjclose': round(df['Adj Close'][i].iloc[0], 2)}
        elif i == "^IXIC":
            data = {'name': 'Nasdaq Composite', 'nameKR': '나스닥 종합지수', 'symbol': i, 'adjclose': round(df['Adj Close'][i].iloc[0], 2)}
        elif i == "^GSPC":
            data = {'name': 'S&P500', 'nameKR': 'S&P500', 'symbol': i, 'adjclose': round(df['Adj Close'][i].iloc[0], 2)}

        indicesResult.append(data)

    return HttpResponse(json_util.dumps(indicesResult, ensure_ascii=False), content_type="application/json;  charset=utf-8")