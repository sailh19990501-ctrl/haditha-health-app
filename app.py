import streamlit as st
from supabase import create_client
from datetime import datetime, date

# إعدادات الربط
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="نظام مختبرات حديثة - العرض والبحث", layout="wide")

# تنسيق الواجهة
st.markdown("""<style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"] { direction: rtl; }
    div[data-testid="stExpander"] { background-color: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0; }
    label { font-weight: bold; font-size: 16px; color: #1e40af; }
    .stButton>button { width: 100%; border-radius: 8px; }
    </style>""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.title("🏥 تسجيل الدخول - نظام الصحة")
    # القائمة المحدثة
    centers_list = [
        'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
        'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
        'مركز صحي حقلانيه', 'مركز صحي خفاجيه', 'مركز صحي بني زاهر',
        'مركز صحي بني داهر', 'مركز صحي الوس', 'مركز صحي السكران',
        'أطباء الاختصاص (للبحث والعرض فقط)'
    ]
    center = st.selectbox("اختر المركز أو الجهة:", centers_list)
    code = st.text_input("كود الدخول:", type="password")
    
    if st.button("دخول للنظام"):
        res = supabase.table("center_access").select("*").eq("center_name", center).eq("access_code", code).execute()
        if len(res.data) > 0:
            st.session_state.logged_in = True
            st.session_state.center = center
            st.session_state.is_admin = res.data[0]['is_admin']
            # تحديد إذا كان المستخدم "طبيب اختصاص" للتقييد
            st.session_state.is_doctor = "أطباء الاختصاص" in center
            st.rerun()
        else: st.error("الكود غير صحيح!")

else:
    st.sidebar.info(f"المستخدم: {st.session_state.center}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # الصلاحيات: إذا كان طبيب، تظهر صفحة البحث فقط
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 البحث في سجل المصابين"])
        show_add_tab = False
    else:
        tabs = st.tabs(["📝 إدخال بيانات", "🔍 البحث في السجل"])
        show_add_tab = True

    # --- خانة الإدخال (تظهر فقط للمراكز والمختبرات) ---
    if show_add_tab:
        with tabs[0]:
            st.subheader("تسجيل حالة إصابة جديدة أو أرشفة")
            with st.form("entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("العنوان:")
                    test_dt = st.date_input("تاريخ الفحص:", value=date.today(), min_value=date(1990,1,1), max_value=date.today())
                with c2:
                    inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    dev = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR", "VITEK"])
                    rem = st.text_input("ملاحظات إضافية:")
                
                if st.form_submit_button("حفظ البيانات"):
                    if name and addr:
                        supabase.table("patients").insert({
                            "full_name": name, "address": addr, "test_date": str(test_dt),
                            "infection_type": inf, "test_device": dev, "pcr_result": rem,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("تم الحفظ بنجاح")
                    else: st.warning("يرجى إكمال البيانات")

    # --- خانة البحث (تظهر للجميع) ---
    search_tab_index = 0 if st.session_state.is_doctor else 1
    with tabs[search_tab_index]:
        search = st.text_input("🔍 ابحث بالاسم الرباعي للتأكد من حالة المريض:")
        if search:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{search}%").order("test_date", desc=True).execute()
            if res.data:
                for row in res.data:
                    with st.expander(f"📄 مراجع: {row['full_name']} | التاريخ: {row['test_date']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**📍 السكن:** {row['address']}")
                            st.markdown(f"**📅 تاريخ الفحص:** {row['test_date']}")
                            st.markdown(f"**🧬 نوع الإصابة:** {row['infection_type']}")
                        with col2:
                            st.markdown(f"**🏢 المركز الفاحص:** {row['entry_center']}")
                            st.markdown(f"**🔬 الجهاز:** {row['test_device']}")
                            st.markdown(f"**📝 ملاحظات:** {row['pcr_result']}")
                        
                        # منع الطبيب من الحذف أو التعديل
                        if not st.session_state.is_doctor:
                            if st.session_state.is_admin or st.session_state.center == row['entry_center']:
                                if st.button(f"🗑️ حذف السجل", key=f"del_{row['id']}"):
                                    supabase.table("patients").delete().eq("id", row['id']).execute()
                                    st.rerun()
            else:
                st.info("لا توجد نتائج مطابقة.")


