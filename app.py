import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. الاتصال بالسيرفر ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error("فشل الاتصال")

# --- 2. التنسيق البصري (حل مشكلة الطول + مربعات الدردشة) ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; }
    
    /* تنسيق السجلات لتكون عريضة ومنظمة */
    .patient-record {
        background: #1e293b; padding: 20px; border-radius: 12px;
        margin-bottom: 15px; border-right: 8px solid #3b82f6;
    }
    
    /* تنسيق الدردشة على شكل مربعات (Bubbles) */
    .chat-bubble {
        background-color: #262730; padding: 10px 15px; border-radius: 15px;
        margin-bottom: 10px; border: 1px solid #3b82f6; width: fit-content;
        max-width: 80%;
    }
    .chat-user { color: #60a5fa; font-weight: bold; font-size: 0.9em; }
    .chat-time { color: #94a3b8; font-size: 0.7em; }

    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>🏥 نظام مختبرات حديثة المركزي</h2>", unsafe_allow_html=True)
    centers = ['مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية', 'المركز التخصصي للاسنان', 'مركز صحي بروانه', 'أطباء الاختصاص']
    u_center = st.selectbox("اختر جهة العمل:", centers)
    u_code = st.text_input("الرمز السري:", type="password")
    
    if st.button("دخول"):
        res = supabase.table("center_access").select("*").eq("center_name", u_center).eq("access_code", u_code).execute()
        if res.data:
            st.session_state.logged_in = True
            st.session_state.center = u_center
            st.session_state.is_admin = (u_center == 'مختبر مستشفى حديثة للفحوصات الفيروسية')
            st.session_state.is_doctor = (u_center == 'أطباء الاختصاص')
            st.rerun()
        else: st.error("الرمز غير صحيح")

else:
    # التبويبات العلوية
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 السجل العام"])
    else:
        tabs = st.tabs(["🔍 السجل العام", "📝 إضافة جديد", "💬 الدردشة"])

    # --- تبويب السجل (مع الحذف والتعديل حسب الصلاحية) ---
    with tabs[0]:
        st.subheader("🔍 سجل المراجعين")
        q = st.text_input("ابحث عن اسم:")
        
        if q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").order("created_at", desc=True).execute()
        else:
            res = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if res.data:
            for p in res.data:
                # قانون الصلاحية
                can_manage = st.session_state.is_admin or (p['entry_center'] == st.session_state.center)
                
                st.markdown(f"""<div class='patient-record'>
                    <h3 style='margin:0;'>👤 {p['full_name']}</h3>
                    <p style='margin:5px 0;'>📍 {p['address']} | 🔬 {p['infection_type']} | 📅 {p['test_date']}</p>
                    <small>🏢 {p['entry_center']} | 📝 {p['pcr_result']}</small>
                </div>""", unsafe_allow_html=True)
                
                if not st.session_state.is_doctor:
                    c1, c2 = st.columns(2)
                    with c1:
                        if can_manage:
                            if st.button(f"🗑️ حذف", key=f"d_{p['id']}"):
                                supabase.table("patients").delete().eq("id", p['id']).execute()
                                st.rerun()
                        else: st.write("🔒 للقراءة")
                    with c2:
                        if can_manage:
                            with st.expander("⚙️ تعديل"):
                                new_n = st.text_input("تحديث الملاحظة:", value=p['pcr_result'], key=f"i_{p['id']}")
                                if st.button("حفظ", key=f"u_{p['id']}"):
                                    supabase.table("patients").update({"pcr_result": new_n}).eq("id", p['id']).execute()
                                    st.rerun()
        st.write("---")

    # --- تبويب الإضافة ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            st.subheader("📝 تسجيل إصابة")
            with st.form("add_f", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("الاسم:")
                    addr = st.text_input("السكن:")
                with col2:
                    inf = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    dt = st.date_input("التاريخ:", value=date.today())
                note = st.text_area("الملاحظات:")
                if st.form_submit_button("إرسال"):
                    if name and addr:
                        supabase.table("patients").insert({"full_name": name, "address": addr, "infection_type": inf, "test_date": str(dt), "pcr_result": note, "entry_center": st.session_state.center}).execute()
                        st.success("تم الحفظ")
                    else: st.error("املأ الحقول")

        # --- تبويب الدردشة (مربعات ثابتة) ---
        with tabs[2]:
            st.subheader("💬 منصة التواصل")
            chat_data = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(20).execute()
            for m in reversed(chat_data.data):
                st.markdown(f"""<div class='chat-bubble'>
                    <div class='chat-user'>{m['username']}</div>
                    <div>{m['message']}</div>
                    <div class='chat-time'>{m['created_at'][11:16]}</div>
                </div>""", unsafe_allow_html=True)
            
            with st.form("chat_form", clear_on_submit=True):
                msg = st.text_input("اكتب رسالتك:")
                if st.form_submit_button("إرسال") and msg:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": msg}).execute()
                    st.rerun()

    if st.sidebar.button("🔴 خروج"):
        st.session_state.clear()
        st.rerun()
        
