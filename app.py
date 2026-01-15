import streamlit as st
import ai_engine as ai
import api_handler as api
from dotenv import load_dotenv
import re

# Load cấu hình
load_dotenv()

# QUAN TRỌNG: Phải gọi cấu hình AI ngay lập tức
ai_ready = ai.configure_gemini()

st.set_page_config(page_title="AI Research Assistant", layout="wide")

st.title("🛡️ Ứng dụng AI hỗ trợ Nghiên cứu Khoa học")
st.subheader("Đảm bảo tính minh bạch và truy vết dữ liệu")

if not ai_ready:
    st.error("❌ Lỗi: Chưa tìm thấy GOOGLE_API_KEY trong file .env")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "source_map" not in st.session_state:
    st.session_state.source_map = {}

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Quản lý Tài liệu")
    uploaded_files = st.file_uploader("Tải lên PDF, DOCX, TXT", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    
    if uploaded_files:
        combined_text = ""
        for file in uploaded_files:
            # Gửi sang Java lưu DB
            api.upload_file_to_java(file)
            # Trích xuất và đánh dấu nguồn
            combined_text += ai.get_file_text(file)
        
        st.session_state.pdf_content = combined_text
        st.session_state.source_map = ai.create_source_map(combined_text)
        st.success("✅ Đã nạp tài liệu và sẵn sàng truy vết")

# --- CHAT AREA ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            # Tự động tìm các trích dẫn trong câu trả lời để hiển thị bằng chứng
            sources = re.findall(r"\((Trang \d+|Đoạn \d+)\)", msg["content"])
            if sources:
                with st.expander("🔍 Xác thực bằng chứng (Truy vết)"):
                    for src in set(sources):
                        if src in st.session_state.source_map:
                            st.write(f"**Nguồn {src}:**")
                            st.info(st.session_state.source_map[src])

if prompt := st.chat_input("Hỏi về tài liệu..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if "pdf_content" in st.session_state:
            with st.spinner("AI đang truy vết dữ liệu..."):
                answer = ai.ask_gemini(st.session_state.pdf_content, prompt)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun() 
        else:
            st.warning("Vui lòng tải tài liệu lên trước khi hỏi!")