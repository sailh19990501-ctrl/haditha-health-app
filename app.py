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
    
    /* بطاقة المصاب المختصرة */
    .patient-summary {
        background: #1e293b; padding: 15px; border-radius: 10px;
        margin-bottom: 5px; border-right: 8px solid #3b82f6; width: 100%;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    .chat-msg {
        background: #202c33; padding: 12px; border-radius: 10px;
        margin-bottom: 8px; border-right: 4px solid #00a884; width: fit-content; max-width: 90%;
    }

    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer, header { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# --- 3. نظام تنظيف الدردشة ---
def clean_old_chats():
    try:
        time_limit = (datetime.now() - timedelta(minutes=35)).isoformat()
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
    st.write(f"🟢 المتصل: **{st.session_state.center}**")
    if st.button("🔴 تسجيل خروج"):
        st.session_state.clear()
        st.rerun()

    tabs = st.tabs(["🔍 سجل المصابين", "📝 إضافة جديد", "💬 الدردشة"]) if not st.session_state.is_doctor else st.tabs(["🔍 سجل المصابين"])

    # --- تبويب السجل (العرض المختصر) ---
    with tabs[0]:
        q = st.text_input("بحث بالاسم:")
        res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").order("created_at", desc=True).execute()
        
        if res.data:
            for p in res.data:
                # عرض السطر المختصر
                st.markdown(f"""<div class="patient-summary">
                    <span>👤 <b>{p.get('full_name')}</b></span>
                    <span>🔬 الإصابة: <b>{p.get('infection_type')}</b></span>
                    <span>🏢 المركز: <b>{p.get('entry_center')}</b></span>
                </div>""", unsafe_allow_html=True)
                
                # صندوق التفاصيل المخفي
                with st.expander("إظهار التفاصيل الدقيقة وخيارات التحكم"):
                    st.write(f"🎂 **العمر:** {p.get('age', '---')} سنة")
                    st.write(f"📱 **رقم الهاتف:** {p.get('phone_number', '---')}")
                    st.write(f"📍 **العنوان:** {p.get('address', '---')}")
                    st.write(f"⚙️ **الجهاز المستخدم:** {p.get('test_device')}")
                    st.write(f"📅 **تاريخ الفحص:** {p.get('test_date')}")
                    st.divider()
                    
                    can_edit = st.session_state.is_admin or (p.get('entry_center') == st.session_state.center)
                    if can_edit and not st.session_state.is_doctor:
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button(f"🗑️ حذف نهائي", key=f"del_{p['id']}"):
                                supabase.table("patients").delete().eq("id", p['id']).execute()
                                st.rerun()
                        with c2:
                            with st.form(f"ed_{p['id']}"):
                                en = st.text_input("تعديل الاسم:", value=p.get('full_name'))
                                ea = st.text_input("تعديل العمر:", value=p.get('age'))
                                ep = st.text_input("تعديل الهاتف:", value=p.get('phone_number'))
                                ead = st.text_input("تعديل العنوان:", value=p.get('address'))
                                if st.form_submit_button("حفظ التحديثات"):
                                    supabase.table("patients").update({"full_name":en, "age":ea, "phone_number":ep, "address":ead}).eq("id", p['id']).execute()
                                    st.rerun()
        else: st.info("لا توجد سجلات")

    # --- تبويب الإضافة ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            with st.form("add_form", clear_on_submit=True):
                ca, cb = st.columns(2)
                with ca:
                    n_name = st.text_input("الاسم الرباعي:")
                    n_age = st.text_input("العمر:")
                    n_phone = st.text_input("رقم الهاتف:")
                with cb:
                    n_addr = st.text_input("العنوان:")
                    n_inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    n_tech = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR"])
                n_date = st.date_input("التاريخ:", value=date.today())
                if st.form_submit_button("حفظ في السجل"):
                    if n_name:
                        supabase.table("patients").insert({
                            "full_name": n_name, "age": n_age, "phone_number": n_phone, 
                            "address": n_addr, "infection_type": n_inf, "test_device": n_tech, 
                            "test_date": str(n_date), "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الإضافة")
                        st.rerun()

        # --- تبويب الدردشة ---
        with tabs[2]:
            clean_old_chats()
            st.subheader("💬 المحادثة")
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(50).execute()
            for m in reversed(msgs.data):
                st.markdown(f'<div class="chat-msg"><div style="color:#00a884; font-weight:bold;">{m["username"]}</div>{m["message"]}</div>', unsafe_allow_html=True)
            with st.form("chat_input", clear_on_submit=True):
                txt = st.text_input("اكتب رسالة...")
                if st.form_submit_button("إرسال") and txt:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": txt}).execute()
                    st.rerun()
