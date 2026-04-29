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

# --- 2. التنسيق (CSS) لإنهاء مشكلة النص الطولي نهائياً ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; padding: 1rem; }
    
    /* حل مشكلة النص الطولي: منع الأعمدة من ضغط المحتوى */
    .patient-box {
        background: #1e293b; padding: 20px; border-radius: 12px;
        margin-bottom: 20px; border-right: 8px solid #3b82f6;
        width: 100%; display: block; clear: both;
    }
    .patient-box b { color: #60a5fa; font-size: 1.1em; }
    
    /* مربعات الدردشة الاحترافية */
    .chat-bubble {
        background-color: #262730; padding: 12px 18px; border-radius: 15px;
        margin-bottom: 12px; border: 1px solid #3b82f6; width: fit-content;
        max-width: 85%; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .chat-user { color: #60a5fa; font-weight: bold; font-size: 0.9em; margin-bottom: 5px; border-bottom: 1px solid #334155; }
    
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; }
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. بوابة الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center; color: #3b82f6;'>🏥 نظام مختبرات قضاء حديثة</h2>", unsafe_allow_html=True)
    with st.container():
        centers = [
            'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
            'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 'أطباء الاختصاص'
        ]
        u_center = st.selectbox("اختر المركز:", centers)
        u_code = st.text_input("رمز الدخول:", type="password")
        if st.button("دخول للنظام"):
            res = supabase.table("center_access").select("*").eq("center_name", u_center).eq("access_code", u_code).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                st.session_state.is_admin = (u_center == 'مختبر مستشفى حديثة للفحوصات الفيروسية')
                st.session_state.is_doctor = (u_center == 'أطباء الاختصاص')
                st.rerun()
            else: st.error("❌ الرمز غير صحيح")

else:
    # القائمة العلوية (التبويبات)
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 سجل المراجعين"])
    else:
        tabs = st.tabs(["🔍 السجل والبحث", "📝 إضافة إصابة", "💬 الدردشة الفورية"])

    # --- تبويب السجل (مع الصلاحيات الدقيقة) ---
    with tabs[0]:
        st.subheader("🔍 قاعدة بيانات المصابين")
        q = st.text_input("ابحث عن اسم المراجع:")
        
        if q:
            results = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").order("created_at", desc=True).execute()
        else:
            results = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if results.data:
            for p in results.data:
                # قانون الصلاحيات
                can_manage = st.session_state.is_admin or (p['entry_center'] == st.session_state.center)
                
                # استخدام Div بدلاً من Columns داخل Expander لمنع النص الطولي
                with st.expander(f"👤 {p['full_name']} | {p['infection_type']}"):
                    st.markdown(f"""<div class='patient-box'>
                        <b>📍 السكن:</b> {p['address']}<br>
                        <b>🔬 الإصابة:</b> {p['infection_type']} | <b>📅 التاريخ:</b> {p['test_date']}<br>
                        <b>🏢 المركز المسجل:</b> {p['entry_center']}<br>
                        <b>📝 ملاحظات/PCR:</b> {p['pcr_result']}
                    </div>""", unsafe_allow_html=True)
                    
                    if not st.session_state.is_doctor:
                        # الأزرار خارج الـ Div لضمان عملها برمجياً
                        if can_manage:
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button(f"🗑️ حذف السجل", key=f"del_{p['id']}"):
                                    supabase.table("patients").delete().eq("id", p['id']).execute()
                                    st.rerun()
                            with c2:
                                with st.form(f"edit_f_{p['id']}", clear_on_submit=True):
                                    new_n = st.text_input("تعديل الملاحظة:", value=p['pcr_result'])
                                    if st.form_submit_button("تحديث"):
                                        supabase.table("patients").update({"pcr_result": new_n}).eq("id", p['id']).execute()
                                        st.rerun()
                        else:
                            st.info("🔒 لا تملك صلاحية التعديل على هذا السجل")

    # --- تبويب إضافة بيانات ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            st.subheader("📝 تسجيل مراجع جديد")
            with st.form("main_add_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("الاسم الرباعي:")
                    addr = st.text_input("عنوان السكن:")
                    inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with col2:
                    dev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    dt = st.date_input("التاريخ:", value=date.today())
                    note = st.text_area("ملاحظات إضافية:")
                
                if st.form_submit_button("حفظ وإرسال"):
                    if name and addr:
                        supabase.table("patients").insert({
                            "full_name": name, "address": addr, "infection_type": inf,
                            "test_device": dev, "test_date": str(dt), "pcr_result": note,
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الحفظ بنجاح")
                    else: st.warning("⚠️ يرجى ملء الاسم والسكن")

        # --- تبويب الدردشة (مربعات) ---
        with tabs[2]:
            st.subheader("💬 منصة التنسيق بين المراكز")
            chat_res = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(20).execute()
            for m in reversed(chat_res.data):
                st.markdown(f"""<div class='chat-bubble'>
                    <div class='chat-user'>{m['username']}</div>
                    <div>{m['message']}</div>
                </div>""", unsafe_allow_html=True)
            
            with st.form("chat_input_form", clear_on_submit=True):
                msg = st.text_input("اكتب رسالتك:")
                if st.form_submit_button("إرسال") and msg:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": msg}).execute()
                    st.rerun()

    if st.sidebar.button("🔴 تسجيل خروج"):
        st.session_state.clear()
        st.rerun()
        
