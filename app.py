import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. الاتصال ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error("فشل الاتصال")

# --- 2. التنسيق (إنهاء النص الطولي + مربعات الدردشة) ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; }
    
    /* منع ضغط النصوص */
    .stMarkdown, .stText, p, div { white-space: normal !important; word-wrap: break-word !important; }
    
    /* مربعات الدردشة (مثل الواتساب) */
    .chat-bubble {
        background-color: #1e293b; padding: 12px; border-radius: 15px;
        margin-bottom: 10px; border: 1px solid #3b82f6; width: fit-content;
        min-width: 150px; max-width: 90%;
    }
    .chat-user { color: #60a5fa; font-weight: bold; font-size: 0.85em; margin-bottom: 4px; border-bottom: 1px solid #334155; }
    
    /* بطاقة المراجع */
    .p-card {
        background: #1e293b; padding: 15px; border-radius: 10px;
        margin-bottom: 10px; border-right: 6px solid #3b82f6; width: 100%;
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>🏥 نظام مختبرات حديثة المركزي</h2>", unsafe_allow_html=True)
    centers = ['مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية', 'المركز التخصصي للاسنان', 'مركز صحي بروانه', 'أطباء الاختصاص']
    u_center = st.selectbox("المركز:", centers)
    u_code = st.text_input("الرمز:", type="password")
    if st.button("دخول للنظام"):
        res = supabase.table("center_access").select("*").eq("center_name", u_center).eq("access_code", u_code).execute()
        if res.data:
            st.session_state.logged_in = True
            st.session_state.center = u_center
            st.session_state.is_admin = (u_center == 'مختبر مستشفى حديثة للفحوصات الفيروسية')
            st.session_state.is_doctor = (u_center == 'أطباء الاختصاص')
            st.rerun()
else:
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 السجل العام والبحث"])
    else:
        tabs = st.tabs(["🔍 السجل العام", "📝 إضافة مراجع", "💬 الدردشة الفورية"])

    # --- التبويب الأول: السجل ---
    with tabs[0]:
        st.subheader("🔍 قاعدة بيانات المصابين")
        q = st.text_input("ابحث عن اسم المراجع:")
        res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").order("created_at", desc=True).execute() if q else supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if res.data:
            for p in res.data:
                can_manage = st.session_state.is_admin or (p['entry_center'] == st.session_state.center)
                st.markdown(f"""<div class='p-card'>
                    <b>👤 {p['full_name']}</b><br>
                    📍 {p['address']} | 🔬 {p['infection_type']} | 📅 {p['test_date']}<br>
                    🏢 {p['entry_center']} | 📝 {p['pcr_result']}
                </div>""", unsafe_allow_html=True)
                
                if not st.session_state.is_doctor and can_manage:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"🗑️ حذف", key=f"d_{p['id']}"):
                            supabase.table("patients").delete().eq("id", p['id']).execute()
                            st.rerun()
                    with c2:
                        with st.expander("⚙️ تعديل"):
                            new_n = st.text_input("تعديل الملاحظة:", value=p['pcr_result'], key=f"i_{p['id']}")
                            if st.button("تحديث", key=f"u_{p['id']}"):
                                supabase.table("patients").update({"pcr_result": new_n}).eq("id", p['id']).execute()
                                st.rerun()

    # --- التبويب الثاني: الإضافة ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            st.subheader("📝 إضافة بيانات مراجع")
            with st.form("f_add"):
                name = st.text_input("الاسم:")
                addr = st.text_input("السكن:")
                inf = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                dt = st.date_input("التاريخ:", value=date.today())
                nt = st.text_area("ملاحظة:")
                if st.form_submit_button("إرسال"):
                    supabase.table("patients").insert({"full_name":name,"address":addr,"infection_type":inf,"test_date":str(dt),"pcr_result":nt,"entry_center":st.session_state.center}).execute()
                    st.success("تم الحفظ")

        # --- التبويب الثالث: الدردشة ---
        with tabs[2]:
            st.subheader("💬 منصة التنسيق المختبري")
            chats = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(25).execute()
            for m in reversed(chats.data):
                st.markdown(f"""<div class='chat-bubble'>
                    <div class='chat-user'>{m['username']}</div>
                    <div>{m['message']}</div>
                </div>""", unsafe_allow_html=True)
            
            with st.form("f_chat", clear_on_submit=True):
                msg = st.text_input("اكتب رسالتك...")
                if st.form_submit_button("إرسال") and msg:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": msg}).execute()
                    st.rerun()

    if st.sidebar.button("خروج"):
        st.session_state.clear()
        st.rerun()
