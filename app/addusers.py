from app.ciscowebex import add_users
from app import db
from app.models import User, Space, Email

def addusers(space_id, user_token):
    space = Space.query.get(space_id)
    webex_id = space.webex_id
    emails = Email.query.filter_by(space_id=space_id).all()
    email_list = list()
    results = list()
    for e in emails:
        print (e.id, e.email_address, e.space_id)
        result = add_users(user_token, e.email_address, webex_id)
        e.result=result
        db.session.commit()
        email_list.append(e.email_address)
        results.append(result)
    space.processed=True
    db.session.commit()
    return email_list, results
