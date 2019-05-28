from datetime import date, datetime
from app import db

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer(), primary_key=True)
    person_ID = db.Column(db.String(100))
    username = db.Column(db.String(40))
    access_token = db.Column(db.String(100))
    access_expdate = db.Column(db.DateTime())
    refresh_token = db.Column(db.String(100))
    refresh_expdate = db.Column(db.DateTime())
    message = db.Column(db.String(500))
    end_date = db.Column(db.DateTime())
    webhookID = db.Column(db.String(100))
    OOO_enabled = db.Column(db.Boolean(), default=False)
    spaces = db.relationship('Space', backref='owner', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

 
class Space(db.Model):
    __tablename__ = 'space'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    spacename = db.Column(db.String(40))
    activate_date = db.Column(db.Date(), default = date.today)
    processed = db.Column(db.Boolean(), default=False)
    webex_id = db.Column(db.String(100))
    message = db.Column(db.String(500))
    emails = db.relationship('Email')

    def __repr__(self):
        return '<Space {}>'.format(self.spacename)

class Email(db.Model):
    __tablename__ = 'emails'
    id = db.Column(db.Integer(), primary_key=True)
    space_id = db.Column(db.Integer(), db.ForeignKey('space.id'))
    email_address = db.Column(db.String(50))
    result = db.Column(db.String(50))

    def __repr__(self):
        return '<Email {}>'.format(self.email_address)

