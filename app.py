import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta

# --- 1. الاتصال بالسيرفر ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception:
    st.error("فشل الاتصال بالسيرفر المركزي.")

# --- 2. التنسيق البصري الاحترافي ---
st.set_page_config(page_title="أرشيف المصابين الموحد", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; padding: 1rem 2rem !important; }
    
    /* منع السايدبار */
    [data-testid="stSidebar"] { display: none; }
    
    /* بطاقة المصاب - عريضة ومرتبة */
    .patient-card {
        background: #1e293b; padding: 25px; border-radius: 15px;
        margin-bottom: 20px; border-right: 10px solid #3b82f6; width: 100%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* نظام الدردشة المطور (داخل الصندوق) */
    .chat-container {
        height: 400px; overflow-y: auto; background: #0b141a;
        padding: 20px; border-radius: 15px; border: 1px solid #202c33;
        display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px;
    }
    .chat-bubble {
        background: #202c33; padding: 12px; border-radius: 12px;
        width: fit-content; max-width: 85%; border-right: 4px solid #00a884;
    }
    .chat-sender { color: #00a884; font-weight: bold; font-size: 0.85em; }

    #MainMenu, footer, header { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# --- 3. نظام النشاط ---
def update_activity():
    if 'center' in st.session_state:
        try:
            supabase.table("active_sessions").upsert({
                "center_name": st.session_state.center,
                "last_active": datetime.now().isoformat(),
                "is_doctor": st.session_state.is_doctor
            }).execute()
        except: pass

def get_active_users():
    try:
        limit = (datetime.now() - timedelta(minutes=5)).isoformat()
        res = supabase.table("active_sessions").select("*").gt("last_active", limit).execute()
        centers = [m['center_name'] for m in res.data if not m['is_doctor']]
        doctors_count = sum(1 for m in res.data if m['is_doctor'])
        return list(set(centers)), doctors_count
    except: return [], 0

# --- 4. الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🏥 أرشيف المصابين بالأمراض الانتقالية</h1>", unsafe_allow_html=True)
    access_map = {
        'مركز مصرف الدم الرئيسي': 'HAD-BLOOD-2026',
        'مختبر مستشفى حديثة للفحوصات الفيروسية': 'HAD-VIRUS-2026',
        'المركز التخصصي للاسنان': 'HAD-DENT-2026',
        'مركز صحي بروانه': 'BAR-HEALTH-2026',
        'أطباء الاختصاص (طبيب الاختصاص)': 'DOC-READ-2026'
    }
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u_center = st.selectbox("جهة العمل:", list(access_map.keys()))
        u_code = st.text_input("الرمز السري:", type="password")
        if st.button("دخول للنظام"):
            if u_code == access_map[u_center]:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                st.session_state.is_admin = u_center in ['مركز مصرف الدم الرئيسي', 'مختبر مستشفى حديثة للفحوصات الفيروسية']
                st.session_state.is_doctor = (u_center == 'أطباء الاختصاص (طبيب الاختصاص)')
                update_activity()
                st.rerun()
            else: st.error("الرمز خطأ")
else:
    update_activity()
    active_centers, active_docs = get_active_users()
    with st.expander(f"👤 {st.session_state.center} | 🟢 المتصلون: {len(active_centers) + active_docs}"):
        st.write(f"المراكز النشطة: {', '.join(active_centers)}")
        st.write(f"الأطباء المتصلون: {active_docs}")
        if st.button("تسجيل الخروج"):
            st.session_state.clear()
            st.rerun()

    # --- 5. التبويبات ---
    tabs = st.tabs(["🔍 السجل والبحث", "📝 إضافة جديد", "💬 الدردشة"]) if not st.session_state.is_doctor else st.tabs(["🔍 سجل المصابين"])

    with tabs[0]:
        st.subheader("🔍 استعراض سجل المصابين")
        q = st.text_input("ابحث عن اسم:")
        res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").order("created_at", desc=True).execute()
        
        if res.data:
            for p in res.data:
                can_manage = st.session_state.is_admin or (p.get('entry_center') == st.session_state.center)
                st.markdown(f"""<div class="patient-card">
                    <h3>👤 {p.get('full_name')}</h3>
                    <p>📱 الهاتف: {p.get('phone_number')} | 📍 العنوان: {p.get('address')}</p>
                    <p>🔬 الإصابة: {p.get('infection_type')} | ⚙️ الجهاز: {p.get('test_device')} | 📅 التاريخ: {p.get('test_date')}</p>
                    <p>🏢 المركز المسجل: {p.get('entry_center')}</p>
                </div>""", unsafe_allow_html=True)
                
                if can_manage and not st.session_state.is_doctor:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"🗑️ مسح نهائي", key=f"del_{p['id']}"):
                            supabase.table("patients").delete().eq("id", p['id']).execute()
                            st.success("تم الحذف")
                            st.rerun()
                    with c2:
                        with st.expander("🛠️ تعديل البيانات"):
                            with st.form(f"ed_{p['id']}"):
                                en = st.text_input("الاسم:", value=p.get('full_name'))
                                ep = st.text_input("الهاتف:", value=p.get('phone_number'))
                                ea = st.text_input("العنوان:", value=p.get('address'))
                                ei = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"], index=0)
                                ed = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR"], index=0)
                                et = st.date_input("التاريخ:", value=date.today())
                                if st.form_submit_button("حفظ"):
                                    supabase.table("patients").update({"full_name":en, "phone_number":ep, "address":ea, "infection_type":ei, "test_device":ed, "test_date":str(et)}).eq("id", p['id']).execute()
                                    st.rerun()
        else: st.info("لا توجد بيانات")

    if not st.session_state.is_doctor:
        with tabs[1]:
            with st.form("add_f", clear_on_submit=True):
                c_a, c_b = st.columns(2)
                with c_a:
                    name = st.text_input("الاسم الرباعي:")
                    phone = st.text_input("رقم الهاتف:")
                    addr = st.text_input("العنوان بالتفصيل:")
                with c_b:
                    inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    tech = st.selectbox("الجهاز المستخدم:", ["Strips", "ELISA", "PCR"])
                    dt = st.date_input("تاريخ الفحص:", value=date.today())
                if st.form_submit_button("حفظ"):
                    supabase.table("patients").insert({"full_name": name, "phone_number": phone, "address": addr, "infection_type": inf, "test_device": tech, "test_date": str(dt), "entry_center": st.session_state.center}).execute()
                    st.success("تم الحفظ")

        with tabs[2]:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
            for m in reversed(msgs.data):
                st.markdown(f'<div class="chat-bubble"><div class="chat-sender">{m["username"]}</div>{m["message"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            with st.form("ch_f", clear_on_submit=True):
                txt = st.text_input("رسالتك...")
                if st.form_submit_button("إرسال") and txt:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": txt}).execute()
                    st.rerun()
