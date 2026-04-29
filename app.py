import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta

# --- 1. الاتصال بالسيرفر ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception:
    st.error("فشل الاتصال بالسيرفر")

# --- 2. التنسيق ومنع النصوص الطولية ---
st.set_page_config(page_title="أرشيف حديثة الموحد", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; padding: 1rem 2rem !important; }
    
    /* بطاقة المصاب العريضة */
    .patient-card {
        background: #1e293b; padding: 20px; border-radius: 12px;
        margin-bottom: 15px; border-right: 8px solid #3b82f6; width: 100%;
    }
    
    /* تصميم الدردشة بدون المربع المحشور */
    .chat-msg {
        background: #202c33; padding: 12px; border-radius: 10px;
        margin-bottom: 8px; border-right: 4px solid #00a884; width: fit-content; max-width: 90%;
    }
    .chat-user { color: #00a884; font-weight: bold; font-size: 0.9em; }

    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer, header { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# --- 3. نظام تنظيف الدردشة (كل 35 دقيقة) ---
def clean_old_chats():
    try:
        # تحديد الوقت قبل 35 دقيقة من الآن
        time_limit = (datetime.now() - timedelta(minutes=35)).isoformat()
        # حذف أي رسالة أقدم من هذا الوقت
        supabase.table("chat_messages").delete().lt("created_at", time_limit).execute()
    except: pass

# --- 4. تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>🏥 أرشيف المصابين بالأمراض الانتقالية</h2>", unsafe_allow_html=True)
    access_map = {
        'مركز مصرف الدم الرئيسي': 'HAD-BLOOD-2026',
        'مختبر مستشفى حديثة للفحوصات الفيروسية': 'HAD-VIRUS-2026',
        'المركز التخصصي للاسنان': 'HAD-DENT-2026',
        'مركز صحي بروانه': 'BAR-HEALTH-2026',
        'أطباء الاختصاص (طبيب الاختصاص)': 'DOC-READ-2026'
    }
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u_center = st.selectbox("اختر المركز:", list(access_map.keys()))
        u_code = st.text_input("الرمز السري:", type="password")
        if st.button("دخول"):
            if u_code == access_map[u_center]:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                st.session_state.is_admin = u_center in ['مركز مصرف الدم الرئيسي', 'مختبر مستشفى حديثة للفحوصات الفيروسية']
                st.session_state.is_doctor = (u_center == 'أطباء الاختصاص (طبيب الاختصاص)')
                st.rerun()
            else: st.error("الرمز خطأ")

else:
    # زر الخروج في الأعلى
    if st.button("🔴 تسجيل خروج " + st.session_state.center):
        st.session_state.clear()
        st.rerun()

    # التبويبات
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 سجل المصابين"])
    else:
        tabs = st.tabs(["🔍 سجل المصابين", "📝 إضافة جديد", "💬 الدردشة الفورية"])

    # --- تبويب السجل ---
    with tabs[0]:
        q = st.text_input("بحث بالاسم الرباعي:")
        res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").order("created_at", desc=True).execute()
        
        if res.data:
            for p in res.data:
                can_edit = st.session_state.is_admin or (p.get('entry_center') == st.session_state.center)
                st.markdown(f"""<div class="patient-card">
                    <h3>👤 {p.get('full_name')}</h3>
                    <p>📱 الهاتف: {p.get('phone_number')} | 📍 العنوان: {p.get('address')}</p>
                    <p>🔬 الإصابة: {p.get('infection_type')} | ⚙️ الجهاز: {p.get('test_device')} | 📅 التاريخ: {p.get('test_date')}</p>
                    <p style="font-size: 0.8em; color: #94a3b8;">🏢 المركز: {p.get('entry_center')}</p>
                </div>""", unsafe_allow_html=True)
                
                if can_edit and not st.session_state.is_doctor:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"🗑️ حذف", key=f"del_{p['id']}"):
                            supabase.table("patients").delete().eq("id", p['id']).execute()
                            st.rerun()
                    with c2:
                        with st.expander("🛠️ تعديل"):
                            with st.form(f"ed_{p['id']}"):
                                en = st.text_input("الاسم:", value=p.get('full_name'))
                                ep = st.text_input("الهاتف:", value=p.get('phone_number'))
                                ea = st.text_input("العنوان:", value=p.get('address'))
                                ei = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                                ed = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR"])
                                if st.form_submit_button("تحديث"):
                                    supabase.table("patients").update({"full_name":en, "phone_number":ep, "address":ea, "infection_type":ei, "test_device":ed}).eq("id", p['id']).execute()
                                    st.rerun()
        else: st.info("لا يوجد مصابين بهذا الاسم")

    # --- تبويب الإضافة (التحديث التلقائي) ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            with st.form("add_form", clear_on_submit=True):
                ca, cb = st.columns(2)
                with ca:
                    n_name = st.text_input("الاسم الرباعي:")
                    n_phone = st.text_input("رقم الهاتف:")
                    n_addr = st.text_input("العنوان:")
                with cb:
                    n_inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    n_tech = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR"])
                    n_date = st.date_input("التاريخ:", value=date.today())
                if st.form_submit_button("إرسال للسجل"):
                    if n_name:
                        supabase.table("patients").insert({
                            "full_name": n_name, "phone_number": n_phone, "address": n_addr,
                            "infection_type": n_inf, "test_device": n_tech, "test_date": str(n_date),
                            "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الإضافة بنجاح")
                        st.rerun() # هذا الأمر يقوم بتحديث السجل فوراً

        # --- تبويب الدردشة (بدون مربعات حاشرة + تنظيف تلقائي) ---
        with tabs[2]:
            clean_old_chats() # تنظيف الرسائل القديمة أول ما يفتح التبويب
            st.subheader("💬 المحادثة الفورية (تُمسح كل 35 دقيقة)")
            
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(50).execute()
            for m in reversed(msgs.data):
                st.markdown(f"""<div class="chat-msg">
                    <div class="chat-user">{m['username']}</div>
                    <div>{m['message']}</div>
                </div>""", unsafe_allow_html=True)
            
            with st.form("chat_input", clear_on_submit=True):
                txt = st.text_input("اكتب هنا...")
                if st.form_submit_button("إرسال"):
                    if txt:
                        supabase.table("chat_messages").insert({"username": st.session_state.center, "message": txt}).execute()
                        st.rerun()
