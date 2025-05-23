import streamlit as st
import bcrypt
import smtplib
from email.mime.text import MIMEText
import yaml
import uuid
import datetime
import os

TOKEN_FILE = "reset_tokens.yaml"

def load_users():
    with open("users.yaml", "r") as f:
        return yaml.safe_load(f)["users"]

def save_users(users):
    with open("users.yaml", "w") as f:
        yaml.safe_dump({"users": users}, f)

def send_reset_email(to_email, token):
    from_email = "selengetu@gmail.com"
    app_password = "vweepuccljudmkio"  # your Gmail app password
    subject = "Reset your password"
    body = f"""Hi,

Click the token below to reset your password:

{token}

If you didn’t request this, you can ignore this email.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, app_password)
        server.sendmail(from_email, to_email, msg.as_string())

def save_token(email, token):
    tokens = []

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded and "tokens" in loaded:
                tokens = loaded["tokens"]

    tokens.append({
        "email": email,
        "token": token,
        "expires": (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat()
    })

    with open(TOKEN_FILE, "w") as f:
        yaml.safe_dump({"tokens": tokens}, f)

def verify_token(token):
    if not os.path.exists(TOKEN_FILE):
        return None

    with open(TOKEN_FILE, "r") as f:
        tokens = yaml.safe_load(f).get("tokens", [])

    now = datetime.datetime.utcnow()
    for entry in tokens:
        if entry["token"] == token:
            if datetime.datetime.fromisoformat(entry["expires"]) > now:
                return entry["email"]
    return None

def update_password(email, new_password):
    users = load_users()
    for user in users:
        if user["email"] == email:
            user["password"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            save_users(users)
            return True
    return False

# Streamlit UI


st.title("🔐 Forgot or Reset Password")

view = st.sidebar.radio("View", ["Request Reset Link", "Reset Form"])

if view == "Request Reset Link":
    email = st.text_input("Enter your email")
    if st.button("Send Reset Link"):
        users = load_users()
        if any(u["email"] == email for u in users):
            token = str(uuid.uuid4())
            save_token(email, token)
            send_reset_email(email, token)
            st.success("✅ Reset link sent to your email.")
        else:
            st.error("Email not found.")

elif view == "Reset Form":
    token = st.text_input("Enter reset token from your email")
    new_pw = st.text_input("New Password", type="password")
    confirm_pw = st.text_input("Confirm Password", type="password")

    if st.button("Reset Password"):
        if new_pw != confirm_pw:
            st.error("Passwords do not match.")
        else:
            email = verify_token(token)
            if email:
                update_password(email, new_pw)
                st.success(f"✅ Password updated for {email}.")
            else:
                st.error("Invalid or expired token.")
