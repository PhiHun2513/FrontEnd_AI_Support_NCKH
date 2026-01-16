import streamlit as st
import ai_engine as ai
import api_handler as api
from dotenv import load_dotenv
import re



# 1. Load cấu hình
load_dotenv()
ai_ready = ai.configure_gemini()

st.set_page_config(page_title="AI Research Assistant", layout="wide")


# ====================================================
# PHẦN 0: KIỂM TRA ĐĂNG NHẬP (USER LOGIN SYSTEM)
# ====================================================
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# Nếu CHƯA đăng nhập -> Hiện form Login/Register
if not st.session_state.user_info:
    st.title("🔐 Đăng nhập Hệ thống Nghiên cứu")
    
    tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký tài khoản mới"])
    
    # --- TAB 1: LOGIN ---
    with tab1:
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập", type="primary"):
            user = api.login(username, password)
            if user:
                st.session_state.user_info = user
                st.success(f"Chào mừng {user['username']}!")
                st.rerun() # Load lại trang để vào phần chính
            else:
                st.error("❌ Sai tài khoản hoặc mật khẩu!")

    # --- TAB 2: REGISTER ---
    with tab2:
        new_user = st.text_input("Tên đăng nhập mới")
        new_pass = st.text_input("Mật khẩu mới", type="password")
        if st.button("Đăng ký"):
            if api.register(new_user, new_pass):
                st.success("✅ Đăng ký thành công! Hãy quay lại tab Đăng nhập.")
            else:
                st.error("❌ Tên đăng nhập đã tồn tại hoặc lỗi hệ thống.")
    
    st.info("Vui lòng đăng nhập để quản lý tài liệu cá nhân của bạn.")
    st.stop() # Dừng code tại đây, không chạy phần dưới khi chưa login

# ====================================================
# PHẦN CHÍNH: ỨNG DỤNG (CHỈ CHẠY KHI ĐÃ LOGIN)
# ====================================================

# Lấy thông tin User đang đăng nhập
current_user = st.session_state.user_info
user_id = current_user['id']

# Khởi tạo các biến Session khác
if "messages" not in st.session_state: st.session_state.messages = []
if "source_map" not in st.session_state: st.session_state.source_map = {}
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "current_folder_id" not in st.session_state: st.session_state.current_folder_id = None

st.title("🛡️ Ứng dụng AI hỗ trợ Nghiên cứu Khoa học")
st.caption(f"Đang làm việc với tư cách: **{current_user['username']}**")

# Kiểm tra API Key Google
if not ai_ready:
    st.error("❌ Lỗi: Chưa tìm thấy GOOGLE_API_KEY trong file .env")
    st.stop()


if "upload_success_count" not in st.session_state:
    st.session_state.upload_success_count = 0

# Nếu có đánh dấu thành công từ lần chạy trước -> Hiện thông báo
if st.session_state.upload_success_count > 0:
    count = st.session_state.upload_success_count
    st.toast(f"✅ Đã lưu thành công {count} tài liệu!", icon="🎉")
    st.success(f"Đã cập nhật thêm {count} tài liệu vào đề tài!")
    
    # Reset về 0 để không hiện lại lần sau
    st.session_state.upload_success_count = 0

# --- SIDEBAR: QUẢN LÝ ---
with st.sidebar:
    st.header(f"👤 {current_user['username']}")
    if st.button("Đăng xuất"):
        st.session_state.user_info = None
        st.rerun()
    
    st.divider()
    st.subheader("📂 Quản lý Đề tài")

    # 1. TẠO THƯ MỤC MỚI (GỬI KÈM USER_ID)
    with st.expander("➕ Tạo Đề tài mới", expanded=False):
        new_folder_name = st.text_input("Tên đề tài", key="new_folder_name")
        new_folder_desc = st.text_input("Mô tả ngắn", key="new_folder_desc")
        
        if st.button("Tạo ngay", type="primary"):
            if new_folder_name.strip():
                # Gửi user_id vào hàm tạo
                if api.create_new_folder(new_folder_name, new_folder_desc, user_id):
                    st.success("✅ Đã tạo thành công!")
                    st.rerun()
                else:
                    st.error("Lỗi: Có thể tên đã trùng!")
            else:
                st.warning("Nhập tên đề tài!")

    st.divider()

    # 2. DANH SÁCH THƯ MỤC (CHỈ LẤY CỦA USER NÀY)
    folders = api.get_all_folders(user_id) # Truyền user_id vào
    
    folder_options = {f["folderName"]: f["id"] for f in folders}
    folder_options["-- Không lưu vào thư mục --"] = None
    
    selected_folder_name = st.selectbox(
        "Chọn đề tài:",
        options=list(folder_options.keys()),
        index=0
    )
    
    selected_folder_id = folder_options[selected_folder_name]

    # XỬ LÝ CHUYỂN ĐỔI FOLDER
    if selected_folder_id != st.session_state.current_folder_id:
        st.session_state.current_folder_id = selected_folder_id
        st.session_state.messages = [] 
        
        if selected_folder_id:
            with st.spinner(f"Đang tải '{selected_folder_name}'..."):
                # Tải Context
                old_context = api.get_folder_context(selected_folder_id)
                st.session_state.pdf_content = old_context
                st.session_state.source_map = ai.create_source_map(old_context) if old_context else {}

                # Tải Lịch sử Chat
                history = api.get_chat_history(selected_folder_id)
                for msg in history:
                    st.session_state.messages.append({
                        "role": msg["role"], 
                        "content": msg["content"]
                    })
        else:
            st.session_state.pdf_content = ""
            st.session_state.source_map = {}
            st.session_state.messages = []

    # CÀI ĐẶT FOLDER (SỬA / XÓA / FILE)
    if selected_folder_id:
        with st.expander(f"⚙️ Cài đặt: {selected_folder_name}"):
            tab_edit, tab_files, tab_delete = st.tabs(["Sửa", "Files", "Xóa"])
            
            with tab_edit:
                e_name = st.text_input("Tên mới", value=selected_folder_name)
                curr_desc = next((f["description"] for f in folders if f["id"] == selected_folder_id), "")
                e_desc = st.text_input("Mô tả mới", value=curr_desc)
                if st.button("Lưu"):
                    if api.update_folder(selected_folder_id, e_name, e_desc):
                        st.success("Xong!")
                        st.rerun()

            with tab_files:
                files = api.get_files_in_folder(selected_folder_id)
                if files:
                    for file in files:
                        c1, c2 = st.columns([0.8, 0.2])
                        c1.write(f"📄 {file['fileName']}")
                        if c2.button("Xóa", key=f"del_{file['id']}"):
                            api.delete_file(file['id'])
                            st.rerun()
                else:
                    st.info("Trống")

            with tab_delete:
                if st.button("Xóa Đề tài", type="primary"):
                    api.delete_folder(selected_folder_id)
                    st.session_state.current_folder_id = None
                    st.rerun()

  # 3. UPLOAD FILE
    st.subheader("Tải tài liệu lên")
    
    with st.form("upload_form", clear_on_submit=True):
        uploaded_files = st.file_uploader("Chọn file (PDF, DOCX, TXT)", accept_multiple_files=True)
        submitted = st.form_submit_button("⬆️ Tải lên ngay")
        
        if submitted and uploaded_files:
            if not selected_folder_id:
                st.error("⚠️ Chưa chọn Đề tài! Vui lòng chọn đề tài phía trên.")
                st.stop()

            success_count = 0
            with st.spinner("Đang xử lý và lưu..."):
                for file in uploaded_files:
                    # 1. Đọc nội dung
                    text = ai.get_file_text(file)
                    
                    # 2. Gửi API
                    if api.upload_file_to_java(file, selected_folder_id, text):
                        # Cập nhật context cho Chat ngay lập tức
                        st.session_state.pdf_content += "\n" + text
                        st.session_state.source_map.update(ai.create_source_map(text))
                        success_count += 1

            if success_count > 0:
                # --- QUAN TRỌNG: Lưu số lượng thành công vào Session ---
                st.session_state.upload_success_count = success_count
                
                # Làm mới trang để hiện file trong danh sách
                st.rerun()
            else:
                st.error("Lỗi: Không lưu được file nào. Kiểm tra kết nối Server.")

# --- CHAT AREA ---
if not st.session_state.pdf_content:
    st.info("👋 Hãy chọn một đề tài hoặc tải tài liệu để bắt đầu.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            sources = re.findall(r"\((Trang \d+|Đoạn \d+)\)", msg["content"])
            if sources:
                with st.expander("🔍 Nguồn dẫn chứng"):
                    for src in set(sources):
                        if src in st.session_state.source_map:
                            st.info(f"**{src}**: {st.session_state.source_map[src]}")

if prompt := st.chat_input("Hỏi AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    # Lưu câu hỏi User
    if st.session_state.current_folder_id:
        api.save_chat_message(st.session_state.current_folder_id, "user", prompt)

    with st.chat_message("assistant"):
        if st.session_state.pdf_content:
            with st.spinner("Đang suy nghĩ..."):
                answer = ai.ask_gemini(st.session_state.pdf_content, prompt)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Lưu câu trả lời AI
                if st.session_state.current_folder_id:
                    api.save_chat_message(st.session_state.current_folder_id, "assistant", answer)
                
                st.rerun()
        else:
            st.warning("Chưa có tài liệu nào để phân tích!")

# 2. Xử lý câu trả lời của AI
    with st.chat_message("assistant"):
        if st.session_state.pdf_content:
            with st.spinner("AI đang đọc và phân tích..."):
                # 1. Gọi AI
                raw_answer = ai.ask_gemini(st.session_state.pdf_content, prompt)
                
                # --- [XỬ LÝ HIỂN THỊ VĂN BẢN] ---
                # Thay thế các từ khóa cũ/kỹ thuật thành từ ngữ đẹp hơn
                # Logic: Nếu AI nói "Đoạn" -> đổi thành "Trích đoạn" cho hay
                display_answer = raw_answer.replace("(Đoạn", "(Trích đoạn")
                
                # Tô màu xanh đậm cho TẤT CẢ các loại nguồn (Trang/Đoạn/Trích đoạn/Tham chiếu)
                # Regex này chấp nhận mọi biến thể từ ngữ
                formatted_answer = re.sub(
                    r"\((Trang|Đoạn|Trích đoạn|Tham chiếu)\s+(\d+)(?:-(\d+))?\)", 
                    r':green[**\g<0>**]', 
                    display_answer
                )
                
                st.markdown(formatted_answer)

                # Lưu DB
                st.session_state.messages.append({"role": "assistant", "content": formatted_answer})
                if st.session_state.current_folder_id:
                    api.save_chat_message(st.session_state.current_folder_id, "assistant", raw_answer)
                
                # =========================================================
                # [GIAO DIỆN TABS TRA CỨU - PHIÊN BẢN VẠN NĂNG]
                # =========================================================
                
                # 1. Regex tìm nguồn: Bắt dính cả "Trang", "Đoạn", "Trích đoạn", "Tham chiếu"
                sources = re.findall(r"\((Trang|Đoạn|Trích đoạn|Tham chiếu)\s+(\d+)(?:-(\d+))?\)", raw_answer)
                
                if sources:
                    valid_sources_content = [] # Danh sách chứa (Tên Tab, Nội dung)
                    
                    seen_indices = set() # Để lọc trùng (VD: AI nhắc đoạn 5 hai lần)

                    for dtype, start, end in set(sources):
                        s = int(start)
                        e = int(end) if end else s
                        
                        for i in range(s, e + 1):
                            # Tạo định danh duy nhất để không bị trùng lặp
                            unique_id = f"{dtype}_{i}"
                            if unique_id in seen_indices: continue
                            seen_indices.add(unique_id)

                            # --- THUẬT TOÁN TÌM KIẾM THÔNG MINH ---
                            # Dù AI nói là "Đoạn" hay "Trích đoạn", ta đều thử tra trong từ điển
                            # để tìm ra nội dung gốc.
                            
                            content_found = None
                            final_label = ""
                            
                            # Thử các khả năng key có thể có trong source_map
                            possible_keys = [
                                f"Trích đoạn {i}", # Ưu tiên tìm cái này mới
                                f"Đoạn {i}",       # Tìm cái cũ
                                f"Trang {i}",      # Tìm trang PDF
                                f"Tham chiếu {i}"
                            ]
                            
                            for key in possible_keys:
                                if key in st.session_state.source_map:
                                    content_found = st.session_state.source_map[key]
                                    # Đặt tên Tab cho đẹp (đồng bộ hóa)
                                    if "Trang" in key:
                                        final_label = f"Trang {i}"
                                    else:
                                        final_label = f"Trích đoạn {i}"
                                    break
                            
                            # Nếu tìm thấy nội dung -> Thêm vào danh sách hiển thị
                            if content_found:
                                valid_sources_content.append((final_label, content_found))
                    
                    # Sắp xếp danh sách theo số thứ tự (số nhỏ đứng trước)
                    # Logic sort: Lấy số từ chuỗi "Trích đoạn 10" -> 10
                    valid_sources_content.sort(key=lambda x: int(x[0].split(' ')[1]))
                    
                    # --- HIỂN THỊ RA MÀN HÌNH ---
                    if valid_sources_content:
                        st.divider()
                        st.caption("🔎 **Bấm vào thẻ bên dưới để xem nội dung gốc:**")
                        
                        # Tách thành 2 list riêng để nạp vào st.tabs
                        labels = [item[0] for item in valid_sources_content]
                        contents = [item[1] for item in valid_sources_content]
                        
                        # Tạo Tabs
                        tabs = st.tabs(labels)
                        
                        for idx, tab in enumerate(tabs):
                            with tab:
                                st.info(contents[idx], icon="📄")

        else:
            st.warning("⚠️ Vui lòng tải tài liệu lên trước khi hỏi!")