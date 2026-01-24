import streamlit as st
import ai_engine as ai
import api_handler as api
from dotenv import load_dotenv
import re
import pandas as pd  # <--- THÊM MỚI: Dùng cho bảng Admin
import time          # <--- THÊM MỚI: Dùng cho Admin

# 1. Load cấu hình
load_dotenv()
ai_ready = ai.configure_gemini()

st.set_page_config(page_title="AI Research Assistant", layout="wide")

# ====================================================
# KHỞI TẠO SESSION STATE
# ====================================================
if "user_info" not in st.session_state: st.session_state.user_info = None
if "messages" not in st.session_state: st.session_state.messages = []
if "source_map" not in st.session_state: st.session_state.source_map = {}
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "current_folder_id" not in st.session_state: st.session_state.current_folder_id = None
if "upload_success_count" not in st.session_state: st.session_state.upload_success_count = 0
if "delete_success" not in st.session_state: st.session_state.delete_success = False
if "selected_ai_mode" not in st.session_state: st.session_state.selected_ai_mode = "🔍 Tra cứu chính xác"

# --- HÀM HIỂN THỊ CHÍNH SÁCH (Sử dụng st.dialog - Streamlit bản mới) ---
@st.dialog("📜 Chính sách & Điều khoản Sử dụng")
def show_policy_modal():
    st.markdown("""
    ### 1. Mục đích thu thập dữ liệu
    Hệ thống này là một phần của đề tài nghiên cứu khoa học. Bằng việc đăng ký và sử dụng, bạn đồng ý cho phép chúng tôi:
    - Lưu trữ các tài liệu (PDF, Word) bạn tải lên.
    - Sử dụng nội dung tài liệu để phân tích, huấn luyện và cải thiện độ chính xác của mô hình AI.
    - Admin hệ thống có quyền truy cập và kiểm duyệt các tài liệu này để đảm bảo tính an toàn thông tin.

    ### 2. Quyền riêng tư
    - Chúng tôi cam kết không chia sẻ dữ liệu cá nhân (tên đăng nhập, mật khẩu) cho bên thứ ba.
    - Dữ liệu tài liệu chỉ được sử dụng trong phạm vi nghiên cứu nội bộ của trường/nhóm nghiên cứu.

    ### 3. Trách nhiệm người dùng
    - Không tải lên các tài liệu chứa nội dung đồi trụy, phản động, hoặc vi phạm bản quyền nghiêm trọng.
    - Bạn chịu trách nhiệm hoàn toàn về tính hợp pháp của tài liệu mình tải lên.

    *Nhấn nút X ở góc để đóng cửa sổ này.*
    """)

# HÀM HỖ TRỢ HIỂN THỊ )
def refresh_current_folder():
    """Tải lại dữ liệu từ Server."""
    if st.session_state.current_folder_id:
        context = api.get_folder_context(st.session_state.current_folder_id)
        st.session_state.pdf_content = context
        st.session_state.source_map = ai.create_source_map(context) if context else {}

def format_answer_with_clickable_details(raw_text, source_map):

    raw_text = raw_text.replace("**", "") 

    def replacer(match):
        filename = match.group(1).strip()
        label_part = match.group(2).strip()
        display_label = label_part.replace("DOAN", "Trích đoạn").replace("Doan", "Trích đoạn").replace("Đoạn", "Trích đoạn")
        lookup_label = display_label
        first_num_match = re.search(r"\d+", lookup_label)
        if first_num_match:
            first_num = first_num_match.group(0)
            clean_type = "Trang" if "Trang" in lookup_label else "Trích đoạn"
            key = f"{filename} - {clean_type} {first_num}"
        else:
            key = "unknown"

        content = source_map.get(key, "⚠️ Không tìm thấy nội dung gốc.")
        safe_content = content.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        icon = "📄" if "docx" in filename.lower() else "📄"
        return f""" <details style="display:inline;vertical-align:middle;"><summary style="display:inline-flex;align-items:center;cursor:pointer;color:#1c7ed6;background:#e7f5ff;border:1px solid #a5d8ff;padding:0px 6px;border-radius:10px;font-size:0.75em;font-weight:bold;margin-left:2px;margin-right:2px;margin-bottom:2px;list-style:none;" title="Nguồn: {filename} ({display_label})">{icon}</summary><div style="display:block;margin-top:6px;margin-bottom:6px;padding:10px;background-color:#e7f5ff;border-left:3px solid #228be6;border-radius:4px;font-size:0.9em;color:#333;box-shadow:0 4px 6px rgba(0,0,0,0.05);"><div style="font-weight:bold;color:#1864ab;margin-bottom:4px;">📂 {filename} - {display_label}</div><div style="font-style:italic;color:#495057;">"{safe_content}"</div></div></details>"""
    return re.sub(r"[\s\n\r]*\(Nguồn: (.*?) - ([^\)]+?)\)[\s\n\r]*([.,;]?)", replacer, raw_text)



def render_admin_interface():
    # CSS cho các khối số liệu đẹp hơn
    st.markdown("""<style>div.stMetric {background-color: #f0f2f6; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px;}</style>""", unsafe_allow_html=True)
    
    admin_user = st.session_state.user_info
    
    # --- SIDEBAR MENU ---
    with st.sidebar:
        st.title("🛡️ ADMIN PORTAL")
        st.info(f"Xin chào, {admin_user['username']}")
        
        # Menu chọn chức năng (Thêm mục thứ 3)
        menu = st.radio("Menu quản lý", ["📊 Dashboard", "👥 Quản lý User", "🗄️ Quản lý Tài liệu"])
        
        st.divider()
        if st.button("Đăng xuất", type="secondary"):
            st.session_state.user_info = None
            st.rerun()

    # --- TAB 1: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.header("📊 Thống kê hệ thống")
        stats = api.get_admin_stats()
        if stats:
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng Người dùng", stats.get("totalUsers", 0), "👤") 
            c2.metric("Tổng Đề tài", stats.get("totalFolders", 0), "📂")
            c3.metric("Tổng tài liệu", stats.get("totalDocuments", 0), "📄")
        else:
            st.error("Không kết nối được server!")

    # --- TAB 2: QUẢN LÝ USER ---
    elif menu == "👥 Quản lý User":
        st.header("👥 Danh Sách Người Dùng")
        users = api.get_all_users()
        
        if users:
            # 1. Sắp xếp danh sách theo ID tăng dần
            users = sorted(users, key=lambda x: x['id'])
            
            # 2. Tạo DataFrame và thêm cột "STT" (Số thứ tự hiển thị)
            df = pd.DataFrame(users)
            
            # Tạo cột STT chạy từ 1 đến hết danh sách
            df.insert(0, 'STT', range(1, 1 + len(df)))
            
            # Xử lý các cột còn lại
            if 'password' in df.columns: df = df.drop(columns=['password'])
            
            # Đổi tên cột cho tiếng Việt dễ hiểu
            # Lưu ý: ID vẫn phải giữ để đối chiếu khi xóa, nhưng STT sẽ giúp nhìn danh sách liền mạch
            df.rename(columns={'id': 'ID Hệ thống', 'username': 'Tên đăng nhập', 'role': 'Quyền'}, inplace=True)
            
            # Hiển thị bảng full chiều rộng
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 3. Khu vực xóa User (Đã tối ưu hóa)
            st.write("") # Tạo khoảng cách
            with st.expander("❌ Xóa tài khoản", expanded=True):
                st.warning("⚠️ Cảnh báo: Hành động này sẽ xóa User và toàn bộ dữ liệu liên quan!")
                
                c1, c2 = st.columns([3, 1])
                
                with c1:
                    # Tạo danh sách lựa chọn thông minh: "ID - Tên"
                    user_options = [f"{u['id']} - {u['username']}" for u in users]
                    
                    # Selectbox cho phép chọn hoặc gõ để tìm
                    selected_str = st.selectbox(
                        "Chọn hoặc nhập ID người dùng cần xóa:", 
                        options=user_options,
                        help="Gõ số ID hoặc tên người dùng để lọc nhanh"
                    )
                
                with c2:
                    st.write("") # Căn chỉnh nút bấm xuống dòng cho thẳng hàng với ô nhập
                    st.write("")
                    if st.button("Xóa ngay", type="primary", use_container_width=True):
                        if selected_str:
                            # Tách lấy ID thực sự từ chuỗi "ID - Tên"
                            uid_to_delete = int(selected_str.split(" - ")[0])
                            
                            # Chặn không cho xóa chính mình
                            if uid_to_delete == admin_user['id']:
                                st.toast("⛔ Không thể tự xóa tài khoản Admin đang đăng nhập!", icon="🚫")
                            else:
                                if api.delete_user_by_admin(uid_to_delete):
                                    st.success(f"Đã xóa User ID {uid_to_delete}")
                                    time.sleep(1)
                                    st.rerun() # Tải lại trang để cập nhật bảng ngay lập tức
                                else:
                                    st.error("Lỗi server, chưa xóa được.")
        else: 
            st.info("Hệ thống chưa có user nào.")

    # --- TAB 3: QUẢN LÝ TÀI LIỆU (MỚI) ---
    elif menu == "🗄️ Quản lý Tài liệu":
        st.header("🗄️ Kho Tài Liệu Toàn Hệ Thống")
        st.caption("Danh sách tất cả tài liệu được tải lên bởi sinh viên. Dùng để kiểm duyệt và thu thập dataset.")
        
        all_docs = api.get_all_documents_admin()
        
        if all_docs:
            # Xử lý dữ liệu để hiển thị bảng đẹp
            data = []
            for d in all_docs:
                owner = "Unknown"
                # Lấy tên người sở hữu từ JSON trả về
                if d.get("folder") and d["folder"].get("user"):
                    owner = d["folder"]["user"]["username"]
                
                data.append({
                    "ID": d["id"],
                    "Tên File": d["fileName"],
                    "Kích thước (KB)": round(d["fileSize"] / 1024, 2),
                    "Người gửi": owner,
                    "Thời gian": d["uploadTime"]
                })
            
            df_docs = pd.DataFrame(data)
            st.dataframe(df_docs, use_container_width=True, hide_index=True)
            
            st.divider()
            
            # --- KHU VỰC TẢI FILE VỀ ---
            c1, c2 = st.columns([3, 1])
            with c1:
                # Dropdown chọn ID tài liệu
                if not df_docs.empty:
                    selected_id = st.selectbox("Chọn ID tài liệu cần tải về:", df_docs["ID"].tolist())
                    # Tìm lại tên file tương ứng để hiển thị nút
                    selected_filename = df_docs[df_docs["ID"] == selected_id]["Tên File"].values[0]
                else:
                    selected_id = None
            
            with c2:
                st.write("") 
                st.write("")
                
                if selected_id:
                    if st.button("📥 Chuẩn bị tải"):
                        with st.spinner("Đang tải dữ liệu từ server..."):
                            file_bytes = api.download_document_bytes(selected_id)
                            if file_bytes:
                                st.download_button(
                                    label=f"Lưu: {selected_filename}",
                                    data=file_bytes,
                                    file_name=selected_filename,
                                    mime="application/octet-stream",
                                    type="primary",
                                    use_container_width=True
                                )
                            else:
                                st.error("Lỗi tải file!")
        else:
            st.info("Hệ thống chưa có tài liệu nào.")
# KIỂM TRA ĐĂNG NHẬP 
if not st.session_state.user_info:
    st.write("")
    st.write("") 
    col1, col2, col3 = st.columns([1, 0.8, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #1c7ed6;'>🔐 Đăng nhập</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Hệ thống Trợ lý AI Nghiên cứu Khoa học</p>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
        
        # TAB 1: ĐĂNG NHẬP 
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

        # TAB 2: ĐĂNG KÝ 
        with tab2:
            st.info("Tạo tài khoản mới để bắt đầu lưu trữ tài liệu nghiên cứu của bạn.")
            if st.button("📄 Đọc kỹ Chính sách & Quyền riêng tư", key="btn_policy_reg", use_container_width=True):
                show_policy_modal()

            with st.form("register_form"):
                nu = st.text_input("Chọn tên đăng nhập")
                np = st.text_input("Chọn mật khẩu", type="password")
                
                st.markdown("---")
                agree_reg = st.checkbox("Tôi đã đọc và đồng ý với các điều khoản trên.")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.form_submit_button("Tạo tài khoản mới", use_container_width=True):
                    if not nu or not np:
                        st.warning("⚠️ Vui lòng điền đủ thông tin!")
                    elif not agree_reg:
                        st.warning("⚠️ Bạn cần đồng ý với chính sách để đăng ký!")
                    elif api.register(nu, np): 
                        st.success("✅ Đăng ký thành công! Mời bạn quay lại tab Đăng nhập.")
                    else: 
                        st.error("❌ Tên đăng nhập đã tồn tại.")
    
    st.stop()

#  ĐIỀU HƯỚNG: NẾU LÀ ADMIN THÌ CHẠY HÀM TRÊN RỒI DỪNG
if st.session_state.user_info.get("role") == "ADMIN":
    render_admin_interface()
    st.stop() 


# GIAO DIỆN USER
current_user = st.session_state.user_info
user_id = current_user['id']

st.title("🛡️ Trợ lý AI hỗ trợ Nghiên cứu Khoa học")

if st.session_state.upload_success_count > 0:
    st.toast(f"✅ Đã lưu {st.session_state.upload_success_count} file!", icon="🎉")
    st.session_state.upload_success_count = 0
if st.session_state.delete_success:
    st.toast("🗑️ Đã xóa đề tài!", icon="✅")
    st.session_state.delete_success = False

# SIDEBAR USER
with st.sidebar:
    st.header(f"👤 {current_user['username']}")
    if st.button("Đăng xuất", type="secondary", use_container_width=True, key="user_logout_sidebar_final"):
        st.session_state.user_info = None
        st.rerun()
    
    
    # TẠO ĐỀ TÀI MỚI
    st.subheader("📂 Quản lý Đề tài")
    with st.expander("➕ Tạo Đề tài mới"):
        with st.form("create_folder_form", clear_on_submit=True):
            n_name = st.text_input("Tên đề tài")
            n_desc = st.text_input("Mô tả ngắn")
            if st.form_submit_button("Tạo ngay", type="primary"):
                if n_name and api.create_new_folder(n_name, n_desc, user_id):
                    st.session_state.target_folder_name = n_name
                    st.rerun()
                else:
                    st.error("Lỗi: Tên đề tài không được để trống hoặc lỗi server.")

    # 3. DANH SÁCH & CHỌN ĐỀ TÀI
    folders = api.get_all_folders(user_id)
    f_opts = {"-- Chọn đề tài --": None}
    for f in folders:
        f_opts[f["folderName"]] = f["id"]
    
    # Logic tự động chọn folder vừa tạo
    def_idx = 0
    if "target_folder_name" in st.session_state:
        tgt = st.session_state.target_folder_name
        if tgt in f_opts:
            def_idx = list(f_opts.keys()).index(tgt)
        del st.session_state.target_folder_name

    s_name = st.selectbox("Đề tài hiện tại:", list(f_opts.keys()), index=def_idx)
    s_id = f_opts[s_name]

    # XỬ LÝ KHI CHUYỂN ĐỔI FOLDER
    if s_id != st.session_state.current_folder_id:
        st.session_state.current_folder_id = s_id
        st.session_state.messages = []
        st.session_state.sidebar_upload_status = None 
        st.session_state.file_action_msg = None 
        
        if s_id:
            with st.spinner("Đang tải dữ liệu..."):
                refresh_current_folder()
                hist = api.get_chat_history(s_id)
                for m in hist:
                    st.session_state.messages.append({"role": m["role"], "content": m["content"]})
        else:
            st.session_state.pdf_content = ""
            st.session_state.source_map = {}
        st.rerun()

    # CÀI ĐẶT FOLDER (SỬA / FILE / XÓA)
    if s_id:
        with st.expander(f"⚙️ Cài đặt: {s_name}"):
            t1, t2, t3 = st.tabs(["Sửa", "Files", "Xóa"])
            
            #  TAB 1: SỬA TÊN/MÔ TẢ ---
            with t1:
                cur_f = next((f for f in folders if f["id"] == s_id), None)
                curr_d = cur_f["description"] if cur_f else ""
                en = st.text_input("Tên mới", value=s_name)
                ed = st.text_input("Mô tả mới", value=curr_d)
                if st.button("Lưu thay đổi"): 
                    api.update_folder(s_id, en, ed)
                    st.rerun()
            
            # TAB 2: QUẢN LÝ FILE 
            with t2:
                if st.session_state.get("file_action_msg"):
                    st.success(st.session_state.file_action_msg, icon="✅")
                    st.session_state.file_action_msg = None

                fls = api.get_files_in_folder(s_id)
                if fls:
                    file_map = {f"{f['fileName']}": f for f in fls}
                    
                    # MENU CHỌN TÀI LIỆU
                    selected_name = st.selectbox("Chọn tài liệu:", list(file_map.keys()), index=0)
                    
                    if selected_name:
                        target_file = file_map[selected_name]
                        if st.session_state.get("cached_file_id") != target_file['id']:
                            with st.spinner("Đang kết nối..."):
                                st.session_state.cached_file_bytes = api.download_document_bytes(target_file['id'])
                                st.session_state.cached_file_id = target_file['id']
                        
                        st.caption(f"📦 {round(target_file['fileSize']/1024, 2)} KB | 🕒 {target_file['uploadTime']}")
                        
                        # KHU VỰC THAO TÁC    
                        # Nút Tải xuống 
                        if st.session_state.get("cached_file_bytes"):
                            st.download_button(
                                label="📥 Tải xuống tài liệu",
                                data=st.session_state.cached_file_bytes,
                                file_name=target_file['fileName'],
                                mime="application/octet-stream",
                                type="primary",
                                use_container_width=True
                            )
                        
                        st.write("")                        
                        #  Xóa 
                        if st.session_state.get("confirm_delete_id") != target_file['id']:
                            if st.button("🗑️ Xóa tài liệu này", use_container_width=True):
                                st.session_state.confirm_delete_id = target_file['id']
                                st.rerun()
                        
                        # khung Xác nhận 
                        else:
                            with st.container(border=True):
                                st.markdown(f":red[**Xác nhận xóa vĩnh viễn?**]")
                                c_huy, c_xoa = st.columns(2)
                                if c_huy.button("Hủy", use_container_width=True):
                                    st.session_state.confirm_delete_id = None
                                    st.rerun()
                                if c_xoa.button("Xóa ngay", type="primary", use_container_width=True):
                                    if api.delete_file(target_file['id']):
                                        st.session_state.file_action_msg = f"Đã xóa: {target_file['fileName']}"
                                        st.session_state.cached_file_id = None
                                        st.session_state.cached_file_bytes = None
                                        st.session_state.confirm_delete_id = None # Reset trạng thái
                                        refresh_current_folder()
                                        st.rerun()

                    st.divider()
                    st.markdown(f"**Danh sách file ({len(fls)}):**")
                    for f in fls:
                        st.caption(f"• {f['fileName']}")

                else:
                    st.info("Chưa có tài liệu nào.")
            
            #TAB 3: XÓA ĐỀ TÀI 
            with t3:
                st.warning("Hành động này không thể hoàn tác.")
                if st.button("Xóa vĩnh viễn Đề tài", type="primary"):
                    if api.delete_folder(s_id):
                        st.session_state.current_folder_id = None
                        st.session_state.delete_success = True
                        st.rerun()
    

    # 5. UPLOAD FILE 
    st.subheader("⬆️ Tải tài liệu")

    # Hiển thị thông báo thành công ngay tại đây
    if st.session_state.get("sidebar_upload_status"):
        st.success(st.session_state.sidebar_upload_status, icon="✅")
        st.session_state.sidebar_upload_status = None 

    with st.form("upload_form", clear_on_submit=True):
        up_files = st.file_uploader("Chọn file PDF/Word", accept_multiple_files=True, type=['pdf', 'docx', 'txt'])
        
        if st.form_submit_button("Tải lên ngay", type="primary") and up_files:
            cnt = 0
            for f in up_files:
                txt = ai.get_file_text(f) # Trích xuất text
                if api.upload_file_to_java(f, s_id, txt): # Gửi sang Java
                    st.session_state.pdf_content += "\n" + txt
                    st.session_state.source_map.update(ai.create_source_map(txt))
                    cnt += 1
            
            if cnt > 0:
                st.session_state.sidebar_upload_status = f"Đã thêm {cnt} tài liệu mới!"
                refresh_current_folder()
                st.rerun()

# KHU VỰC CHAT
if not st.session_state.pdf_content:
    st.info("👋 Vui lòng chọn Đề tài và Tải tài liệu để bắt đầu.")
    st.stop()

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            html_content = format_answer_with_clickable_details(msg["content"], st.session_state.source_map)
            st.markdown(html_content, unsafe_allow_html=True)

#MENU CÔNG CỤ CỐ ĐỊNH 
st.markdown("""
    <style>
    /* 1. ĐỊNH VỊ CẢ KHỐI POPOVER */
    [data-testid="stPopover"] {
        position: fixed;
        bottom: 115px; 
        left: 27.5rem;  
        z-index: 99999;
        width: auto !important; 
    }

    /* 2. ÉP NÚT BẤM (BUTTON) BÊN TRONG PHẢI NHỎ GỌN */
    [data-testid="stPopover"] > button {
        width: auto !important;          
        height: auto !important;         
        min-height: 0px !important;       
        padding: 4px 12px !important;    
        
        /* Tạo khung viền giống cái nhãn (Tag) */
        border: 1px solid #e0e0e0 !important;
        border-radius: 20px !important;  
        background-color: white !important;
        
        /* Chỉnh chữ */
        font-size: 14px !important;
        color: #555 !important;
        font-weight: 500 !important;
        
        /* Đổ bóng nhẹ cho nổi */
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        transition: all 0.2s ease;
    }

    /* Hiệu ứng khi di chuột vào */
    [data-testid="stPopover"] > button:hover {
        border-color: #ff4b4b !important; 
        color: #ff4b4b !important;
        background-color: #fff5f5 !important;
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# Logic hiển thị nút
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
   

mode_key = "strict" if st.session_state.selected_ai_mode == "🔍 Tra cứu chính xác" else "creative"

# INPUT CHAT
if prompt := st.chat_input("Hỏi trợ lý AI..."):
    if not st.session_state.current_folder_id:
        st.warning("⚠️ Chọn đề tài trước!"); st.stop()
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    api.save_chat_message(st.session_state.current_folder_id, "user", prompt)

    with st.chat_message("assistant"):
        if st.session_state.pdf_content:
            with st.spinner("AI đang phân tích..."):
                ans = ai.ask_gemini(st.session_state.pdf_content, prompt, mode=mode_key)
                
                html_ans = format_answer_with_clickable_details(ans, st.session_state.source_map)
                st.markdown(html_ans, unsafe_allow_html=True)
                
                st.session_state.messages.append({"role": "assistant", "content": ans})
                api.save_chat_message(st.session_state.current_folder_id, "assistant", ans)
        else:
            st.warning("Chưa có tài liệu!")