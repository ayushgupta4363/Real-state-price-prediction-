import os
import json
import urllib.parse
import streamlit as st
import bcrypt
import requests
import db
import util

st.set_page_config(page_title="Bangalore House Price Predictor", layout="wide")

# Initialize database
db.init_db()

# --- 1. Load Google Client Secrets (Cloud st.secrets fallback to local JSON) ---
# --- 1. Load Google Client Secrets (Cloud st.secrets fallback to local JSON) ---
base_dir = os.path.dirname(__file__)
client_secrets_file = os.path.join(base_dir, "client_secret.json")

# Safely check if Streamlit secrets exist
has_cloud_secrets = False
try:
    if "google_oauth" in st.secrets:
        has_cloud_secrets = True
except Exception:
    has_cloud_secrets = False

if has_cloud_secrets:
    # Read and aggressively strip all spaces, newlines, and carriage returns
    raw_id = str(st.secrets["google_oauth"]["client_id"])
    raw_secret = str(st.secrets["google_oauth"]["client_secret"])
    raw_uri = str(st.secrets["google_oauth"]["redirect_uri"])

    CLIENT_ID = "".join(raw_id.split())
    CLIENT_SECRET = "".join(raw_secret.split())
    REDIRECT_URI = "".join(raw_uri.split())

    AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URI = "https://oauth2.googleapis.com/token"
elif os.path.exists(client_secrets_file):
    with open(client_secrets_file, "r") as f:
        client_config = json.load(f)["web"]
    CLIENT_ID = client_config["client_id"].strip()
    CLIENT_SECRET = client_config["client_secret"].strip()
    REDIRECT_URI = client_config["redirect_uris"][0].strip()
    AUTH_URI = client_config.get("auth_uri", "https://accounts.google.com/o/oauth2/auth")
    TOKEN_URI = client_config.get("token_uri", "https://oauth2.googleapis.com/token")
else:
    st.error("Missing OAuth credentials. Set [google_oauth] in Streamlit Secrets or provide client_secret.json.")
    st.stop()

USERINFO_URI = "https://openidconnect.googleapis.com/v1/userinfo"

# --- 2. Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

# --- 3. Handle OAuth Callback Exchange (Direct HTTP POST) ---
query_params = st.query_params
if "code" in query_params and not st.session_state["authenticated"]:
    auth_code = query_params["code"]
    try:
        # Exchange authorization code for tokens directly
        token_payload = {
            "code": auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(TOKEN_URI, data=token_payload)
        token_data = token_response.json()

        if "access_token" in token_data:
            access_token = token_data["access_token"]
            
            # Fetch user email profile from OpenID Connect endpoint
            user_response = requests.get(
                USERINFO_URI,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_info = user_response.json()
            oauth_email = user_info.get("email")

            if oauth_email:
                # Save user to SQLite if first time
                if not db.get_user_by_email(oauth_email):
                    db.register_user(oauth_email, password_hash=None, provider="google")
                
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = oauth_email
                st.query_params.clear()
                st.rerun()
        else:
            st.error(f"Google Token Error: {token_data.get('error_description', 'Failed to retrieve access token')}")
            st.query_params.clear()

    except Exception as e:
        st.error(f"Google Authentication Failed: {e}")
        st.query_params.clear()

# --- Custom Styling ---
st.markdown("""
    <style>
    .auth-title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 1.2rem;
    }
    .divider-text {
        text-align: center;
        font-size: 0.8rem;
        color: #888;
        margin: 1.2rem 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .google-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        width: 100%;
        background-color: #ffffff;
        color: #3c4043 !important;
        font-weight: 500;
        font-size: 0.95rem;
        padding: 10px 16px;
        border-radius: 8px;
        border: 1px solid #dadce0;
        text-decoration: none !important;
        box-shadow: 0 1px 2px rgba(60,64,67,0.1);
        transition: background-color 0.2s, box-shadow 0.2s;
    }
    .google-btn:hover {
        background-color: #f8f9fa;
        box-shadow: 0 1px 3px rgba(60,64,67,0.25);
        text-decoration: none !important;
        color: #202124 !important;
    }
    .google-icon {
        width: 18px;
        height: 18px;
        flex-shrink: 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. Unauthenticated View (Login / Register / Google OIDC) ---
if not st.session_state["authenticated"]:
    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        with st.container(border=True):
            if st.session_state["auth_mode"] == "login":
                email = st.text_input("Email Address", placeholder="you@company.com").strip().lower()
                password = st.text_input("Password", type="password")

                if st.button("Sign In", type="primary", use_container_width=True):
                    if not email or not password:
                        st.warning("Please fill in both fields.")
                    else:
                        user = db.get_user_by_email(email)
                        if user and user[1]:
                            stored_hash = user[1].encode("utf-8")
                            if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
                                st.session_state["authenticated"] = True
                                st.session_state["user_email"] = email
                                st.rerun()
                            else:
                                st.error("Invalid email or password.")
                        elif user and not user[1]:
                            st.info("This account was created with Google Sign-In. Use Google button below.")
                        else:
                            st.error("Account not found. Please register below.")

                st.write("")
                col_text, col_link = st.columns([1.6, 1])
                with col_text:
                    st.write("Don't have an account?")
                with col_link:
                    if st.button("Register here", type="tertiary"):
                        st.session_state["auth_mode"] = "signup"
                        st.rerun()

            else:
                st.markdown("<div class='auth-title'>Create an Account</div>", unsafe_allow_html=True)
                email = st.text_input("Email Address", placeholder="you@company.com").strip().lower()
                password = st.text_input("Password", type="password")

                if st.button("Register & Sign In", type="primary", use_container_width=True):
                    if not email or not password:
                        st.warning("Please fill in both fields.")
                    elif "@" not in email or "." not in email:
                        st.error("Please enter a valid email address.")
                    else:
                        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                        success = db.register_user(email, hashed_pw, provider="local")
                        if success:
                            st.session_state["authenticated"] = True
                            st.session_state["user_email"] = email
                            st.rerun()
                        else:
                            st.error("An account with this email already exists.")

                st.write("")
                col_text, col_link = st.columns([1.6, 1])
                with col_text:
                    st.write("Already have an account?")
                with col_link:
                    if st.button("Sign in here", type="tertiary"):
                        st.session_state["auth_mode"] = "login"
                        st.rerun()

            st.markdown("<div class='divider-text'>─── Or Continue With ───</div>", unsafe_allow_html=True)

            # Direct Standard OAuth2 Authorization URL Construction
            oauth_params = {
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "consent",
            }
            auth_url = f"{AUTH_URI}?{urllib.parse.urlencode(oauth_params)}"

            st.markdown(
                f"""
                <a href="{auth_url}" target="_top" class="google-btn">
                    <svg class="google-icon" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                    </svg>
                    <span>Sign in with Google</span>
                </a>
                """,
                unsafe_allow_html=True
            )

# --- 5. Authenticated Dashboard View ---
else:
    header_col, user_col, logout_col = st.columns([3, 1.2, 0.8])
    with header_col:
        st.title("🏡 Bangalore House Price Predictor")
    with user_col:
        st.write("")
        st.write(f"👤 `{st.session_state['user_email']}`")
    with logout_col:
        st.write("")
        if st.button("Sign Out", type="secondary", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["user_email"] = None
            st.query_params.clear()
            st.rerun()

    st.write("Enter the details of the property to get an estimated price.")
    st.divider()

    # Load ML artifacts once
    if "data_loaded" not in st.session_state:
        util.load_saved_artifacts()
        st.session_state["data_loaded"] = True
        st.session_state["locations"] = util.get_location_names()

    col1, col2 = st.columns(2)
    with col1:
        total_sqft = st.number_input("Total Square Feet", min_value=300, max_value=50000, value=1000)
        location = st.selectbox("Location", options=st.session_state["locations"])
    with col2:
        bhk = st.radio("BHK", options=[1, 2, 3, 4, 5], index=1, horizontal=True)
        bath = st.radio("Bathrooms", options=[1, 2, 3, 4, 5], index=1, horizontal=True)

    if st.button("Estimate Price", type="primary"):
        try:
            price = util.get_estimated_price(location, total_sqft, bhk, bath)
            st.success(f"### The estimated price is ₹ {price} Lakhs")
        except Exception as e:
            st.error(f"Error in prediction: {e}")