#!/usr/bin/env python3

import os
import xmlrpc.client
import requests
import uuid

from pdaltagent.config import MONGODB_URL, SUPERVISOR_URL, PDAGENTD_ADMIN_USER, PDAGENTD_ADMIN_PASS, PDAGENTD_ADMIN_DB
from pdaltagent.enrichment import Enrichment

from pdaltagent.api.routes.users import users_blueprint
from pdaltagent.api.routes.maints import maints_blueprint

from pdaltagent.api.models.security import User, Role

from flask import Flask, Response, redirect, render_template_string, send_from_directory, request, jsonify
import flask_wtf
from mongoengine import connect
from mongoengine.errors import NotUniqueError

from flask_security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, auth_required, hash_password, permissions_accepted, current_user
class Api:
    def __init__(self):
        # Create app
        self.app = Flask(
            __name__,
        )

        # dev mode settings
        self.DEV = os.getenv('DEV', 'false').lower() in ['true', '1']
        self.VITE_DEV_SERVER_URL = os.getenv('VITE_DEV_SERVER_URL', 'http://localhost:5173')

        # Generate a nice key using secrets.token_urlsafe()
        self.app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw')
        # Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
        # Generate a good salt using: secrets.SystemRandom().getrandbits(128)
        self.app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", '146585145368132386173505678016728509634')
        # Don't worry if email has findable domain
        self.app.config["SECURITY_EMAIL_VALIDATOR_ARGS"] = {"check_deliverability": False}

        flask_wtf.CSRFProtect(self.app)

        self.app.config.update(
            SECURITY_FLASH_MESSAGES=False,
            WTF_CSRF_CHECK_DEFAULT=False,
            SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS=True,
        )

        self.app.url_map.strict_slashes = False

        # Create database connection object
        self.app.db = connect(alias=PDAGENTD_ADMIN_DB, db=PDAGENTD_ADMIN_DB, host=MONGODB_URL)

        # Setup Flask-Security
        self.app.user_datastore = MongoEngineUserDatastore(self.app.db, User, Role)
        self.app.security = Security(self.app, self.app.user_datastore)

        self.app.enrich = Enrichment(MONGODB_URL)

        self.setup_admin_user()
        self.setup_routes()

    # proxy request to vite dev server for dev mode
    def proxy_request(self, path):
        url = f"{self.VITE_DEV_SERVER_URL}/{path}"
        headers = {key: value for (key, value) in request.headers if key != 'Host'}
        headers['Host'] = self.VITE_DEV_SERVER_URL

        # Stream=True makes the request without immediately downloading the response body.
        # This allows us to proxy the response.
        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True
        )

        # Exclude certain headers from being forwarded
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in response.raw.headers.items() if name.lower() not in excluded_headers]

        # Create a new response object passing through the proxied response's content
        proxied_response = Response(response.content, response.status_code, headers)

        return proxied_response

    # Restart all processes managed by supervisord in the "workers" group
    def restart_all(self):
        # XML-RPC server endpoint with authentication and over HTTP
        server = xmlrpc.client.ServerProxy(SUPERVISOR_URL)

        # Connect to the supervisord server
        try:
            info = server.supervisor.getState()
            print("Supervisor state: ", info)
        except ConnectionError as e:
            print("Failed to connect to supervisord:", e)
            return

        # Restart all processes
        try:
            print("Restarting all managed processes...")
            server.supervisor.stopProcessGroup('workers', True)
            server.supervisor.startProcessGroup('workers', True)
        except Exception as e:
            print("Error restarting processes:", e)

    def setup_routes(self):
        self.app.register_blueprint(users_blueprint)
        self.app.register_blueprint(maints_blueprint)

        @self.app.route("/restart", methods=["POST"])
        @auth_required()
        def restart():
            self.restart_all()
            return jsonify({"status": "ok"})

        @self.app.route("/")
        @self.app.route("/<path:subpath>")
        # @auth_required()
        def home(subpath='index.html'):
            try:
                if self.DEV:
                    return self.proxy_request(subpath)
                return send_from_directory(os.path.join(self.app.root_path, 'static'), subpath)
            except Exception as e:
                print(f"Error: {e}")
                return "An internal error occurred on home", 500

    # Create default roles and admin user from environment variables
    def setup_admin_user(self):
        # one time setup
        with self.app.app_context():
            # Create default roles and admin user
            try:
                self.app.security.datastore.find_or_create_role(
                    name="user", permissions={"user-read", "user-write"}
                )
                self.app.security.datastore.find_or_create_role(
                    name="admin", permissions={"admin", "user-read", "user-write"}
                )
            except NotUniqueError:
                print("Roles already exist")

            if not self.app.security.datastore.find_user(email=PDAGENTD_ADMIN_USER):
                print(f"Creating admin user {PDAGENTD_ADMIN_USER}")
                try:
                    self.app.security.datastore.create_user(
                        id=str(uuid.uuid4()),
                        email=PDAGENTD_ADMIN_USER,
                        password=hash_password(PDAGENTD_ADMIN_PASS),
                        roles=["user", "admin"]
                    )
                except NotUniqueError:
                    print(f"User {PDAGENTD_ADMIN_USER} already exists")
            else:
                print(f"Admin user {PDAGENTD_ADMIN_USER} already exists")

    def get_app(self):
        print("App created")
        return self.app

# WSGI entry point
app_instance = Api()
app = app_instance.get_app()

if __name__ == '__main__':
    app.run()
