import streamlit as st
import config
from pathlib import Path
import base64

def apply_custom_css():
    """Load custom CSS styles for the login page"""
    # st.markdown(config.CUSTOM_CSS, unsafe_allow_html=True)
    
# Custom CSS for the login page

def inject_custom_css():
    """Inject custom CSS without creating extra containers"""
    # Use st.markdown with specific key to prevent duplicate injection
    st.markdown("""
        <style>
            /* Reset Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Reset container padding */
            .block-container {
                padding: 0 !important;
            }
            
            div[data-testid="stVerticalBlock"] {
                padding: 0 !important;
            }
            
            /* Card-like container styling */
            .login-container {
                background-color: rgba(255, 255, 255, 0.95);
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin: 0 auto;
                max-width: 450px;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
            }
            
            /* Header styling */
            .login-header {
                text-align: center;
                color: #2c3e50;
                margin-bottom: 1rem;
            }
            
            /* Logo container */
            .logo-container {
                text-align: center;
                margin-bottom: 1.5rem;
            }
            
            .logo-container img {
                max-width: 150px;
                height: auto;
            }
            
            /* Input field styling */
            .stTextInput input {
                border-radius: 5px;
                border: 1px solid #e0e0e0;
                padding: 0.5rem;
                font-size: 16px;
            }
            
            /* Button styling */
            .stButton button {
                background-color: #2c3e50;
                color: white;
                border-radius: 5px;
                padding: 0.5rem 2rem;
                font-size: 16px;
                border: none;
                width: 100%;
                transition: background-color 0.3s;
            }
            
            .stButton button:hover {
                background-color: #34495e;
            }
            
            /* Error message styling */
            .login-error {
                color: #e74c3c;
                text-align: center;
                padding: 0.5rem;
                margin-top: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

def load_css():
    """Load custom CSS styles for the login page with enhanced visual design"""
    st.markdown("""
        <style>
            /* Page background with gradient */
            .stApp {
                background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
                background-size: 400% 400%;
                animation: gradient 15s ease infinite;
            }
            
            @keyframes gradient {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            
            /* Card-like container styling */
            .login-container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 2.5rem;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                margin: 4rem auto;
                max-width: 400px;
                transform: translateY(-20px);
                animation: float 6s ease-in-out infinite;
            }
            
            @keyframes float {
                0% { transform: translateY(-20px); }
                50% { transform: translateY(-10px); }
                100% { transform: translateY(-20px); }
            }
            
            /* Header styling */
            .login-header {
                text-align: center;
                color: #1a2a6c;
                margin-bottom: 1.5rem;
                font-size: 1.8rem;
                font-weight: 600;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            
            /* Logo container */
            .logo-container {
                text-align: center;
                margin-bottom: 2rem;
                padding: 1rem;
            }
            
            .logo-container img {
                max-width: 180px;
                height: auto;
                filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
                transition: transform 0.3s ease;
            }
            
            .logo-container img:hover {
                transform: scale(1.05);
            }
            
            /* Input field styling */
            .stTextInput > div > div {
                border-radius: 8px !important;
            }
            
            .stTextInput input {
                border-radius: 8px !important;
                border: 2px solid #e0e0e0 !important;
                padding: 0.75rem !important;
                font-size: 16px !important;
                transition: all 0.3s ease !important;
                background: rgba(255, 255, 255, 0.9) !important;
            }
            
            .stTextInput input:focus {
                border-color: #1a2a6c !important;
                box-shadow: 0 0 0 2px rgba(26, 42, 108, 0.2) !important;
            }
            
            /* Button styling */
            .stButton button {
                background: linear-gradient(45deg, #1a2a6c, #b21f1f) !important;
                color: white !important;
                border-radius: 8px !important;
                padding: 0.75rem 2rem !important;
                font-size: 16px !important;
                font-weight: 600 !important;
                border: none !important;
                width: 100% !important;
                transition: all 0.3s ease !important;
                text-transform: uppercase !important;
                letter-spacing: 1px !important;
                margin-top: 1rem !important;
            }
            
            .stButton button:hover {
                background: linear-gradient(45deg, #b21f1f, #1a2a6c) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
            }
            
            /* Error message styling */
            .login-error {
                color: #e74c3c;
                text-align: center;
                padding: 0.75rem;
                margin-top: 1rem;
                background: rgba(231, 76, 60, 0.1);
                border-radius: 8px;
                font-weight: 500;
                animation: shake 0.5s ease-in-out;
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            
            /* Form label styling */
            .stTextInput label {
                color: #1a2a6c !important;
                font-weight: 500 !important;
                font-size: 14px !important;
                margin-bottom: 4px !important;
            }
            
            /* Placeholder styling */
            .stTextInput input::placeholder {
                color: #999 !important;
                font-size: 14px !important;
            }
        </style>
    """, unsafe_allow_html=True)

def load_logo():
    """Load and display the logo from the images folder"""
    try:
        logo_path = Path("images/logo.png")
        if logo_path.exists():
            st.markdown(
                f'<div class="logo-container"><img src="data:image/png;base64,{base64.b64encode(logo_path.read_bytes()).decode()}" alt="Company Logo"></div>',
                unsafe_allow_html=True
            )
        else:
            st.warning("Logo file not found in images folder", icon="⚠️")
    except Exception as e:
        print(f"Error loading logo: {e}")
        # Silently fail if logo cannot be loaded


