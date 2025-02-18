import streamlit as st
import sqlite3
import bcrypt
import lang as gu_lang
import auth as gu_auth

def init_users():
    if 'users' not in st.session_state:
        st.session_state.users = {}
        conn = sqlite3.connect('auth/users.db')
        c = conn.cursor()
        c.execute('SELECT username, password_hash, role, permissions FROM users')
        for row in c.fetchall():
            st.session_state.users[row[0]] = {
                'password': row[1],
                'role': row[2],
                'permissions': row[3].split(',')
            }
        conn.close()

def get_role_permissions():
    return {
        'Admin': ['overview', 'inventory_status', 'shipment_planning', 'loss_analysis', 
                 'profit_analysis', 'max_drr', 'drr_timeline', 'labels', 'manage_users'],
        'admin': ['overview', 'inventory_status', 'shipment_planning', 'loss_analysis', 
                 'profit_analysis', 'max_drr', 'drr_timeline', 'labels'],
        'inventory': ['overview', 'inventory_status', 'shipment_planning', 'max_drr', 'drr_timeline'],
        'Labels': ['overview', 'labels'],
        'viewer': ['overview']
    }

def add_user(username, password, role, email='', full_name=''):
    conn = sqlite3.connect('auth/users.db')
    c = conn.cursor()

    # Hash the password for security
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Get the permissions based on the role
    permissions = ','.join(get_role_permissions().get(role, []))

    try:
        # Insert the user into the database
        c.execute('INSERT INTO users (username, password_hash, role, permissions, email, full_name, is_root) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                  (username, password_hash, role, permissions, email, full_name, False))
        conn.commit()

        # Send a confirmation email with user details
        subject = "New User Added"
        body = f"""
        Hello {full_name or username},

        A new user has been successfully added to the system.

        Username: {username}
        Email: {email}
        Role: {role}
        Permissions: {permissions}

        You can access the system here: # (replace with actual dashboard URL)

        Regards,
        Admin
        """
        if email:  # Ensure the email is provided
            gu_auth.send_email_via_hostinger(email, subject, body)

        return True, "User added successfully and notification sent."
    
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    except Exception as e:
        return False, f"An error occurred: {str(e)}"
    
    finally:
        conn.close()

def remove_user(username):
    conn = sqlite3.connect('auth/users.db')
    c = conn.cursor()
    
    # Check if the user exists and is not a root user
    c.execute('SELECT is_root FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    
    if result is None:  # No user found
        conn.close()
        return False, "User not found"
    
    is_root = result[0]
    if is_root:
        conn.close()
        return False, "Cannot remove root user"
    
    # Remove the user
    c.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()
    return True, "User removed successfully"

def update_user_role(username, new_role, new_full_name=None, new_password=None):
    conn = sqlite3.connect('auth/users.db')
    c = conn.cursor()
    
    c.execute('SELECT is_root, password_hash FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    
    if not result:  # No user found
        conn.close()
        return False, "User not found"

    is_root, current_password_hash = result

    if is_root:
        conn.close()
        return False, "Cannot modify root user role"
    
    # Update the role and permissions
    permissions = ','.join(get_role_permissions()[new_role])
    
    # Update the full name if provided
    if new_full_name:
        c.execute('UPDATE users SET full_name = ? WHERE username = ?', (new_full_name, username))
    
    # Update password if provided
    if new_password:
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        c.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_password_hash, username))
    
    # Update the role and permissions
    c.execute('UPDATE users SET role = ?, permissions = ? WHERE username = ?', (new_role, permissions, username))
    
    conn.commit()
    conn.close()

    return True, "User role, full name, and/or password updated successfully"

def manage_users():
    if st.session_state.current_user == 'Harsh':
        if st.sidebar.button(gu_lang.LangConfig.get("MANAGE_USERS")):
            st.session_state.show_user_management = True

    if st.session_state.get('show_user_management', False):
        gu_auth.login.user_management()
        if st.button(gu_lang.LangConfig.get("BACK_TO_DASHBOARD")):
            st.session_state.show_user_management = False
            st.rerun()
        return True

    return False