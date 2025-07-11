import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from kittie_app import create_app, db
application = create_app()

with application.app_context():
    db.create_all()