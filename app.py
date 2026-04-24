import streamlit as st
from supabase import create_client

# إعدادات الربط
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

# تنسيق RTL
st.markdown("""<style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"] { direction: rtl; }
    div[data-testid="stMarkdownContainer"] { text-align: right; }
    label { text-align: right !important; width: 100%; }
    </style>""", unsafe_allow_html=True)

centers = ['مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية', 'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 'مركز صحي بني زاهر', 'مركز صحي حقلانيه', 'مركز صحي خفاجيه', 'مركز صحي بني داهر', 'مركز صحي الوس', 'مركز صحي السكران']

st.title("🏥 نظام إدارة الفحوصات الفيروسية - قضاء حديثة")

if 'logged_in' not in st.session_state:
    st.subheader("تسجيل الدخول للمراكز")
    center = st.selectbox("اختر المركز:", centers)
    code = st.text_input("أدخل كود الدخول:", type="password")
    if st.button("دخول"):
        res = supabase.table("center_access").select("*").eq("center_name", center).eq("access_code", code).execute()
        if len(res.data) > 0:
            st.session_state.logged_in = True
            st.session_state.center = center
            st.session_state.is_admin = res.data[0]['is_admin']
            st.rerun()
        else:
            st.error("الكود غير صحيح!")
else:
    st.sidebar.success(f"متصل: {st.session_state.center}")
    if st.sidebar.button("خروج"):
        del st.session_state.logged_in
        st.rerun()

    t1, t2 = st.tabs(["➕ إدخال مراجع", "🔍 بحث"])
    with t1:
        with st.form("f1", clear_on_submit=True):
            n = st.text_input("الاسم الرباعي:")
            a = st.text_input("العنوان:")
            i = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
            d = st.radio("الجهاز:", ["Strips", "ELISA", "PCR"], horizontal=True)
            p = st.text_input("نتيجة PCR (إن وجدت):")
            if st.form_submit_button("حفظ"):
                if n:
                    supabase.table("patients").insert({"full_name": n, "address": a, "infection_type": i, "test_device": d, "pcr_result": p, "entry_center": st.session_state.center}).execute()
                    st.success("تم الحفظ!")
                else: st.warning("اكتب الاسم!")
    with t2:
        st.subheader("البحث")
        sn = st.text_input("ابحث بالاسم:")
        query = supabase.table("patients").select("*")
        if not st.session_state.is_admin: query = query.eq("entry_center", st.session_state.center)
        if sn: query = query.ilike("full_name", f"%{sn}%")
        res = query.order("created_at", desc=True).execute()
        st.table(res.data)
