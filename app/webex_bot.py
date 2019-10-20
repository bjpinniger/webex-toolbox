import requests
import json
from webexteamssdk import WebexTeamsAPI, ApiError, Webhook
from app.ciscowebex import set_OOO, send_directmessage

api = WebexTeamsAPI()

def incoming_msg(webhook_obj, OOO):
    room = api.rooms.get(webhook_obj.data.roomId)
    message = api.messages.get(webhook_obj.data.id)
    person = api.people.get(message.personId)
    # loop prevention...
    me = api.people.me()
    if message.personId == me.id:
        return {'Message': 'OK'}
    else:
        if "Hi" in message.text:
            response_txt = "Hello"
            api.messages.create(room.id, text=response_txt)
        elif "help" == message.text.lower():
            markdown = "**You need to login to Webex Toolbox before you can configure an Out of Office message. Please click [here](https://www.webex-toolbox.com) to login.**\n\n**OOO:** Use this command to activate/modify your out of office settings.\n\n**Enabled:** Activates the Out of Office Assistant.\n\n**Direct:** Responds to Direct messages.\n\n**Mentions:** Responds to messages where you are @Mentioned.\n\n**NOTE:** If the Out of Office Assistant is disabled but Direct and/or Mentions is active *and* your Webex Teams status is **Out Of Office** a generic response will be sent as follows: **I'm out of the office.**"
            result = send_directmessage('', message.personId, '', markdown)
        elif "ooo" ==  message.text.lower():
            try:
                access_token = OOO['access_token']
                set_OOO(message.personId, OOO, access_token)
            except Exception as e:
                print ("Exception: " + str(e))
                markdown = 'You need to login to Webex Toolbox before you can configure an Out of Office message. Please click [here](https://www.webex-toolbox.com) to login.'
                result = send_directmessage('', message.personId, '', markdown)
                print (result)

