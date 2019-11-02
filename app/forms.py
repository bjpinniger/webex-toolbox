from flask_wtf import FlaskForm
from wtforms import FieldList, validators, ValidationError
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, FormField, SubmitField, DateField, SelectField, SelectMultipleField, TextAreaField, BooleanField, IntegerField, DateTimeField, PasswordField
from wtforms.validators import DataRequired, Email, Required
from datetime import date
from app.custom_forms import MultiCheckboxField

class EmailsForm(FlaskForm):
    email_address = StringField('Email Address')

class ManageSpaceForm(FlaskForm):
    space = SelectField('Space', render_kw={'autofocus': True})
    filter = StringField('Filter')
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
    filter = StringField('Filter')
    submit = SubmitField()

class DeleteMessagesForm(FlaskForm):
    space = SelectField('Space', render_kw={'autofocus': True})
    filter = StringField('Filter')
    messages = SelectMultipleField('Messages')
    #messages = MultiCheckboxField('Messages')
    submit = SubmitField()

class OOOForm(FlaskForm):
    message = TextAreaField('Message')
    end_date = DateTimeField('End Date', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    TZ_Offset = IntegerField('TZ Offset')
    TZ_Name = StringField('TZ Offset')
    OOO_enabled = BooleanField('Enabled')
    Direct = BooleanField('Direct')
    Mentions = BooleanField('Mentions')
    submit = SubmitField()

class Webex_Meetings(FlaskForm):
    type = SelectField('Report Type', choices=[('meet', 'Meetings'), ('event', 'Events')])
    start_date = DateField('Start Date', default=date.today)

class SettingsForm(FlaskForm):
    site_name = StringField('Site Name', render_kw={'autofocus': True})
    user_email = StringField('User Email', validators=[Email()])
    user_pwd = PasswordField('Password')
    sortBy = SelectField('Sort By', choices=[('created', 'Created'), ('lastactivity', 'Last Activity')])
    maxResults = IntegerField('Max Results')
    submit = SubmitField()

