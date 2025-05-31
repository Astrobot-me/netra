import streamlit as st
import base64
import CONTANTS

st.set_page_config(layout="wide")
st.title("Intelligent Traffic Management Panel")

# Function to embed video from local path
def video_tag(path):
    with open(path, "rb") as file:
        data = file.read()
        encoded = base64.b64encode(data).decode()
        return f"""
        <video width='100%' autoplay loop muted playsinline>
            <source src='data:video/mp4;base64,{encoded}' type='video/mp4'>
        </video>
        """

# Use remote path or base64 video
def video_html(src):
    return f"""
    <video width="100%" autoplay loop muted playsinline>
        <source src="{src}" type="video/mp4">
        Your browser does not support the video tag.
    </video>
    """

# Function to generate solid colored circle based on status
def status_circle(color):
    return f"""
    <div style='width: 15px; height: 15px; border-radius: 50%; background-color: {color}; display: inline-block;'></div>
    """

# Simulated dynamic values (replace with DB values later)
lane_timings = {
    "Lane 1": "23s",
    "Lane 2": "17s",
    "Lane 3": "42s",
    "Lane 4": "8s",
}

lane_status = {
    "Lane 1": "green",
    "Lane 2": "red",
    "Lane 3": "yellow",
    "Lane 4": "green",
}

lane_videos = {
    "Lane 1": CONTANTS.V1,
    "Lane 2": CONTANTS.V2,
    "Lane 3": CONTANTS.V3,
    "Lane 4": CONTANTS.V4,
}

# Layout rendering
left_col, right_col = st.columns([4, 1])

with left_col:
    row1 = st.columns(2)
    row2 = st.columns(2)

    lanes = ["Lane 1", "Lane 2", "Lane 3", "Lane 4"]
    rows = [row1, row2]

    for idx, lane in enumerate(lanes):
        col = rows[idx // 2][idx % 2]
        with col:
            st.markdown(f"""
            <div style='border: 1px solid #555; border-radius: 10px; padding: 10px; background-color: #111; display: flex; flex-direction: column; gap: 10px;'>

               
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <div style='font-size: 20px; color: white;'>{lane}</div>
                    {status_circle(lane_status[lane])}
                    <span style='color: #4fc3f7;'>{lane_timings[lane]}</span>
                </div>

                
                <div>
                    {video_html(lane_videos[lane])}
                </div>

            </div>
            """, unsafe_allow_html=True)

with right_col:
    st.markdown("""
    <div style='border: 1px solid #555; border-radius: 10px; padding: 20px; background-color: #111; height: 100%;'>
        <h3 style='color: white;'>Accident</h3>
        <p style='color: gray;'>Future card content will appear here.</p>
    </div>
    """, unsafe_allow_html=True)
