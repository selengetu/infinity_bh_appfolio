import streamlit as st
import dashboard  # Import the dashboard module
# Set page layout
st.set_page_config(page_title="Appfolio Dashboards", layout="wide")

def check_login(email, password):
    default_user = {
        "email": "aaron@zuckermanautomationgroup.com",
        "password": "Pass12345",
        "name": "Test User"
    }
    if email == default_user["email"] and password == default_user["password"]:
        return {"name": default_user["name"], "email": default_user["email"]}
    return None

def main():
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Show login form
    if not st.session_state['logged_in']:
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
