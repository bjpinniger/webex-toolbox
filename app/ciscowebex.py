import requests
import json
from webexteamssdk import WebexTeamsAPI, ApiError


def get_tokens(clientID, secretID, code, redirectURI):
    """Gets access token and refresh token"""
    print ("code:", code)
    url = "https://api.ciscospark.com/v1/access_token"
    headers = {'accept':'application/json','content-type':'application/x-www-form-urlencoded'}
    payload = ("grant_type=authorization_code&client_id={0}&client_secret={1}&"
                    "code={2}&redirect_uri={3}").format(clientID, secretID, code, redirectURI)
    req = requests.post(url=url, data=payload, headers=headers)
    results = json.loads(req.text)
    print (results)
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
    return personID, emailID, displayName, status

def get_rooms(user_token, person_ID, room_filter):
    api = WebexTeamsAPI(access_token=user_token) 
    rooms = api.rooms.list(type='group', sortBy='created')
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
        result = "There was a problem refreshing the token."
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

def create_webhook(user_token, webhookURI, webhookID):
    api = WebexTeamsAPI(access_token=user_token)
    if webhookID is None or webhookID == '':
        try:
            webhook = api.webhooks.create(name="OOO-Assistant Webhook",targetUrl=webhookURI,resource="messages", event="created")
            webhookID = webhook.id
            print(webhookID)
            result = "Success"
        except ApiError as error:
            result = "There was a problem creating the webhook."
    else:
        try:
            get_webhook = api.webhooks.get(webhookID)
            print ("Webhook is " + get_webhook.status)
            result = "Success"
        except ApiError as error:
            print ("There was a problem getting the webhook, it was probably deleted.")
            try:
                webhook = api.webhooks.create(name="OOO-Assistant Webhook",targetUrl=webhookURI,resource="messages", event="created")
                webhookID = webhook.id
                print(webhookID)
                result = "Success"
            except ApiError as error:
                result = "There was a problem creating the webhook."
    return result, webhookID

def send_directmessage(user_token, personID, message):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        sendmsg = api.messages.create(toPersonId=personID,text=message)
        result = "Success"
    except ApiError as error:
        result = "There was a problem sending the message."
    return result

def get_messages(user_token, spaceID, personID):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        msgs = api.messages.list(roomId=spaceID,max=50)
        msg_list = [(msg.id,msg.text) for msg in msgs if msg.personId == personID]
        result = "Success"
    except ApiError as error:
        result = "There was a problem getting the messages."
    return result, msg_list

def delete_message(user_token, msgID):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        msgs = api.messages.delete(msgID)
        result = "Deleted"
    except ApiError as error:
        result = "There was a problem deleting the message."
    return result

def get_members(user_token, spaceID):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        members = api.memberships.list(roomId=spaceID,max=100)
        members_list = [(member.personDisplayName + ' - ' + member.personEmail) for member in members]
        member_list = sorted(members_list)
        result = "Success"
    except ApiError as error:
        result = "There was a problem getting the memberships."
    return result, member_list