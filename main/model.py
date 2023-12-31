from main import app, datab, UserMixin, bcrypt, loginmanager

@loginmanager.user_loader #Required property for the users to be authenticated
def load_user(user_id):
    return User.query.get(user_id)

#Create class user with Database Model, create various columns
class User(datab.Model, UserMixin): #Use UserMixin class to add prexisting methods
    #Create id wtih primary key, and standard user details
    id = datab.Column(datab.Integer(), primary_key = True)
    username = datab.Column(datab.String(length = 45), nullable = False, unique = True)
    email_address = datab.Column(datab.String(), unique = True, nullable = False)
    password_hash = datab.Column(datab.String(), nullable = False)

    #Create a password property
    @property
    def password(self):
      return self.password
    
    @password.setter #Used to set the property of password into a hashed one using bcrypt class
    def password(self, plain_text_password):
      self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
    
    #Create a method that returns a boolean by checking an attempted password with the stored hash
    def check_password_correction(self, attempted_password):
      return bcrypt.check_password_hash(self.password_hash, attempted_password) #checks the hash password with the attempted one
    