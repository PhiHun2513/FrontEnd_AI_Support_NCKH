import streamlit as st
import time
import api_handler as api
import ai_engine as ai
import utils
from views import dialogs 

def render_user_interface():
    current_user = st.session_state.user_info
    user_id = current_user['id']


    # 1. SIDEBAR USER
    with st.sidebar:
        st.header(f"👤 {current_user['username']}")
        if st.button("Đăng xuất", type="secondary", use_container_width=True, key="logout_btn"):
            st.session_state.user_info = None
            st.rerun()
        
        if "folder_selectbox_key" not in st.session_state:
            st.session_state.folder_selectbox_key = "-- Chọn đề tài --"

        with st.expander("➕ Tạo Đề tài mới"):
            with st.form("create_folder_form", clear_on_submit=True):
                n_name = st.text_input("Tên đề tài")
                n_desc = st.text_input("Mô tả ngắn")
                if st.form_submit_button("Tạo ngay", type="primary"):
                    if n_name and api.create_new_folder(n_name, n_desc, user_id):
                        st.session_state.folder_selectbox_key = n_name
                        st.rerun()
                    else: st.error("Lỗi kết nối server.")

        # Chọn đề tài
        folders = api.get_all_folders(user_id)
        f_opts = ["-- Chọn đề tài --"] + [f["folderName"] for f in folders]
        f_id_map = {f["folderName"]: f["id"] for f in folders}
        
        if st.session_state.folder_selectbox_key not in f_opts:
            st.session_state.folder_selectbox_key = "-- Chọn đề tài --"

        s_name = st.selectbox("Đề tài hiện tại:", options=f_opts, key="folder_selectbox_key")
        s_id = f_id_map.get(s_name)

        # Xử lý đổi folder
        if s_id != st.session_state.current_folder_id:
            st.session_state.current_folder_id = s_id
            st.session_state.messages = []
            if s_id:
                with st.spinner("Đang nạp dữ liệu..."):
                    utils.refresh_current_folder()
                    hist = api.get_chat_history(s_id)
                    for m in hist: st.session_state.messages.append({"role": m["role"], "content": m["content"]})
            else:
                st.session_state.pdf_content = ""
                st.session_state.source_map = {}
            st.rerun()

        # Cài đặt Folder
        if s_id:
            with st.expander(f"⚙️ Cài đặt: {s_name}"):
                t1, t2, t3 = st.tabs(["Sửa", "Files", "Xóa"])
                with t1:
                    cur_f = next((f for f in folders if f["id"] == s_id), None)
                    en = st.text_input("Tên mới", value=s_name)
                    ed = st.text_input("Mô tả mới", value=cur_f["description"] if cur_f else "")
                    if st.button("Lưu thay đổi"):
                        api.update_folder(s_id, en, ed); st.rerun()
                
                with t2:
                    fls = api.get_files_in_folder(s_id)
                    if fls:
                        file_map = {f"{f['fileName']}": f for f in fls}
                        selected_name = st.selectbox("Chọn file:", list(file_map.keys()), index=0)
                        if selected_name:
                            tgt = file_map[selected_name]
                            if st.session_state.get("cached_file_id") != tgt['id']:
                                with st.spinner("Kết nối..."):
                                    st.session_state.cached_file_bytes = api.download_document_bytes(tgt['id'])
                                    st.session_state.cached_file_id = tgt['id']
                            
                            st.caption(f"📦 {round(tgt['fileSize']/1024, 2)} KB")
                            if st.session_state.get("cached_file_bytes"):
                                st.download_button("📥 Tải xuống", data=st.session_state.cached_file_bytes, file_name=tgt['fileName'], mime="application/octet-stream", type="primary", use_container_width=True)
                            
                            st.write("")
                            if st.button("🗑️ Xóa file này", use_container_width=True):
                                if api.delete_file(tgt['id']):
                                    st.session_state.file_action_msg = f"Đã xóa: {tgt['fileName']}"
                                    st.session_state.cached_file_id = None; st.session_state.cached_file_bytes = None
                                    utils.refresh_current_folder(); st.rerun()
                        st.divider()
                        for f in fls: st.caption(f"• {f['fileName']}")
                    else: st.info("Chưa có tài liệu.")

                with t3:
                    if st.button("Xóa vĩnh viễn Đề tài", type="primary", use_container_width=True):
                        if api.delete_folder(s_id):
                            st.session_state.current_folder_id = None; st.session_state.delete_success = True; st.rerun()

            # Upload file
            st.divider(); st.subheader("⬆️ Upload tài liệu")
            with st.form("upload_form", clear_on_submit=True):
                up_files = st.file_uploader("Chọn file:", accept_multiple_files=True, type=['pdf', 'docx', 'txt'])
                if st.form_submit_button("Tải lên", type="primary", use_container_width=True) and up_files:
                    prog = st.progress(0, "Chuẩn bị...")
                    cnt = 0
                    for i, f in enumerate(up_files):
                        txt = ai.get_file_text(f)
                        if api.upload_file_to_java(f, s_id, txt):
                            st.session_state.pdf_content += "\n" + txt
                            st.session_state.source_map.update(ai.create_source_map(txt))
                            cnt += 1
                        prog.progress((i+1)/len(up_files))
                    if cnt > 0: st.session_state.upload_success_count = cnt; st.rerun()
        else:
            st.info("Vui lòng chọn hoặc tạo đề tài để bắt đầu.")


    # HEADER & TOOLS
    st.title("🛡️ Trợ lý AI hỗ trợ Nghiên cứu Khoa học")
    # Toast thông báo
    if st.session_state.upload_success_count > 0:
        st.toast(f"✅ Đã lưu {st.session_state.upload_success_count} file!", icon="🎉")
        st.session_state.upload_success_count = 0        
    if st.session_state.delete_success:
        st.toast("🗑️ Đã xóa đề tài!", icon="✅")
        st.session_state.delete_success = False

    if "show_history" not in st.session_state:
        st.session_state.show_history = True
    
    # Tạo container cho các nút điều khiển
    with st.container(border=True):
        col_tools_1, col_tools_2 = st.columns([0.7, 0.3])
        with col_tools_1:
            current_mode_val = st.session_state.get("selected_ai_mode", "🔍 Tra cứu chính xác")
            popover_label = "🔍 Tra cứu" if current_mode_val == "🔍 Tra cứu chính xác" else "💡 Sáng tạo"
            with st.popover(popover_label, use_container_width=False):
                st.markdown("**🎯 Chế độ AI**")
                st.radio(
                    "Chọn chế độ AI:",
                    ["🔍 Tra cứu chính xác", "💡 Tư duy & Sáng tạo"],
                    key="selected_ai_mode",
                    label_visibility="collapsed"
                )
                st.divider()
                st.caption("🔍 **Tra cứu:** để đảm bảo tính xác thực nguồn tin.\n\n💡 **Sáng tạo:** để khai thác chiều sâu và phát triển luận điểm.")
        
        with col_tools_2:
            lbl_h = "➡️ Ẩn Lịch sử" if st.session_state.show_history else "📜 Xem Lịch sử"
            if st.button(lbl_h, use_container_width=True):
                st.session_state.show_history = not st.session_state.show_history
                st.rerun()

    # 3. NỘI DUNG CHÍNH (CHIA KHUNG CUỘN RIÊNG)
    if st.session_state.show_history:
        col_chat, col_hist = st.columns([0.7, 0.3], gap="small")
    else:
        col_chat = st.container()
        col_hist = None

    # KHUNG CHAT 
    with col_chat:
        st.caption(f"Đang chat trong: **{s_name}**")
        with st.container(height=440, border=False):
            if not st.session_state.messages:
                st.info("👋 Hãy bắt đầu bằng việc đặt câu hỏi về tài liệu của bạn.")         
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    if msg["role"] == "user": 
                        st.markdown(msg["content"])
                    else: 
                        st.markdown(utils.format_answer_with_clickable_details(msg["content"], st.session_state.source_map), unsafe_allow_html=True)

    # KHUNG LỊCH SỬ 
    if col_hist:
        with col_hist:
            st.caption("📚 Lịch sử câu hỏi")
            with st.container(height=440, border=True):
                user_qs = [(i, m["content"]) for i, m in enumerate(st.session_state.messages) if m["role"] == "user"]

                if not user_qs:
                    st.caption("Chưa có lịch sử.")
                else:
                    for idx, q_content in reversed(user_qs):
                        display_text = q_content[:40] + "..." if len(q_content) > 40 else q_content
                        if st.button(f"❓ {display_text}", key=f"hist_btn_{idx}", use_container_width=True):
                            ans_text = "⏳ Đang xử lý..."
                            if idx + 1 < len(st.session_state.messages):
                                next_msg = st.session_state.messages[idx+1]
                                if next_msg["role"] == "assistant":
                                    ans_text = next_msg["content"]
                            dialogs.show_chat_detail(q_content, ans_text, st.session_state.source_map)
                            
    # 4. INPUT CHAT (LUÔN Ở DƯỚI CÙNG)   
    mode_key = "strict" if st.session_state.selected_ai_mode == "🔍 Tra cứu chính xác" else "creative"
    
    if prompt := st.chat_input("Nhập câu hỏi nghiên cứu..."):
        if not st.session_state.current_folder_id:
            st.warning("⚠️ Vui lòng chọn một đề tài trước khi hỏi!")
            st.stop()
        # Hiển thị ngay câu hỏi người dùng
        st.session_state.messages.append({"role": "user", "content": prompt})
        api.save_chat_message(st.session_state.current_folder_id, "user", prompt)
        st.rerun() 

    # Xử lý phản hồi AI 
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_msg = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"): 
             pass      
        if st.session_state.pdf_content:
            with st.spinner("AI đang phân tích tài liệu..."):
                ans = ai.ask_gemini(st.session_state.pdf_content, last_msg, mode=mode_key)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                api.save_chat_message(st.session_state.current_folder_id, "assistant", ans)
                st.rerun()
        else:
             st.warning("⚠️ Đề tài này chưa có tài liệu.")
