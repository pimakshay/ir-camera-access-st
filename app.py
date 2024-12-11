import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
import numpy as np
import threading
from typing import Union
import av
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
import logging
import queue

logger = logging.getLogger(__name__)

# Setup streamlit page
st.set_page_config(page_title="Access IR Camera",layout="wide")

SIDEBAR_OPTIONS = ["Streamlit Camera Input", "Streamlit Webrtc"]


def streamlit_menu():
        
        selected = option_menu(
            menu_title=None,  # required
            options=SIDEBAR_OPTIONS,  # required
            icons=["house", "book"],  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
        )
        return selected


selected = streamlit_menu()

if selected == SIDEBAR_OPTIONS[0]:

    st.subheader("Using streamlit camera input")

    st.markdown("""**Current Challenges**: 
             1. Captured image shape is not same as camera output shape but is the shape of camera_input window.
             2. Cannot identify usb cameras connected to smartphones (Android)
             """)

    img_file_buffer = st.camera_input("Take a picture")

    if img_file_buffer is not None:
        # To read image file buffer as a PIL Image:
        img = Image.open(img_file_buffer)

        # To convert PIL Image to numpy array:
        img_array = np.array(img)

        # Check the type of img_array:
        # Should output: <class 'numpy.ndarray'>
        st.write(type(img_array))

        # Check the shape of img_array:
        # Should output original camera shape: (height, width, channels)
        # however outputs camera_input window size
        st.write(img_array.shape)


if selected == SIDEBAR_OPTIONS[1]:

    link_text = "Streamlit-WebRTC"
    url = "https://github.com/whitphx/streamlit-webrtc"
    st.subheader(f"Learn more about [{link_text}]({url})")

    st.markdown("""**Current Challenges**: 
             1. Capturing images or videos is not straightforward.
             2. Cannot identify usb cameras connected to smartphones (Android)
             """)
    
    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        print(img.shape)

        # img = cv2.resize(img, (256, 384))
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    
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
            logger.warning("VideoReciver is not set. Abort.")
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


# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)