import streamlit as st
import pandas as pd
import time
import api_handler as api
import altair as alt 
def render_admin_interface():

    admin_user = st.session_state.user_info
    
    #  SIDEBAR ADMIN 
    with st.sidebar:
        st.title("🛡️ ADMIN PORTAL")
        st.info(f"Xin chào, {admin_user['username']}")
        
        menu = st.radio("Menu quản lý", ["📊 Dashboard", "👥 Quản lý User", "🗄️ Quản lý Tài liệu"])
        
        st.divider()
        if st.button("Đăng xuất", type="secondary", use_container_width=True):
            st.session_state.user_info = None
            st.rerun()

    #  DASHBOARD (THỐNG KÊ BIỂU ĐỒ)
    if menu == "📊 Dashboard":
        st.header("📊 Tổng quan Hệ thống")
        
        #  Lấy dữ liệu thực tế
        stats = api.get_admin_stats()
        all_docs = api.get_all_documents_admin()
        
        # Hiển thị Số liệu tổng
        if stats:
            c1, c2, c3 = st.columns(3)
            c1.metric("Tổng Người dùng", stats.get("totalUsers", 0), "👤")
            c2.metric("Tổng Đề tài", stats.get("totalFolders", 0), "📂")
            c3.metric("Tổng tài liệu", stats.get("totalDocuments", 0), "📄")
        else:
            st.error("Không kết nối được server!")

        st.divider()
        
        # Vẽ biểu đồ 
        if all_docs:
            data_list = []
            for d in all_docs:
                owner = d["folder"]["user"]["username"] if d.get("folder") and d["folder"].get("user") else "Unknown"
                ext = d["fileName"].split('.')[-1].lower() if '.' in d["fileName"] else "unknown"
                data_list.append({"User": owner, "Type": ext, "Count": 1})
            
            df = pd.DataFrame(data_list)
            
            col_chart1, col_chart2 = st.columns(2)
            
            # Biểu đồ 1: Lưu lượng theo User 
            with col_chart1:
                st.subheader("Lưu lượng theo User")
                if not df.empty:
                    user_counts = df["User"].value_counts().reset_index()
                    user_counts.columns = ["Người dùng", "Số file"]
                    
                    chart1 = alt.Chart(user_counts).mark_bar().encode(
                        x=alt.X('Số file:Q', title='Số lượng file'),
                        y=alt.Y('Người dùng:N', sort='-x', title='Tên người dùng', axis=alt.Axis(labelLimit=200)),
                        color=alt.Color('Người dùng:N', legend=None),
                        tooltip=['Người dùng', 'Số file']
                    ).properties(height=300)
                    
                    st.altair_chart(chart1, use_container_width=True)
                else: st.caption("Chưa có dữ liệu.")

            # Biểu đồ 2: Phân bố loại file 
            with col_chart2:
                st.subheader("📁 Phân bố loại file")
                if not df.empty:
                    type_counts = df["Type"].value_counts().reset_index()
                    type_counts.columns = ["Loại", "Số lượng"]
                    
                    chart2 = alt.Chart(type_counts).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta(field="Số lượng", type="quantitative"),
                        color=alt.Color(field="Loại", type="nominal"),
                        tooltip=['Loại', 'Số lượng']
                    ).properties(height=300)
                    
                    st.altair_chart(chart2, use_container_width=True)
        else:
            st.info("Chưa có tài liệu nào để thống kê.")

    # QUẢN LÝ USER 
    elif menu == "👥 Quản lý User":
        st.header("👥 Danh Sách Người Dùng")
        users = api.get_all_users()
        
        if users:
            users = sorted(users, key=lambda x: x['id'])
            df_u = pd.DataFrame(users)
            df_u.insert(0, 'STT', range(1, 1 + len(df_u)))
            
            if 'password' in df_u.columns: df_u = df_u.drop(columns=['password'])
            df_u.rename(columns={'id': 'ID Hệ thống', 'username': 'Tên đăng nhập', 'role': 'Quyền'}, inplace=True)
            
            st.dataframe(df_u, use_container_width=True, hide_index=True)
            
            with st.expander("❌ Xóa tài khoản", expanded=False):
                st.warning("⚠️ Cảnh báo: Hành động này không thể hoàn tác!")
                c1, c2 = st.columns([3, 1])
                with c1:
                    u_opts = [f"{u['id']} - {u['username']}" for u in users]
                    selected_u = st.selectbox("Chọn tài khoản:", options=u_opts)
                with c2:
                    st.write(""); st.write("")
                    if st.button("Xóa", type="primary", use_container_width=True):
                        uid = int(selected_u.split(" - ")[0])
                        if uid == admin_user['id']:
                            st.toast("🚫 Không thể xóa chính mình!", icon="⛔")
                        elif api.delete_user_by_admin(uid):
                            st.success(f"Đã xóa User {uid}"); time.sleep(1); st.rerun()
                        else: st.error("Lỗi xóa user.")
        else: st.info("Hệ thống trống.")

    # QUẢN LÝ TÀI LIỆU 
    elif menu == "🗄️ Quản lý Tài liệu":
        st.header("🗄️ Kho Tài Liệu Hệ Thống")
        all_docs = api.get_all_documents_admin()
        
        if all_docs:
            data = []
            for d in all_docs:
                owner = d["folder"]["user"]["username"] if d.get("folder") and d["folder"].get("user") else "Unknown"
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
            c1, c2 = st.columns([3, 1])
            with c1:
                sel_id = st.selectbox("Chọn ID file để kiểm tra:", df_docs["ID"].tolist())
                sel_name = df_docs[df_docs["ID"] == sel_id]["Tên File"].values[0] if sel_id else ""
            with c2:
                st.write(""); st.write("")
                if sel_id and st.button("📥 Chuẩn bị tải", use_container_width=True):
                    f_bytes = api.download_document_bytes(sel_id)
                    if f_bytes:
                        st.download_button(label=f"Lưu: {sel_name}", data=f_bytes, file_name=sel_name, type="primary", use_container_width=True)
        else: st.info("Chưa có tài liệu.")