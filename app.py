import streamlit as st
import ai_engine as ai
import api_handler as api
from dotenv import load_dotenv
import re

# 1. Load cấu hình môi trường
load_dotenv()

# 2. Cấu hình AI ngay lập tức
ai_ready = ai.configure_gemini()

st.set_page_config(page_title="AI Research Assistant", layout="wide")

st.title("🛡️ Ứng dụng AI hỗ trợ Nghiên cứu Khoa học")
st.subheader("Đảm bảo tính minh bạch và truy vết dữ liệu")

# 3. Kiểm tra API Key
if not ai_ready:
    st.error("❌ Lỗi: Chưa tìm thấy GOOGLE_API_KEY trong file .env")
    st.stop()

# 4. Khởi tạo Session State (Bộ nhớ tạm)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "source_map" not in st.session_state:
    st.session_state.source_map = {}
if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = ""

# --- SIDEBAR: QUẢN LÝ TÀI LIỆU ---
with st.sidebar:
    st.header("📂 Quản lý Đề tài Nghiên cứu")
    
    # 1. FORM TẠO THƯ MỤC MỚI
    with st.expander("➕ Tạo Đề tài/Thư mục mới"):
        new_folder_name = st.text_input("Tên đề tài (VD: Blockchain)")
        new_folder_desc = st.text_input("Mô tả ngắn")
        if st.button("Tạo ngay"):
            if api.create_new_folder(new_folder_name, new_folder_desc):
                st.success("Đã tạo thành công!")
                st.rerun() # Load lại trang để cập nhật danh sách
            else:
                st.error("Lỗi khi tạo folder!")

    st.divider() # Đường kẻ ngang

    # 2. CHỌN THƯ MỤC LÀM VIỆC
    # Lấy danh sách từ Java đổ vào Dropdown
    folders = api.get_all_folders()
    
    # Tạo dictionary để map: "Tên hiển thị" -> "ID"
    folder_options = {f["folderName"]: f["id"] for f in folders}
    
    # Thêm lựa chọn "Không chọn thư mục"
    folder_options["-- Không lưu vào thư mục --"] = None
    
    selected_folder_name = st.selectbox(
        "Đang làm việc với đề tài:",
        options=list(folder_options.keys()),
        index=0
    )
    
    # Lấy ID thực tế để gửi cho Backend
    selected_folder_id = folder_options[selected_folder_name]

    st.divider()

    # 3. UPLOAD FILE (Đã nâng cấp)
    st.subheader("Tải tài liệu lên")
    uploaded_files = st.file_uploader(
        f"Thêm tài liệu vào: {selected_folder_name}", 
        type=["pdf", "docx", "txt"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        combined_text = ""
        for file in uploaded_files:
            # Gửi file + ID thư mục sang Java
            if api.upload_file_to_java(file, selected_folder_id):
                st.toast(f"✅ Đã lưu '{file.name}' vào CSDL!", icon="💾")
            else:
                st.toast(f"❌ Lưu thất bại '{file.name}'", icon="⚠️")
                
            # Phần xử lý AI (giữ nguyên)
            combined_text += ai.get_file_text(file)
        
        # Chỉ cập nhật nội dung AI nếu có text mới
        if combined_text:
            st.session_state.pdf_content = combined_text
            st.session_state.source_map = ai.create_source_map(combined_text)
            st.success("✅ AI đã đọc xong tài liệu!")

# --- CHAT AREA (KHU VỰC CHAT) ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Nếu là câu trả lời của AI -> Hiển thị công cụ truy vết
        if msg["role"] == "assistant":
            sources = re.findall(r"\((Trang \d+|Đoạn \d+)\)", msg["content"])
            if sources:
                with st.expander("🔍 Xác thực bằng chứng (Truy vết)"):
                    for src in set(sources):
                        if src in st.session_state.source_map:
                            st.markdown(f"**Nguồn {src}:**")
                            st.info(st.session_state.source_map[src])

# Input nhập câu hỏi
if prompt := st.chat_input("Hỏi về tài liệu..."):
    # 1. Hiển thị câu hỏi người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Xử lý câu trả lời của AI
    with st.chat_message("assistant"):
        if st.session_state.pdf_content:
            with st.spinner("AI đang truy vết dữ liệu..."):
                answer = ai.ask_gemini(st.session_state.pdf_content, prompt)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun() # Reload để hiện nút Expand nguồn
        else:
            st.warning("⚠️ Vui lòng tải tài liệu lên trước khi hỏi!")