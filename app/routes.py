import requests
import json
import os
import urllib
from datetime import date, datetime, timedelta

from flask import Flask, session, render_template, flash, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from app import app, db
from app.forms import CombinedForm, SelectSpaceForm, AddSpaceForm, DeleteSpaceForm, OOOForm, DeleteMessagesForm
from app.models import User, Space, Email
from app.ciscowebex import  get_tokens, get_oauthuser_info, get_rooms, add_user, create_space, delete_space, send_message, create_webhook, send_directmessage, get_messages, delete_message
from app.addusers import addusers
from config import Config

app.config.from_object(Config)

app.secret_key = Config.SECRET_KEY
clientID = Config.clientID
secretID = Config.secretID
redirectURI = Config.redirectURI
webhookURI = Config.webhookURI

# - - - Routes - - -

@app.route("/",methods = ['GET', 'POST']) 

def index():
    if request.method == 'POST':
        json_data = request.json
        print (json_data)
        person_ID = json_data["createdBy"]
        roomType = json_data["data"]["roomType"]
        sender_ID = json_data["data"]["personId"]
        user = User.query.filter_by(person_ID=person_ID).first()
        message = user.message
        OOO_enabled = user.OOO_enabled
        access_token = user.access_token
        if person_ID == sender_ID or OOO_enabled is False:
            print ("no response")
            return ""
        elif len(message) == 0:
            personID, emailID, displayName, status = get_oauthuser_info(access_token)
            #if status == "OutOfOffice":
            if status == "inactive":
                message_text = "OOO Assistant: I'm out of the office."
                result = send_directmessage(access_token, sender_ID, message_text)
                print (result)
                return ""
        else:
            enddatetime = user.end_date
            end_date = enddatetime.strftime('%d/%m/%Y')
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
        result, owner, user_id = add_user(personID, displayName, access_token, token_expires, refresh_token, refresh_expires)
        print (result)
        session['user'] = user_id
        firstName, lastName = displayName.split(' ')
        return render_template("granted.html", Display_Name=firstName)
    else:
        return render_template("index.html")

@app.route('/selectspace', methods = ['GET', 'POST'])
def selectspace():
    user_id = session.get('user')
    owner = User.query.get(user_id)
    accesstoken = owner.access_token
    person_ID = owner.person_ID
    room_list = get_rooms(accesstoken, person_ID, "all")
    form = SelectSpaceForm()
    form.space.choices = room_list
    print (room_list)
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('selectspace.html', form = form)
        else:
            spaceId = request.form['space']
            spaceName =  dict(form.space.choices).get(form.space.data)
            message_text = request.form['message']
            s = Space(owner=owner, spacename=spaceName, webex_id=spaceId, message=message_text)
            db.session.add(s)
            db.session.commit()
            s_id = s.id
            print (s_id)
            return redirect(url_for('addemails', s_id=s_id))
    elif request.method == 'GET':
        return render_template('selectspace.html', form = form)  

@app.route('/addspace', methods = ['GET', 'POST'])
def addspace():
    form = AddSpaceForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('All fields are required.')
            return render_template('addspace.html', form = form)
        else:
            spaceName=request.form['space']
            message_text = request.form['message']
            user_id = session.get('user')
            owner = User.query.get(user_id)
            accesstoken = owner.access_token
            result, roomId = create_space(accesstoken, spaceName)
            print (result)
            if result == "Success":
                s = Space(owner=owner, spacename=spaceName, webex_id=roomId, message=message_text)
                db.session.add(s)
                db.session.commit()
                s_id = s.id
                print (s_id)
                return redirect(url_for('addemails', s_id=s_id))
            else:
                return render_template('success.html', result=result)
    elif request.method == 'GET':
        return render_template('addspace.html', form = form)  

@app.route('/addemails/<int:s_id>', methods=['GET', 'POST'])
def addemails(s_id):
    space = Space.query.get(s_id)

    # if there are no emails, provide an empty one so the table is rendered
    if len(space.emails) == 0:
        space.emails = [Email(email_address="user@example.com")]

    # else: forms loaded through db relation
    form = CombinedForm(obj=space)

    if form.validate_on_submit():
        form.populate_obj(space)
        db.session.commit()
        message_text = request.form['message']
        user_id = session.get('user')
        owner = User.query.get(user_id)
        accesstoken = owner.access_token
        emails, results = addusers(s_id, accesstoken)
        if len(message_text) > 0:
            result = send_message(user_token=accesstoken, spaceId=s_id, message=message_text)
            print (result)
        return render_template('success.html', messages=zip(emails,results), ColumnName="Email Address")
    else:
        return render_template('addemails.html', form=form)

@app.route('/deletespace', methods = ['GET', 'POST'])
def deletespace():
    user_id = session.get('user')
    owner = User.query.get(user_id)
    accesstoken = owner.access_token
    person_ID = owner.person_ID
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
    user_id = session.get('user')
    owner = User.query.get(user_id)
    accesstoken = owner.access_token
    person_ID = owner.person_ID
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

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.clear()
    return redirect(url_for('index'))

@app.route('/home')
def home():
    user_id = session.get('user')
    owner = User.query.get(user_id)
    displayName = owner.username
    firstName, lastName = displayName.split(' ')
    return render_template("granted.html", Display_Name=firstName)

@app.route('/ooomessage', methods = ['GET', 'POST'])
def ooomessage():
    user_id = session.get('user')
    owner = User.query.get(user_id)
    form = OOOForm(obj=owner)
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
            accesstoken = owner.access_token
            webhookID = owner.webhookID
            result, webhook_ID = create_webhook(accesstoken, webhookURI, webhookID)
            print (result)
            if result == "Success":
                owner.message = message_text
                owner.end_date = end_date
                owner.webhookID = webhook_ID
                owner.OOO_enabled = OOO_enabled
                db.session.commit()
            return render_template('success.html', result=result)
    elif request.method == 'GET':
        return render_template('ooo-message.html', form = form)  

@app.route('/messages/<spaceId>')
def messages(spaceId):
    user_id = session.get('user')
    owner = User.query.get(user_id)
    accesstoken = owner.access_token
    person_ID = owner.person_ID
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