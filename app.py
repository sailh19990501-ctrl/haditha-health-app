import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- إعدادات الربط ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

# --- تنسيق الواجهة RTL ---
st.markdown("""<style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"], .stTabs, .stForm { direction: rtl; text-align: right; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; }
    label { font-weight: bold; font-size: 1.1rem; color: #1e3a8a; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #1e3a8a; color: white; }
    </style>""", unsafe_allow_html=True)

# --- قائمة المراكز ---
centers_list = [
    'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
    'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
    'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
    'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص (للبحث والعرض فقط)'
]

# --- نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.title("🏥 نظام الإدارة الصحية - قضاء حديثة")
    st.subheader("🔐 تسجيل الدخول الموحد")
    center_choice = st.selectbox("اختر الجهة / المركز:", centers_list)
    access_code = st.text_input("أدخل كود الدخول السري:", type="password")
    
    if st.button("دخول للنظام"):
        res = supabase.table("center_access").select("*").eq("center_name", center_choice).eq("access_code", access_code).execute()
        if res.data:
            st.session_state.logged_in = True
            st.session_state.center = center_choice
            st.session_state.is_admin = res.data[0]['is_admin']
            st.session_state.is_doctor = "أطباء الاختصاص" in center_choice
            st.rerun()
        else:
            st.error("❌ الكود غير صحيح")
else:
    st.sidebar.info(f"المستخدم: {st.session_state.center}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # --- التبويبات ---
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 البحث في السجل"])
    else:
        tabs = st.tabs(["📝 تسجيل إصابة", "🔍 سجل المرضى والبحث"])

    # --- 1. واجهة الإدخال ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.subheader("📋 تسجيل بيانات المصاب")
            with st.form("entry_form_final", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    fname = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("العنوان:")
                    tdate = st.date_input("تاريخ الفحص:", value=date.today(), min_value=date(1990,1,1))
                with c2:
                    itype = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    tdev = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR", "VITEK"])
                    pcr = st.text_input("ملاحظات / نتيجة PCR:")
                
                if st.form_submit_button("حفظ وإرسال"):
                    if fname and addr:
                        supabase.table("patients").insert({
                            "full_name": fname, "address": addr, "test_date": str(tdate),
                            "infection_type": itype, "test_device": tdev, "pcr_result": pcr,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الحفظ")
                    else:
                        st.warning("⚠️ يرجى ملء الاسم والعنوان")

    # --- 2. واجهة البحث (شاملة للبيانات القديمة) ---
    st_idx = 0 if st.session_state.is_doctor else 1
    with tabs[st_idx]:
        st.subheader("🔍 استعلام عن حالة مراجع")
        q = st.text_input("ادخل الاسم الرباعي للبحث:")
        if q:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").execute()
            if results.data:
                for row in results.data:
                    # جلب البيانات مع ضمان عدم حدوث خطأ إذا كانت فارغة
                    n = row.get('full_name', '-')
                    d = row.get('test_date') or "بيانات قديمة"
                    a = row.get('address') or "غير مسجل"
                    c = row.get('entry_center') or "مركز سابق"
                    
                    with st.expander(f"👤 {n} | الحالة: {row.get('infection_type','-')}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**📍 العنوان:** {a}")
                            st.write(f"**📅 التاريخ:** {d}")
                            st.write(f"**🧬 الإصابة:** {row.get('infection_type','-')}")
                        with col_b:
                            st.write(f"**🏢 المركز:** {c}")
                            st.write(f"**🔬 الجهاز:** {row.get('test_device','-')}")
                            st.write(f"**📝 ملاحظات:** {row.get('pcr_result','-')}")
                        
                        if not st.session_state.is_doctor:
                            if st.session_state.is_admin or st.session_state.center == c:
                                if st.button("🗑️ حذف السجل", key=f"d_{row['id']}"):
                                    supabase.table("patients").delete().eq("id", row['id']).execute()
                                    st.rerun()
            else:
                st.info("لا توجد نتائج")








