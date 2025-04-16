import psycopg2
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(email, password):
    hashed_pw = hash_password(password)
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="appfolio_db",  # Replace with your actual database name
            user="postgres",  # Replace with your username
            password="123"  # Replace with your password (use env vars in production!)
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, hashed_pw))
        user = cur.fetchone()  # Fetch the user data
        cur.close()
        conn.close()
        return user  # Return the user data (or None if not found)
    except Exception as e:
        print(f"Database error: {e}")  # Log the error
        return None  # Return None on error