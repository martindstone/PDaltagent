from mongoengine import Document, connect
from mongoengine.fields import (
    # BinaryField,
    BooleanField,
    DateTimeField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)
from flask_security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, auth_required, hash_password, permissions_accepted, current_user

from pdaltagent.config import PDAGENTD_ADMIN_DB

class Role(Document, RoleMixin):
    name = StringField(max_length=80, unique=True)
    description = StringField(max_length=255)
    permissions = ListField(required=False)
    meta = {"db_alias": PDAGENTD_ADMIN_DB}

class User(Document, UserMixin):
    id = StringField(primary_key=True)
    email = StringField(max_length=255, unique=True)
    password = StringField(max_length=255)
    active = BooleanField(default=True)
    fs_uniquifier = StringField(max_length=64, unique=True)
    confirmed_at = DateTimeField()
    roles = ListField(ReferenceField(Role), default=[])
    meta = {"db_alias": PDAGENTD_ADMIN_DB}
