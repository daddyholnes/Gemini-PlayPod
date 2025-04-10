
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import os
import datetime
import json
import base64
import tempfile
import threading
import html
from io import BytesIO
from PIL import Image
from utils.ui_components import render_voice_command_ui, render_floating_voice_button
from utils.themes import apply_theme, THEMES
from utils.emoji_picker import render_emoji_gif_picker, add_to_message_input
from utils.models import (
    get_gemini_response,
    get_vertex_ai_response,
    get_openai_response,
    get_anthropic_response,
    get_perplexity_response
)
from utils.auth import check_login, logout_user
from utils.database import init_db, save_conversation, load_conversations, get_most_recent_chat

# Set page configuration
st.set_page_config(
    page_title="AI Chat Studio",
    page_icon="assets/favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user" not in st.session_state:
    st.session_state.user = None
if "current_model" not in st.session_state:
    st.session_state.current_model = "Gemini"
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "send_message_cooldown" not in st.session_state:
    st.session_state.send_message_cooldown = False
if "last_sent_time" not in st.session_state:
    st.session_state.last_sent_time = None
    
# Voice command state variables
if "voice_commands_active" not in st.session_state:
    st.session_state.voice_commands_active = False
if "voice_processor" not in st.session_state:
    st.session_state.voice_processor = None
if "is_listening" not in st.session_state:
    st.session_state.is_listening = False
    
# Theme state - initialize before use
if "current_theme" not in st.session_state:
    st.session_state.current_theme = "Amazon Q Purple"
    
# Emoji picker state
if "user_message" not in st.session_state:
    st.session_state.user_message = ""
if "favorite_emojis" not in st.session_state:
    st.session_state.favorite_emojis = ["😀", "👍", "🔥", "❤️", "😊", "👏", "🎉", "🙏"]

# Apply the current theme's CSS
theme_css = apply_theme(st.session_state.current_theme)
st.markdown(theme_css, unsafe_allow_html=True)

# Add custom CSS for chat container styling
st.markdown("""
<style>
/* Chat container styling */
.chat-container {
    height: 500px; /* Fixed height for the chat container */
    overflow-y: auto; /* Enable vertical scrolling */
    border: 1px solid #333;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    background-color: #1a1a1a;
}

/* Message input styling */
.stTextArea textarea {
    min-height: 100px !important;
    border-radius: 8px;
}

/* Custom scrollbar for chat container */
[data-testid="stVerticalBlock"] div:has(> div.chat-container) {
    overflow-y: auto;
    max-height: 500px; /* Match the height of the chat container */
    scrollbar-width: thin;
    scrollbar-color: #666 #1a1a1a;
}

[data-testid="stVerticalBlock"] div:has(> div.chat-container)::-webkit-scrollbar {
    width: 8px;
}

[data-testid="stVerticalBlock"] div:has(> div.chat-container)::-webkit-scrollbar-track {
    background: #1a1a1a;
}

[data-testid="stVerticalBlock"] div:has(> div.chat-container)::-webkit-scrollbar-thumb {
    background-color: #666;
    border-radius: 10px;
}

/* Message styling */
.user-message {
    display: flex;
    align-items: start;
    margin-bottom: 15px;
    animation: fadeIn 0.3s ease-in-out;
}

.ai-message {
    display: flex;
    align-items: start;
    margin-bottom: 15px;
    animation: fadeIn 0.3s ease-in-out;
}

/* Avatar styling */
.avatar {
    background-color: #8c52ff;
    color: white;
    border-radius: 50%;
    height: 32px;
    width: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 10px;
    flex-shrink: 0;
}

.user-avatar {
    background-color: #f50057;
}

/* Message bubble styling */
.message-bubble {
    background-color: #272727;
    border-radius: 10px;
    padding: 10px;
    max-width: 90%;
}

.user-bubble {
    background-color: #1e1e1e;
}

/* Text styling */
.message-text {
    margin: 0;
    color: white;
    white-space: pre-wrap;
}

/* Animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Cooldown indicator */
.cooldown-indicator {
    position: absolute;
    bottom: 10px;
    right: 10px;
    color: #f50057;
    font-size: 12px;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0% { opacity: 0.5; }
    50% { opacity: 1; }
    100% { opacity: 0.5; }
}

/* Fix sidebar placement */
[data-testid="stSidebar"] {
    position: fixed;
    left: 0;
    top: 0;
    height: 100%;
    width: 20%; /* Adjust the width as needed */
    background-color: #0e1117; /* Match the theme */
    padding-top: 20px;
    overflow-y: auto; /* In case the content overflows */
}
</style>
""", unsafe_allow_html=True)

# Check user login
check_login()

# Helper function to encode image for API calls
def encode_image(uploaded_file):
    if uploaded_file is not None:
        # Read the file and encode it
        bytes_data = uploaded_file.getvalue()
        
        # Convert to base64
        encoded = base64.b64encode(bytes_data).decode('utf-8')
        return encoded
    return None

# Main function
def main():
    # Initialize database
    init_db()
    
    # Layout with main content area and sidebar - improve ratio for better chat display
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Main chat area with enhanced Google AI Studio style header
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="font-size: 2.2rem; margin-bottom: 5px;">Talk with AI live</h1>
            <p style="color: #888; font-size: 1.1rem;">Interact with AI models using text, code, images, audio, or upload files</p>
            <div style="max-width: 600px; margin: 10px auto; padding: 8px; background-color: #0f0f0f; border-radius: 8px; border: 1px solid #333;">
                <p style="margin: 0; color: #4285f4;">
                    <strong>Model:</strong> <span id="current-model">{}</span>
                </p>
            </div>
        </div>
        """.format(st.session_state.current_model), unsafe_allow_html=True)
        
        # Create a fixed-height container for chat messages with scrolling
        chat_container = st.container()
        
        # Custom HTML for message container with better styling and scrolling
        st.markdown("""
        <div class="chat-container" id="chat-messages">
            <!-- Messages will be displayed here -->
        </div>
        <script>
            // Auto-scroll to bottom of chat container
            function scrollToBottom() {
                const container = document.querySelector('.chat-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            }
            // Call on page load
            window.addEventListener('load', scrollToBottom);
        </script>
        """, unsafe_allow_html=True)
        
        # Display chat messages in a clean Google AI Studio style within the fixed container
        with chat_container:
            for i, message in enumerate(st.session_state.messages):
                # Custom styling for messages based on role
                if message["role"] == "user":
                    # User message with custom styling
                    st.markdown(f"""
                    <div class="user-message">
                        <div class="avatar user-avatar">👤</div>
                        <div class="message-bubble user-bubble">
                            <p class="message-text">{html.escape(message["content"]).replace(chr(10), '<br>')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                    # If there's an image in the message
                    if message.get("image"):
                        try:
                            # Display the image below the text
                            image_data = base64.b64decode(message["image"])
                            image = Image.open(BytesIO(image_data))
                            st.image(image, caption="Uploaded Image", width=300)
                        except Exception as e:
                            st.error(f"Could not display image: {str(e)}")
                else:
                    # AI message with custom styling
                    st.markdown(f"""
                    <div class="ai-message">
                        <div class="avatar">🤖</div>
                        <div class="message-bubble">
                            <p class="message-text">{html.escape(message["content"]).replace(chr(10), '<br>')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add simplified reaction buttons for AI messages 
                    if i > 0 and message["role"] == "assistant":
                        # Create a unique key for each message's reaction section
                        message_key = f"reaction_{i}"
                        
                        # Initialize reaction counts in session state if not already set
                        if message_key not in st.session_state:
                            st.session_state[message_key] = {"👍": 0, "❤️": 0, "😂": 0, "😮": 0, "🔥": 0}
                        
                        # Display the reactions as small text instead of buttons
                        reaction_html = ""
                        reactions = ["👍", "❤️", "😂", "😮", "🔥"]
                        
                        for emoji in reactions:
                            count = st.session_state[message_key][emoji]
                            reaction_html += f"<span style='margin-right:8px;font-size:15px;'>{emoji} {count if count > 0 else ''}</span>"
                        
                        # Show them in a clean HTML layout
                        st.markdown(f"""
                        <div style="margin-top:5px;margin-bottom:10px;margin-left:40px;">
                            {reaction_html}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Only show react button if there are no counts yet
                        empty_reactions = all(count == 0 for count in st.session_state[message_key].values())
                        
                        # Add react button
                        cols = st.columns([1, 3])
                        if cols[0].button("👍 React", key=f"react_btn_{i}", use_container_width=True):
                            st.session_state[message_key]["👍"] += 1
        
        # Input options area with tabs for different input types
        input_tabs = st.tabs(["Image Upload", "Audio Recording", "File Upload"])
        
        # Image upload tab
        with input_tabs[0]:
            uploaded_file = st.file_uploader("Upload an image for analysis", type=["jpg", "jpeg", "png"])
            if uploaded_file:
                # Save the uploaded image to session state
                st.session_state.uploaded_image = encode_image(uploaded_file)
                
                # Preview the image
                st.image(uploaded_file, caption="Image ready for analysis", width=300)
        
        # Audio recording tab
        with input_tabs[1]:
            if "audio_data" not in st.session_state:
                st.session_state.audio_data = None
                st.session_state.audio_path = None
                st.session_state.audio_recording_unavailable = False
            
            # Check if audio recording was previously determined to be unavailable
            if not st.session_state.audio_recording_unavailable:
                # Place buttons side by side without nested columns
                st.write("Choose recording duration:")
                b1, b2 = st.columns(2) # This is not nested - it's at the root level of the tab
                
                # Record 5-second audio
                if b1.button("Record Audio (5 seconds)", use_container_width=True):
                    try:
                        from utils.audio import record_audio, encode_audio, cleanup_audio_file
                        
                        # Record audio for 5 seconds
                        audio_bytes, temp_file_path = record_audio(duration=5)
                        
                        # Save to session state
                        st.session_state.audio_data = encode_audio(audio_bytes)
                        st.session_state.audio_path = temp_file_path
                        
                        # Show success message
                        st.success("Audio recorded successfully!")
                        
                        # Add an audio player to preview the recording
                        st.audio(temp_file_path)
                    except Exception as e:
                        error_message = str(e)
                        if "microphone is not accessible" in error_message or "Invalid input device" in error_message:
                            st.error("Microphone not available in this environment.")
                            st.info("You can upload an audio file instead or use text input.")
                            st.session_state.audio_recording_unavailable = True
                        else:
                            st.error(f"Failed to record audio: {error_message}")
                
                # Record 10-second audio
                if b2.button("Record Audio (10 seconds)", use_container_width=True):
                    try:
                        from utils.audio import record_audio, encode_audio, cleanup_audio_file
                        
                        # Record audio for 10 seconds
                        audio_bytes, temp_file_path = record_audio(duration=10)
                        
                        # Save to session state
                        st.session_state.audio_data = encode_audio(audio_bytes)
                        st.session_state.audio_path = temp_file_path
                        
                        # Show success message
                        st.success("Audio recorded successfully!")
                        
                        # Add an audio player to preview the recording
                        st.audio(temp_file_path)
                    except Exception as e:
                        error_message = str(e)
                        if "microphone is not accessible" in error_message or "Invalid input device" in error_message:
                            st.error("Microphone not available in this environment.")
                            st.info("You can upload an audio file instead or use text input.")
                            st.session_state.audio_recording_unavailable = True
                        else:
                            st.error(f"Failed to record audio: {error_message}")
            else:
                # Show alternative options when recording is unavailable
                st.warning("Audio recording is not available in this environment.")
                st.info("You can upload a pre-recorded audio file or use text input instead.")
                st.session_state.audio_recording_unavailable = True
            
            # Upload audio file as alternative
            uploaded_audio = st.file_uploader("Or upload audio file", type=["wav", "mp3", "ogg"], key="audio_upload")
            if uploaded_audio:
                try:
                    # Read the file and encode it
                    audio_bytes = uploaded_audio.getvalue()
                    
                    # Create temporary file
                    temp_file = tempfile.NamedTemporaryFile(suffix="." + uploaded_audio.name.split(".")[-1], delete=False)
                    temp_file_path = temp_file.name
                    temp_file.write(audio_bytes)
                    temp_file.close()
                    
                    # Save to session state
                    from utils.audio import encode_audio
                    st.session_state.audio_data = encode_audio(audio_bytes)
                    st.session_state.audio_path = temp_file_path
                    
                    # Show success and preview
                    st.success("Audio file uploaded successfully!")
                    st.audio(temp_file_path)
                except Exception as e:
                    st.error(f"Failed to process audio file: {str(e)}")
            
            # Button to clear recorded/uploaded audio
            if st.session_state.audio_data and st.button("Clear Audio"):
                if st.session_state.audio_path:
                    try:
                        from utils.audio import cleanup_audio_file
                        cleanup_audio_file(st.session_state.audio_path)
                    except:
                        pass
                st.session_state.audio_data = None
                st.session_state.audio_path = None
                st.rerun()
                
        # File upload tab
        with input_tabs[2]:
            uploaded_doc = st.file_uploader("Upload a document", type=["txt", "pdf", "doc", "docx"], 
                                          help="Upload a document for the AI to analyze")
            if uploaded_doc:
                # Read file content
                if uploaded_doc.type == "text/plain":
                    # Handle text files
                    text_content = uploaded_doc.getvalue().decode("utf-8")
                    st.text_area("Document Content", text_content, height=200)
                    if st.button("Send Document to AI"):
                        # Add document content to user message
                        st.session_state.document_text = f"I'm sharing this document with you: \n\n{text_content}\n\nPlease analyze this content."
                else:
                    # For other file types, just show the filename
                    st.info(f"File '{uploaded_doc.name}' uploaded. Send a message to the AI to analyze it.")
        
        # Emoji & GIF Picker in a small expander to be less prominent
        with st.expander("📋 Emoji & GIF Menu", expanded=False):
            render_emoji_gif_picker()
        
        # Chat input with custom container and improved sizing
        st.markdown("""
        <div class="chat-input-container">
            <h4 style="margin-bottom: 10px; color: #4285f4;">Message</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Create message input with larger height
        user_input = st.text_area(
            "Message the AI...",
            height=120,
            key="message_input",
            placeholder="Type your message here...",
            label_visibility="collapsed"
        )
        
        # Add cooldown mechanism to prevent double-sending
        col1, col2 = st.columns([3, 1])
        send_button_disabled = st.session_state.send_message_cooldown
        
        with col1:
            if st.button("Send Message", disabled=send_button_disabled, use_container_width=True, type="primary"):
                # Implement cooldown
                import time
                current_time = time.time()
                
                # Check if we're in cooldown (prevent rapid clicking)
                cooldown_active = False
                if hasattr(st.session_state, 'last_sent_time'):
                    if st.session_state.last_sent_time and (current_time - st.session_state.last_sent_time) < 1.0:
                        cooldown_active = True
                
                if not cooldown_active and user_input.strip():
                    # Set cooldown flag
                    st.session_state.send_message_cooldown = True
                    st.session_state.last_sent_time = current_time
                    
                    # If document was uploaded and button clicked, use document text as message
                    message_to_send = user_input
                    if hasattr(st.session_state, 'document_text'):
                        message_to_send = st.session_state.document_text
                        # Clear it after use
                        delattr(st.session_state, 'document_text')
                    
                    # Create message object
                    user_message = {"role": "user", "content": message_to_send}
                    
                    # Add image to message if one is uploaded
                    if st.session_state.uploaded_image:
                        user_message["image"] = st.session_state.uploaded_image
                        
                    # Add audio to message if recorded
                    if hasattr(st.session_state, 'audio_data') and st.session_state.audio_data:
                        user_message["audio"] = st.session_state.audio_data
                        # Clear audio data after use
                        st.session_state.audio_data = None
                        st.session_state.audio_path = None
                    
                    # Add user message to chat
                    st.session_state.messages.append(user_message)
                    
                    # Get AI response based on selected model
                    with st.spinner(f"Thinking... using {st.session_state.current_model}"):
                        try:
                            image_data = user_message.get("image")
                            model_name = st.session_state.current_model.lower()
                            
                            # Extract model call sign from selected model if available
                            model_call_sign = None
                            if "(" in st.session_state.current_model and ")" in st.session_state.current_model:
                                model_call_sign = st.session_state.current_model.split("(")[1].split(")")[0]
                            
                            # Gemini models
                            if "gemini" in model_name:
                                # Use extracted call sign or fallback to default
                                gemini_version = model_call_sign if model_call_sign else "gemini-1.5-pro"
                                
                                # Get audio data if available
                                audio_data = user_message.get("audio")
                                
                                ai_response = get_gemini_response(
                                    user_input, 
                                    st.session_state.messages,
                                    image_data=image_data,
                                    audio_data=audio_data,
                                    temperature=st.session_state.temperature,
                                    model_name=gemini_version
                                )
                            
                            # Vertex AI models - direct routing to appropriate API based on model
                            elif "vertex ai" in model_name:
                                if "claude" in model_name.lower():
                                    # Use the extracted call sign or default to Claude 3.5
                                    claude_model = model_call_sign if model_call_sign else "claude-3-5-sonnet-20241022"
                                    ai_response = get_anthropic_response(
                                        user_input, 
                                        st.session_state.messages,
                                        model_name=claude_model
                                    )
                                elif "gpt" in model_name.lower():
                                    # Use the extracted call sign or default to GPT-4o
                                    gpt_model = model_call_sign if model_call_sign else "gpt-4o"
                                    ai_response = get_openai_response(
                                        user_input, 
                                        st.session_state.messages,
                                        model_name=gpt_model
                                    )
                                else:
                                    # For any other Vertex AI models, try the vertex function but with warning
                                    ai_response = "Note: This model may not be directly accessible through the current API configuration. " + \
                                                "For best results with third-party models, please select them from their native provider section instead."
                            
                            # OpenAI models
                            elif "openai" in model_name:
                                # Use the extracted call sign or default to gpt-4o
                                openai_model = model_call_sign if model_call_sign else "gpt-4o"
                                ai_response = get_openai_response(
                                    user_input, 
                                    st.session_state.messages,
                                    model_name=openai_model
                                )
                            
                            # Anthropic models
                            elif "anthropic" in model_name:
                                # Use the extracted call sign or default to claude-3-5-sonnet-20241022
                                anthropic_model = model_call_sign if model_call_sign else "claude-3-5-sonnet-20241022"
                                ai_response = get_anthropic_response(
                                    user_input, 
                                    st.session_state.messages,
                                    model_name=anthropic_model
                                )
                            
                            # Perplexity models
                            elif "perplexity" in model_name:
                                # Use the extracted call sign or fallback to default
                                perplexity_model = model_call_sign if model_call_sign else "pplx-70b-online"
                                
                                ai_response = get_perplexity_response(
                                    user_input, 
                                    st.session_state.messages,
                                    temperature=st.session_state.temperature,
                                    model_name=perplexity_model
                                )
                            
                            # Fallback for unknown models
                            else:
                                ai_response = "Error: The selected model is not yet implemented."
                                
                            # Add AI response to chat
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                            
                            # Clear uploaded image after processing
                            st.session_state.uploaded_image = None
                            
                            # Save conversation to database
                            save_conversation(
                                st.session_state.user,
                                st.session_state.current_model,
                                st.session_state.messages
                            )
                            
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {str(e)}"})
                            
                            # Clear uploaded image if there was an error
                            st.session_state.uploaded_image = None
                    
                    # Force a rerun to show the new messages
                    st.rerun()

        with col2:
            # Clear button
            if st.button("Clear", use_container_width=True):
                # Reset the input field
                st.session_state.user_message = ""
                # Force a rerun to clear the text area
                st.rerun()
    
    with col2:
        # Sidebar with enhanced Google AI Studio style settings
        with st.container():
            st.markdown("""
            <div style="padding: 10px 0; border-bottom: 1px solid #333; margin-bottom: 15px;">
                <h3 style="color: #4285f4; font-size: 1.3rem;">AI Studio Settings</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Voice command functions
            def toggle_voice_commands(enable):
                """Toggle voice commands on/off"""
                if enable:
                    if not st.session_state.voice_processor:
                        try:
                            # Import voice command processor
                            from utils.voice_commands import VoiceCommandProcessor
                            
                            # Initialize processor with command callbacks
                            processor = VoiceCommandProcessor()
                            
                            # Register command callbacks
                            processor.register_callback("new_chat", lambda: st.session_state.update(messages=[]))
                            processor.register_callback("select_model_gemini", lambda: st.session_state.update(current_model="Gemini"))
                            processor.register_callback("select_model_claude", lambda: st.session_state.update(current_model="Anthropic (claude-3-5-sonnet-20241022)"))
                            processor.register_callback("select_model_gpt", lambda: st.session_state.update(current_model="OpenAI (gpt-4o)"))
                            processor.register_callback("set_theme_amazonqpurple", lambda: st.session_state.update(current_theme="Amazon Q Purple"))
                            processor.register_callback("set_theme_light", lambda: st.session_state.update(current_theme="Light"))
                            processor.register_callback("set_theme_dark", lambda: st.session_state.update(current_theme="Dark"))
                            processor.register_callback("add_emoji_thumbsup", lambda: add_to_message_input("👍"))
                            processor.register_callback("add_emoji_heart", lambda: add_to_message_input("❤️"))
                            processor.register_callback("send_message", lambda: st.session_state.update(send_message=True)) # placeholder only
                            
                            # Start listening
                            st.session_state.voice_processor = processor
                            st.session_state.voice_processor.start_listening()
                            st.session_state.is_listening = True
                            st.success("Voice commands are now active. Try saying 'New chat', 'Select Model Gemini', 'Add Emoji Thumbs Up', etc.")
                        except Exception as e:
                            st.error(f"Could not initialize voice commands: {str(e)}")
                            st.info("Ensure you have the required dependencies installed and microphone access is enabled.")
                else:
                    if st.session_state.voice_processor:
                        # Stop listening
                        st.session_state.voice_processor.stop_listening()
                        st.session_state.voice_processor = None
                        st.session_state.is_listening = False
                        st.info("Voice commands disabled.")
            
            # Toggle voice commands
            voice_commands_enabled = st.checkbox(
                "Enable Voice Commands",
                value=st.session_state.voice_commands_active,
                help="Enable/disable voice command processing"
            )
            
            # Apply toggle if changed
            if voice_commands_enabled != st.session_state.voice_commands_active:
                st.session_state.voice_commands_active = voice_commands_enabled
                toggle_voice_commands(voice_commands_enabled)
            
            # Show current voice command status
            status_text = "🟢 Listening..." if st.session_state.is_listening else "🔴 Not Listening"
            status_color = "green" if st.session_state.is_listening else "red"
            st.markdown(f"<p style='color:{status_color};'>{status_text}</p>", unsafe_allow_html=True)
            
            # Model selection
            model_options = ["Gemini", "Vertex AI (claude-3-5-sonnet-20241022)", "Vertex AI (gpt-4o)", "OpenAI (gpt-4o)", "Anthropic (claude-3-5-sonnet-20241022)", "Perplexity (pplx-70b-online)"]
            current_model_index = model_options.index(st.session_state.current_model)
            selected_model = st.selectbox(
                "Choose AI Model",
                options=model_options,
                index=current_model_index,
                help="Select the AI model to use for generating responses"
            )
            