import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template_string, session, url_for

# Load configuration from .env
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("AUTH0_SECRET")

# Initialize Authlib client
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# Shared HTML Navigation Bar
NAV_BAR = """
<nav>
    <a href="/">Home</a> | 
    <a href="/protected">Protected Page</a>
</nav>
<hr>
"""

# 1. Home Route
@app.route("/")
def home():
    user = session.get("user")
    head = "<!DOCTYPE html><title>CST8919 - Auth0 App</title>"

    if user:
        return render_template_string(f"""
            {head}
            <h1>Welcome to the CST8919 Auth0 App</h1>
            {NAV_BAR}
            <h3>Hello, {user['userinfo']['name']}!</h3>
            <p><a href="/logout">Log Out</a></p>
            <h4>Your Auth0 Profile Data:</h4>
            <pre>{json.dumps(user['userinfo'], indent=2)}</pre>
        """)

    return render_template_string(f"""
        {head}
        <h1>Welcome to the CST8919 Auth0 App</h1>
        {NAV_BAR}
        <h3>You are not logged in.</h3>
        <p><a href="/login">Log In Here</a></p>
    """)

# 2. Login Route
@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

# 3. Callback Route
@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect(url_for("home"))

# 4. Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# 5. REQUIRED LAB CUSTOMIZATION: Protected route with middleware logic
@app.route("/protected")
def protected():
    user = session.get("user")
    
    # Interceptor: If no user session is found, redirect straight to login
    if not user:
        return redirect(url_for("login"))
        
    head = "<!DOCTYPE html><title>Protected Dashboard</title>"
    return render_template_string(f"""
        {head}
        <h1>🔒 Protected Dashboard</h1>
        {NAV_BAR}
        <h2>Access Granted!</h2>
        <p>This page is hidden behind Auth0 authentication middleware fallback logic.</p>
        <p><strong>Logged in securely as:</strong> {user['userinfo']['email']}</p>
        <p><a href="/logout">Log Out</a></p>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(env.get("PORT", 3000)), debug=True)