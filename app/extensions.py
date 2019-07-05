from flask_pymongo import PyMongo
from datetime import date, datetime

mongo = PyMongo()

def add_usr(personID, displayName, access_token, token_expires, refresh_token, refresh_expires):
    user_collection = mongo.db.users
    user = user_collection.find_one({'person_ID' : personID})
    if user is None:
        user_collection.insert({'person_ID' : personID, 'name' : displayName, 'access_token' : access_token, 'access_expdate' : token_expires, 'refresh_token' : refresh_token, 'refresh_expdate' : refresh_expires})
        result = "user added"
    else:
        result = user["name"] + " - user already exists"
    return result

def get_user(person_ID):
    user_collection = mongo.db.users 
    mongo_user = user_collection.find_one({'person_ID' : person_ID})
    user = {}
    user['access_token'] = mongo_user["access_token"]
    user['name'] = mongo_user["name"]
    return user

def get_OOO(person_ID):
    user_collection = mongo.db.users 
    mongo_user = user_collection.find_one({'person_ID' : person_ID})
    OOO = {}
    try:
        OOO['end_date'] = mongo_user["end_date"]
        OOO['message'] = mongo_user["message"]
        OOO['OOO_enabled'] = mongo_user["OOO_enabled"]
        OOO['access_token'] = mongo_user["access_token"]
        OOO['webhookID'] = mongo_user["webhookID"]
    except:
        print ("no OOO data")
    return OOO

def update_OOO(person_ID, message_text, endDate, webhook_ID, OOO_enabled):
    user_collection = mongo.db.users 
    user_collection.update({'person_ID' : person_ID}, {"$set":{"message" : message_text, "end_date" : endDate, "webhookID" : webhook_ID, "OOO_enabled" : OOO_enabled}})
    return ''