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

# ====================================================
# HÀM HỖ TRỢ HIỂN THỊ
# ====================================================
def refresh_current_folder():
    """Tải lại dữ liệu từ Server."""
    if st.session_state.current_folder_id:
        context = api.get_folder_context(st.session_state.current_folder_id)
        st.session_state.pdf_content = context
        st.session_state.source_map = ai.create_source_map(context) if context else {}

def format_answer_with_clickable_details(raw_text, source_map):
    """
    Biến đổi text: (Nguồn: ...) -> Icon nhỏ 📄.
    Phiên bản V7 (Final): 
    - "Hàn" lại các câu bị gãy do AI xuống dòng bừa bãi.
    - Xóa khoảng trắng thừa trước và sau icon.
    """
    
    # 1. Xóa dấu ** (in đậm)
    raw_text = raw_text.replace("**", "") 

    def replacer(match):
        # match.group(0) là toàn bộ cụm bắt được
        filename = match.group(1).strip()
        label_part = match.group(2).strip()
        
        # Chuẩn hóa từ khóa
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
        # 📕
        return f""" <details style="display:inline;vertical-align:middle;"><summary style="display:inline-flex;align-items:center;cursor:pointer;color:#1c7ed6;background:#e7f5ff;border:1px solid #a5d8ff;padding:0px 6px;border-radius:10px;font-size:0.75em;font-weight:bold;margin-left:2px;margin-right:2px;margin-bottom:2px;list-style:none;" title="Nguồn: {filename} ({display_label})">{icon}</summary><div style="display:block;margin-top:6px;margin-bottom:6px;padding:10px;background-color:#e7f5ff;border-left:3px solid #228be6;border-radius:4px;font-size:0.9em;color:#333;box-shadow:0 4px 6px rgba(0,0,0,0.05);"><div style="font-weight:bold;color:#1864ab;margin-bottom:4px;">📂 {filename} - {display_label}</div><div style="font-style:italic;color:#495057;">"{safe_content}"</div></div></details>"""
    return re.sub(r"[\s\n\r]*\(Nguồn: (.*?) - ([^\)]+?)\)[\s\n\r]*([.,;]?)", replacer, raw_text)

#  KIỂM TRA ĐĂNG NHẬP
if not st.session_state.user_info:
    st.title("🔐 Đăng nhập Hệ thống Nghiên cứu")
    tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
    with tab1:
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập", type="primary"):
            user = api.login(u, p)
            if user:
                st.session_state.user_info = user
                st.rerun()
            else: st.error("❌ Sai thông tin!")
    with tab2:
        nu = st.text_input("User mới"); np = st.text_input("Pass mới", type="password")
        if st.button("Đăng ký"):
            if api.register(nu, np): st.success("✅ Đăng ký thành công! Mời đăng nhập.")
            else: st.error("❌ Lỗi đăng ký.")
    st.stop()


# GIAO DIỆN CHÍNH
current_user = st.session_state.user_info
user_id = current_user['id']

st.title("🛡️ Trợ lý AI hỗ trợ Nghiên cứu Khoa học")

if st.session_state.upload_success_count > 0:
    st.toast(f"✅ Đã lưu {st.session_state.upload_success_count} file!", icon="🎉")
    st.session_state.upload_success_count = 0
if st.session_state.delete_success:
    st.toast("🗑️ Đã xóa đề tài!", icon="✅")
    st.session_state.delete_success = False

# SIDEBAR
with st.sidebar:
    st.header(f"👤 {current_user['username']}")
    if st.button("Đăng xuất"): st.session_state.user_info = None; st.rerun()
    
    st.subheader("📂 Quản lý Đề tài")
    with st.expander("➕ Tạo Đề tài mới"):
        n_name = st.text_input("Tên", key="n_n")
        n_desc = st.text_input("Mô tả", key="n_d")
        if st.button("Tạo ngay", type="primary"):
            if n_name and api.create_new_folder(n_name, n_desc, user_id):
                st.session_state.target_folder_name = n_name
                st.rerun()
            else: st.error("Lỗi tạo.")

    folders = api.get_all_folders(user_id)
    f_opts = {"-- Chọn đề tài --": None}
    for f in folders: f_opts[f["folderName"]] = f["id"]
    
    def_idx = 0
    if "target_folder_name" in st.session_state:
        tgt = st.session_state.target_folder_name
        if tgt in f_opts: def_idx = list(f_opts.keys()).index(tgt)
        del st.session_state.target_folder_name

    s_name = st.selectbox("Đề tài hiện tại:", list(f_opts.keys()), index=def_idx)
    s_id = f_opts[s_name]

    if s_id != st.session_state.current_folder_id:
        st.session_state.current_folder_id = s_id
        st.session_state.messages = []
        if s_id:
            with st.spinner("Đang tải dữ liệu..."):
                refresh_current_folder()
                hist = api.get_chat_history(s_id)
                for m in hist: st.session_state.messages.append({"role": m["role"], "content": m["content"]})
        else:
            st.session_state.pdf_content = ""; st.session_state.source_map = {}

    if s_id:
        with st.expander(f"⚙️ Cài đặt: {s_name}"):
            t1, t2, t3 = st.tabs(["Sửa", "Files", "Xóa"])
            with t1:
                cur_f = next((f for f in folders if f["id"] == s_id), None)
                curr_d = cur_f["description"] if cur_f else ""
                en = st.text_input("Tên", value=s_name)
                ed = st.text_input("Mô tả", value=curr_d)
                if st.button("Lưu"): 
                    api.update_folder(s_id, en, ed); st.rerun()
            with t2:
                fls = api.get_files_in_folder(s_id)
                if fls:
                    for f in fls:
                        c1, c2 = st.columns([0.8, 0.2])
                        c1.write(f"📄 {f['fileName']}")
                        if c2.button("X", key=f"d_{f['id']}"):
                            api.delete_file(f['id']); refresh_current_folder(); st.rerun()
                else: st.info("Trống")
            with t3:
                if st.button("Xóa vĩnh viễn", type="primary"):
                    if api.delete_folder(s_id):
                        st.session_state.current_folder_id = None
                        st.session_state.delete_success = True
                        st.rerun()
    
    st.subheader("⬆️ Tải tài liệu")
    with st.form("up", clear_on_submit=True):
        up_files = st.file_uploader("Chọn file", accept_multiple_files=True)
        if st.form_submit_button("Tải lên") and up_files and s_id:
            cnt = 0
            for f in up_files:
                txt = ai.get_file_text(f)
                if api.upload_file_to_java(f, s_id, txt):
                    st.session_state.pdf_content += "\n" + txt
                    st.session_state.source_map.update(ai.create_source_map(txt))
                    cnt += 1
            if cnt > 0:
                st.session_state.upload_success_count = cnt
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
        left: 30rem;  
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

# Vẽ nút
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
   
# ------------------------------------------------------------------

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