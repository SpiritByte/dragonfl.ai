from main import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError

#Obtain user class from models
from main.model import User

class Register(FlaskForm):
  def validate_username(self, username_to_check):
    user = User.query.filterby(username = username_to_check)

    if user:
      raise ValidationError("Username Already Exists")  #Creates an error that will be used in the flash messages for validators 

    def validate_email_address(self, address_to_check):
        user = User.query.filter_by(email_address = address_to_check.data).first()

        if user:
            raise ValidationError("Email already used!")  

    #Create fields with various validators such as certain length, nullable = false  
    username = StringField(label = "Username", validators = [Length(min=2, max=30), DataRequired()])
    email_address = StringField(label = "Email", validators = [Email(), DataRequired()])
    password = PasswordField(label = "Password", validators = [Length(min=6), DataRequired()])
    password_confirm = PasswordField(label = "Password Confirmation", validators = [EqualTo('password'), DataRequired()])

    submit = SubmitField(label = "Create Account")


class LoginForm(FlaskForm): 
    username = StringField(label = "Username", validators = [Length(min=2, max=30), DataRequired()])
    password = PasswordField(label = "Password", validators = [Length(min=6), DataRequired()])
    submit = SubmitField(label = "Login")