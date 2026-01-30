import streamlit as st
import api_handler as api
from views import dialogs

def render_auth_interface():
    st.write(""); st.write("") 
    col1, col2, col3 = st.columns([1, 0.8, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #1c7ed6;'>🔐 Đăng nhập</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Hệ thống Trợ lý AI Nghiên cứu Khoa học</p>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
        
        #  ĐĂNG NHẬP 
        with tab1:
            with st.form("login_form"):
                u = st.text_input("Tên đăng nhập")
                p = st.text_input("Mật khẩu", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.form_submit_button("Truy cập hệ thống", type="primary", use_container_width=True):
                    if not u or not p:
                         st.warning("⚠️ Vui lòng nhập đầy đủ thông tin!")
                    else:
                        user = api.login(u, p)
                        if user:
                            st.session_state.user_info = user
                            st.rerun()
                        else: 
                            st.error("❌ Sai thông tin đăng nhập!")

        #  ĐĂNG KÝ 
        with tab2:
            st.info("Tạo tài khoản mới để bắt đầu lưu trữ tài liệu nghiên cứu của bạn.")
            if st.button("📄 Đọc kỹ Chính sách & Quyền riêng tư", key="btn_policy_reg", use_container_width=True):
                dialogs.show_policy_modal()

            with st.form("register_form"):
                nu = st.text_input("Chọn tên đăng nhập")
                np = st.text_input("Chọn mật khẩu", type="password")
                st.markdown("---")
                agree_reg = st.checkbox("Tôi đã đọc và đồng ý với các điều khoản trên.")
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.form_submit_button("Tạo tài khoản mới", use_container_width=True):
                    if not nu or not np: st.warning("⚠️ Vui lòng điền đủ thông tin!")
                    elif not agree_reg: st.warning("⚠️ Bạn cần đồng ý với chính sách để đăng ký!")
                    elif api.register(nu, np): st.success("✅ Đăng ký thành công! Mời bạn quay lại tab Đăng nhập.")
                    else: st.error("❌ Tên đăng nhập đã tồn tại.")