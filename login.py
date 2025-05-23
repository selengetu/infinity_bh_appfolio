from reset_password import save_token, verify_token, update_password, send_reset_email
import uuid
import datetime
import streamlit as st
import dashboard  # Import the dashboard module
import yaml
import bcrypt
# Set page layout
st.set_page_config(page_title="Appfolio Dashboards", layout="wide", page_icon="logo.png")

def load_users():
    with open("users.yaml", "r") as f:
        return yaml.safe_load(f)["users"]

def check_login(email, password):
    users = load_users()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    print("Paste this into users.yaml:", hashed)

    for user in users:

        try:
            match = bcrypt.checkpw(password.encode(), user["password"].encode())
            print("Password match:", match)
        except Exception as e:
            print("❌ bcrypt error:", e)
            continue

        if user["email"] == email and match:
            return {"name": user["name"], "email": user["email"]}

    return None

def main():
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Show login form
    if not st.session_state['logged_in']:
        if not st.session_state['logged_in']:

            view = st.radio("Select Option", ["Login", "Forgot Password", "Reset Password"])

            if view == "Login":
                # Create layout with 2 columns
                col1, col2 = st.columns([1,1])

                # Left column with illustration
                with col1:
                    st.image("login_img.png")

                # Right column with login form
                with col2:
                    st.markdown('<div class="form-container">', unsafe_allow_html=True)
                    st.markdown("<h2>Hello!</h2>", unsafe_allow_html=True)
                    st.markdown("**Login to Get Started**")

                    # Login form
                    email = st.text_input("Email Address", placeholder="Enter your email",  key="login_email")
                    password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

                    if st.button("Login"):
                        user = check_login(email, password)
                        if user:
                            # Handle tuple or dict formats safely
                            if isinstance(user, dict):
                                st.session_state.user = user
                            elif isinstance(user, tuple) and len(user) >= 2:
                                name = user[0]
                                email = user[1]
                                st.session_state.user = {"name": name, "email": email}
                            else:
                                st.error("Unexpected user format")
                                return

                            st.session_state.logged_in = True
                            st.rerun()
                        else:
                            st.error("Invalid credentials")

                    st.markdown('</div>', unsafe_allow_html=True)

                    # Footer with forgot password link
                    st.markdown('<div class="footer-text">', unsafe_allow_html=True)
                    st.markdown('<p><a href="#">Forgot Password?</a></p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            elif view == "Forgot Password":
                email = st.text_input("Enter your email to get a reset token")
                if st.button("Generate Reset Token"):
                    users = load_users()
                    if any(u["email"] == email for u in users):
                        token = str(uuid.uuid4())
                        save_token(email, token)

                        try:
                            send_reset_email(email, token)
                            st.success("✅ Reset token sent to your email.")
                            # Optional: still show for testing
                            # st.info("For testing/dev, here is your token:")
                            # st.code(token)
                        except Exception as e:
                            st.error(f"❌ Failed to send email: {e}")
                else:
                    st.error("Email not found.")
            elif view == "Reset Password":
                    token = st.text_input("Enter your reset token")
                    new_pw = st.text_input("New Password", type="password")
                    confirm_pw = st.text_input("Confirm New Password", type="password")

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
       

    #  Show dashboard if logged in
    if st.session_state['logged_in']:
        st.sidebar.success(f"Logged in as {st.session_state.user['email']}")
        
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

        dashboard.show_dashboard()  # Call the dashboard function

if __name__ == "__main__":
    main()
