
import pymongo
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

client = pymongo.MongoClient('mongodb+srv://alaxhenry:Tmdcjdahzk123@alaxhenry.3bowh.mongodb.net/?retryWrites=true&w=majority')
db = client['wallboy_db']
ownAssetCol = db["ownAsset"]

userInfoCol = db["userInfo"]
ownStockCol = db["ownStock"]

@csrf_exempt
def my_scheduled_job():
    for x in userInfoCol.find():
        total = 0

        for y in ownStockCol.find({'owner': x["id"]}):
            print(y)
            
            sum = float(y["price"]) * float(y["quantity"])
            total += sum

        data = {'id': x["id"], 'cash': x["cash"], 'stockValue': str(total), 'updatedAt': datetime.now()}
        ownAssetCol.insert_one(data)