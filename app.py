import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import numpy as np
import threading
from typing import Union
import av
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
from streamlit.components.v1 import html
import snapshot as snap
import logging
import queue

logger = logging.getLogger(__name__)

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

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        print(img.shape)
        # Here you can perform any pre-processing on the image
        # For example, you could resize the image:
        # img = cv2.resize(img, (256, 384))
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    class IRVideoTransformer(VideoTransformerBase):
        def transform(self, frame):
            # Additional processing (e.g., image enhancement) can be done here
            st.write(type(frame))
            return frame
    
    class VideoTransformer(VideoTransformerBase):
            frame_lock: threading.Lock  # `transform()` is running in another thread, then a lock object is used here for thread-safety.
            in_image: Union[np.ndarray, None]
            out_image: Union[np.ndarray, None]
    
            def __init__(self) -> None:
                self.frame_lock = threading.Lock()
                self.in_image = None
                self.out_image = None
    
            def transform(self, frame: av.VideoFrame) -> np.ndarray:
                in_image = frame.to_ndarray(format="bgr24")
    
                out_image = in_image[:, ::-1, :]  # Simple flipping for example.
    
                with self.frame_lock:
                    self.in_image = in_image
                    self.out_image = out_image
    
                return out_image
    # video_constraints={
    #     "deviceId": "your_camera_id",
    #     "width": 1280,
    #     "height": 720,
    #     "frameRate": 30
    # }

    ir_frame = webrtc_streamer(
        key="ir-camera-stream",
        mode=WebRtcMode.SENDRECV,
        # rtc_configuration="iceServers",
        video_processor_factory=VideoTransformer,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={
            "video": True, #{"frameRate": 25,"height":384, "width":256},
            "audio": False,
            },
        async_processing=True,
        )
    snap_button = st.button("Snapshot")

    if ir_frame.state.playing:
        st.write("Stream is active")
    else:
        st.write("Stream is not active")

    image_place = st.empty()

    while True:
        if ir_frame.video_receiver:
            try:
                video_frame = ir_frame.video_receiver.get_frame(timeout=1)
            except queue.Empty:
                logger.warning("Queue is empty. Abort.")
                break

            img_rgb = video_frame.to_ndarray(format="rgb24")
            image_place.image(img_rgb)
        else:
            logger.warning("AudioReciver is not set. Abort.")
            break

    if ir_frame.state.playing:
        print("Hello")
        if snap_button:
            with ir_frame.input_video_track.frame_lock:
                out_image = ir_frame.video_transformer.out_image
                # If the image is not empty, display it and pass to model
            if out_image is not None:
                
                st.image(out_image, channels="BGR")
        
            # In case ICE state is not successful, show warning
            else:
                st.warning("No frames available yet.")

    # Step 3: Capture images from the feed
    st.write("You can use the 'Capture' button below to take pictures.")

    captured_image = st.button("Capture Image")
    if captured_image:
        st.write("Captured image processing will be implemented here.")

