from flask import Blueprint, jsonify, current_app, request
from flask_security import auth_required, roles_required, hash_password, current_user

import uuid
from mongoengine.errors import NotUniqueError

from pdaltagent.config import PDAGENTD_ADMIN_USER
from pdaltagent.api.models.security import User
users_blueprint = Blueprint('users', __name__, url_prefix='/users')

# list users
@users_blueprint.route('/')
@auth_required()
def list_users():
    # Implement your logic here
    return jsonify([{"id": user.id, "email": user.email, "roles": [r.name for r in user.roles]} for user in User.objects])

# me
@users_blueprint.route('/me')
@auth_required()
def me():
    user = User.objects.get(email=current_user.email)
    return jsonify({"email": user.email, "roles": [r.name for r in user.roles]})

# add user
@users_blueprint.route('/', methods=["POST"])
@roles_required('admin')
def add_user():
    # get the JSON post body
    data = request.json
    try:
        email = data["email"]
        password = data["password"]
        roles = data["roles"]
    except KeyError:
        return jsonify({"status": "error", "message": "Missing required field"}), 400

    try:
        current_app.security.datastore.create_user(
            id=str(uuid.uuid4()),
            email=email,
            password=hash_password(password),
            roles=roles
        )
        return jsonify({"status": "ok"})
    except NotUniqueError:
        print(f"User {email} already exists")
        return jsonify({"status": "error", "message": "User already exists"}), 400
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({"status": "error", "message": "Error creating user"}), 500

# delete user by email
@users_blueprint.route('/<email>', methods=["DELETE"])
@roles_required('admin')
def delete_user(email):
    user = User.objects.get(email=email)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    if email == PDAGENTD_ADMIN_USER:
        return jsonify({"status": "error", "message": "Cannot delete default admin user"}), 400
    try:
        user.delete()
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({"status": "error", "message": "Error deleting user"}), 500
    return jsonify({"status": "ok"})

# update user by email
@users_blueprint.route('/<email>', methods=["PUT"])
@roles_required('admin')
def update_user(email):
    user = User.objects.get(email=email)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    if email == PDAGENTD_ADMIN_USER:
        return jsonify({"status": "error", "message": "Cannot update default admin user"}), 400
    data = request.json
    try:
        if data.get("password"):
            user.password = hash_password(data["password"])
        if data.get("roles"):
            role_objs = [current_app.security.datastore.find_role(r) for r in data["roles"]]
            user.roles = role_objs
        user.save()
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Error updating user: {e}")
        return jsonify({"status": "error", "message": "Error updating user"}), 500