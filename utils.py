import streamlit as st
import api_handler as api
import re

def load_css(file_name="style.css"):
    """Đọc file CSS và áp dụng vào Streamlit."""
    try:
        with open(file_name, "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass 

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
    """
    Hàm xử lý văn bản (Bản Fix lỗi xuống dòng):
    - Thay thế newline (\n) bằng khoảng trắng để văn bản dàn ngang (Justify).
    """
    if not isinstance(raw_text, str): return str(raw_text)

    # 1. Xóa in đậm
    raw_text = raw_text.replace("**", "") 

    def replacer(match):
        filename = match.group(1).strip()
        label_part = match.group(2).strip()
        
        display_label = label_part.replace("DOAN", "Trích đoạn").replace("Doan", "Trích đoạn").replace("Đoạn", "Trích đoạn")
        
        # Tìm key trong source_map
        first_num_match = re.search(r"\d+", display_label)
        if first_num_match:
            first_num = first_num_match.group(0)
            clean_type = "Trang" if "Trang" in display_label else "Trích đoạn"
            possible_keys = [
                f"{filename} - {clean_type} {first_num}",
                f"{filename} - {display_label}",
                f"[SOURCE: {filename} | TRANG: {first_num}]",
                f"[SOURCE: {filename} | DOAN: {first_num}]"
            ]
            content = "⚠️ Không tìm thấy nội dung gốc."
            for key in possible_keys:
                if key in source_map:
                    content = source_map.get(key)
                    break
        else:
            content = "⚠️ Không tìm thấy nội dung gốc."

        # --- SỬA LỖI TẠI ĐÂY ---
        # Cũ: replace('\n', '<br>') -> Gây lỗi xuống dòng lung tung
        # Mới: replace('\n', ' ') -> Biến xuống dòng thành dấu cách để chữ chạy ngang
        safe_content = content.replace('<', '&lt;').replace('>', '&gt;').replace('\n', ' ')
        
        # Xóa khoảng trắng thừa do việc nối dòng tạo ra
        safe_content = re.sub(r'\s+', ' ', safe_content).strip()

        icon = "📄" 
        if "docx" in filename.lower(): icon = "📝"
        if "Google" in filename or "http" in label_part: icon = "🌐"

        # CSS text-align: justify -> Căn đều 2 bên cho đẹp
        return f"""&nbsp;<details style="display:inline;vertical-align:middle;"><summary style="display:inline-flex;align-items:center;cursor:pointer;color:#1c7ed6;background:#e7f5ff;border:1px solid #a5d8ff;padding:0px 6px;border-radius:10px;font-size:0.75em;font-weight:bold;list-style:none;" title="Nguồn: {filename} ({display_label})">{icon}</summary><div style="display:block;width:100%;box-sizing:border-box;margin-top:6px;padding:10px;background-color:#f8f9fa;border-left:3px solid #228be6;border:1px solid #dee2e6;border-radius:4px;font-size:0.9em;color:#333;box-shadow:0 4px 6px rgba(0,0,0,0.05);"><div style="font-weight:bold;color:#1864ab;margin-bottom:4px;border-bottom:1px solid #ddd;padding-bottom:4px;">📂 {filename} - {display_label}</div><div style="font-style:italic;color:#495057;text-align:justify;line-height:1.5;">"{safe_content}"</div></div></details>"""

    pattern = r"[\s\n\r]*\(Nguồn: (.*?) - ([^\)]+?)\)[\s\n\r]*([.,;]?)"
    
    def final_replacer(match):
        return replacer(match)

    return re.sub(pattern, final_replacer, raw_text)

def refresh_current_folder():
    """Tải lại dữ liệu context từ Server."""
    if st.session_state.current_folder_id:
        context = api.get_folder_context(st.session_state.current_folder_id)
        st.session_state.pdf_content = context
        import ai_engine as ai
        st.session_state.source_map = ai.create_source_map(context) if context else {}