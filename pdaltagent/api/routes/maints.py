import hashlib
import json
import time

from flask import Blueprint, jsonify, current_app, request
from flask_security import auth_required, roles_required, hash_password, current_user

maints_blueprint = Blueprint('maints', __name__, url_prefix='/maints')

def md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def require_json(f):
    def decorated_function(*args, **kwargs):
        if request.headers.get('Accept') != 'application/json':
            return jsonify({'error': 'Unsupported Media Type'}), 415
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@maints_blueprint.route("/", methods=["GET"])
@require_json
@auth_required()
def list_maints():
    return jsonify(current_app.enrich.maintenances)

@maints_blueprint.route("/", methods=["POST"])
@require_json
@auth_required()
def add_maint():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    for k in ["name", "start", "end", "condition", "frequency"]:
        if not data.get(k):
            return jsonify({"status": "error", "message": f"Missing required field: {k}"}), 400
    if not data.get("frequency").lower() in ["once", "daily", "weekly"]:
        return jsonify({"status": "error", "message": "Invalid frequency"}), 400
    if data.get("frequency").lower() != "once" and not data.get("frequency_data", {}).get("duration"):
        return jsonify({"status": "error", "message": "Missing required field: duration"}), 400
    if not data.get('id'):
        # set id to md5 of the data
        data['id'] = md5_hash(json.dumps(data))
    if not data.get('maintenance_key'):
        data['maintenance_key'] = 'MNT-' + md5_hash(json.dumps(data))[-12:]
    data['created_by'] = current_user.email
    data['created_at'] = int(time.time())
    data['updated_by'] = current_user.email
    data['updated_at'] = int(time.time())
    print(json.dumps(data, indent=2))
    r = current_app.enrich.add_maint(data)
    del r['_id']
    return jsonify({"status": "ok", "data": r})

@maints_blueprint.route("/<id>", methods=["DELETE"])
@auth_required()
def delete_maint(id):
    print(f"Deleting {id}")
    current_app.enrich.delete_maint(id)
    return jsonify({"status": "ok"})

@maints_blueprint.route("/<id>", methods=["PUT"])
@auth_required()
def update_maint(id):
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    print(f"Updating {id}")
    data['updated_by'] = current_user.email
    data['updated_at'] = int(time.time())
    current_app.enrich.update_maint(id, data)
    return jsonify({"status": "ok"})