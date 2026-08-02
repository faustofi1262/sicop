import os
import psycopg2


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))
from functools import wraps

from flask import session, redirect, url_for


def login_required(role=None):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            if "user_id" not in session:
                return redirect(
                    url_for("main.login_form")
                )

            if role and session.get("rol") != role:
                return redirect(
                    url_for("main.login_form")
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator