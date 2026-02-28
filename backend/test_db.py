from database import SessionLocal
from models.models import User

def test_connection():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        print(f"Successfully connected! Found demo user: {user.id}")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
