import streamlit as st
import os
import json
import datetime
from typing import Optional

def check_login() -> None:
    """
    Checks if a user is logged in and handles the login process if not.
    Updates session state with user information.
    """
    # If user is not logged in, show login form
    if not st.session_state.user:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.title("AI Chat Studio")
            st.subheader("Welcome! Please enter your username to continue")
            
            # Username input
            username = st.text_input("Username", key="username_input")
            
            if st.button("Continue"):
                if username.strip():
                    # Store username in session state
                    st.session_state.user = username
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.error("Please enter a valid username")
            
            # Prevent rest of app from loading
            st.stop()

def logout_user() -> None:
    """
    Logs out the current user by clearing the session state.
    """
    st.session_state.user = None
    st.session_state.messages = []
    st.session_state.current_model = "Gemini"
    st.rerun()

def get_current_user() -> Optional[str]:
    """
    Returns the currently logged in username or None.
    
    Returns:
        The current username or None if not logged in
    """
    return st.session_state.get("user")
