import requests
import json
import os
import urllib
from datetime import date, datetime, timedelta
from webexteamssdk import WebexTeamsAPI, Webhook

from flask import Flask, session, render_template, flash, request, redirect, url_for, jsonify, Response
from flask_pymongo import PyMongo
from app import app
from app.forms import SelectSpaceForm, AddSpaceForm, DeleteSpaceForm, OOOForm, DeleteMessagesForm, Webex_Meetings
from app.ciscowebex import  get_tokens, get_oauthuser_info, get_rooms, create_space, delete_space, send_message, create_webhook, send_directmessage, get_messages, delete_message, get_message
from app.addusers import addusers
from app.meetings import get_meetings
from app.webex_bot import incoming_msg
from app.extensions import mongo, add_usr, get_user, get_OOO, update_OOO
from config import Config

app.config.from_object(Config)

app.secret_key = Config.SECRET_KEY
clientID = Config.clientID
secretID = Config.secretID
redirectURI = Config.redirectURI
webhookURI = Config.webhookURI

# - - - Routes - - -

@app.route("/", methods = ['GET', 'POST']) 

def index():
    if request.method == 'POST':
        json_data = request.json
        print (json_data)
        Webhook_name = json_data["name"]
        person_ID = json_data["createdBy"]
        roomType = json_data["data"]["roomType"]
        sender_ID = json_data["data"]["personId"]
        message_ID = json_data["data"]["id"]
        if Webhook_name == "Webex_Toolbox_Webhook":
            webhook_obj = Webhook(json_data)
            incoming_msg(webhook_obj)
            return "OK"
        else:
            OOO = get_OOO(person_ID)
            message = OOO['message']
            OOO_enabled = OOO['OOO_enabled']
            access_token = OOO['access_token']
            result, message_text = get_message(access_token, message_ID)
            if person_ID == sender_ID or OOO_enabled is False or "OOO Assistant" in message_text:
                print ("no response")
                return ""
            elif len(message) == 0:
                personID, emailID, displayName, status = get_oauthuser_info(access_token)
                if status == "OutOfOffice":
                    message_text = "OOO Assistant: I'm out of the office."
                    result = send_directmessage(access_token, sender_ID, message_text)
                    print (result)
                    return ""
            else:
                end_date = OOO['end_date']
                message_text = "OOO Assistant: " + message + " until " + end_date
                result = send_directmessage(access_token, sender_ID, message_text)
                print (result)
                return ""
    else:
        """Main Grant page"""
        redirect_URI = urllib.parse.quote_plus(redirectURI)
        return render_template('index.html', client_ID=clientID, redirect_URI=redirect_URI)

@app.route("/oauth")
def oauth():
    """Retrieves oauth code to generate tokens for users"""
    state = request.args.get("state") #Captures value of the state.
    if "code" in request.args and state == "SpaceWizard":
        code = request.args.get("code") #Captures value of the code.
        access_token, expires_in, refresh_token, refresh_token_expires_in = get_tokens(clientID, secretID, code, redirectURI)
        personID, emailID, displayName, status = get_oauthuser_info(access_token)
        token_expires = datetime.now() + timedelta(seconds=expires_in)
        refresh_expires = datetime.now() + timedelta(seconds=refresh_token_expires_in)
        result = add_usr(personID, displayName, access_token, token_expires, refresh_token, refresh_expires)
        print (result)
        session['user'] = personID
        if ' ' in displayName:
            firstName, lastName = displayName.split(' ')
        else:
            firstName = displayName
        return render_template("granted.html", Display_Name=firstName)
    else:
        return render_template("index.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.clear()
    return redirect(url_for('index'))

@app.route('/home')
def home():
    person_ID = session.get('user')
    user = get_user(person_ID)
    displayName = user["name"]
    if ' ' in displayName:
        firstName, lastName = displayName.split(' ')
    else:
        firstName = displayName
    return render_template("granted.html", Display_Name=firstName)

@app.route('/selectspace', methods = ['GET', 'POST'])
def selectspace():
    person_ID = session.get('user')
    user = get_user(person_ID)
    accesstoken = user['access_token']
    room_list = get_rooms(accesstoken, person_ID, "all")
    form = SelectSpaceForm()
    form.space.choices = room_list
    if request.method == 'POST':
        spaceId = request.form['space']
        print ("space ID: " + spaceId)
        spaceName =  dict(form.space.choices).get(form.space.data)
        email_list = form.emails.entries
        message_text = request.form['message']
        if len(message_text) > 0:
            result = send_message(user_token=accesstoken, spaceId=spaceId, message=message_text)
            print (result)
        emails, results = addusers(spaceId, accesstoken, email_list)
        return render_template('success.html', messages=zip(emails,results), ColumnName="Email Address")
    elif request.method == 'GET':
        return render_template('selectspace.html', form = form)  

@app.route('/addspace', methods = ['GET', 'POST'])
def addspace():
    form = AddSpaceForm()
    if request.method == 'POST':
        spaceName=request.form['space']
        person_ID = session.get('user')
        user = get_user(person_ID)
        accesstoken = user['access_token']
        result, spaceId = create_space(accesstoken, spaceName)
        print (result)
        if result == "Success":
            message_text = request.form['message']
            email_list = form.emails.entries
            if len(message_text) > 0:
                result = send_message(user_token=accesstoken, spaceId=spaceId, message=message_text)
                print (result)
            emails, results = addusers(spaceId, accesstoken, email_list)
        return render_template('success.html', messages=zip(emails,results), ColumnName="Email Address")
    elif request.method == 'GET':
        return render_template('addspace.html', form = form)  

@app.route('/deletespace', methods = ['GET', 'POST'])
def deletespace():
    person_ID = session.get('user')
    user = get_user(person_ID)
    accesstoken = user['access_token']
    room_list = get_rooms(accesstoken, person_ID, "creator")
    form = DeleteSpaceForm()
    form.space.choices = room_list
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('deletespace.html', form = form)
        else:
            spaceIdList = request.form.getlist('space')
            spaceNameList = form.space.data
            print (spaceNameList)
            results = list()
            spaces = list()
            for spaceId in spaceIdList:
                matches = [el for el in room_list if spaceId in el]
                match = matches[0]
                spaceName = match[1]
                result = delete_space(accesstoken, spaceId)
                spaces.append(spaceName)
                results.append(result)
            return render_template('success.html', messages=zip(spaces,results), ColumnName="Space")
    elif request.method == 'GET':
        flash('WARNING: Once a space is deleted it cannot be recovered!')
        flash('NOTE: You can only delete spaces that you created.')
        return render_template('deletespace.html', form = form)

@app.route('/deletemessages', methods = ['GET', 'POST'])
def deletemessages():
    person_ID = session.get('user')
    user = get_user(person_ID)
    accesstoken = user['access_token']
    room_list = get_rooms(accesstoken, person_ID, "all")
    form = DeleteMessagesForm()
    form.space.choices = room_list
    if request.method == 'POST':
        spaceId = request.form['space']
        print (spaceId)
        result, msg_list = get_messages(accesstoken, spaceId, person_ID)
        msgIdList = request.form.getlist('messages')
        msgNameList = form.messages.data
        print (msgNameList)
        results = list()
        msg_results = list()
        for msgId in msgIdList:
            matches = [el for el in msg_list if msgId in el]
            match = matches[0]
            message_text = match[1]
            result = delete_message(accesstoken, msgId)
            msg_results.append(message_text)
            results.append(result)
        return render_template('success.html', messages=zip(msg_results,results), ColumnName="Message")
    elif request.method == 'GET':
        space = room_list[0]
        spaceId = space[0]
        result, msg_list = get_messages(accesstoken, spaceId, person_ID)
        form.messages.choices = msg_list
        flash('WARNING: Once a message is deleted it cannot be recovered!')
        flash('NOTE: You can only delete messages that you created.')
        return render_template('deletemessages.html', form = form)  

@app.route('/ooomessage', methods = ['GET', 'POST'])
def ooomessage():
    person_ID = session.get('user')
    OOO = get_OOO(person_ID)
    try:
        end_date = datetime.strptime(OOO['end_date'], '%Y-%m-%d').date()
        OOO['end_date'] = end_date
        accesstoken = OOO['access_token']
        webhookID = OOO['webhookID']
    except:
        user = get_user(person_ID)
        accesstoken = user['access_token']
        webhookID = ''
    form = OOOForm(data=OOO)
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('ooo-message.html', form = form)
        else:
            endDate = request.form['end_date']
            end_date = date(*map(int, endDate.split('-')))
            message_text = request.form['message']
            OOO_enabled = form.data.get('OOO_enabled')
            print ("enabled: " + str(OOO_enabled))
            result, webhook_ID = create_webhook(accesstoken, webhookURI, webhookID)
            print (result)
            if result == "Success":
                update_OOO(person_ID, message_text, endDate, webhook_ID, OOO_enabled)
            return render_template('success.html', result=result)
    elif request.method == 'GET':
        return render_template('ooo-message.html', form = form)  

@app.route('/messages/<spaceId>')
def messages(spaceId):
    person_ID = session.get('user')
    user = get_user(person_ID)
    accesstoken = user['access_token']
    result, msg_list = get_messages(accesstoken, spaceId, person_ID)

    msgArray = []
    index = 0

    for msg in msg_list:
        msgObj = {}
        msg = msg_list[index]
        msgObj['id'] = msg[0]
        msgObj['msgtxt'] = msg[1]
        index = index + 1
        msgArray.append(msgObj)

    return jsonify({'messages' : msgArray})

@app.route('/meetings', methods = ['GET', 'POST'])
def meetings():
    form = Webex_Meetings()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('meetings.html', form = form)
        else:
            return render_template('success.html', result=result)
    elif request.method == 'GET':
        return render_template('meetings.html', form = form)  

@app.route('/reports/<report_type>/<start_date>')
def reports(report_type, start_date):
    result, key_list, title_list, host_list, startdate_list, duration_list = get_meetings(report_type, start_date)
    mtgArray = []
    index = 0
    for mtg in key_list:
        mtgObj = {}
        key = key_list[index]
        title = title_list[index]
        host = host_list[index]
        startdate = startdate_list[index]
        duration = duration_list[index]
        mtgObj['key'] = key
        mtgObj['title'] = title
        mtgObj['host'] = host
        mtgObj['startdate'] = startdate
        mtgObj['duration'] = duration
        index = index + 1
        mtgArray.append(mtgObj)
    return jsonify({'meetings' : mtgArray})
