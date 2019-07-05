import requests
import json
from webexteamssdk import WebexTeamsAPI, ApiError, Webhook

api = WebexTeamsAPI()

def incoming_msg(webhook_obj):
    # Get the room details
    room = api.rooms.get(webhook_obj.data.roomId)

    # Get the message details
    message = api.messages.get(webhook_obj.data.id)

    # Get the sender's details
    person = api.people.get(message.personId)

    # This is a VERY IMPORTANT loop prevention control step.
    # If you respond to all messages...  You will respond to the messages
    # that the bot posts and thereby create a loop condition.
    me = api.people.me()
    if message.personId == me.id:
        # Message was sent by me (bot); do not respond.
        return {'Message': 'OK'}

    else:
        # Message was sent by someone else; parse message and respond.
        if "Hi" in message.text:
            response_txt = "Hello"
            # Post to the room where the request was received
            api.messages.create(room.id, text=response_txt)

