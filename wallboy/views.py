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
from datetime import datetime, timedelta
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

# Stock ?????? ??????
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
        print("???????????? ??????")
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
            print("??????????????? ????????? ?????? ????????? ??? ????????????.")
            success = "{upload : fail}"
    else:
        print("????????? ?????? ????????? ????????????")
        success = "{upload : fail}"

    return HttpResponse(json.dumps(success), content_type="application/json")

@csrf_exempt
def userRegisterAPI(request, id, email):
    
    result = userInfoCol.find_one({"id": id})

    if result == None and request.method == 'POST':
        
        data = {'id': id, 'createdAt': datetime.now(), 'email': email, 'nickname': "Wallboy", 'cash': '10000', 'imageURL': "https://cdn.vectorstock.com/i/preview-1x/22/05/male-profile-picture-vector-1862205.jpg"}
        userInfoCol.insert_one(data)

        success = "{upload : ???????????? ??????!}"
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
        print("request.data??? ??????: ",type(request.data))
        print("request.FILES: ",request.FILES)
        print("request.FILES??? ??????: ",type(request.FILES))
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

        success = "[{upload : ?????? ?????? ??????!}]"
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
            data = {'name': 'Dow Jones Composite', 'nameKR': '???????????? ????????????', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        elif i == "^IXIC":
            data = {'name': 'Nasdaq Composite', 'nameKR': '????????? ????????????', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        elif i == "^GSPC":
            data = {'name': 'S&P500', 'nameKR': 'S&P500', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        elif i == "^VIX":
            data = {'name': 'CBOE Volatility Index', 'nameKR': 'VIX ??????', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        elif i == "^RUT":
            data = {'name': 'Russell 2000', 'nameKR': 'Russell 2000', 'symbol': i, 'adjclose': round(df_US['Adj Close'][i].iloc[0], 2)}
        
        indices.append(data)


    for i in indicesAsia:
        indicesAsiaText += f"{i} "

    date = datetime.today().strftime('%Y-%m-%d')
    df_KR = yf.download(indicesAsiaText[0:-1], date).reset_index(drop=True)

    for i in indicesAsia:
        if i == "^KS11":
            data = {'name': 'KOSPI Composite Index', 'nameKR': '????????? ????????????', 'symbol': i, 'adjclose': round(df_KR['Adj Close'][i].iloc[0], 2)}
        elif i == "^KQ11":
            data = {'name': 'Kosdaq Composite Index', 'nameKR': '????????? ????????????', 'symbol': i, 'adjclose': round(df_KR['Adj Close'][i].iloc[0], 2)}
        elif i == "^N225":
            data = {'name': 'Nikkei 225', 'nameKR': '????????? 225', 'symbol': i, 'adjclose': round(df_KR['Adj Close'][i].iloc[0], 2)}

        indices.append(data)

    csi300 = yf.Ticker("000300.SS").stats()["price"]["regularMarketPrice"]
    data = {'name': 'CSI 300 Index', 'nameKR': '?????????&?????? 300', 'symbol': "000300.SS", 'adjclose': round(csi300, 2)}
    indices.append(data)

    hsi = yf.Ticker("^HSI").stats()["price"]["regularMarketPrice"]
    data = {'name': 'HANG SENG INDEX', 'nameKR': '?????? ????????????', 'symbol': "^HSI", 'adjclose': round(hsi, 2)}
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
            data = {"name": "Crude Oil", "nameKR": "WTI???" , "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "BZ=F":
            data = {"name": "Brent Oil", "nameKR": "????????????" ,  "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "RB=F":
            data = {"name": "RBOB Gasoline", "nameKR": "????????? RBOB" ,  "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "NG=F":
            data = {"name": "Natuaral Gas", "nameKR": "????????????" ,  "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "HO=F":
            data = {"name": "Heating oil", "nameKR": "?????????" ,  "symbol": i, "unit": "USD/bbl.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "energy"}
        elif i == "GC=F":
            data = {"name": "Gold", "nameKR": "???" , "symbol": i, "unit": "USD/t oz.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "SI=F":
            data = {"name": "Silver", "nameKR": "???" ,  "symbol": i, "unit": "USD/t oz.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "HG=F":
            data = {"name": "Copper", "nameKR": "??????" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "PL=F":
            data = {"name": "Platinum", "nameKR": "????????????" ,  "symbol": i, "unit": "USD/t oz.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "PA=F":
            data = {"name": "Palladium", "nameKR": "?????????" ,  "symbol": i, "unit": "USD/t oz.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "ALI=F":
            data = {"name": "Aluminum", "nameKR": "????????????" ,  "symbol": i, "unit": "USD/MT", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "metal"}
        elif i == "ZC=F":
            data = {"name": "Corn", "nameKR": "?????????" , "symbol": i, "unit": "USd/bu.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZW=F":
            data = {"name": "Wheat", "nameKR": "???" ,  "symbol": i, "unit": "USd/bu.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZO=F":
            data = {"name": "Oats", "nameKR": "??????" ,  "symbol": i, "unit": "USd/bu.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZR=F":
            data = {"name": "Rough Rice", "nameKR": "???" ,  "symbol": i, "unit": "USD/cwt", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZS=F":
            data = {"name": "Soybean", "nameKR": "??????" ,  "symbol": i, "unit": "USd/bu.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZM=F":
            data = {"name": "Soybean Meal", "nameKR": "?????????" ,  "symbol": i, "unit": "USD/T.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "ZL=F":
            data = {"name": "Soybeam Oil", "nameKR": "?????????" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "grain"}
        elif i == "CC=F":
            data = {"name": "Cocoa", "nameKR": "?????????" , "symbol": i, "unit": "USD/MT", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "KC=F":
            data = {"name": "Coffee", "nameKR": "??????" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "SB=F":
            data = {"name": "Sugar", "nameKR": "??????" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "OJ=F":
            data = {"name": "Orange Juice", "nameKR": "???????????????" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "CT=F":
            data = {"name": "Cotton", "nameKR": "??????" ,  "symbol": i, "unit": "USd/lb.", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}
        elif i == "LBS=F":
            data = {"name": "Lumber", "nameKR": "??????" ,  "symbol": i, "unit": "USD/1000 board feet", "regularMarketPrice": df_futures['Adj Close'][i].iloc[0], "type": "soft"}

        futures.append(data)

    for j in symbols2:
        if j == "CU=F":
            data = {"name": "Ethanol", "nameKR": "?????????" ,  "symbol": j, "unit": "USD/gal.", "regularMarketPrice": df_futures2['Adj Close'][j].iloc[0], "type": "soft"}
        elif j == "LE=F":
            data = {"name": "Live Cattle", "nameKR": "??????" , "symbol": j, "unit": "USd/lb.", "regularMarketPrice": df_futures2['Adj Close'][j].iloc[0], "type": "livestock"}
        elif j == "GF=F":
            data = {"name": "Feeder Cattle", "nameKR": "??????" ,  "symbol": j, "unit": "USd/lb.", "regularMarketPrice": df_futures2['Adj Close'][j].iloc[0], "type": "livestock"}
        elif j == "HE=F":
            data = {"name": "Lean Hogs", "nameKR": "??????" ,  "symbol": j, "unit": "USd/lb.", "regularMarketPrice": df_futures2['Adj Close'][j].iloc[0], "type": "livestock"}
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
            data = {'name': 'Dow Jones Composite', 'nameKR': '???????????? ????????????', 'symbol': i, 'adjclose': round(df['Adj Close'][i].iloc[0], 2)}
        elif i == "^IXIC":
            data = {'name': 'Nasdaq Composite', 'nameKR': '????????? ????????????', 'symbol': i, 'adjclose': round(df['Adj Close'][i].iloc[0], 2)}
        elif i == "^GSPC":
            data = {'name': 'S&P500', 'nameKR': 'S&P500', 'symbol': i, 'adjclose': round(df['Adj Close'][i].iloc[0], 2)}

        indicesResult.append(data)

    return HttpResponse(json_util.dumps(indicesResult, ensure_ascii=False), content_type="application/json;  charset=utf-8")

@csrf_exempt
def singleIndex(request, symbol):
    print(symbol)
    date = datetime.today().strftime('%Y-%m-%d')
    index = []
    
    if symbol == "CL=F":
        crudeOil = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Crude Oil", "nameKR": "WTI???" , "symbol": symbol, "unit": "USD/bbl.", "regularMarketPrice": round(crudeOil, 2), "type": "energy"}
        index.append(data)
    elif symbol == "BZ=F":
        brentOil = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Brent Oil", "nameKR": "????????????" ,  "symbol": symbol, "unit": "USD/bbl.", "regularMarketPrice": round(brentOil, 2), "type": "energy"}
        index.append(data)
    elif symbol == "RB=F":
        gasoline = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "RBOB Gasoline", "nameKR": "????????? RBOB" ,  "symbol": symbol, "unit": "USD/bbl.", "regularMarketPrice": round(gasoline, 2), "type": "energy"}
        index.append(data)
    elif symbol == "NG=F":
        naturalGas = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Natuaral Gas", "nameKR": "????????????" ,  "symbol": symbol, "unit": "USD/bbl.", "regularMarketPrice": round(naturalGas, 2), "type": "energy"}
        index.append(data)
    elif symbol == "HO=F":
        heatingOil = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Heating oil", "nameKR": "?????????" ,  "symbol": symbol, "unit": "USD/bbl.", "regularMarketPrice": round(heatingOil, 2), "type": "energy"}
        index.append(data)
    elif symbol == "GC=F":
        gold = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Gold", "nameKR": "???" , "symbol": symbol, "unit": "USD/t oz.", "regularMarketPrice": round(gold, 2), "type": "metal"}
        index.append(data)
    elif symbol == "SI=F":
        silver = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Silver", "nameKR": "???" ,  "symbol": symbol, "unit": "USD/t oz.", "regularMarketPrice": round(silver, 2), "type": "metal"}
        index.append(data)
    elif symbol == "HG=F":
        copper = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Copper", "nameKR": "??????" ,  "symbol": symbol, "unit": "USd/lb.", "regularMarketPrice": round(copper, 2), "type": "metal"}
        index.append(data)
    elif symbol == "PL=F":
        platinum = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Platinum", "nameKR": "????????????" ,  "symbol": symbol, "unit": "USD/t oz.", "regularMarketPrice": round(platinum, 2), "type": "metal"}
        index.append(data)
    elif symbol == "PA=F":
        palladium = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Palladium", "nameKR": "?????????" ,  "symbol": symbol, "unit": "USD/t oz.", "regularMarketPrice": round(palladium, 2), "type": "metal"}
        index.append(data)
    elif symbol == "ALI=F":
        aluminum = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Aluminum", "nameKR": "????????????" ,  "symbol": symbol, "unit": "USD/MT", "regularMarketPrice": round(aluminum, 2), "type": "metal"}
        index.append(data)
    elif symbol == "ZC=F":
        corn = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Corn", "nameKR": "?????????" , "symbol": symbol, "unit": "USd/bu.", "regularMarketPrice": round(corn, 2), "type": "grain"}
        index.append(data)
    elif symbol == "ZW=F":
        wheat = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Wheat", "nameKR": "???" ,  "symbol": symbol, "unit": "USd/bu.", "regularMarketPrice": round(wheat, 2), "type": "grain"}
        index.append(data)
    elif symbol == "ZO=F":
        oats = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Oats", "nameKR": "??????" ,  "symbol": symbol, "unit": "USd/bu.", "regularMarketPrice": round(oats, 2), "type": "grain"}
        index.append(data)
    elif symbol == "ZR=F":
        roughRice = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Rough Rice", "nameKR": "???" ,  "symbol": symbol, "unit": "USD/cwt", "regularMarketPrice": round(roughRice, 2), "type": "grain"}
        index.append(data)
    elif symbol == "ZS=F":
        soybean = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Soybean", "nameKR": "??????" ,  "symbol": symbol, "unit": "USd/bu.", "regularMarketPrice": round(soybean, 2), "type": "grain"}
        index.append(data)
    elif symbol == "ZM=F":
        soybeanMeal = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Soybean Meal", "nameKR": "?????????" ,  "symbol": symbol, "unit": "USD/T.", "regularMarketPrice": round(soybeanMeal, 2), "type": "grain"}
        index.append(data)
    elif symbol == "ZL=F":
        soybeanOil = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Soybeam Oil", "nameKR": "?????????" ,  "symbol": symbol, "unit": "USd/lb.", "regularMarketPrice": round(soybeanOil, 2), "type": "grain"}
        index.append(data)
    elif symbol == "CC=F":
        cocoa = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Cocoa", "nameKR": "?????????" , "symbol": symbol, "unit": "USD/MT", "regularMarketPrice": round(cocoa, 2), "type": "soft"}
        index.append(data)
    elif symbol == "KC=F":
        coffee = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Coffee", "nameKR": "??????" ,  "symbol": symbol, "unit": "USd/lb.", "regularMarketPrice": round(coffee, 2), "type": "soft"}
        index.append(data)
    elif symbol == "SB=F":
        sugar = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Sugar", "nameKR": "??????" ,  "symbol": symbol, "unit": "USd/lb.", "regularMarketPrice": round(sugar, 2), "type": "soft"}
        index.append(data)
    elif symbol == "OJ=F":
        orangeJuice = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Orange Juice", "nameKR": "???????????????" ,  "symbol": symbol, "unit": "USd/lb.", "regularMarketPrice": round(orangeJuice, 2), "type": "soft"}
        index.append(data)
    elif symbol == "CT=F":
        cotton = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Cotton", "nameKR": "??????" ,  "symbol": symbol, "unit": "USd/lb.", "regularMarketPrice": round(cotton, 2), "type": "soft"}
        index.append(data)
    elif symbol == "LBS=F":
        lumber = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Lumber", "nameKR": "??????" ,  "symbol": symbol, "unit": "USD/1000 board feet", "regularMarketPrice": round(lumber, 2), "type": "soft"}
        index.append(data)
    elif symbol == "CU=F":
        ethanol = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Ethanol", "nameKR": "?????????" ,  "symbol": symbol, "unit": "USD/gal.", "regularMarketPrice": round(ethanol, 2), "type": "soft"}
        index.append(data)
    elif symbol == "LE=F":
        liveCattle = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Live Cattle", "nameKR": "??????" , "symbol": symbol, "unit": "USd/lb.", "regularMarketPrice": round(liveCattle, 2), "type": "livestock"}
        index.append(data)
    elif symbol == "GF=F":
        feederCattle = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Feeder Cattle", "nameKR": "??????" ,  "symbol": symbol, "unit": "USd/lb.", "regularMarketPrice": round(feederCattle, 2), "type": "livestock"}
        index.append(data)
    elif symbol == "HE=F":
        leanHogs = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {"name": "Lean Hogs", "nameKR": "??????" ,  "symbol": symbol, "unit": "USd/lb.", "regularMarketPrice": round(leanHogs, 2), "type": "livestock"}
        index.append(data)
    elif symbol == "^DJI":
        dowjones = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {'name': 'Dow Jones Composite', 'nameKR': '???????????? ????????????', 'symbol': symbol, "unit": "point", 'regularMarketPrice': round(dowjones, 2), "type": "index"}
        index.append(data)
    elif symbol == "^IXIC":
        nasdaqComposition = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {'name': 'Nasdaq Composite', 'nameKR': '????????? ????????????', 'symbol': symbol, "unit": "point", 'regularMarketPrice': round(nasdaqComposition, 2), "type": "index"}
        index.append(data)
    elif symbol == "^GSPC":
        sp500 = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {'name': 'S&P500', 'nameKR': 'S&P500', 'symbol': symbol, "unit": "point", 'regularMarketPrice': round(sp500, 2), "type": "index"}
        index.append(data)
    elif symbol == "^VIX":
        vix = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {'name': 'CBOE Volatility Index', 'nameKR': 'VIX ??????', 'symbol': symbol, "unit": "point", 'regularMarketPrice': round(vix, 2), "type": "index"}
        index.append(data)
    elif symbol == "^RUT":
        russell2000 = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {'name': 'Russell 2000', 'nameKR': 'Russell 2000', 'symbol': symbol, "unit": "point", 'regularMarketPrice': round(russell2000, 2), "type": "index"}
        index.append(data)
    elif symbol == "^KS11":
        kospi = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {'name': 'KOSPI Composite Index', 'nameKR': '????????? ????????????', 'symbol': symbol, "unit": "point", 'regularMarketPrice': round(kospi, 2), "type": "index"}
        index.append(data)
    elif symbol == "^KQ11":
        kosdaq = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {'name': 'Kosdaq Composite Index', 'nameKR': '????????? ????????????', 'symbol': symbol, "unit": "point", 'regularMarketPrice': round(kosdaq, 2), "type": "index"}
        index.append(data)
    elif symbol == "^N225":
        nikkei225 = yf.Ticker(symbol).stats()["price"]["regularMarketPrice"]
        data = {'name': 'Nikkei 225', 'nameKR': '????????? 225', 'symbol': symbol, "unit": "point", 'regularMarketPrice': round(nikkei225, 2), "type": "index"}
        index.append(data)
    elif symbol == "^HSI":
        hsi = yf.Ticker("^HSI").stats()["price"]["regularMarketPrice"]
        data = {'name': 'HANG SENG INDEX', 'nameKR': '?????? ????????????', 'symbol': "^HSI", "unit": "point", 'regularMarketPrice': round(hsi, 2), "type": "index"}
        index.append(data)
    elif symbol == "000300.SS":
        csi300 = yf.Ticker("000300.SS").stats()["price"]["regularMarketPrice"]
        data = {'name': 'CSI 300 Index', 'nameKR': '?????????&?????? 300', 'symbol': "000300.SS", "unit": "point", 'regularMarketPrice': round(csi300, 2), "type": "index"}
        index.append(data)

    return HttpResponse(json_util.dumps(index, ensure_ascii=False), content_type="application/json;  charset=utf-8")

@csrf_exempt
def indexPriceHistory(request, symbol):
    datebox = []
    prices = []
    priceHistory = []

    date = (datetime.now() - timedelta(days=31)).strftime('%Y-%m-%d')
    df = yf.download(symbol, date)

    for i in df.index:
        datebox.append(i.strftime('%Y-%m-%d'))

    for i in df["Adj Close"]:
        prices.append(i)

    for date, price in zip(datebox, prices):
        data =  {"date": date, "adjClose": price}
        priceHistory.append(data)
    return HttpResponse(json_util.dumps(priceHistory, ensure_ascii=False), content_type="application/json;  charset=utf-8")

@csrf_exempt
def indexChosenPeriodPriceHistory(request, symbol, period):
    datebox = []
    prices = []
    priceHistory = []

    print(symbol)
    print(period)

    if period == "1w":
        date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        df = yf.download(symbol, date)
    elif period == "1mo":
        date = (datetime.now() - timedelta(days=31)).strftime('%Y-%m-%d')
        df = yf.download(symbol, date)
    elif period == "3mo":
        date = (datetime.now() - timedelta(days=93)).strftime('%Y-%m-%d')
        df = yf.download(symbol, date)
    elif period == "6mo":
        date = (datetime.now() - timedelta(days=186)).strftime('%Y-%m-%d')
        df = yf.download(symbol, date)
    elif period == "1y":
        print(period)
        date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        df = yf.download(symbol, date)
    elif period == "3y":
        date = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
        df = yf.download(symbol, date)
    elif period == "5y":
        date = (datetime.now() - timedelta(days=1825)).strftime('%Y-%m-%d')
        df = yf.download(symbol, date)
    elif period == "all":
        df = yf.download(symbol)

    for i in df.index:
        datebox.append(i.strftime('%Y-%m-%d'))

    for i in df["Adj Close"]:
        prices.append(i)

    for date, price in zip(datebox, prices):
        data =  {"date": date, "adjClose": price}
        priceHistory.append(data)
    return HttpResponse(json_util.dumps(priceHistory, ensure_ascii=False), content_type="application/json;  charset=utf-8")

