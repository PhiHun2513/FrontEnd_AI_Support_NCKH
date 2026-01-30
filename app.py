import streamlit as st
import ai_engine as ai
import utils
from dotenv import load_dotenv
from views import auth_view, admin_view, user_view  

# Cấu hình
load_dotenv()
ai.configure_gemini()
st.set_page_config(page_title="AI Research Assistant", layout="wide")

#Khởi tạo Session & Load CSS
utils.init_session_state()
utils.load_css("style.css") 

# Điều hướng Giao diện
if not st.session_state.user_info:
    auth_view.render_auth_interface()
else:
    # Kiểm tra quyền
    if st.session_state.user_info.get("role") == "ADMIN":
        admin_view.render_admin_interface()
    else:
        user_view.render_user_interface()