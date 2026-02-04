import streamlit as st
import api_handler as api
import re
import ai_engine as ai 

def load_css(file_name="style.css"):
    try:
        with open(file_name, "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def init_session_state():
    if "user_info" not in st.session_state: st.session_state.user_info = None
    if "messages" not in st.session_state: st.session_state.messages = []
    if "source_map" not in st.session_state: st.session_state.source_map = {}
    if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
    if "current_folder_id" not in st.session_state: st.session_state.current_folder_id = None
    if "upload_success_count" not in st.session_state: st.session_state.upload_success_count = 0
    if "delete_success" not in st.session_state: st.session_state.delete_success = False
    if "selected_ai_mode" not in st.session_state: st.session_state.selected_ai_mode = "🔍 Tra cứu chính xác"
    if "show_history" not in st.session_state: st.session_state.show_history = False
    if "prompt_history" not in st.session_state: st.session_state.prompt_history = [] 

def format_answer_with_clickable_details(raw_text, source_map):
    """Định dạng câu trả lời với chi tiết nguồn có thể click để xem nội dung gốc."""
    # Tiền xử lý văn bản thô
    if isinstance(raw_text, tuple): raw_text = raw_text[0]
    if not isinstance(raw_text, str): return str(raw_text)
    raw_text = re.sub(r"\*\*\s*(\(Nguồn:.*?\))\s*\*\*", r"\1", raw_text)
    raw_text = raw_text.replace("**", "")
    
    # Logic hiển thị chi tiết nguồn
    def replacer(match):
        filename = match.group(1).strip()
        label_part = match.group(2).strip()
        first_num_match = re.search(r"\d+", label_part)
        if first_num_match:
            num = first_num_match.group(0)
            type_tag = "TRANG" if "Trang" in label_part or "TRANG" in label_part else "DOAN"
            key = f"[SOURCE: {filename} | {type_tag}: {num}]"
        else:
            key = "unknown"

        content = source_map.get(key, "⚠️ Không tìm thấy nội dung gốc.")
        safe_content = content.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        
        return f"""
            <div style="display: inline-block; vertical-align: middle; margin: 2px;">
                <details style="position: relative; display: inline;">
                    <summary style="list-style:none; cursor:pointer; display:inline-flex; align-items:center; justify-content:center;
                                max-width: 100%; height: 18px; background:#e0f2fe; border:1px solid #7dd3fc; 
                                border-radius:50%; font-size:14px;" title="Nguồn: {filename}">📄</summary>
                    <div style="display: block; margin-top: 10px; width: 600px; min-width: 100%; max-width: 100%;
                                background: white; border: 1px solid #cbd5e1; border-radius: 8px; 
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); z-index: 100;">
                        <div style="background: #f1f5f9; padding: 8px 12px; border-bottom: 1px solid #e2e8f0; font-size: 12px; font-weight: bold; color: #334155;">
                            📂 {filename} ({label_part})
                        </div>
                        <div style="padding: 12px; font-size: 14px; background: #ffffff; font-style: italic;">
                            "{safe_content}"
                        </div>
                    </div>
                </details>
            </div>"""
    return re.sub(r"[\s\n\r]*\(Nguồn: (.*?) - ([^\)]+?)\)[\s\n\r]*([.,;]?)", replacer, raw_text)

def refresh_current_folder():
    """Tải lại dữ liệu context và duy trì lịch sử prompt. Có Try-Catch để tránh crash."""
    try:
        if st.session_state.get("current_folder_id"):
            folder_id = st.session_state.current_folder_id
            context = api.get_folder_context(folder_id)
            st.session_state.pdf_content = context
            
            if context:
                st.session_state.source_map = ai.create_source_map(context)
            else:
                st.session_state.source_map = {}

            if "prompt_history" not in st.session_state:
                st.session_state.prompt_history = []
                
    except Exception as e:
        print(f"⚠️ Lỗi khi làm mới folder: {e}")
        st.session_state.pdf_content = ""
        st.session_state.source_map = {}