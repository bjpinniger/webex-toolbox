import requests
import json
from xml.etree import ElementTree as ET
from app import app
from config import Config

webex_admin = Config.webex_admin
webex_pwd = Config.webex_pwd
webex_site = Config.webex_site

url = "https://%s.webex.com/WBXService/XMLService" % webex_site

def create_meeting(MRN):
    SIP_URI = ""
    payload = '<serv:message xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n\t<header>\n\t\t<securityContext>\n\t\t\t<webExID>%s</webExID>\n\t\t\t<password>%s</password>\n\t\t\t<siteName>%s</siteName>\n\t\t</securityContext>\n\t</header>\n\t<body>\n\t\t<bodyContent xsi:type=\"java:com.webex.service.binding.meeting.CreateMeeting\">\n\t\t\t<accessControl>\n\t\t\t\t<meetingPassword>ewrt74tkj4et</meetingPassword>\n\t\t\t</accessControl>\n\t\t\t<metaData>\n\t\t\t\t<confName>%s</confName>\n\t\t\t</metaData>\n\t\t\t<schedule>\n\t\t\t\t<startDate/>\n\t\t\t</schedule>\n\t\t</bodyContent>\n\t</body>\n</serv:message>' % (webex_admin, webex_pwd, webex_site, MRN)
    headers = {
        'Content-Type': "text/plain",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': "%s.webex.com" % webex_site,
        'accept-encoding': "gzip, deflate",
        'content-length': "665",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
        }
    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        ns = {
            'meet' : "http://www.webex.com/schemas/2002/06/service/meeting"
            }
        if response.status_code == 200:
            result = "Success"
            root = ET.fromstring(response.text)
            meetingID_resp = root.find('.//meet:meetingkey', ns)
            meetingID = meetingID_resp.text
            result, SIP_URI = get_meeting(meetingID)
        else:
            result = "Failure: Status Code " + str(response.status_code)
    except requests.exceptions.ConnectionError:
        result = "Failed to connect to the Webex Service"
    return result, SIP_URI

def get_meeting(meetingID):
    SIP_URI = ""
    payload = '<serv:message xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n\t<header>\n\t\t<securityContext>\n\t\t\t<webExID>%s</webExID>\n\t\t\t<password>%s</password>\n\t\t\t<siteName>%s</siteName>\n\t\t</securityContext>\n\t</header>\n\t<body>\n\t\t<bodyContent xsi:type=\"java:com.webex.service.binding.meeting.GetMeeting\">\n\t\t\t<meetingKey>%s</meetingKey>\n\t\t</bodyContent>\n\t</body>\n</serv:message>' % (webex_admin, webex_pwd, webex_site, meetingID)
    headers = {
        'Content-Type': "text/plain",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': "%s.webex.com" % webex_site,
        'accept-encoding': "gzip, deflate",
        'content-length': "665",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
        }
    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        ns = {
            'meet' : "http://www.webex.com/schemas/2002/06/service/meeting"
            }
        if response.status_code == 200:
            result = "Success"
            root = ET.fromstring(response.text)
            SIPURI_resp = root.find('.//meet:sipURL', ns)
            SIP_URI = SIPURI_resp.text
        else:
            result = "Failure: Status Code " + str(response.status_code)
    except requests.exceptions.ConnectionError:
        result = "Failed to connect to the Webex Service"
    return result, SIP_URI


def get_meetings(type, startdate, webex_settings):
    try:
        site_name = webex_settings['site_name']
        user_email = webex_settings['user_email']
        user_pwd = webex_settings['user_pwd']
    except:
        site_name = webex_site
        user_email = webex_admin
        user_pwd = webex_pwd
    if user_pwd == "":
        site_name = webex_site
        user_email = webex_admin
        user_pwd = webex_pwd
    year, month, day, time = startdate.split(" ")
    start_date = (month + "/" + day + "/" + year + " " + time + ":00")
    mtgArray = []
    if type == "meet":
        payload = '<serv:message xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n\t<header>\n\t\t<securityContext>\n\t\t\t<webExID>%s</webExID>\n\t\t\t<password>%s</password>\n\t\t\t<siteName>%s</siteName>\n\t\t</securityContext>\n\t</header>\n\t<body>\n\t\t<bodyContent xsi:type=\"java:com.webex.service.binding.meeting.LstsummaryMeeting\">\n\t\t\t<order>\n\t\t\t\t<orderBy>STARTTIME</orderBy>\n\t\t\t</order>\n\t\t\t<dateScope>\n\t\t\t\t<startDateStart>%s</startDateStart>\n\t\t\t</dateScope>\n\t\t</bodyContent>\n\t</body>\n</serv:message>' % (user_email, user_pwd, site_name, start_date)
    else:
        payload = '<serv:message xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n\t<header>\n\t\t<securityContext>\n\t\t\t<webExID>%s</webExID>\n\t\t\t<password>%s</password>\n\t\t\t<siteName>%s</siteName>\n\t\t</securityContext>\n\t</header>\n\t<body>\n\t\t<bodyContent\n\t\t\txsi:type=\"java:com.webex.service.binding.event.LstsummaryEvent\">\n\t\t\t\t<listControl>\t\n\t\t\t\t\t<startFrom>1</startFrom>\n\t\t\t\t\t<maximumNum>1000</maximumNum>\n\t\t\t\t\t<listMethod>OR</listMethod>\n\t\t\t\t</listControl>\n\t\t\t<order>\n\t\t\t\t<orderBy>HOSTWEBEXID</orderBy>\n\t\t\t\t<orderAD>ASC</orderAD>\n\t\t\t\t<orderBy>EVENTNAME</orderBy>\n\t\t\t\t<orderAD>ASC</orderAD>\n\t\t\t\t<orderBy>STARTTIME</orderBy>\n\t\t\t\t<orderAD>ASC</orderAD>\n\t\t\t</order>\n\t\t\t<dateScope>\n\t\t\t\t<startDateStart>%s</startDateStart>\n\t\t\t</dateScope>\n\t\t</bodyContent>\n\t</body>\n</serv:message>' % (user_email, user_pwd, site_name, start_date)
    headers = {
        'Content-Type': "text/plain",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': "%s.webex.com" % webex_site,
        'accept-encoding': "gzip, deflate",
        'content-length': "665",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
        }
    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        if type == "meet":
            ns = {
                'meet' : "http://www.webex.com/schemas/2002/06/service/meeting"
            }
            if response.status_code == 200:
                result = "Success"
                tree=ET.fromstring(response.text)
                for meet in tree.findall('.//meet:meeting', ns):
                    key = (meet.find('.//meet:meetingKey', ns))
                    title = (meet.find('.//meet:confName', ns))
                    host = (meet.find('.//meet:hostWebExID', ns))
                    startdate = (meet.find('.//meet:startDate', ns))
                    duration = (meet.find('.//meet:duration', ns))
                    mtgObj = {}
                    mtgObj['key'] = key.text
                    mtgObj['title'] = title.text
                    mtgObj['host'] = host.text
                    mtgObj['startdate'] = startdate.text
                    mtgObj['duration'] = duration.text
                    mtgArray.append(mtgObj)
            else:
                result = "Failure: Status Code " + str(response.status_code)
        else:
            ns = {
                'event' : "http://www.webex.com/schemas/2002/06/service/event"
            }
            if response.status_code == 200:
                result = "Success"
                tree=ET.fromstring(response.text)
                for event in tree.findall('.//event:event', ns):
                    key = (event.find('.//event:sessionKey', ns))
                    title = (event.find('.//event:sessionKey', ns))
                    host = (event.find('.//event:hostWebExID', ns))
                    startdate = (event.find('.//event:startDate', ns))
                    duration = (event.find('.//event:duration', ns))
                    mtgObj = {}
                    mtgObj['key'] = key.text
                    mtgObj['title'] = title.text
                    mtgObj['host'] = host.text
                    mtgObj['startdate'] = startdate.text
                    mtgObj['duration'] = duration.text
                    mtgArray.append(mtgObj)
            else:
                result = "Failure: Status Code " + str(response.status_code)
    except requests.exceptions.ConnectionError:
        result = "Failed to connect to the Webex Service"
    return result, mtgArray
