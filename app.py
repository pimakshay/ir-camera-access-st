import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import numpy as np

import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
from streamlit.components.v1 import html


# Setup streamlit page
st.set_page_config(page_title="Access IR Camera",layout="wide")

# 1=sidebar menu, 2=horizontal menu, 3=horizontal menu w/ custom menu
EXAMPLE_NO = 2
SIDEBAR_OPTIONS = ["Trends", "Detections", "Thermal Patterns"]


def streamlit_menu(example=1):
    if example == 1:
        # 1. as sidebar menu
        with st.sidebar:
            selected = option_menu(
                menu_title="Main Menu",  # required
                options=SIDEBAR_OPTIONS,  # required
                icons=["house", "book", "envelope"],  # optional
                menu_icon="cast",  # optional
                default_index=0,  # optional
            )
        return selected

    if example == 2:
        # 2. horizontal menu w/o custom style
        selected = option_menu(
            menu_title=None,  # required
            options=SIDEBAR_OPTIONS,  # required
            icons=["house", "book", "envelope"],  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
        )
        return selected

    if example == 3:
        # 2. horizontal menu with custom style
        selected = option_menu(
            menu_title=None,  # required
            options=SIDEBAR_OPTIONS,  # required
            icons=["house", "book", "envelope"],  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "green"},
            },
        )
        return selected


selected = streamlit_menu(example=EXAMPLE_NO)

if selected in SIDEBAR_OPTIONS:
    st.title(f"You have selected {selected}")

# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)


if selected == SIDEBAR_OPTIONS[0]:
    enable = st.checkbox("Enable USB camera")
    picture = st.camera_input("Take a picture", disabled=not enable)
    
    # st.write(f"Type: {type(picture)}, datatype: {type(picture.data)}")
    if picture:
        st.image(picture)

    if picture is not None:
        # To read image file buffer as bytes
        bytes_data = picture.getvalue()

        # Convert the bytes data to a PIL Image object
        img = Image.open(picture)
        
        # Convert PIL Image to numpy array
        img_array = np.array(img)
        
        # Display the shape of the numpy array
        st.write("Shape of the image array:", img_array.shape)
        
        # You can now use img_array for further processing or display
        st.image(img_array, caption="Captured Image as NumPy Array")

if selected == SIDEBAR_OPTIONS[1]:

    st.title("Infrared Thermal USB Camera Selector")
    st.subheader("Select and Use Your IR Camera")
    
    # Instructions for Android/iOS/Web Users
    st.write("""
    This app lists USB-connected cameras on your device. 
    Please allow camera permissions to proceed.
    """)
    
    # Step 2: Start camera feed based on selection
    selected_camera = st.text_input("Enter the device ID of the IR Camera (from above):")
    
    if selected_camera:
        st.info(f"Starting camera feed for Device ID: {selected_camera}")
        
        class IRVideoTransformer(VideoTransformerBase):
            def transform(self, frame):
                # Additional processing (e.g., image enhancement) can be done here
                return frame
        
        webrtc_streamer(
            key="ir-camera-stream",
            mode=WebRtcMode.SENDRECV,
            video_transformer_factory=IRVideoTransformer,
            media_stream_constraints={
                "video": {"deviceId": {"exact": selected_camera}},
                "audio": False,
            }
        )
    
    # Step 3: Capture images from the feed
    st.write("You can use the 'Capture' button below to take pictures.")

    captured_image = st.button("Capture Image")
    if captured_image:
        st.write("Captured image processing will be implemented here.")

