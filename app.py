import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات الاتصال ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"فشل الاتصال بقاعدة البيانات: {e}")

# --- 2. التنسيق (CSS) ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; }
    div[data-testid="stExpander"] { background: #1e293b; border-radius: 10px; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; }
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>🏥 دخول نظام مختبرات حديثة</h2>", unsafe_allow_html=True)
    with st.container():
        centers = [
            'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
            'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
            'مركز صحي حقلانية', 'أطباء الاختصاص'
        ]
        u_center = st.selectbox("جهة العمل:", centers)
        u_code = st.text_input("الرمز السري:", type="password")
        if st.button("دخول"):
            res = supabase.table("center_access").select("*").eq("center_name", u_center).eq("access_code", u_code).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                st.session_state.is_admin = (u_center == 'مختبر مستشفى حديثة للفحوصات الفيروسية')
                st.session_state.is_doctor = (u_center == 'أطباء الاختصاص')
                st.rerun()
            else:
                st.error("⚠️ الرمز غير صحيح")
else:
    # القائمة العلوية للتنقل (Tabs)
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 سجل المرضى والبحث"])
    else:
        tabs = st.tabs(["🔍 سجل المرضى", "📝 تسجيل إصابة", "💬 الدردشة المباشرة"])

    # --- التبويب الأول: السجل والبحث ---
    with tabs[0]:
        st.subheader("🔍 قاعدة بيانات المصابين")
        search_query = st.text_input("ابحث عن اسم المراجع:")
        
        if search_query:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{search_query}%").order("created_at", desc=True).execute()
        else:
            results = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if results.data:
            for p in results.data:
                # التحقق من الصلاحية (المدير أو صاحب السجل)
                is_owner = (p['entry_center'] == st.session_state.center)
                can_action = st.session_state.is_admin or is_owner
                
                with st.expander(f"👤 {p['full_name']} - ({p['infection_type']})"):
                    st.write(f"📍 **السكن:** {p['address']}")
                    st.write(f"📅 **التاريخ:** {p['test_date']} | 🏢 **الجهة:** {p['entry_center']}")
                    st.write(f"📝 **الملاحظات:** {p['pcr_result']}")
                    
                    if not st.session_state.is_doctor:
                        col1, col2 = st.columns(2)
                        with col1:
                            if can_action:
                                if st.button(f"🗑️ حذف السجل", key=f"del_{p['id']}"):
                                    supabase.table("patients").delete().eq("id", p['id']).execute()
                                    st.rerun()
                            else:
                                st.info("🔒 للقراءة فقط")
                        with col2:
                            if can_action:
                                new_note = st.text_input("تعديل الملاحظة:", value=p['pcr_result'], key=f"note_{p['id']}")
                                if st.button("تحديث السجل", key=f"upd_{p['id']}"):
                                    supabase.table("patients").update({"pcr_result": new_note}).eq("id", p['id']).execute()
                                    st.rerun()

    # --- التبويب الثاني: الإضافة ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            st.subheader("📝 إدخال بيانات إصابة جديدة")
            with st.form("add_patient"):
                f_name = st.text_input("الاسم الرباعي:")
                f_addr = st.text_input("السكن:")
                f_inf = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                f_dev = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR", "VITEK"])
                f_date = st.date_input("التاريخ:", value=date.today())
                f_note = st.text_area("ملاحظات:")
                if st.form_submit_button("حفظ وإرسال"):
                    if f_name and f_addr:
                        supabase.table("patients").insert({
                            "full_name": f_name, "address": f_addr, "infection_type": f_inf,
                            "test_device": f_dev, "test_date": str(f_date), "pcr_result": f_note,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الحفظ")
                    else: st.warning("⚠️ املأ البيانات")

        # --- التبويب الثالث: الدردشة ---
        with tabs[2]:
            st.subheader("💬 منصة التواصل الفوري")
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(20).execute()
            for m in reversed(msgs.data):
                st.markdown(f"**{m['username']}**: {m['message']}")
            
            with st.form("chat_form", clear_on_submit=True):
                msg_txt = st.text_input("اكتب رسالتك:")
                if st.form_submit_button("إرسال") and msg_txt:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": msg_txt}).execute()
                    st.rerun()

    if st.sidebar.button("🔴 خروج"):
        st.session_state.clear()
        st.rerun()
