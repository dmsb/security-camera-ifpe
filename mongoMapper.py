import mongoengine as me

class User(me.Document):
    _id: me.ObjectIdField()
    username = me.StringField(required=True)
    password = me.StringField(required=True)
    name = me.StringField(required=True)

class Camera(me.Document):
    _id: me.ObjectIdField()
    macAddress = me.StringField(required=True)