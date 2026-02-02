
import sys
import os
sys.path.append(os.getcwd())
from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f"Found {len(users)} users.")
    for u in users:
        print(f"User: {u.username} | is_admin: {u.is_admin}")
        print(f"  Roles: {[r.name for r in u.roles]}")
        # print(f"  Permissions: {[p.name for r in u.roles for p in r.permissions]}")
