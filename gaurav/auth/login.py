import streamlit as st
import hashlib
import pandas as pd
import auth as gu_auth
import lang as gu_lang
import ui as gu_css
import sqlite3
import bcrypt
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

# Define the path for the database inside the 'auth' folder
db_path = os.path.join('auth', 'users.db')

# Function to send email using Hostinger SMTP server
def send_email_via_hostinger(receiver_email, subject, body):
    smtp_server = "smtp.hostinger.com"  # Hostinger SMTP server
    smtp_port = 587  # Port for TLS

    sender_email = "info@shavgun.com"  # Your full email address
    password = "Lapu971915@#"  # The password you set for the email account
    # Create the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Set up SSL context
    context = ssl.create_default_context()

    try:
        # Connect to the Hostinger SMTP server using TLS
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)  # Start TLS encryption
            server.login(sender_email, password)  # Login with your email credentials
            server.sendmail(sender_email, receiver_email, message.as_string())  # Send email
            print("Email sent successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
        
        
def create_auth_folder_and_db():
    # Check if the 'auth' folder exists, if not, create it
    if not os.path.exists('auth'):
        os.makedirs('auth')
    
    # Check if the database file exists, if not, create it
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create the 'users' table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            permissions TEXT NOT NULL,
            email TEXT NOT NULL,
            is_root BOOLEAN NOT NULL DEFAULT 0,
            full_name TEXT
        )
    ''')
    
    # Check if the 'is_root' column exists, and add it if it doesn't
    c.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in c.fetchall()]
    if 'is_root' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN is_root BOOLEAN NOT NULL DEFAULT 0')
    if 'full_name' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN full_name TEXT')
    conn.commit()
    conn.close()
    

    # Add default root user (Harsh) if no users exist
    if not check_if_users_exist():
        add_user('Harsh', '9838', 'Admin', ['overview', 'inventory_status', 'shipment_planning', 'loss_analysis', 'profit_analysis', 'max_drr', 'drr_timeline', 'labels', 'manage_users'], 'lapu630@gmail.com', is_root=True)

def add_user(username, password, role, permissions, email, is_root=False):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        c.execute('INSERT INTO users (username, password_hash, role, permissions, email, is_root) VALUES (?, ?, ?, ?, ?, ?)', 
                  (username, password_hash, role, ','.join(permissions), email, is_root))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"User '{username}' already exists.")
    finally:
        conn.close()

def check_if_users_exist():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    user_count = c.fetchone()[0]
    conn.close()
    return user_count > 0

def generate_otp():
    return str(random.randint(100000, 999999))

# Streamlit login function supporting both username-password and email OTP login
def check_password():
    """Handle login authentication with username-password and email OTP"""

    # Initialize session state variables if not present
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False
    if "otp" not in st.session_state:
        st.session_state.otp = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "valid_credentials" not in st.session_state:
        st.session_state.valid_credentials = False
    if "current_user" not in st.session_state:  # Ensure current_user is initialized
        st.session_state.current_user = None
    if "current_role" not in st.session_state:  # Initialize current_role if needed
        st.session_state.current_role = None

    if not st.session_state.authenticated:
        st.title("Login System")

        # Step 1: Enter Username or Email
        identifier = st.text_input("Enter Username or Email", placeholder="Username or Email")
        password = st.text_input("Enter Password", type="password", placeholder="Password")

        if identifier and password:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()

            # Check if identifier is a username or email
            if "@" in identifier:  # Email-based login
                # Fetch the username associated with the provided email
                c.execute('SELECT username, password_hash FROM users WHERE email = ?', (identifier,))
                result = c.fetchone()
                
                if result:
                    username, stored_password_hash = result
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash):
                        st.session_state.email = identifier
                        st.session_state.valid_credentials = True
                        st.session_state.current_user = username  # Set the associated username
                    else:
                        st.error("Invalid password!")
                else:
                    st.error("Email not registered!")

            else:  # Username-based login
                c.execute('SELECT email, password_hash FROM users WHERE username = ?', (identifier,))
                result = c.fetchone()

                if result:
                    stored_email, stored_password_hash = result
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash):
                        st.session_state.email = stored_email
                        st.session_state.valid_credentials = True
                        st.session_state.current_user = identifier  # Use username, not email
                    else:
                        st.error("Invalid password!")
                else:
                    st.error("Username not found!")

            conn.close()

            # Step 2: Send OTP after password verification
            if st.session_state.valid_credentials and not st.session_state.otp_sent:
                if st.button("Send OTP"):
                    otp = generate_otp()
                    st.session_state.otp = otp
                    subject = "Your OTP Code"
                    body = f"Your OTP for login is: {otp}"
                    send_email_via_hostinger(st.session_state.email, subject, body)
                    st.session_state.otp_sent = True
                    st.success("OTP sent to your email.")

        # Step 3: Verify OTP
        if st.session_state.otp_sent:
            entered_otp = st.text_input("Enter OTP", placeholder="Enter the OTP sent to your email")

            if st.button("Verify OTP"):
                if entered_otp == st.session_state.otp:
                    st.success("OTP Verified! You are logged in.")
                    st.session_state.authenticated = True
                    st.session_state.otp_sent = False  # Reset OTP session
                    st.rerun()
                else:
                    st.error("Invalid OTP. Please try again.")

    # Only display username (not email) for authenticated users
    if st.session_state.authenticated:
        st.sidebar.title(f"Welcome {st.session_state.current_user}!")  # Display username only

    return st.session_state.authenticated


def user_management():
    if st.session_state.current_user != 'Harsh':
        st.warning("Only admin can manage users")
        return

    st.subheader("User Management")
    
    tab1, tab2, tab3 = st.tabs(["Add User", "Remove User", "Update Role"])

    # Add User Tab
    with tab1:
        full_name = st.text_input("Full Name")
        email_id = st.text_input("Email Id")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        new_role = st.selectbox("Select Role", options=list(gu_auth.user.get_role_permissions().keys()))
        if st.button("Add User"):
            success, message = gu_auth.user.add_user(new_username, new_password, new_role, email_id, full_name)
            if success:
                st.success(message)
            else:
                st.error(message)

    # Remove User Tab
    with tab2:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT username FROM users WHERE is_root = 0')
        users_to_remove = [row[0] for row in c.fetchall()]
        conn.close()

        username_to_remove = st.selectbox("Select User to Remove", options=users_to_remove)
        
        if username_to_remove:
            # Confirmation for user removal
            confirmation = st.checkbox(f"Are you sure you want to remove user: {username_to_remove}?")
            if confirmation and st.button("Remove User"):
                success, message = gu_auth.user.remove_user(username_to_remove)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # Update Role Tab
    with tab3:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT username FROM users WHERE is_root = 0')
        users_to_update = [row[0] for row in c.fetchall()]
        conn.close()

        username_to_update = st.selectbox("Select User to Update", options=users_to_update)
        new_role = st.selectbox("Select New Role", options=list(gu_auth.user.get_role_permissions().keys()))
        new_full_name = st.text_input("New Full Name", "")
        new_password = st.text_input("New Password (Leave blank if no change)", type="password")

        if username_to_update:
            if st.button("Update Role"):
                success, message = gu_auth.user.update_user_role(
                    username_to_update, new_role, new_full_name, new_password
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # Display Current Users
    st.write("Current Users:")
    conn = sqlite3.connect(db_path)
    user_list = pd.read_sql('SELECT username, role, permissions FROM users', conn)
    conn.close()
    st.dataframe(user_list)

def has_permission(permission):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT permissions FROM users WHERE username = ?', (st.session_state.current_user,))
    permissions = c.fetchone()[0].split(',')
    conn.close()
    return permission in permissions

def login_check_and_sidebar_actions():
    # Login Check
    if not check_password():
        return False

    # Sidebar Content
    st.sidebar.title(gu_lang.LangConfig.get("WELCOME", st.session_state.current_user))
    st.sidebar.write(gu_lang.LangConfig.get("ROLE", st.session_state.current_role))

    # Logout Button
    if st.sidebar.button(gu_lang.LangConfig.get("LOGOUT")):
        st.session_state.authenticated = False
        st.rerun()

    return True