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

if 'logged_in' not in st.session_state:
    st.title("🏥 دخول النظام الموحد - قضاء حديثة")
    center = st.selectbox("اختر المركز:", centers)
    code = st.text_input("أدخل كود الدخول:", type="password")
    if st.button("دخول"):
        res = supabase.table("center_access").select("*").eq("center_name", center).eq("access_code", code).execute()
        if len(res.data) > 0:
            st.session_state.logged_in = True
            st.session_state.center = center
            st.session_state.is_admin = (center == 'مركز مستشفى حديثة للتبرع بالدم')
            st.rerun()
        else: st.error("الكود خطأ!")
else:
    st.sidebar.title(f"📍 {st.session_state.center}")
    if st.sidebar.button("خروج"):
        del st.session_state.logged_in
        st.rerun()

    t1, t2 = st.tabs(["➕ إضافة مراجع", "🔍 سجل الفحوصات العام"])

    with t1:
        with st.form("entry_form", clear_on_submit=True):
            n = st.text_input("الاسم الرباعي:")
            a = st.text_input("العنوان السكني:")
            i = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
            d = st.radio("الجهاز المستخدم:", ["Strips", "ELISA", "PCR"], horizontal=True)
            p = st.text_input("نتيجة الـ PCR:")
            if st.form_submit_button("حفظ"):
                if n:
                    supabase.table("patients").insert({"full_name": n, "address": a, "infection_type": i, "test_device": d, "pcr_result": p, "entry_center": st.session_state.center}).execute()
                    st.success("تم الحفظ بنجاح")
                else: st.error("اكتب الاسم!")

    with t2:
        st.subheader("البحث في قاعدة البيانات الموحدة")
        search = st.text_input("ابحث بالاسم:")
        query = supabase.table("patients").select("*")
        if search: query = query.ilike("full_name", f"%{search}%")
        data = query.order("created_at", desc=True).execute().data

        if data:
            for item in data:
                with st.expander(f"👤 {item['full_name']} - ({item['entry_center']})"):
                    # صلاحية التعديل والحذف
                    has_permission = st.session_state.is_admin or (st.session_state.center == item['entry_center'])
                    
                    if has_permission:
                        with st.form(key=f"edit_{item['id']}"):
                            new_n = st.text_input("تعديل الاسم:", value=item['full_name'])
                            new_p = st.text_input("تعديل PCR:", value=item['pcr_result'])
                            col_up, col_del = st.columns(2)
                            if col_up.form_submit_button("✅ حفظ التعديلات"):
                                supabase.table("patients").update({"full_name": new_n, "pcr_result": new_p}).eq("id", item['id']).execute()
                                st.success("تم التحديث")
                                st.rerun()
                            if col_del.form_submit_button("🗑️ حذف نهائي"):
                                supabase.table("patients").delete().eq("id", item['id']).execute()
                                st.warning("تم الحذف بنجاح")
                                st.rerun()
                    else:
                        st.write(f"**نوع الإصابة:** {item['infection_type']}")
                        st.write(f"**العنوان:** {item['address']}")
                        st.info("ℹ️ لا تملك صلاحية تعديل هذا السجل لأنه تابع لمركز آخر.")
        else: st.info("لا توجد بيانات.")
