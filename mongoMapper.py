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
    network_stream_protocol = me.StringField()
    compression_format = me.StringField()
    password = me.StringField()
    username = me.StringField()
    port = me.StringField()
    company = me.StringField()