from flask_wtf import FlaskForm
from wtforms import FieldList, validators, ValidationError, widgets
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, FormField, SubmitField, DateField, SelectField, SelectMultipleField, TextAreaField, BooleanField, IntegerField, DateTimeField, PasswordField
from wtforms.validators import DataRequired, Email, Required

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()