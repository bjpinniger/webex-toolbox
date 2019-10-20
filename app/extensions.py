from flask_pymongo import PyMongo
from flask import jsonify
from datetime import date, datetime, timedelta
import phonenumbers
from phonenumbers import timezone, geocoder
import pytz
import json
from simplecrypt import encrypt, decrypt
from base64 import b64encode, b64decode
from config import Config

ENCRYPT_PASS = Config.ENCRYPT_PASS
webex_admin = Config.webex_admin
webex_pwd = Config.webex_pwd
webex_site = Config.webex_site

mongo = PyMongo()

def add_usr(personID, displayName, access_token, token_expires, refresh_token, refresh_expires):
    user_collection = mongo.db.users
    user = user_collection.find_one({'person_ID' : personID})
    if user is None:
        user_collection.insert({'person_ID' : personID, 'name' : displayName, 'access_token' : access_token, 'access_expdate' : token_expires, 'refresh_token' : refresh_token, 'refresh_expdate' : refresh_expires})
        result = "user added"
    else:
        exp_date = user["access_expdate"]
        if exp_date <= datetime.now():
            user_collection.update({'person_ID' : personID}, {"$set":{'access_token' : access_token, 'access_expdate' : token_expires, 'refresh_token' : refresh_token, 'refresh_expdate' : refresh_expires}})
        print ("Access Token Update Successfull")
        result = user["name"] + " - user already exists"
    return result

def get_user(person_ID):
    user_collection = mongo.db.users 
    mongo_user = user_collection.find_one({'person_ID' : person_ID})
    user = {}
    try:
        user['access_token'] = mongo_user["access_token"]
        user['name'] = mongo_user["name"]
        result = "success"
    except Exception as e:
        print ("Exception: " + str(e))
        result = "no user data"
    return result, user

def get_OOO(person_ID):
    user_collection = mongo.db.users 
    mongo_user = user_collection.find_one({'person_ID' : person_ID})
    OOO = {}
    try:
        OOO['end_date'] = mongo_user["end_date"]
        OOO['country'] = mongo_user["country"]
        OOO['message'] = mongo_user["message"]
        OOO['OOO_enabled'] = mongo_user["OOO_enabled"]
        OOO['access_token'] = mongo_user["access_token"]
        OOO['webhookID_D'] = mongo_user["webhookID"]["direct"]
        OOO['webhookID_M'] = mongo_user["webhookID"]["mentions"]
        OOO['Direct'] = eval("len(OOO['webhookID_D']) > 0")
        OOO['Mentions'] = eval("len(OOO['webhookID_M']) > 0")
        OOO['TZ_Name'] = mongo_user["TZ"]
        result = "success"
    except Exception as e:
        print ("Exception: " + str(e))
        result = "no OOO data"
    return result, OOO

def update_OOO(person_ID, message_text, endDate, country, webhook_ID_D, webhook_ID_M, OOO_enabled, TZ_Name):
    try:
        user_collection = mongo.db.users
        if message_text == '':
            user_collection.update({'person_ID' : person_ID}, {"$set":{"end_date" : endDate, "TZ" : TZ_Name}})
        else:
            user_collection.update({'person_ID' : person_ID}, {"$set":{"message" : message_text, "end_date" : endDate, "country" : country, "TZ" : TZ_Name, "webhookID.direct" : webhook_ID_D, "webhookID.mentions" : webhook_ID_M, "OOO_enabled" : OOO_enabled}})
        result = "Update successful"
    except Exception as e:
        print ("Exception: " + str(e))
        result = "Update Failed"
    return result

def webex_settings(person_ID, site_name, user_email, user_pwd):
    encoded_pwd = encrypt_pwd(user_pwd)
    try:
        user_collection = mongo.db.users 
        user_collection.update({'person_ID' : person_ID}, {"$set":{"webex.site_name" : site_name, "webex.user_email" : user_email, "webex.user_pwd" : encoded_pwd}})
        result = "Update Successfull"
    except:
        result = "Update Failed"
    return result

def get_webex_settings(person_ID):
    user_collection = mongo.db.users 
    mongo_user = user_collection.find_one({'person_ID' : person_ID})
    webex_settings = {}
    try:
        webex_settings['site_name'] = mongo_user["webex"]["site_name"]
        webex_settings['user_email'] = mongo_user["webex"]["user_email"]
        decoded_pwd = decrypt_pwd(mongo_user["webex"]["user_pwd"])
        webex_settings['user_pwd'] = decoded_pwd.decode('utf-8')
    except Exception as e:
        webex_settings['site_name'] = webex_site
        webex_settings['user_email'] = webex_admin
        webex_settings['user_pwd'] = webex_pwd
        print ("Exception: " + str(e))
        print ("user has no webex settings")
    return webex_settings

def get_countries():
    Country_Array = []
    for country in pytz.country_timezones:
        countries = {}
        countries['title'] = pytz.country_names[country]
        countries['value'] = country
        Country_Array.append(countries)
    Countries_Array = sorted(Country_Array, key = lambda i: i['title'])
    return Countries_Array

def get_timezones(country):
    TZ_Array = []
    for TZ in pytz.country_timezones[country]:
        timezones = {}
        timezones['title'] = TZ
        timezones['value'] = TZ
        TZ_Array.append(timezones)
    return TZ_Array

def get_TZ_fromPhone(phone_num):
    x = phonenumbers.parse(phone_num, None)
    TZ = timezone.time_zones_for_number(x)
    country = geocoder.region_code_for_number(x)
    return TZ[0], country

def encrypt_pwd(pwd):
    cipher = encrypt(ENCRYPT_PASS, pwd)
    encoded_pwd = b64encode(cipher)
    return encoded_pwd

def decrypt_pwd(encoded_pwd):
    cipher = b64decode(encoded_pwd)
    decoded_pwd = decrypt(ENCRYPT_PASS, cipher)
    return decoded_pwd

def update_UTC(TZ_Name, original_date):
    offset = datetime.now(pytz.timezone(TZ_Name))
    utc_offset = offset.utcoffset().total_seconds()/60
    UTC_Date = original_date - timedelta(minutes=int(utc_offset))
    return UTC_Date

def update_local(TZ_Name, original_date):
    offset = datetime.now(pytz.timezone(TZ_Name))
    utc_offset = offset.utcoffset().total_seconds()/60
    Local_Date = original_date + timedelta(minutes=int(utc_offset))
    return Local_Date