import streamlit as st
from supabase import create_client
from datetime import datetime, date

# إعدادات الربط
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="نظام مختبرات حديثة المركزي", layout="wide")

# تنسيق الواجهة RTL
st.markdown("""<style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"] { direction: rtl; }
    div[data-testid="stExpander"] { background-color: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0; text-align: right; }
    label { font-weight: bold; font-size: 16px; color: #1e40af; }
    </style>""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.title("🏥 تسجيل الدخول - نظام الصحة")
    centers_list = [
        'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
        'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
        'مركز صحي حقلانيه', 'مركز صحي خفاجيه', 'مركز صحي بني داهر',
        'مركز صحي الوس', 'مركز صحي السكران',
        'أطباء الاختصاص (للبحث والعرض فقط)'
    ]
    center = st.selectbox("اختر المركز أو الجهة:", centers_list)
    code = st.text_input("كود الدخول:", type="password")
    
    if st.button("دخول للنظام"):
        res = supabase.table("center_access").select("*").eq("center_name", center).eq("access_code", code).execute()
        if len(res.data) > 0:
            st.session_state.logged_in, st.session_state.center = True, center
            st.session_state.is_admin = res.data[0]['is_admin']
            st.session_state.is_doctor = "أطباء الاختصاص" in center
            st.rerun()
        else: st.error("الكود غير صحيح!")
else:
    st.sidebar.info(f"المستخدم: {st.session_state.center}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    is_doc = st.session_state.is_doctor
    tabs = st.tabs(["🔍 البحث في السجل"] if is_doc else ["📝 إدخال بيانات", "🔍 البحث في السجل"])

    if not is_doc:
        with tabs[0]:
            st.subheader("تسجيل حالة جديدة")
            with st.form("entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("العنوان:")
                    test_dt = st.date_input("تاريخ الفحص:", value=date.today(), min_value=date(1990,1,1), max_value=date.today())
                with c2:
                    inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    dev = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR", "VITEK"])
                    rem = st.text_input("ملاحظات:")
                
                if st.form_submit_button("حفظ"):
                    if name:
                        supabase.table("patients").insert({
                            "full_name": name, "address": addr, "test_date": str(test_dt),
                            "infection_type": inf, "test_device": dev, "pcr_result": rem,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("تم الحفظ بنجاح")
                        st.rerun()
                    else: st.warning("يرجى كتابة الاسم على الأقل")

    search_tab = tabs[0] if is_doc else tabs[1]
    with search_tab:
        search = st.text_input("🔍 ابحث بالاسم الرباعي:")
        if search:
            # البحث عن الاسم
            res = supabase.table("patients").select("*").ilike("full_name", f"%{search}%").execute()
            if res.data:
                for row in res.data:
                    # معالجة البيانات المفقودة للأسماء القديمة
                    p_name = row.get('full_name') or "بدون اسم"
                    p_date = row.get('test_date') or "بيانات قديمة"
                    p_addr = row.get('address') or "غير مسجل"
                    p_center = row.get('entry_center') or "غير محدد"
                    p_inf = row.get('infection_type') or "-"
                    p_dev = row.get('test_device') or "-"

                    with st.expander(f"👤 {p_name} | الحالة: {p_inf}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**📍 العنوان:** {p_addr}")
                            st.write(f"**📅 تاريخ الفحص:** {p_date}")
                        with col2:
                            st.write(f"**🏢 المركز الفاحص:** {p_center}")
                            st.write(f"**🔬 جهاز الفحص:** {p_dev}")
                        
                        if not is_doc:
                            if st.session_state.is_admin or st.session_state.center == p_center:
                                if st.button(f"🗑️ حذف السجل", key=f"del_{row['id']}"):
                                    supabase.table("patients").delete().eq("id", row['id']).execute()
                                    st.success("تم الحذف")
                                    st.rerun()
            else:
                st.info("لا توجد نتائج مطابقة لهذا الاسم.")





