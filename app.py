import streamlit as st
from supabase import create_client
from datetime import datetime, date

# 1. إعدادات الربط المركزية
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"
supabase = create_client(URL, KEY)

# 2. إعدادات الصفحة واللغة
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

# تنسيق الواجهة ليدعم اللغة العربية وتصميم احترافي (RTL)
st.markdown("""<style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stBlock"], .stTabs, .stForm { direction: rtl; text-align: right; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    label { font-weight: bold; font-size: 1.1rem; color: #1e3a8a; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>""", unsafe_allow_html=True)

# 3. قائمة الجهات المعتمدة
centers_list = [
    'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
    'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
    'مركز صحي حقلانيه', 'مركز صحي خفاجيه', 'مركز صحي بني داهر',
    'مركز صحي الوس', 'مركز صحي السكران',
    'أطباء الاختصاص (لالبحث والعرض فقط)'
]

# 4. نظام إدارة الجلسة والدخول
if 'logged_in' not in st.session_state:
    st.title("🏥 نظام الإدارة الصحية - قضاء حديثة")
    st.subheader("🔐 تسجيل الدخول الموحد")
    
    col_login, _ = st.columns([1, 1])
    with col_login:
        center_choice = st.selectbox("اختر الجهة / المركز:", centers_list)
        access_code = st.text_input("أدخل كود الدخول السري:", type="password")
        
        if st.button("دخول للنظام"):
            # التحقق من قاعدة البيانات
            res = supabase.table("center_access").select("*").eq("center_name", center_choice).eq("access_code", access_code).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.center = center_choice
                st.session_state.is_admin = res.data[0]['is_admin']
                st.session_state.is_doctor = "أطباء الاختصاص" in center_choice
                st.rerun()
            else:
                st.error("❌ الكود غير صحيح، يرجى التأكد من الصلاحيات.")

else:
    # القائمة الجانبية
    st.sidebar.title("👤 معلومات الدخول")
    st.sidebar.info(f"الجهة: {st.session_state.center}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    # تحديد التبويبات بناءً على الصلاحية
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 البحث في قاعدة البيانات المركزية"])
    else:
        tabs = st.tabs(["📝 تسجيل إصابة (جديدة/أرشيف)", "🔍 سجل المرضى والبحث"])

    # --- تبويب الإدخال (يختفي عند الأطباء) ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.subheader("📋 استمارة تسجيل بيانات المصاب")
            with st.form("main_entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    full_name = st.text_input("الاسم الرباعي للمراجع:")
                    address = st.text_input("عنوان السكن الحالي (المنطقة/الحي):")
                    # التقويم المرن للأرشفة
                    test_date = st.date_input("تاريخ إجراء الفحص (يومي/قديم):", 
                                            value=date.today(),
                                            min_value=date(1990, 1, 1),
                                            max_value=date.today())
                with c2:
                    inf_type = st.selectbox("نوع الإصابة المكتشفة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    test_dev = st.selectbox("الجهاز المستخدم في الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    pcr_note = st.text_input("ملاحظات إضافية أو نتيجة PCR:")
                
                if st.form_submit_button("حفظ البيانات وإرسالها للسجل المركزي"):
                    if full_name and address:
                        data_payload = {
                            "full_name": full_name,
                            "address": address,
                            "test_date": str(test_date),
                            "infection_type": inf_type,
                            "test_device": test_dev,
                            "pcr_result": pcr_note,
                            "entry_center": st.session_state.center
                        }
                        supabase.table("patients").insert(data_payload).execute()
                        st.success(f"✅ تم حفظ بيانات المراجع {full_name} بنجاح.")
                    else:
                        st.warning("⚠️ يرجى إدخال الاسم والعنوان لإتمام العملية.")

    # --- تبويب البحث (متاح للجميع مع فروقات الصلاحية) ---
    search_tab_idx = 0 if st.session_state.is_doctor else 1
    with tabs[search_tab_idx]:
        st.subheader("🔍 استعلام عن حالة مراجع")
        search_query = st.text_input("ادخل الاسم الرباعي للبحث عنه في كافة المراكز:")
        
        if search_query:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{search_query}%").order("test_date", desc=True).execute()
            
            if results.data:
                for row in results.data:
                    # معالجة عرض البيانات حتى لو كانت قديمة (ناقصة)
                    p_name = row.get('full_name', 'غير متوفر')
                    p_date = row.get('test_date', 'غير مسجل')
                    p_addr = row.get('address', 'غير مسجل')
                    p_center = row.get('entry_center', 'مركز سابق')
                    
                    with st.expander(f"👤 {p_name} | الحالة: {row.get('infection_type', '-')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**📍 العنوان:** {p_addr}")
                            st.write(f"**📅 تاريخ الفحص:** {p_date}")
                            st.write(f"**🧬 نوع الإصابة:** {row.get('infection_type', '-')}")
                        with col2:
                            st.write(f"**🏢 المركز الفاحص:** {p_center}")
                            st.write(f"**🔬 جهاز الفحص:** {row.get('test_device', '-')}")
                            st.write(f"**📝 ملاحظات:** {row.get('pcr_result', '-')}")

                        # ضوابط الحذف والتعديل
                        if not st.session_state.is_doctor:
                            # يحذف فقط إذا كان آدمن أو هو صاحب المركز الذي أدخل البيانات
                            if st.session_state.is_admin or st.session_state.center == p_center:
                                if st.button(f"🗑️ حذف السجل نهائياً", key=f"del_{row['id']}"):
                                    supabase.table("patients").delete().eq("id", row['id']).execute()
                                    st.warning("تم حذف السجل.")
                                    st.rerun()
            else:
                st.info("لا توجد سجلات مطابقة لهذا الاسم.")







