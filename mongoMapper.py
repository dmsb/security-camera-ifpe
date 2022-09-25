import mongoengine as me

class User(me.Document):
    _id = me.ObjectIdField()
    username = me.StringField(required=True)
    password = me.StringField(required=True)
    name = me.StringField(required=True)

class Camera(me.Document):
    _id = me.ObjectIdField()
    mac_address = me.StringField(required=True)
    department = me.StringField()
    location = me.StringField()
    specific_location = me.StringField()
    brand = me.StringField()
    model = me.StringField()
    is_enabled = me.BooleanField()

class google_token(me.Document):
    _id = me.ObjectIdField()
    token_uri = me.StringField()
    client_id = me.StringField()
    client_secret = me.StringField()
    scopes = me.ListField()
    token = me.StringField()
    refresh_token = me.StringField()
    expiry = me.DateTimeField()
    authorization_code = me.StringField()
    state = me.StringField()