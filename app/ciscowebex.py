import requests
import json
from app import db
from app.models import User, Space, Email
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

def add_user(personID, displayName, user_token, access_expdate, refresh_token, refresh_expdate):
    user = User.query.filter_by(person_ID=personID).first()
    if user is None:
        u = User(person_ID=personID, username=displayName, access_token=user_token, access_expdate=access_expdate, refresh_token=refresh_token, refresh_expdate=refresh_expdate)
        print (u.person_ID, u.username, u.access_token, u.access_expdate, u.refresh_token, u.refresh_expdate)
        db.session.add(u)
        db.session.commit()
        owner = u
        print (owner)
        user_id = u.id
        result = "User added to db"
    else:
        owner = user
        user_id = user.id
        user.access_token=user_token
        user.access_expdate=access_expdate
        user.refresh_token=refresh_token
        user.refresh_expdate=refresh_expdate
        db.session.commit()
        result = "User already exists in db"
    return result, owner, user_id

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
        space = Space.query.get(spaceId)
        webex_id = space.webex_id
        sendmsg = api.messages.create(roomId=webex_id,text=message)
        result = "Success"
    except ApiError as error:
        result = "There was a problem sending the message."
    return result

def create_webhook(user_token, webhookURI, webhookID):
    api = WebexTeamsAPI(access_token=user_token)
    if webhookID is None:
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
        result = "There was a problem sending the message."
    return result, msg_list

def delete_message(user_token, msgID):
    api = WebexTeamsAPI(access_token=user_token)
    try:
        msgs = api.messages.delete(msgID)
        result = "Deleted"
    except ApiError as error:
        result = "There was a problem sending the message."
    return result