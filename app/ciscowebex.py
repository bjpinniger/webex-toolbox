import requests
import json
from datetime import date, datetime, timedelta
from webexteamssdk import WebexTeamsAPI, ApiError
from config import Config
from app.extensions import get_countries, get_timezones, update_OOO, update_local, update_UTC, get_TZ_fromPhone

BOT_Token = Config.BOT_TOKEN

def get_tokens(clientID, secretID, code, redirectURI):
    """Gets access token and refresh token"""
    url = "https://api.ciscospark.com/v1/access_token"
    headers = {'accept':'application/json','content-type':'application/x-www-form-urlencoded'}
    payload = ("grant_type=authorization_code&client_id={0}&client_secret={1}&"
                    "code={2}&redirect_uri={3}").format(clientID, secretID, code, redirectURI)
    req = requests.post(url=url, data=payload, headers=headers)
    results = json.loads(req.text)
    access_token = results["access_token"]
    expires_in = results["expires_in"]
    refresh_token = results["refresh_token"]
    refresh_token_expires_in = results["refresh_token_expires_in"]
    return access_token, expires_in, refresh_token, refresh_token_expires_in

def get_oauthuser_info(access_token):
    """Retreives OAuth user's details."""
    url = "https://api.ciscospark.com/v1/people/me"
    headers = {'accept':'application/json','Content-Type':'application/json','Authorization': 'Bearer '+ access_token}
    req = requests.get(url=url, headers=headers)
    results = json.loads(req.text)
    personID = results["id"]
    emailID = results["emails"][0]
    displayName = results["displayName"]
    status = results["status"]
    phone_nums = []
    try:
        phone_nums = [phone["value"] for phone in results["phoneNumbers"] if phone["type"] == "work"]
    except:
        result = "failure"
    return personID, emailID, displayName, status, phone_nums

def get_rooms(user_token, person_ID, room_filter):
    api = WebexTeamsAPI(access_token=user_token) 
    rooms = api.rooms.list(type='group', sortBy='lastactivity')
    if room_filter == "creator":
        room_list = [(room.id,room.title) for room in rooms if room.creatorId == person_ID]
    else:
        room_list = [(room.id,room.title) for room in rooms]
    return room_list

def add_users(user_token, email, spaceId):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        api.memberships.create(roomId=spaceId, personEmail=email)
        result = "Success"
    except ApiError as error:
        try:
            api.rooms.get(roomId=spaceId)
            memberships = api.memberships.list(roomId=spaceId)
            for membership in memberships:
                if membership.personEmail == email:
                    result = "User already exists in space"
                    break
                else:
                    result = "Error: There was a problem addding this user."
        except ApiError as error:
            result = "Error: There was a problem adding users to this space."
    return result

def create_space(user_token, spaceName):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        room = api.rooms.create(title=spaceName)
        roomId=room.id
        result = "Success"
    except ApiError as error:
        result = "There was a problem creating the space."
    return result, roomId

def delete_space(user_token, roomId):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        room = api.rooms.delete(roomId)
        result = "Deleted"
    except ApiError as error:
        result = "There was a problem deleting the space."
    return result

def leave_space(user_token, roomId, personID):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        memberships = api.memberships.list(roomId=roomId, personId=personID)
        print (memberships)
        for membership in memberships:
            membership_id = membership.id
            print (membership_id)
            api.memberships.delete(membership_id)
        result = "Removed"
    except ApiError as error:
        result = "There was a problem deleting the membership."
    return result

def get_refresh_token(user_token, clientID, secretID, refresh_token):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        refresh = api.access_tokens.refresh(client_id=clientID, client_secret=secretID, refresh_token=refresh_token)
        access_token = refresh.access_token
        expires_in = refresh.expires_in
        new_refresh_token = refresh.refresh_token
        refresh_token_expires_in = refresh.refresh_token_expires_in
        result = "Success"
    except ApiError as error:
        result = "There was a problem refreshing the token: " + str(error)
    return result, access_token, expires_in, new_refresh_token, refresh_token_expires_in

def send_message(user_token, spaceId, message):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        sendmsg = api.messages.create(roomId=spaceId,text=message)
        result = "Success"
    except ApiError as error:
        result = "There was a problem sending the message."
    return result

def get_message(user_token, messageId):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        getmsg = api.messages.get(messageId)
        message_text = getmsg.text
        result = "Success"
    except ApiError as error:
        result = "There was a problem getting the message."
    return result, message_text

def create_webhook(user_token, webhookURI, webhookID, webhookType):
    api = WebexTeamsAPI(access_token=user_token)
    if webhookID is None or webhookID == '':
        try:
            if webhookType == "direct":
                webhook = api.webhooks.create(name="OOO-Assistant Webhook",targetUrl=webhookURI,resource="messages", event="created", filter="roomType=direct")
            else:
                webhook = api.webhooks.create(name="OOO-Assistant Webhook",targetUrl=webhookURI,resource="messages", event="created", filter="mentionedPeople=me")
            webhookID = webhook.id
            result = "Webhook created"
        except ApiError as error:
            result = "There was a problem creating the webhook."
    else:
        try:
            get_webhook = api.webhooks.get(webhookID) 
            result = ("Webhook is " + get_webhook.status)
        except ApiError as error:
            print ("There was a problem getting the webhook, it was probably deleted.")
            try:
                if webhookType == "direct":
                    webhook = api.webhooks.create(name="OOO-Assistant Webhook",targetUrl=webhookURI,resource="messages", event="created", filter="roomType=direct")
                else:
                    webhook = api.webhooks.create(name="OOO-Assistant Webhook",targetUrl=webhookURI,resource="messages", event="created", filter="mentionedPeople=me")
                webhookID = webhook.id
                result = "Webhook created"
            except ApiError as error:
                result = "There was a problem creating the webhook."
    return result, webhookID

def delete_webhook(user_token, webhookID):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        webhook = api.webhooks.delete(webhookId=webhookID)
        result = "Webhook deleted"
    except ApiError as error:
        result = "There was a problem deleting the webhook."
    return result

def list_webhooks(user_token):
    api = WebexTeamsAPI(access_token=user_token)
    webhook_list = []
    try:
        webhooks = api.webhooks.list()
        webhook_list = [(webhook.id,webhook.filter,webhook.created) for webhook in webhooks if webhook.name == "OOO-Assistant Webhook"]
        result = "Webhook list retrieved"
    except ApiError as error:
        result = "There was a problem retrieving the webhook list: " + str(error)
    return result, webhook_list

def send_directmessage(user_token, personID, message, markdown):
    if user_token == '':
        user_token = BOT_Token
    api = WebexTeamsAPI(access_token=user_token)
    try:
        if markdown == '':
            sendmsg = api.messages.create(toPersonId=personID,text=message)
        else:
            sendmsg = api.messages.create(toPersonId=personID, markdown=markdown)
        result = "Success"
    except ApiError as error:
        result = "There was a problem sending the message."
    return result

def OOO_webhook(person_ID, accesstoken, webhookURI, webhookID_D, webhookID_M, message_text, endDate, country, OOO_enabled, Direct, Mentions, TZ_Name):
    print ("enabled: " + str(OOO_enabled))
    datetime_object = datetime.strptime(endDate, '%Y-%m-%d %H:%M')
    if len(TZ_Name) > 0:
        datetime_object = update_UTC(TZ_Name, datetime_object)
    webhook_ID_D = ""
    webhook_ID_M = ""
    if Direct:
        webhookType = "direct"
        result, webhook_ID_D = create_webhook(accesstoken, webhookURI, webhookID_D, webhookType)
        print ("Direct " + result)
    else:
        if len(webhookID_D) > 0:
            result = delete_webhook(accesstoken, webhookID_D)
            print ("Direct " + result)
    if Mentions:
        webhookType = "mentions"
        result, webhook_ID_M = create_webhook(accesstoken, webhookURI, webhookID_M, webhookType)
        print ("Mentions " + result)
    else:
        if len(webhookID_M) > 0:
            result = delete_webhook(accesstoken, webhookID_M)
            print ("Mentions " + result)
    result = update_OOO(person_ID, message_text, datetime_object, country, webhook_ID_D, webhook_ID_M, OOO_enabled, TZ_Name)
    return ''

def get_messages(user_token, spaceID, personID, getList):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        msgs = api.messages.list(roomId=spaceID,max=50)
        msgArray = []
        if getList:
            msgArray = [(msg.id,msg.text) for msg in msgs if msg.personId == personID]
        else:
            for msg in msgs:
                if msg.personId == personID:
                    msgObj = {}
                    msgObj['id'] = msg.id
                    msgObj['msgtxt'] = msg.text
                    msgArray.append(msgObj)
        result = "Success"
    except ApiError as error:
        result = "There was a problem getting the messages."
    return result, msgArray

def delete_message(user_token, msgID):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        msgs = api.messages.delete(msgID)
        result = "Deleted"
    except ApiError as error:
        result = "There was a problem deleting the message."
    return result

def get_member_details(user_token, spaceID):
    api = WebexTeamsAPI(access_token=user_token)
    Member_Array = []
    try:
        members = api.memberships.list(roomId=spaceID,max=1000)
        for member in members:
            details = {}
            details['DisplayName'] = member.personDisplayName
            details['Email'] = member.personEmail
            Member_Array.append(details)
        Members_Array = sorted(Member_Array, key = lambda i: i['DisplayName'])
        result = "Success"
    except ApiError as error:
        Members_Array = []
        result = "There was a problem getting the memberships."
    return result, Members_Array

def send_card(personID, displayName, message, Text_EndDate, Card_EndDate):
    url = "https://api.ciscospark.com/v1/messages"

    payload = {
        "toPersonId": "%s" % personID,
        "text": "Out of Office Message from %s: %s %s" % (displayName, message, Text_EndDate),
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "Out of Office Message from %s:" % displayName,
                            "weight": "bolder",
                            "size": "large"
                        },
                        {
                            "type": "TextBlock",
                            "text": "%s {{DATE(%s, SHORT)}} at {{TIME(%s)}}" % (message, Card_EndDate, Card_EndDate),
                            "size": "large",
                            "wrap": True
                        }
                    ]
                }
            }
        ]
    }

    headers = {
        'Authorization': "Bearer %s" % BOT_Token,
        'Content-Type': "application/json",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': "api.ciscospark.com",
        'accept-encoding': "gzip, deflate",
        'content-length': "1068",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
        }
    try:
        response = requests.post(url, json=payload, headers=headers)
        results = json.loads(response.text)
        result = "Card sent"
    except:
        result = "There was a problem sending the card."
    return result

def set_OOO(personID, OOO, access_token):
    url = "https://api.ciscospark.com/v1/messages"
    Country_Array = get_countries()
    try:
        message = OOO['message']
        TZ_Name = OOO['TZ_Name']
        TZ_Display = True
        TZ_Text = "Time Zone: " + TZ_Name
        Country_Text = "Change Country"
        end_date = OOO['end_date']
        Local_Date = update_local(TZ_Name, end_date)
        Str_EndDate = datetime.strftime(Local_Date, '%Y-%m-%d')
        Str_EndTime = datetime.strftime(Local_Date, '%H:%M')
        country = OOO['country']
        TZ_Array = get_timezones(country)
        OOO_enabled = str(OOO['OOO_enabled'])
        Direct = str(OOO['Direct'])
        Mentions = str(OOO['Mentions'])
    except Exception as e:
        print ("Exception: " + str(e))
        message = "I'm out of the office"
        Str_EndDate = datetime.strftime(datetime.utcnow(), '%Y-%m-%d')
        Str_EndTime = "17:00"
        OOO_enabled = "True"
        Direct = "True"
        Mentions = "True"
        personID, emailID, displayName, status, phone_nums = get_oauthuser_info(access_token)
        try:
            phone_num = phone_nums[0]
            TZ_Name, country = get_TZ_fromPhone(phone_num)
            TZ_Array = get_timezones(country)
            Country_Text = "Change Country"
            TZ_Display = True
            TZ_Text = "Time Zone: " + TZ_Name
        except:
            TZ_Display = False
            TZ_Text = "Time Zone Not Available"
            Country_Text = "Select Country"
            country = ""
            TZ_Array = []
            TZ_Name = ""

    payload = {
        "toPersonId": "%s" % personID,
        "markdown": "This message uses Webex Teams Cards. Currently, this can only be viewed in the [browser client](https://teams.webex.com)",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [
                        {
                        "type": "Container",
                        "items": [
                            {
                            "type": "TextBlock",
                            "text": "Message"
                            },
                            {
                            "type": "Input.Text",
                            "id": "message",
                            "value": message,
                            "maxLength": 500,
                            "isMultiline": True
                            },
                            {
                            "type": "TextBlock",
                            "text": "End Date/Time"
                            },
                            {
                            "type": "Input.Date",
                            "id": "end_date",
                            "value": Str_EndDate
                            },
                            {
                            "type": "Input.Time",
                            "id": "time",
                            "value": Str_EndTime
                            }
                        ]
                        },
                        {
                        "type": "Container",
                        "style": "default",
                        "items": [
                            {
                            "type": "ColumnSet",
                            "columns": [
                                {
                                "type": "Column",
                                "items": [
                                            {
                                            "type": "Input.Toggle",
                                            "id": "enabled",
                                            "title": "Enabled",
                                            "value": OOO_enabled,
                                            "valueOn": "True",
                                            "valueOff": "False",
                                            "color": "default"
                                            }
                                        ],
                                    "width": "auto"
                                },
                                {
                                "type": "Column",
                                "items": [
                                            {
                                            "type": "Input.Toggle",
                                            "id": "direct",
                                            "title": "Direct",
                                            "value": Direct,
                                            "valueOn": "True",
                                            "valueOff": "False",
                                            "color": "default"
                                            }
                                        ],
                                    "width": "auto"
                                },
                                {
                                "type": "Column",
                                "items": [
                                            {
                                            "type": "Input.Toggle",
                                            "id": "mentions",
                                            "title": "Mentions",
                                            "value": Mentions,
                                            "valueOn": "True",
                                            "valueOff": "False",
                                            "color": "default"
                                            }
                                        ],
                                    "width": "auto"
                                }
                            ]
                        }
                    ]
                    },
                    {
                    "type": "Container",
                    "items": [
                            {
                            "type": "TextBlock",
                            "text": Country_Text
                            },
                            {
                            "type": "Input.ChoiceSet",
                            "id": "country",
                            "style": "compact",
                            "value": country,
                            "choices": Country_Array
                            },
                            {
                            "type": "TextBlock",
                            "text": TZ_Text
                            }
                    ]
                    }
                    ],
                    "actions": [
                    {
                        "type": "Action.ShowCard",
                        "title": "Change Time Zone",
                        "card": {
                            "type": "AdaptiveCard",
                            "body": [
                                {
                                "type": "Input.ChoiceSet",
                                "id": "timezone",
                                "style": "compact",
                                "value": TZ_Name,
                                "choices": TZ_Array
                                }
                            ],
                        }
                    },
                            {
                            "type": "Action.Submit",
                            "title": "Submit",
                            "data": {
                                "card": "set_OOO"
                            }
                            }
                        ]
                        }
                    
                }
            
        ]
    }

    headers = {
        'Authorization': "Bearer %s" % BOT_Token,
        'Content-Type': "application/json",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': "api.ciscospark.com",
        'accept-encoding': "gzip, deflate",
        'content-length': "1068",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
        }
    try:
        response = requests.post(url, json=payload, headers=headers)
        results = json.loads(response.text)
        result = "Card sent"
    except:
        result = "There was a problem sending the card."
    return result

def get_attachment(data_id):

    url = "https://api.ciscospark.com/v1/attachment/actions/%s" % data_id

    headers = {
        'Authorization': "Bearer %s" % BOT_Token,
        'Content-Type': "application/json",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': "api.ciscospark.com",
        'accept-encoding': "gzip, deflate",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
        }

    response = requests.request("GET", url, headers=headers)
    json_data = json.loads(response.text)
    return json_data

def set_TimeZone(personID, country):
    url = "https://api.ciscospark.com/v1/messages"

    TZ_Array = get_timezones(country)

    payload = {
        "toPersonId": "%s" % personID,
        "markdown": "This message uses Webex Teams Cards. Currently, this can only be viewed in the [browser client](https://teams.webex.com)",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [
                        {
                        "type": "TextBlock",
                        "text": "Select TimeZone"
                        },
                        {
                        "type": "Input.ChoiceSet",
                        "id": "timezone",
                        "style": "compact",
                        "value": "1",
                        "choices": TZ_Array
                        }
                    ],
                    "actions": [
                        {
                        "type": "Action.Submit",
                        "title": "Submit",
                        "data": {
                            "card": "set_TZ"
                        }
                        }
                    ]
                }
            }
        ]
    }

    headers = {
        'Authorization': "Bearer %s" % BOT_Token,
        'Content-Type': "application/json",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': "api.ciscospark.com",
        'accept-encoding': "gzip, deflate",
        'content-length': "1068",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
        }
    try:
        response = requests.post(url, json=payload, headers=headers)
        results = json.loads(response.text)
        result = "Card sent"
    except:
        result = "There was a problem sending the card."
    return result

def confirm_TimeZone(personID, TZ):
    url = "https://api.ciscospark.com/v1/messages"

    payload = {
        "toPersonId": "%s" % personID,
        "markdown": "This message uses Webex Teams Cards. Currently, this can only be viewed in the [browser client](https://teams.webex.com)",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [
                        {
                        "type": "TextBlock",
                        "text": "Is this your current TimeZone?"
                        },
                        {
                            "type": "TextBlock",
                            "text": TZ,
                            "weight": "bolder",
                            "size": "large"
                        }
                    ],
                    "actions": [
                        {
                        "type": "Action.Submit",
                        "title": "Yes",
                        "data": {
                            "card": "confirm_TZ",
                            "response": "yes",
                            "TZ": TZ
                        }
                        },
                        {
                        "type": "Action.Submit",
                        "title": "No",
                        "data": {
                            "card": "confirm_TZ",
                            "response": "no",
                            "TZ": TZ
                        }
                        }
                    ]
                }
            }
        ]
    }

    headers = {
        'Authorization': "Bearer %s" % BOT_Token,
        'Content-Type': "application/json",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': "api.ciscospark.com",
        'accept-encoding': "gzip, deflate",
        'content-length': "1068",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
        }
    try:
        response = requests.post(url, json=payload, headers=headers)
        results = json.loads(response.text)
        result = "Card sent"
    except:
        result = "There was a problem sending the card."
    return result