import requests
import json
import os
import urllib
import pytz
from datetime import date, datetime, timedelta
from webexteamssdk import WebexTeamsAPI, Webhook

from flask import Flask, session, render_template, flash, request, redirect, url_for, jsonify, Response
from flask_pymongo import PyMongo
from app import app
from app.forms import SelectSpaceForm, AddSpaceForm, DeleteSpaceForm, OOOForm, DeleteMessagesForm, Webex_Meetings, SettingsForm
from app.ciscowebex import  get_tokens, get_oauthuser_info, get_rooms, create_space, delete_space, send_message, create_webhook, delete_webhook, list_webhooks, send_directmessage, get_messages, delete_message, get_message, get_member_details, send_card, get_attachment, set_TimeZone, confirm_TimeZone, OOO_webhook, leave_space
from app.addusers import addusers
from app.meetings import get_meetings
from app.webex_bot import incoming_msg
from app.extensions import mongo, add_usr, get_user, get_OOO, update_OOO, get_TZ_fromPhone, webex_settings, get_webex_settings, update_UTC
from config import Config

app.config.from_object(Config)

FORCE_SSL = Config.FORCE_SSL
app.secret_key = Config.SECRET_KEY
clientID = Config.clientID
secretID = Config.secretID
redirectURI = Config.redirectURI
webhookURI = Config.webhookURI

# - - - Routes - - -
@app.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

@app.route("/", methods = ['GET', 'POST']) 
def index():
    """Main Grant page"""
    redirect_URI = urllib.parse.quote_plus(redirectURI)
    return render_template('index.html', client_ID=clientID, redirect_URI=redirect_URI)

@app.route("/oauth")
def oauth():
    """Retrieves oauth code to generate tokens for users"""
    state = request.args.get("state") #Captures value of the state.
    if "code" in request.args and state == "Toolbox":
        code = request.args.get("code") #Captures value of the code.
        access_token, expires_in, refresh_token, refresh_token_expires_in = get_tokens(clientID, secretID, code, redirectURI)
        personID, emailID, displayName, status, phone_nums = get_oauthuser_info(access_token)
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
    result, user = get_user(person_ID)
    displayName = user["name"]
    if ' ' in displayName:
        firstName, lastName = displayName.split(' ')
    else:
        firstName = displayName
    return render_template("granted.html", Display_Name=firstName)

@app.route('/settings', methods = ['GET', 'POST'])
def settings():
    person_ID = session.get('user')
    wbx_settings = get_webex_settings(person_ID)
    form = SettingsForm(data=wbx_settings)
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('settings.html', form = form)
        else:
            site_name = request.form['site_name']
            user_email = request.form['user_email']
            user_pwd = request.form['user_pwd']
            result = webex_settings(person_ID, site_name, user_email, user_pwd)
            return render_template('success.html', result=result)
    elif request.method == 'GET':
        return render_template("settings.html", form=form)

@app.route('/selectspace', methods = ['GET', 'POST'])
def selectspace():
    person_ID = session.get('user')
    result, user = get_user(person_ID)
    accesstoken = user['access_token']
    room_list = get_rooms(accesstoken, person_ID, "all")
    form = SelectSpaceForm()
    form.space.choices = room_list
    if request.method == 'POST':
        spaceId = request.form['space']
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
        result, user = get_user(person_ID)
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
    result, user = get_user(person_ID)
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

@app.route('/leavespace', methods = ['GET', 'POST'])
def leavespace():
    person_ID = session.get('user')
    result, user = get_user(person_ID)
    accesstoken = user['access_token']
    room_list = get_rooms(accesstoken, person_ID, "all")
    form = DeleteSpaceForm()
    form.space.choices = room_list
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('leavespace.html', form = form)
        else:
            spaceIdList = request.form.getlist('space')
            spaceNameList = form.space.data
            results = list()
            spaces = list()
            for spaceId in spaceIdList:
                matches = [el for el in room_list if spaceId in el]
                match = matches[0]
                spaceName = match[1]
                result = leave_space(accesstoken, spaceId, person_ID)
                spaces.append(spaceName)
                results.append(result)
            return render_template('success.html', messages=zip(spaces,results), ColumnName="Space")
    elif request.method == 'GET':
        return render_template('leavespace.html', form = form)

@app.route('/deletemessages', methods = ['GET', 'POST'])
def deletemessages():
    person_ID = session.get('user')
    result, user = get_user(person_ID)
    accesstoken = user['access_token']
    room_list = get_rooms(accesstoken, person_ID, "all")
    form = DeleteMessagesForm()
    form.space.choices = room_list
    if request.method == 'POST':
        spaceId = request.form['space']
        result, msg_list = get_messages(accesstoken, spaceId, person_ID, True)
        msgIdList = request.form.getlist('messages')
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
        result, msg_list = get_messages(accesstoken, spaceId, person_ID, True)
        form.messages.choices = msg_list
        flash('WARNING: Once a message is deleted it cannot be recovered!')
        flash('NOTE: You can only delete messages that you created.')
        return render_template('deletemessages.html', form = form)  

@app.route('/ooomessage', methods = ['GET', 'POST'])
def ooomessage():
    person_ID = session.get('user')
    result, OOO = get_OOO(person_ID)
    try:
        Str_EndDate = datetime.strftime(OOO['end_date'], '%b %d %Y %I:%M %p')
        OOO['end_date'] = Str_EndDate
        accesstoken = OOO['access_token']
        webhookID_D = OOO['webhookID_D']
        webhookID_M = OOO['webhookID_M']
        country = OOO['country']
    except:
        result, user = get_user(person_ID)
        OOO['end_date'] = datetime.strftime(datetime.utcnow(), '%b %d %Y %I:%M %p')
        accesstoken = user['access_token']
        webhookID_D = ""
        webhookID_M = ""
        country = ""
    form = OOOForm(data=OOO)
    if request.method == 'POST':
        OOO_enabled = form.data.get('OOO_enabled')
        Direct = form.data.get('Direct')
        Mentions = form.data.get('Mentions')
        if OOO_enabled and Direct == False and Mentions == False:
            flash('If the OOO Message is Enabled you must also select Direct and/or Mentions.')
            return render_template('ooo-message.html', form = form)
        else:
            endDate = request.form['end_date']
            TZ_Name = request.form['TZ_Name']
            datetime_object = datetime.strptime(endDate, '%b %d %Y %I:%M %p')
            UTC_EndDate = datetime_object + timedelta(minutes=int(request.form['TZ_Offset']))
            message_text = request.form['message']
            print ("enabled: " + str(OOO_enabled))
            webhook_ID_D = ""
            webhook_ID_M = ""
            if Direct:
                webhookType = "direct"
                result, webhook_ID_D = create_webhook(accesstoken, (webhookURI + "/ooo"), webhookID_D, webhookType)
                print ("Direct " + result)
            else:
                if len(webhookID_D) > 0:
                    result = delete_webhook(accesstoken, webhookID_D)
                    print ("Direct " + result)
            if Mentions:
                webhookType = "mentions"
                result, webhook_ID_M = create_webhook(accesstoken, (webhookURI + "/ooo"), webhookID_M, webhookType)
                print ("Mentions " + result)
            else:
                if len(webhookID_M) > 0:
                    result = delete_webhook(accesstoken, webhookID_M)
                    print ("Mentions " + result)
            result = update_OOO(person_ID, message_text, UTC_EndDate, country, webhook_ID_D, webhook_ID_M, OOO_enabled, TZ_Name)
            return render_template('success.html', result=result)
    elif request.method == 'GET':
        return render_template('ooo-message.html', form = form)

@app.route('/meetings', methods = ['GET', 'POST'])
def meetings():
    start_date = datetime.strftime(datetime.now(), '%Y %m %d')
    start_date = start_date + " 00:00"
    mtg_data = {}
    mtg_data['start_date'] = start_date
    form = Webex_Meetings(data=mtg_data)
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('meetings.html', form = form)
        else:
            return render_template('success.html', result=result)
    elif request.method == 'GET':
        return render_template('meetings.html', form = form)

# - - - internal routes - - -

@app.route('/messages/<spaceId>')
def messages(spaceId):
    person_ID = session.get('user')
    result, user = get_user(person_ID)
    accesstoken = user['access_token']
    result, msgArray = get_messages(accesstoken, spaceId, person_ID, False)
    return jsonify({'messages' : msgArray})

@app.route('/member_details/<spaceId>')
def member_details(spaceId):
    person_ID = session.get('user')
    result, user = get_user(person_ID)
    accesstoken = user['access_token']
    result, members_list = get_member_details(accesstoken, spaceId)
    return jsonify({'members' : members_list})

@app.route('/webhooks/<action>')
def delete_webhooks(action):
    person_ID = session.get('user')
    result, user = get_user(person_ID)
    accesstoken = user['access_token']
    result, webhooks_list = list_webhooks(accesstoken)
    print (result)
    webhooksArray = []
    for webhook in webhooks_list:
        webhooksObj = {}
        if "mentionedPeople" in webhook[1]:
            webhooksObj['webhook'] = "Mentions"
        else:
            webhooksObj['webhook'] = "Direct"
        webhooksObj['created'] = webhook[2]
        if action == "delete":
            result = delete_webhook(accesstoken, webhook[0])
            webhooksObj['result'] = result
        webhooksArray.append(webhooksObj)
    return jsonify({'webhooks' : webhooksArray})

@app.route('/reports/<report_type>/<start_date>')
def reports(report_type, start_date):
    person_ID = session.get('user')
    wbx_settings = get_webex_settings(person_ID)
    result, mtgArray = get_meetings(report_type, start_date, wbx_settings)
    return jsonify({'meetings' : mtgArray})


# - - - Inbound Webhook Routes - - -

@app.route("/webhook", methods = ['POST']) 
def webhook():
    json_data = request.json
    Webhook_name = json_data["name"]
    person_ID = json_data["createdBy"]
    sender_ID = json_data["data"]["personId"]
    data_id = json_data["data"]["id"]
    attachment_data = get_attachment(data_id)
    result, OOO = get_OOO(sender_ID)
    try:
        access_token = OOO['access_token']
        webhookID_D = OOO['webhookID_D']
        webhookID_M = OOO['webhookID_M']
        TZ_Name = OOO['TZ_Name']
        current_country = OOO['country']
    except:
        result, user = get_user(sender_ID)
        access_token = user['access_token']
        webhookID_D = ""
        webhookID_M = ""
        TZ_Name = ""
    card_name = attachment_data["inputs"]["card"]
    if card_name == "set_OOO":
        message_text = attachment_data["inputs"]["message"]
        end_date = attachment_data["inputs"]["end_date"]
        end_time = attachment_data["inputs"]["time"]
        Str_EndDate = (end_date + " " + end_time)
        country = attachment_data["inputs"]["country"]
        OOO_enabled = eval(attachment_data["inputs"]["enabled"])
        Direct = eval(attachment_data["inputs"]["direct"])
        Mentions = eval(attachment_data["inputs"]["mentions"])
        try:
            TZ_Name = attachment_data["inputs"]["timezone"]
        except:
            print ("timezone not changed")
        if OOO_enabled and Direct == False and Mentions == False:
            message = 'If the OOO Message is Enabled you must also select Direct and/or Mentions.'
            result = send_directmessage('', sender_ID, message, '')
        else:
            try:
                if country != current_country:
                    TZ_Name = ""
            except Exception as e:
                print ("Exception: " + str(e))
            OOO_webhook(sender_ID, access_token, (webhookURI + "/ooo"), webhookID_D, webhookID_M, message_text, Str_EndDate, country, OOO_enabled, Direct, Mentions, TZ_Name)
            if TZ_Name == "":
                try:
                    personID, emailID, displayName, status, phone_nums = get_oauthuser_info(access_token)
                    phone_num = phone_nums[0]
                    TZ, country = get_TZ_fromPhone(phone_num)
                    result = confirm_TimeZone(sender_ID, TZ)
                except Exception as e:
                    print ("Exception: " + str(e))
                    result = set_TimeZone(sender_ID, country)
            elif country != current_country:
                result = set_TimeZone(sender_ID, country)
            else:
                message = 'Thank you. Your Out of Office message has been updated.'
                result = send_directmessage('', sender_ID, message, '')
        return "OK"       
    elif card_name == "set_TZ":
        TZ_Name = attachment_data["inputs"]["timezone"]
        end_date = OOO['end_date']
        UTC_EndDate = update_UTC(TZ_Name, end_date)
        result = update_OOO(sender_ID, '', UTC_EndDate, '', '', '', '', TZ_Name)
        print ("end date changed from " + str(end_date) + " to " + str(UTC_EndDate))
        message = 'Thank you. Your Timezone has been updated.'
        result = send_directmessage('', sender_ID, message, '')
    elif card_name == "confirm_TZ":
        response = attachment_data["inputs"]["response"]
        if response == "yes":
            TZ_Name = attachment_data["inputs"]["TZ"]
            end_date = OOO['end_date']
            UTC_EndDate = update_UTC(TZ_Name, end_date)
            result = update_OOO(sender_ID, '', UTC_EndDate, '', '', '', '', TZ_Name)
            print ("end date changed from " + str(end_date) + " to " + str(UTC_EndDate))
            message = 'Thank you. Your Timezone has been confirmed.'
            result = send_directmessage('', sender_ID, message, '')
        else:
            country = OOO['country']
            result = set_TimeZone(sender_ID, country)
    else:
        print ("no card data")
    return "OK"

@app.route("/ooo", methods = ['POST']) 
def ooo():
    json_data = request.json
    Webhook_name = json_data["name"]
    person_ID = json_data["createdBy"]
    roomType = json_data["data"]["roomType"]
    sender_ID = json_data["data"]["personId"]
    sender_email = json_data["data"]["personEmail"]
    message_ID = json_data["data"]["id"]
    if person_ID == sender_ID or sender_email == "WebexToolbox@webex.bot":
        print ("no response")
        message_text = ""
        return "OK"
    result, OOO = get_OOO(person_ID)
    message = OOO['message']
    OOO_enabled = OOO['OOO_enabled']
    access_token = OOO['access_token']
    Text_EndDate = datetime.strftime(OOO['end_date'], '%b %d %Y %I:%M %p')
    Card_EndDate = datetime.strftime(OOO['end_date'], '%Y-%m-%dT%H:%M:%SZ') 
    result, message_text = get_message(access_token, message_ID)
    personID, emailID, displayName, status, phone_nums = get_oauthuser_info(access_token)
    if status == "OutOfOffice":
        if len(message) == 0:
            message_text = "I'm out of the office."
        else:
            message_text = message + " until "
    elif OOO_enabled is False:
        print ("no response")
        message_text = ""
    else:
        if len(message) == 0:
            message_text = "I'm out of the office until "
        else:
            message_text = message + " until "
    if len(message_text) > 0:
        result = send_card(sender_ID, displayName, message_text, Text_EndDate, Card_EndDate)
        print (result)
    return "OK"

@app.route("/bot", methods = ['POST']) 
def bot():
    json_data = request.json
    Webhook_name = json_data["name"]
    person_ID = json_data["createdBy"]
    roomType = json_data["data"]["roomType"]
    sender_ID = json_data["data"]["personId"]
    sender_email = json_data["data"]["personEmail"]
    message_ID = json_data["data"]["id"]
    if person_ID == sender_ID or sender_email == "WebexToolbox@webex.bot":
        print ("no response")
        message_text = ""
        return "OK"
    else:
        webhook_obj = Webhook(json_data)
        result, OOO = get_OOO(sender_ID)
        if result == "success":
            incoming_msg(webhook_obj, OOO)
        else:
            result, OOO = get_user(sender_ID)
            if result == "success":
                incoming_msg(webhook_obj, OOO)
            else:
                markdown = 'You need to login to the Webex Toolbox before you can configure an Out of Office message. Please click [here](https://www.webex-toolbox.com) to login.'
                result = send_directmessage('', sender_ID, '', markdown)
        return "OK"