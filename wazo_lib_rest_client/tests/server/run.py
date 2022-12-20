# Copyright 2016-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os

from datetime import timedelta
from flask import Flask, send_from_directory
from flask_httpauth import HTTPDigestAuth

ROOT = os.path.dirname(os.path.realpath(__file__))

USERS = {'username': 'password'}

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(seconds=1)

auth = HTTPDigestAuth()


@auth.get_password
def get_password(username):
    return USERS.get(username)


@app.route('/auth/<path:path>')
@auth.login_required
def auth(path):
    return send_from_directory(ROOT, path)


@app.route('/<path:path>')
def root(path):
    print(path)
    return send_from_directory(ROOT, path)


if __name__ == "__main__":
    app.run(port=8000)
