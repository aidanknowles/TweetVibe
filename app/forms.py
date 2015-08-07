from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired


class SearchFrom(Form):
    """
    WTForms model for the homepage search form.
    """

    keyword = StringField('keyword', validators=[DataRequired()])
    count = StringField('count')
    location = StringField('user')

