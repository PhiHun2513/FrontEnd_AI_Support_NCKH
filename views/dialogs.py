import streamlit as st
import utils

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

@st.dialog("📜 Chi tiết Nội dung Câu hỏi & Trả lời", width="large")
def show_chat_detail(q, a, s_map):
    """
    Dialog hiển thị chi tiết nội dung khi bấm vào lịch sử.
    """
    st.markdown(f"**❓ Câu hỏi của bạn:**")
    st.info(q)
    st.divider()
    
    st.markdown(f"**🤖 Câu trả lời từ AI:**")
    st.markdown(utils.format_answer_with_clickable_details(a, s_map), unsafe_allow_html=True)
    
    st.divider()
    col_close, _ = st.columns([0.3, 0.7])
    with col_close:
        if st.button("❌ Đóng cửa sổ này", type="primary", use_container_width=True):
            st.rerun()