
import sys
import traceback

try:
    print("Importing create_app...")
    from app import create_app, db
    
    print("Creating app with 'testing' config...")
    app = create_app('testing')
    
    print("Pushing app context...")
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database created successfully.")
        
        from app.models.user import User
        print("Creating user...")
        u = User(username='test', email='test@test.com')
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()
        print("User created.")
        
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc(limit=1)
