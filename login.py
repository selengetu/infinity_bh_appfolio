import streamlit as st
from utils import check_login  # Import the check_login function
import dashboard  # Import the dashboard module
# Set page layout


def main():
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Show login form
    if not st.session_state['logged_in']:
        # Create layout with 2 columns
        col1, col2 = st.columns([3, 2])

        # Left column with illustration
        with col1:
            st.image("login_img.png", use_container_width=True)

        # Right column with login form
        with col2:
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            st.markdown("<h2>Hello!</h2>", unsafe_allow_html=True)
            st.markdown("**Login to Get Started**")

            # Login form
            email = st.text_input("Email Address", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")

            if st.button("Login"):
                user = check_login(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user  # Store the entire user object
                    #  IMPORTANT:  Do *not* call st.experimental_rerun() here.  Let the natural
                    #  Streamlit flow handle the update.
                else:
                    st.error("Invalid credentials")

            st.markdown('</div>', unsafe_allow_html=True)

            # Footer with forgot password link
            st.markdown('<div class="footer-text">', unsafe_allow_html=True)
            st.markdown('<p><a href="#">Forgot Password?</a></p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    #  Show dashboard if logged in
    if st.session_state['logged_in']:
        dashboard.show_dashboard()  # Call the dashboard function

if __name__ == "__main__":
    main()
