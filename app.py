import streamlit as st
from supabase import create_client

# --- إعدادات الربط الخاصة بمشروعك ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "Sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

supabase = create_client(URL, KEY)

# إعدادات الصفحة
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

# تنسيق اللغة العربية (RTL)
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"] { direction: rtl; }
    div[data-testid="stMarkdownContainer"] { text-align: right; }
    label { text-align: right !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# قائمة المراكز
centers = [
    'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
    'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه',
    'مركز صحي بني زاهر', 'مركز صحي حقلانيه', 'مركز صحي خفاجيه',
    'مركز صحي بني داهر', 'مركز صحي الوس', 'مركز صحي السكران'
]

st.title("🏥 نظام إدارة الفحوصات الفيروسية - قضاء حديثة")

# نظام تسجيل الدخول
if 'logged_in' not in st.session_state:
    with st.container():
        st.subheader("تسجيل الدخول للمراكز")
        center = st.selectbox("اختر المركز الخاص بك:", centers)
        code = st.text_input("أدخل كود الدخول السري:", type="password")
        if st.button("دخول للنظام"):
            res = supabase.table("center_access").select("*").eq("center_name", center).eq("access_code", code).execute()
            if len(res.data) > 0:
                st.session_state.logged_in = True
                st.session_state.center = center
                st.session_state.is_admin = res.data[0]['is_admin']
                st.rerun()
            else:
                st.error("ع
