"""
Emoji Picker and GIF Integration for AI Chat Studio
"""
import streamlit as st
import json
import os
import requests
from typing import List, Dict, Any, Optional
import base64
from PIL import Image
from io import BytesIO

# Common emoji categories and their emojis
EMOJI_CATEGORIES = {
    "Smileys & People": [
        "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "🥲", "☺️", "😊", "😇", 
        "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚", "😋", "😛",
        "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🥸", "🤩", "🥳", "😏", "😒"
    ],
    "Animals & Nature": [
        "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", 
        "🐷", "🐽", "🐸", "🐵", "🙈", "🙉", "🙊", "🐒", "🐔", "🐧", "🐦", "🐤",
        "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🪱", "🐛", "🦋"
    ],
    "Food & Drink": [
        "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🫐", "🍈", "🍒", "🍑", 
        "🥭", "🍍", "🥥", "🥝", "🍅", "🍆", "🥑", "🥦", "🥬", "🥒", "🌶", "🫑",
        "🌽", "🥕", "🧄", "🧅", "🥔", "🍠", "🥐", "🥯", "🍞", "🥖", "🥨", "🧀"
    ],
    "Activities": [
        "⚽️", "🏀", "🏈", "⚾️", "🥎", "🎾", "🏐", "🏉", "🥏", "🎱", "🪀", "🏓", 
        "🏸", "🏒", "🏑", "🥍", "🏏", "🪃", "🥅", "⛳️", "🪁", "🏹", "🎣", "🤿",
        "🥊", "🥋", "🎽", "🛹", "🛼", "🛷", "⛸", "🥌", "🎿", "⛷", "🏂", "🪂"
    ],
    "Travel & Places": [
        "🚗", "🚕", "🚙", "🚌", "🚎", "🏎", "🚓", "🚑", "🚒", "🚐", "🛻", "🚚", 
        "🚛", "🚜", "🦯", "🦽", "🦼", "🛴", "🚲", "🛵", "🏍", "🛺", "🚨", "🚔",
        "🚍", "🚘", "🚖", "🚡", "🚠", "🚟", "🚃", "🚋", "🚞", "🚝", "🚄", "🚅"
    ],
    "Objects": [
        "⌚️", "📱", "📲", "💻", "⌨️", "🖥", "🖨", "🖱", "🖲", "🕹", "🗜", "💽", 
        "💾", "💿", "📀", "📼", "📷", "📸", "📹", "🎥", "📽", "🎞", "📞", "☎️",
        "📟", "📠", "📺", "📻", "🎙", "🎚", "🎛", "🧭", "⏱", "⏲", "⏰", "🕰"
    ],
    "Symbols": [
        "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", 
        "💞", "💓", "💗", "💖", "💘", "💝", "💟", "☮️", "✝️", "☪️", "🕉", "☸️",
        "✡️", "🔯", "🕎", "☯️", "☦️", "🛐", "⛎", "♈️", "♉️", "♊️", "♋️", "♌️"
    ],
    "Flags": [
        "🏳️", "🏴", "🏁", "🚩", "🏳️‍🌈", "🏳️‍⚧️", "🇺🇳", "🇦🇫", "🇦🇽", "🇦🇱", "🇩🇿", "🇦🇸", 
        "🇦🇩", "🇦🇴", "🇦🇮", "🇦🇶", "🇦🇬", "🇦🇷", "🇦🇲", "🇦🇼", "🇦🇺", "🇦🇹", "🇦🇿", "🇧🇸",
        "🇧🇭", "🇧🇩", "🇧🇧", "🇧🇾", "🇧🇪", "🇧🇿", "🇧🇯", "🇧🇲", "🇧🇹", "🇧🇴", "🇧🇦", "🇧🇼"
    ]
}

# For storing favorite/recently used emojis
def get_favorite_emojis() -> List[str]:
    """
    Get user's favorite emojis from session state
    
    Returns:
        List of favorite emoji characters
    """
    if "favorite_emojis" not in st.session_state:
        st.session_state.favorite_emojis = ["😀", "👍", "🔥", "❤️", "😊", "👏", "🎉", "🙏"]
    return st.session_state.favorite_emojis

def add_favorite_emoji(emoji: str) -> None:
    """
    Add an emoji to favorites
    
    Args:
        emoji: Emoji character to add
    """
    if "favorite_emojis" not in st.session_state:
        st.session_state.favorite_emojis = []
    
    # Add to front, remove if exists elsewhere
    if emoji in st.session_state.favorite_emojis:
        st.session_state.favorite_emojis.remove(emoji)
    
    # Add to front, limit to 20 favorites
    st.session_state.favorite_emojis.insert(0, emoji)
    if len(st.session_state.favorite_emojis) > 20:
        st.session_state.favorite_emojis = st.session_state.favorite_emojis[:20]

def render_emoji_picker(callback=None):
    """
    Render an emoji picker with categories
    
    Args:
        callback: Optional callback function to call when emoji is selected
    """
    # Create tabs for emoji categories
    favorite_emojis = get_favorite_emojis()
    
    # Add a "Favorites" category at the beginning
    all_categories = {"Favorites": favorite_emojis, **EMOJI_CATEGORIES}
    
    tab_names = list(all_categories.keys())
    emoji_tabs = st.tabs(tab_names)
    
    # Populate each tab with emojis
    for i, (category, emojis) in enumerate(all_categories.items()):
        with emoji_tabs[i]:
            cols = st.columns(8)  # Display 8 emojis per row
            for j, emoji in enumerate(emojis):
                col_idx = j % 8
                with cols[col_idx]:
                    if st.button(emoji, key=f"emoji_{category}_{j}", help=f"Insert {emoji}"):
                        add_favorite_emoji(emoji)
                        if callback:
                            callback(emoji)

# GIF Search functionality
def search_gifs(query: str, limit: int = 10, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for GIFs using the Tenor API
    
    Args:
        query: Search term
        limit: Maximum number of results to return
        api_key: Tenor API key (optional)
        
    Returns:
        List of GIF data objects
    """
    # If no API key is provided, use a default placeholder response
    if not api_key:
        return get_default_gifs()
    
    try:
        url = f"https://tenor.googleapis.com/v2/search?q={query}&key={api_key}&limit={limit}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        st.error(f"Error fetching GIFs: {str(e)}")
        return get_default_gifs()

def get_default_gifs() -> List[Dict[str, Any]]:
    """
    Get a default list of GIF placeholder data
    
    Returns:
        List of GIF data objects
    """
    # These are just placeholders - in a real implementation you'd use an actual API
    return [
        {
            "id": "default1",
            "title": "Happy",
            "media_formats": {
                "tinygif": {
                    "url": "https://example.com/happy.gif",
                }
            }
        },
        {
            "id": "default2",
            "title": "Sad",
            "media_formats": {
                "tinygif": {
                    "url": "https://example.com/sad.gif",
                }
            }
        }
    ]

def render_gif_picker(callback=None, api_key=None):
    """
    Render a GIF search and picker UI
    
    Args:
        callback: Function to call when a GIF is selected
        api_key: Tenor API key
    """
    st.subheader("GIF Search")
    
    # Search input
    search_term = st.text_input("Search for GIFs", key="gif_search_input")
    
    if search_term:
        # Get GIFs based on search term
        gifs = search_gifs(search_term, api_key=api_key)
        
        if gifs:
            # Display GIFs in a grid
            cols = st.columns(3)  # 3 GIFs per row
            for i, gif in enumerate(gifs[:9]):  # Limit to 9 GIFs
                col_idx = i % 3
                with cols[col_idx]:
                    # In a real implementation, you'd show the actual GIF image
                    gif_url = gif.get("media_formats", {}).get("tinygif", {}).get("url", "")
                    st.write(gif.get("title", ""))
                    if gif_url:
                        st.image(gif_url)
                        if st.button("Select", key=f"gif_{i}"):
                            if callback:
                                callback(gif_url)
        else:
            st.write("No GIFs found. Try another search term.")
    else:
        st.write("Enter a search term to find GIFs.")

# Combined emoji and GIF picker
def render_emoji_gif_picker():
    """
    Render a combined emoji and GIF picker in an expander
    """
    tab1, tab2 = st.tabs(["Emoji Quick-Select", "GIFs"])
    
    with tab1:
        # Just show a simple row of popular emojis instead of the full picker
        st.write("Click to add an emoji to your message:")
        
        # Display favorite/popular emojis in a grid (4 columns)
        popular_emojis = ["😀", "👍", "🔥", "❤️", "😊", "👏", "🎉", "🙏", "😂", "✅", "⭐", "💯"]
        cols = st.columns(4)
        
        for i, emoji in enumerate(popular_emojis):
            col_idx = i % 4
            if cols[col_idx].button(emoji, key=f"quick_emoji_{i}", help=f"Add {emoji} to message"):
                add_to_message_input(emoji)
        
        # Add a button to show more emojis
        if st.checkbox("Show more emojis", key="show_more_emojis", value=False):
            render_emoji_picker(callback=lambda emoji: add_to_message_input(emoji))
        
    with tab2:
        # Get API key from session state or environment
        tenor_api_key = os.environ.get("TENOR_API_KEY", "")
        
        if not tenor_api_key:
            st.warning("To use GIF search, please add a TENOR_API_KEY to your environment variables.")
            
        render_gif_picker(
            callback=lambda gif_url: add_to_message_input(f"![GIF]({gif_url})"),
            api_key=tenor_api_key
        )

def add_to_message_input(text: str) -> None:
    """
    Add text to the message input box
    
    Args:
        text: Text to add to the input
    """
    # Set text directly to clipboard-like session variable
    # that will be accessed when sending messages
    if "emoji_text_to_add" not in st.session_state:
        st.session_state.emoji_text_to_add = text
    else:
        st.session_state.emoji_text_to_add = text
    
    # Force rerun to show the selected emoji immediately
    st.rerun()