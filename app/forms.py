from flask_wtf import FlaskForm
from wtforms import FieldList, validators, ValidationError
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, FormField, SubmitField, DateField, SelectField, SelectMultipleField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Required
from app.models import Email
from datetime import date

class SelectSpaceForm(FlaskForm):
    space = SelectField('Space', render_kw={'autofocus': True})
    activate_date = DateField('Activation Date', default=date.today)
    message = TextAreaField('Message')
    submit = SubmitField()

class EmailForm(NoCsrfForm):
    # this forms is never exposed so we can user the non CSRF version
    email_address = StringField('Email Address', [validators.DataRequired(), validators.Email("Please enter a valid email address.")], render_kw={'autofocus': True})

class AddSpaceForm(FlaskForm):
    space = StringField('Space', validators=[DataRequired()], render_kw={'autofocus': True})
    activate_date = DateField('Activation Date', default=date.today)
    message = TextAreaField('Message')
    submit = SubmitField()

class CombinedForm(FlaskForm):
    spacename = StringField('Space', validators=[DataRequired()])
    activate_date = DateField('Activation Date', default=date.today)
    message = TextAreaField('Message')
    emails = FieldList(FormField(EmailForm, default=lambda: Email()))
    submit = SubmitField('Submit')

class DeleteSpaceForm(FlaskForm):
    space = SelectMultipleField('Space')
    submit = SubmitField()

class DeleteMessagesForm(FlaskForm):
    space = SelectField('Space', render_kw={'autofocus': True})
    messages = SelectMultipleField('Messages')
    submit = SubmitField()

class OOOForm(FlaskForm):
    end_date = DateField('End Date', default=date.today)
    message = TextAreaField('Message')
    OOO_enabled = BooleanField('Enabled')
    submit = SubmitField()