from app import app, db

# creates tables specified in models.py
with app.app_context():
    db.create_all()
    print("All tables should have been created now.")
