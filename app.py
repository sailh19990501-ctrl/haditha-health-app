import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. الاتصال بالسيرفر ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception:
    st.error("خطأ في الاتصال بالسيرفر")

# --- 2. التنسيق (إلغاء الشريط الجانبي وحل النص الطولي) ---
st.set_page_config(page_title="أرشيف المصابين", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
    /* جعل الصفحة تفرش بالكامل ومنع الانضغاط */
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; padding: 1rem 2rem !important; }
    
    /* أيقونة البروفايل في أقصى اليسار */
    .user-profile {
        position: absolute; top: 10px; left: 10px;
        background: #1e293b; padding: 5px 15px; border-radius: 20px;
        border: 1px solid #3b82f6; cursor: pointer; z-index: 1000;
    }

    /* السجل العريض */
    .patient-card {
        background: #1e293b; padding: 20px; border-radius: 12px;
        margin-bottom: 15px; border-right: 8px solid #3b82f6; width: 100%;
    }

    /* الدردشة */
    .chat-window {
        height: 400px; overflow-y: auto; background: #0b141a;
        padding: 15px; border-radius: 12px; border: 1px solid #202c33;
        display: flex; flex-direction: column; gap: 10px;
    }
    .bubble { background: #202c33; padding: 10px; border-radius: 10px; width: fit-content; max-width: 85%; }
    
    /* إخفاء السايدبار نهائياً */
    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer, header { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# --- 3. تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>🏥 أرشيف المصابين بالأمراض الانتقالية</h2>", unsafe_allow_html=True)
    access_map = {
        'مركز مصرف الدم الرئيسي': 'HAD-BLOOD-2026',
        'مختبر مستشفى حديثة للفحوصات الفيروسية': 'HAD-VIRUS-2026',
        'المركز التخصصي للاسنان': 'HAD-DENT-2026',
        'مركز صحي بروانه': 'BAR-HEALTH-2026',
        'أطباء الاختصاص (طبيب الاختصاص)': 'DOC-READ-2026'
    }
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u_center = st.selectbox("اختر جهة العمل:", list(access_map.keys()))
        u_code = st.text_input("الرمز السري:", type="password")
        if st.button("دخول للنظام"):
            if u_code == access_map[u_center]:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                st.session_state.is_admin = u_center in ['مركز مصرف الدم الرئيسي', 'مختبر مستشفى حديثة للفحوصات الفيروسية']
                st.session_state.is_doctor = (u_center == 'أطباء الاختصاص (طبيب الاختصاص)')
                st.rerun()
            else: st.error("الرمز خطأ")

else:
    # --- 4. الأيقونة الذكية (أقصى اليسار) ---
    with st.expander(f"👤 {st.session_state.center}"):
        st.write(f"🏠 الحساب: {st.session_state.center}")
        # محاكاة عدد المتصلين (يمكن ربطها بقاعدة البيانات لاحقاً)
        st.write("🟢 المتصلون الآن: 4 مراكز، 2 طبيب")
        st.write("📍 المراكز النشطة: مصرف الدم، الفيروسية، بروانه")
        if st.button("🔴 تسجيل خروج"):
            st.session_state.clear()
            st.rerun()

    # --- 5. التبويبات الرئيسية ---
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 استعراض السجل والبحث"])
    else:
        tabs = st.tabs(["🔍 سجل المصابين", "📝 إضافة جديد", "💬 الدردشة"])

    # --- تبويب السجل ---
    with tabs[0]:
        st.subheader("🔍 قاعدة البيانات المركزية")
        q = st.text_input("ابحث عن اسم المريض:")
        
        # جلب البيانات والتأكد من الربط
        if q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").order("created_at", desc=True).execute()
        else:
            res = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if res.data:
            for p in res.data:
                can_manage = st.session_state.is_admin or (p['entry_center'] == st.session_state.center)
                st.markdown(f"""<div class="patient-card">
                    <h3>👤 {p['full_name']}</h3>
                    <p>📱 {p.get('phone_number', 'N/A')} | 📍 {p.get('address', 'N/A')}</p>
                    <p>🔬 {p['infection_type']} | ⚙️ {p['test_device']} | 📅 {p['test_date']}</p>
                    <p>🏢 المركز: {p['entry_center']} | 📝 {p['pcr_result']}</p>
                </div>""", unsafe_allow_html=True)
                
                if not st.session_state.is_doctor and can_manage:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"🗑️ مسح", key=f"del_{p['id']}"):
                            supabase.table("patients").delete().eq("id", p['id']).execute()
                            st.rerun()
                    with c2:
                        with st.expander("🛠️ تعديل"):
                            with st.form(f"ed_{p['id']}"):
                                n_name = st.text_input("الاسم:", value=p['full_name'])
                                n_phone = st.text_input("الهاتف:", value=p.get('phone_number',''))
                                n_addr = st.text_input("العنوان:", value=p.get('address',''))
                                n_date = st.date_input("التاريخ:", value=datetime.strptime(p['test_date'], '%Y-%m-%d').date())
                                if st.form_submit_button("حفظ"):
                                    supabase.table("patients").update({"full_name": n_name, "phone_number": n_phone, "address": n_addr, "test_date": str(n_date)}).eq("id", p['id']).execute()
                                    st.rerun()
        else: st.info("لا توجد بيانات")

    # --- تبويب الإضافة ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            with st.form("add_f", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    name = st.text_input("الاسم الرباعي:")
                    phone = st.text_input("رقم الهاتف:")
                    addr = st.text_input("العنوان بالتفصيل:")
                with col_b:
                    inf = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    tech = st.selectbox("التقنية:", ["Strips", "ELISA", "PCR"])
                    dt = st.date_input("التاريخ:", value=date.today())
                note = st.text_area("ملاحظات:")
                if st.form_submit_button("إرسال للسجل"):
                    supabase.table("patients").insert({"full_name": name, "phone_number": phone, "address": addr, "infection_type": inf, "test_device": tech, "test_date": str(dt), "pcr_result": note, "entry_center": st.session_state.center}).execute()
                    st.success("تم الحفظ")

        # --- تبويب الدردشة ---
        with tabs[2]:
            st.markdown('<div class="chat-window">', unsafe_allow_html=True)
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
            for m in reversed(msgs.data):
                st.markdown(f'<div class="bubble"><b>{m["username"]}:</b><br>{m["message"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            with st.form("ch_f", clear_on_submit=True):
                txt = st.text_input("اكتب رسالتك...")
                if st.form_submit_button("إرسال") and txt:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": txt}).execute()
                    st.rerun()
