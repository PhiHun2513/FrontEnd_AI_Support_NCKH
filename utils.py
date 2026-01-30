import streamlit as st
import api_handler as api
import re

def load_css(file_name="style.css"):
    """Đọc file CSS và áp dụng vào Streamlit."""
    try:
        with open(file_name, "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Lỗi: Không tìm thấy file {file_name}")

def init_session_state():
    """Khởi tạo toàn bộ Session State cần thiết."""
    if "user_info" not in st.session_state: st.session_state.user_info = None
    if "messages" not in st.session_state: st.session_state.messages = []
    if "source_map" not in st.session_state: st.session_state.source_map = {}
    if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
    if "current_folder_id" not in st.session_state: st.session_state.current_folder_id = None
    if "upload_success_count" not in st.session_state: st.session_state.upload_success_count = 0
    if "delete_success" not in st.session_state: st.session_state.delete_success = False
    if "selected_ai_mode" not in st.session_state: st.session_state.selected_ai_mode = "🔍 Tra cứu chính xác"
    if "show_history" not in st.session_state: st.session_state.show_history = False

def format_answer_with_clickable_details(raw_text, source_map):
    """Hàm xử lý văn bản trả về từ AI để tạo trích dẫn click được."""
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

def refresh_current_folder():
    """Tải lại dữ liệu context từ Server."""
    if st.session_state.current_folder_id:
        context = api.get_folder_context(st.session_state.current_folder_id)
        st.session_state.pdf_content = context
        st.session_state.source_map = api.ai_engine.create_source_map(context) if hasattr(api, 'ai_engine') else {} 
        import ai_engine as ai
        st.session_state.source_map = ai.create_source_map(context) if context else {}