from flask_wtf import FlaskForm
from wtforms import FieldList, validators, ValidationError
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, FormField, SubmitField, DateField, SelectField, SelectMultipleField, TextAreaField, BooleanField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Email, Required
from datetime import date

class EmailsForm(FlaskForm):
    email_address = StringField('Email Address')

class SelectSpaceForm(FlaskForm):
    space = SelectField('Space', render_kw={'autofocus': True})
    message = TextAreaField('Message')
    emails = FieldList(FormField(EmailsForm), min_entries = 2)
    submit = SubmitField()

class AddSpaceForm(FlaskForm):
    space = StringField('Space', validators=[DataRequired()], render_kw={'autofocus': True})
    message = TextAreaField('Message')
    emails = FieldList(FormField(EmailsForm), min_entries = 2)
    submit = SubmitField()

class DeleteSpaceForm(FlaskForm):
    space = SelectMultipleField('Space')
    submit = SubmitField()

class DeleteMessagesForm(FlaskForm):
    space = SelectField('Space', render_kw={'autofocus': True})
    messages = SelectMultipleField('Messages')
    submit = SubmitField()

class OOOForm(FlaskForm):
    message = TextAreaField('Message')
    end_date = DateTimeField('End Date', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    TZ_Offset = IntegerField('TZ Offset')
    OOO_enabled = BooleanField('Enabled')
    Direct = BooleanField('Direct')
    Mentions = BooleanField('Mentions')
    submit = SubmitField()

class Webex_Meetings(FlaskForm):
    type = SelectField('Report Type', choices=[('meet', 'Meetings'), ('event', 'Events')])
    start_date = DateField('Start Date', default=date.today)