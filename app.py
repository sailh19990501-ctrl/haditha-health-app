import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta

# --- 1. إعدادات الاتصال ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except:
    st.error("خطأ في الاتصال بالسيرفر")

# --- 2. التصميم (CSS) - الخط الكبير والاتجاه ---
st.set_page_config(page_title="أرشيف حديثة الموحد", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; padding: 1rem 2rem !important; }
    
    .patient-card {
        background: #1e293b; padding: 12px 18px; border-radius: 8px;
        margin-bottom: 6px; border-right: 6px solid #3b82f6;
        display: flex; justify-content: flex-start; align-items: center;
        text-align: right; direction: rtl;
    }
    
    .p-title { font-size: 19px; font-weight: bold; color: #f8fafc; margin-left: 12px; }
    .p-info { font-size: 16px; color: #cbd5e1; margin-left: 18px; }
    
    .chat-bubble { 
        background: #202c33; padding: 14px; border-radius: 10px; 
        margin-bottom: 8px; border-right: 4px solid #00a884; 
        width: fit-content; max-width: 85%; text-align: right; font-size: 16px;
    }
    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer, header { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# --- 3. نظام الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🏥 أرشيف المصابين الموحد</h1>", unsafe_allow_html=True)
    access_map = {
        'مركز مستشفى حديثة للتبرع بالدم': 'HAD-BLOOD-2026',
        'مختبر مستشفى حديثة للفحوصات الفيروسية': 'HAD-VIRUS-2026',
        'المركز التخصصي للاسنان': 'DENT-HAD-77',
        'مركز صحي حديثة': 'HHC-MAIN-11',
        'مركز صحي بروانه': 'BARWANA-22',
        'مركز صحي حقلانيه': 'HAKLAN-44',
        'مركز صحي خفاجيه': 'KHAFA-55',
        'مركز صحي بني داهر': 'DAHIR-66',
        'مركز صحي الوس': 'ALUS-88',
        'مركز صحي السكران': 'SAKRAN-99',
        'أطباء الاختصاص': 'DOC-SPEC-2026'
    }
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u_center = st.selectbox("جهة العمل:", list(access_map.keys()))
        u_code = st.text_input("الرمز السري:", type="password")
        if st.button("دخول النظام"):
            if u_code == access_map[u_center]:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                st.session_state.is_admin = u_center in ['مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية']
                st.session_state.is_doctor = (u_center == 'أطباء الاختصاص')
                st.rerun()
            else: st.error("❌ الرمز غير صحيح")

else:
    with st.expander(f"⚙️ إعدادات الحساب: {st.session_state.center}"):
        if st.button("🔴 تسجيل خروج"):
            st.session_state.clear(); st.rerun()

    tabs = st.tabs(["🔍 السجل الموحد"]) if st.session_state.is_doctor else st.tabs(["🔍 السجل الموحد", "📝 إضافة مصاب", "💬 الدردشة"])

    # --- 4. السجل الموحد (تحديث آني وقوي) ---
    with tabs[0]:
        search_q = st.text_input("🔍 ابحث عن اسم:")
        data = supabase.table("patients").select("*").ilike("full_name", f"%{search_q}%").order("created_at", desc=True).execute()
        if data.data:
            for p in data.data:
                st.markdown(f"""<div class="patient-card">
                    <span class="p-title">👤 {p['full_name']}</span>
                    <span class="p-info">| 🔬 {p['infection_type']}</span>
                    <span class="p-info">| 🏢 {p['entry_center']}</span>
                </div>""", unsafe_allow_html=True)
                
                with st.expander("🔍 عرض التفاصيل الكاملة"):
                    st.write(f"🎂 العمر: {p.get('age','--')} | 📱 الهاتف: {p.get('phone_number','--')}")
                    st.write(f"📍 العنوان: {p.get('address','--')} | 📅 التاريخ: {p['test_date']}")
                    st.write(f"⚙️ الجهاز: {p['test_device']}")
                    
                    if not st.session_state.is_doctor:
                        if st.session_state.is_admin or p['entry_center'] == st.session_state.center:
                            st.divider()
                            if st.button(f"🗑️ حذف السجل", key=f"del_{p['id']}"):
                                supabase.table("patients").delete().eq("id", p['id']).execute()
                                st.rerun()
        else: st.info("لا توجد بيانات مطابقة.")

    # --- 5. إضافة مصاب (تحديث فوري بعد الإضافة) ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            with st.form("add_p_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    n = st.text_input("الاسم الرباعي:")
                    a = st.text_input("العمر:")
                    ph = st.text_input("رقم الهاتف:")
                with c2:
                    ad = st.text_input("العنوان:")
                    i = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    t = st.selectbox("الجهاز المستخدم:", ["Strips", "ELISA", "PCR"])
                d = st.date_input("التاريخ:", value=date.today())
                
                if st.form_submit_button("🚀 إرسال إلى قاعدة البيانات المركزية"):
                    if n:
                        supabase.table("patients").insert({
                            "full_name": n, "age": a, "phone_number": ph,
                            "address": ad, "infection_type": i, "test_device": t,
                            "test_date": str(d), "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الإضافة بنجاح!")
                        # هذا السطر يضمن تحديث السجل فوراً في المتصفح
                        st.session_state["added"] = True
                        st.rerun()

    # --- 6. الدردشة ---
    if not st.session_state.is_doctor:
        with tabs[2]:
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(100).execute()
            for m in reversed(msgs.data):
                st.markdown(f'<div class="chat-bubble"><small style="color:#00a884;">{m["username"]}</small><br>{m["message"]}</div>', unsafe_allow_html=True)
            with st.form("msg_form", clear_on_submit=True):
                txt = st.text_input("اكتب رسالة...")
                if st.form_submit_button("إرسال") and txt:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": txt}).execute()
                    st.rerun()
