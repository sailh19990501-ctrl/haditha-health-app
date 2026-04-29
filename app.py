import streamlit as st
from supabase import create_client
from datetime import datetime, date

# إعدادات الربط
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="نظام مختبرات حديثة - الأرشيف", layout="wide")

# تنسيق الواجهة لتدعم اللغة العربية بالكامل
st.markdown("""<style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"] { direction: rtl; }
    div[data-testid="stExpander"] { background-color: #f0f2f6; border-radius: 10px; border: 1px solid #d1d5db; }
    label { font-weight: bold; font-size: 18px; color: #1e3a8a; }
    input { text-align: right; }
    </style>""", unsafe_allow_html=True)

centers_list = [
    'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
    'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
    'مركز صحي حقلانيه', 'مركز صحي خفاجيه', 'مركز صحي بني زاهر',
    'مركز صحي بني داهر', 'مركز صحي الوس', 'مركز صحي السكران',
    'أطباء الاختصاص (دخول متعدد)'
]

if 'logged_in' not in st.session_state:
    st.title("🔐 تسجيل الدخول للنظام")
    center = st.selectbox("اختر المركز أو المختبر:", centers_list)
    code = st.text_input("كود الدخول:", type="password")
    if st.button("دخول"):
        res = supabase.table("center_access").select("*").eq("center_name", center).eq("access_code", code).execute()
        if len(res.data) > 0:
            st.session_state.logged_in = True
            st.session_state.center = center
            st.session_state.is_admin = res.data[0]['is_admin']
            st.rerun()
        else: st.error("الكود خطأ!")
else:
    st.sidebar.title(f"مرحباً: {st.session_state.center}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    tab1, tab2 = st.tabs(["📝 إدخال (جديد أو قديم)", "🔍 البحث وعرض السجلات"])

    with tab1:
        st.subheader("إدخال بيانات المصابين (يدعم الأرشيف القديم)")
        with st.form("archive_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الاسم الرباعي:")
                address = st.text_input("عنوان السكن الحالي:")
                # هنا التقويم اللي طلبته (تقدر ترجع للسنين القديمة)
                selected_date = st.date_input("تاريخ إجراء الفحص (اختر السنة والشهر واليوم):", 
                                            value=date.today(),
                                            min_value=date(1990, 1, 1), # يسمح بالرجوع لعام 1990
                                            max_value=date.today())
            with col2:
                inf_type = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                test_dev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                pcr_val = st.text_input("ملاحظات / نتيجة الـ PCR:")

            if st.form_submit_button("حفظ البيانات في السجل المركزي"):
                if name and address:
                    payload = {
                        "full_name": name,
                        "address": address,
                        "test_date": str(selected_date), # يحفظ التاريخ اللي اختاريته
                        "infection_type": inf_type,
                        "test_device": test_dev,
                        "pcr_result": pcr_val,
                        "entry_center": st.session_state.center
                    }
                    supabase.table("patients").insert(payload).execute()
                    st.success(f"تم بنجاح حفظ سجل: {name} بتاريخ {selected_date}")
                else:
                    st.warning("يرجى ملء الاسم والعنوان.")

    with tab2:
        st.subheader("🔍 البحث في قاعدة البيانات المركزية")
        search = st.text_input("ابحث بالاسم الرباعي:")
        
        # عرض النتائج
        query = supabase.table("patients").select("*")
        if search:
            query = query.ilike("full_name", f"%{search}%")
        
        res = query.order("test_date", desc=True).execute()

        for row in res.data:
            with st.expander(f"👤 {row['full_name']} | التاريخ: {row['test_date']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**📍 العنوان:** {row['address']}")
                    st.write(f"**📅 تاريخ الفحص:** {row['test_date']}")
                    st.write(f"**🧬 نوع الإصابة:** {row['infection_type']}")

