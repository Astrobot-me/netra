import streamlit as st
import CONTANTS

st.set_page_config(layout="wide")
st.title("🚦 Intelligent Traffic Management Panel")

def video_html(src, id):
    return f"""
    <video width="100%" id="{id}" autoplay loop muted playsinline>
        <source src="{src}" type="video/mp4">
        Your browser does not support the video tag.
    </video>
    """

# Initialize session state
if 'traffic_state' not in st.session_state:
    st.session_state.traffic_state = {
        "p1": "play",
        "p2": "stop"
    }

# Sample dynamic values
lane_timings = {
    "Lane1": "23s",
    "Lane2": "17s",
    "Lane3": "42s",
    "Lane4": "8s",
}

lane_status = {
    "Lane1": "green",
    "Lane2": "red",
    "Lane3": "yellow",
    "Lane4": "green",
}

lane_videos = {
    "Lane1": CONTANTS.V1,
    "Lane2": CONTANTS.V2,
    "Lane3": CONTANTS.V3,
    "Lane4": CONTANTS.V4,
}

status_color_map = {
    "green": "🟢",
    "red": "🔴",
    "yellow": "🟡"
}

# Control buttons
# In your sidebar control buttons:
with st.sidebar:

    st.subheader("Traffic Control")
    if st.button("Switch to Phase 1"):
        st.session_state.traffic_state = {"p1": "play", "p2": "stop"}
        st.toast("Switched to Phase 1")
        st.rerun()
    if st.button("Switch to Phase 2"):
        st.session_state.traffic_state = {"p1": "stop", "p2": "play"}
        st.toast("Switched to Phase 2")
        st.rerun()

# Main layout
left_col, right_col = st.columns([4, 1])

with left_col:
    st.subheader("Lane Status Overview")
    
    for i in range(0, 4, 2):
        row = st.columns(2)
        for j in range(2):
            lane_num = i + j + 1
            lane = f"Lane{lane_num}"
            with row[j]:
                st.markdown(f"### Lane {lane_num}")
                color = lane_status[lane]
                st.markdown(
                    f"<p style='font-size:18px;'><b>Signal:</b> <span style='color:{color};'>{status_color_map[lane_status[lane]]} {lane_status[lane].upper()} Signal</span></p>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<p style='font-size:18px; color:white;'><b>Time Left:</b>  <span style='font-size:40px;'>  {lane_timings[lane]} </span> </p>",
                    unsafe_allow_html=True
                )
                # Changed ID to be consistent with JavaScript
                st.markdown(video_html(lane_videos[lane], f"video_{lane_num}"), unsafe_allow_html=True)

with right_col:
    st.subheader("🚨 Accident Log")
    st.info("No recent accidents.")



js_control = f"""
<script>
function controlVideos() {{
    console.log("Executing controlVideos with phase:", {st.session_state.traffic_state});
    
    function controlVideo(id, shouldPlay) {{
        const video = document.getElementById(id);
        console.log(`Controlling ${{id}} - exists: ${{!!video}}`);
        if (video) {{
            try {{
                if (shouldPlay) {{
                    video.play().catch(e => console.log(`Play error for ${{id}}:`, e));
                    console.log(`Playing ${{id}}`);
                }} else {{
                    video.pause();
                    console.log(`Pausing ${{id}}`);
                }}
            }} catch (e) {{
                console.error(`Control error for ${{id}}:`, e);
            }}
        }} else {{
            console.log(`Video ${{id}} not found`);
        }}
    }}

    // Phase control
    const phase = {st.session_state.traffic_state};
    function applyPhaseControl() {{
        if (phase.p1 === "play" && phase.p2 === "stop") {{
            console.log("Activating Phase 1");
            controlVideo('video_1', true);
            controlVideo('video_2', true);
            controlVideo('video_3', false);
            controlVideo('video_4', false);
        }} else if (phase.p1 === "stop" && phase.p2 === "play") {{
            console.log("Activating Phase 2");
            controlVideo('video_3', true);
            controlVideo('video_4', true);
            controlVideo('video_1', false);
            controlVideo('video_2', false);
        }}
    }}

    // Wait for videos to load
    function waitForVideos() {{
        const videos = ['video_1', 'video_2', 'video_3', 'video_4'];
        const allVideosExist = videos.every(id => document.getElementById(id));
        if (allVideosExist) {{
            applyPhaseControl();
        }} else {{
            console.log("Some videos not found, retrying...");
            setTimeout(waitForVideos, 100);
        }}
    }}

    // Execute immediately and on load
    (function() {{
        window.addEventListener('load', waitForVideos);
        waitForVideos();
    }})();
}}    
</script>
"""
# Render with key to force update
st.components.v1.html(js_control, height=0, )