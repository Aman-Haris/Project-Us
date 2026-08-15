import hmac
import streamlit as st


def check_password():
    def login_form():
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            st.markdown("""
            <div style="text-align:center; padding: 2.5rem 0 1.5rem;">
              <div style="font-size:4rem; margin-bottom:0.6rem;
                          filter: drop-shadow(0 0 20px rgba(255,107,74,0.35));">✈️</div>
              <div style="font-family:'Poppins',sans-serif; font-size:1.9rem;
                          font-weight:700; color:#2D2A32; margin-bottom:0.3rem;
                          letter-spacing:0.01em;">
                Travel Planner
              </div>
              <div style="color:#8B8594; font-size:0.9rem; margin-bottom:2rem;
                          letter-spacing:0.05em; text-transform:uppercase; font-size:0.75rem;">
                Your personal adventure tracker
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.form("Credentials"):
                st.text_input("👤  Username", key="username", placeholder="Enter username")
                st.text_input("🔑  Password", type="password", key="password",
                              placeholder="Enter password")
                st.form_submit_button("Sign In →", on_click=password_entered, width="stretch")

    def password_entered():
        try:
            username = st.session_state["username"].strip()
            password = st.session_state["password"]
            stored   = st.secrets["passwords"]
            # Case-insensitive username lookup so "sandra" matches "Sandra"
            matched  = next((u for u in stored if u.lower() == username.lower()), None)
            if matched and hmac.compare_digest(password, str(stored[matched])):
                st.session_state["password_correct"] = True
                st.session_state["logged_in_user"]   = matched  # use canonical casing
                del st.session_state["password"]
                del st.session_state["username"]
            else:
                st.session_state["password_correct"] = False
        except Exception:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 Incorrect username or password — please try again.")
    return False
