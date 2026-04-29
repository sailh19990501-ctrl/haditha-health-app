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

# --- 2. التنسيق البصري (منع النص الطولي وترتيب الواجهة) ---
st.set_page_config(page_title="أرشيف المصابين الموحد", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; padding: 1rem 3rem !important; }
    
    /* إخفاء السايدبار لضمان العرض الكامل */
    [data-testid="stSidebar"] { display: none; }
    
    /* بطاقة المراجع العريضة جداً */
    .patient-card {
        background: #1e293b; padding: 25px; border-radius: 15px;
        margin-bottom: 20px; border-right: 10px solid #3b82f6; width: 100%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* نظام الدردشة المطور */
    .chat-container {
        height: 450px; overflow-y: auto; background: #0b141a;
        padding: 20px; border-radius: 15px; border: 1px solid #202c33;
        display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px;
    }
    .chat-bubble {
        background: #202c33; padding: 12px 18px; border-radius: 12px;
        width: fit-content; max-width: 85%; border-right: 4px solid #00a884;
    }
    .chat-sender { color: #00a884; font-weight: bold; font-size: 0.85em; margin-bottom: 5px; }

    #MainMenu, footer, header { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# --- 3. إدارة النشاط (النشطين حالياً) ---
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

# --- 4. تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🏥 أرشيف المصابين بالأمراض الانتقالية</h1>", unsafe_allow_html=True)
    
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
            else: st.error("⚠️ الرمز السري غير صحيح!")

else:
    update_activity()
    active_centers, active_docs = get_active_users()
    
    # --- 5. أيقونة المستخدم (أعلى الصفحة) ---
    with st.expander(f"👤 {st.session_state.center} | 🟢 النشطين: {len(active_centers) + active_docs}"):
        st.write(f"**حسابك:** {st.session_state.center}")
        st.write(f"**المراكز المتصلة:** {', '.join(active_centers) if active_centers else 'أنت فقط'}")
        st.write(f"**عدد الأطباء المتصلين:** {active_docs}")
        if st.button("🔴 تسجيل الخروج"):
            try: supabase.table("active_sessions").delete().eq("center_name", st.session_state.center).execute()
            except: pass
            st.session_state.clear()
            st.rerun()

    # --- 6. التبويبات ---
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 استعراض السجل العام والبحث"])
    else:
        tabs = st.tabs(["🔍 سجل المراجعين والبحث", "📝 إضافة إصابة جديدة", "💬 الدردشة الفورية"])

    # --- تبويب السجل ---
    with tabs[0]:
        st.subheader("🔍 قاعدة بيانات أرشيف حديثة الموحدة")
        search_q = st.text_input("ابحث عن اسم المصاب الرباعي:")
        
        # جلب البيانات
        if search_q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{search_q}%").order("created_at", desc=True).execute()
        else:
            res = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if res.data:
            for p in res.data:
                can_modify = st.session_state.is_admin or (p.get('entry_center') == st.session_state.center)
                
                st.markdown(f"""<div class="patient-card">
                    <h3>👤 {p.get('full_name', 'غير متوفر')}</h3>
                    <p>📱 <b>رقم الهاتف:</b> {p.get('phone_number', '---')} | 📍 <b>العنوان الكامل:</b> {p.get('address', '---')}</p>
                    <p>🔬 <b>نوع الإصابة:</b> {p.get('infection_type', '---')} | ⚙️ <b>التقنية:</b> {p.get('test_device', '---')}</p>
                    <p>🏢 <b>جهة الإدخال:</b> {p.get('entry_center', '---')} | 📅 <b>تاريخ الفحص:</b> {p.get('test_date', '---')}</p>
                    <p style="color: #94a3b8;">📝 <b>الملاحظات:</b> {p.get('pcr_result', 'لا يوجد')}</p>
                </div>""", unsafe_allow_html=True)
                
                if not st.session_state.is_doctor and can_modify:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"🗑️ مسح السجل", key=f"del_{p['id']}"):
                            supabase.table("patients").delete().eq("id", p['id']).execute()
                            st.rerun()
                    with c2:
                        with st.expander("🛠️ تعديل البيانات"):
                            with st.form(f"edit_{p['id']}"):
                                e_name = st.text_input("تعديل الاسم:", value=p.get('full_name'))
                                e_phone = st.text_input("تعديل الهاتف:", value=p.get('phone_number'))
                                e_addr = st.text_input("تعديل العنوان:", value=p.get('address'))
                                e_date = st.date_input("تعديل التاريخ:", value=date.today())
                                if st.form_submit_button("حفظ التغييرات"):
                                    supabase.table("patients").update({
                                        "full_name": e_name, 
                                        "phone_number": e_phone, 
                                        "address": e_addr,
                                        "test_date": str(e_date)
                                    }).eq("id", p['id']).execute()
                                    st.rerun()
        else: st.info("لا توجد بيانات حالياً.")

    # --- تبويب الإضافة ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            st.subheader("📝 تسجيل مراجع جديد")
            with st.form("add_form", clear_on_submit=True):
                ca, cb = st.columns(2)
                with ca:
                    n_name = st.text_input("الاسم الرباعي:")
                    n_phone = st.text_input("رقم الهاتف:")
                    n_addr = st.text_input("العنوان بالتفصيل:")
                with cb:
                    n_inf = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    n_tech = st.selectbox("التقنية:", ["Strips", "ELISA", "PCR"])
                    n_date = st.date_input("التاريخ:", value=date.today())
                n_note = st.text_area("ملاحظات إضافية:")
                if st.form_submit_button("إرسال للسجل المركزي"):
                    if n_name:
                        supabase.table("patients").insert({
                            "full_name": n_name, "phone_number": n_phone, "address": n_addr,
                            "infection_type": n_inf, "test_device": n_tech, "test_date": str(n_date),
                            "pcr_result": n_note, "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم حفظ المصاب بنجاح")
                    else: st.error("⚠️ يجب كتابة الاسم الرباعي.")

        # --- تبويب الدردشة ---
        with tabs[2]:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(40).execute()
            for m in reversed(msgs.data):
                st.markdown(f"""<div class="chat-bubble">
                    <div class="chat-sender">{m['username']}</div>
                    <div>{m['message']}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.form("chat_box", clear_on_submit=True):
                msg_txt = st.text_input("اكتب رسالتك للمراكز الأخرى...")
                if st.form_submit_button("إرسال") and msg_txt:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": msg_txt}).execute()
                    st.rerun()
