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

# --- 2. التصميم وتنسيق الواجهة ---
st.set_page_config(page_title="أرشيف حديثة الموحد", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; padding: 1rem 2rem !important; }
    .patient-card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 10px; border-right: 8px solid #3b82f6; }
    .chat-bubble { background: #202c33; padding: 12px; border-radius: 10px; margin-bottom: 8px; border-right: 4px solid #00a884; width: fit-content; max-width: 85%; }
    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer, header { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# --- 3. الوظائف الذكية ---
def sync_activity():
    if 'center' in st.session_state:
        try:
            supabase.table("active_sessions").upsert({
                "center_name": st.session_state.center,
                "last_active": datetime.utcnow().isoformat(),
                "is_doctor": st.session_state.get('is_doctor', False)
            }).execute()
        except: pass

def manage_chat_silent_limit():
    try:
        res = supabase.table("chat_messages").select("id").order("created_at", desc=True).execute()
        if len(res.data) > 100:
            cutoff_id = res.data[99]['id']
            supabase.table("chat_messages").delete().lt("id", cutoff_id).execute()
    except: pass

# --- 4. نظام الدخول وقائمة الرموز (حسب جدولك الأخير) ---
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
    sync_activity()
    
    # الترس (الإعدادات والنشاط)
    with st.expander(f"⚙️ إعدادات المتصل: {st.session_state.center}"):
        time_threshold = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        active_res = supabase.table("active_sessions").select("*").gt("last_active", time_threshold).execute()
        centers_active = list(set([s['center_name'] for s in active_res.data if not s['is_doctor']]))
        doctors_count = sum(1 for s in active_res.data if s['is_doctor'])
        st.write(f"🟢 **المراكز النشطة ({len(centers_active)}):** {', '.join(centers_active) if centers_active else 'لا يوجد'}")
        st.write(f"👨‍⚕️ **أطباء الاختصاص المتصلين:** {doctors_count}")
        st.divider()
        if st.button("🔴 تسجيل خروج نهائي"):
            supabase.table("active_sessions").delete().eq("center_name", st.session_state.center).execute()
            st.session_state.clear()
            st.rerun()

    tabs = st.tabs(["🔍 استعراض السجل"]) if st.session_state.is_doctor else st.tabs(["🔍 سجل المصابين", "📝 إضافة إصابة", "💬 الدردشة"])

    # --- تبويب السجل ---
    with tabs[0]:
        search_q = st.text_input("🔍 ابحث عن اسم المريض:")
        data = supabase.table("patients").select("*").ilike("full_name", f"%{search_q}%").order("created_at", desc=True).execute()
        if data.data:
            for p in data.data:
                st.markdown(f'<div class="patient-card"><h3 style="margin:0;">👤 {p["full_name"]}</h3><p style="margin:5px 0;">🔬 {p["infection_type"]} | 🏢 {p["entry_center"]}</p></div>', unsafe_allow_html=True)
                with st.expander("التفاصيل والتحكم"):
                    st.write(f"🎂 العمر: {p.get('age','--')} | 📱 الهاتف: {p.get('phone_number','--')}")
                    st.write(f"📍 العنوان: {p.get('address','--')} | ⚙️ الجهاز: {p['test_device']}")
                    if not st.session_state.is_doctor:
                        st.divider()
                        if st.session_state.is_admin or p['entry_center'] == st.session_state.center:
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button(f"🗑️ حذف", key=f"del_{p['id']}"):
                                    supabase.table("patients").delete().eq("id", p['id']).execute(); st.rerun()
                            with c2:
                                with st.form(f"edit_{p['id']}"):
                                    en = st.text_input("الاسم:", value=p['full_name'])
                                    ep = st.text_input("الهاتف:", value=p.get('phone_number'))
                                    if st.form_submit_button("حفظ"):
                                        supabase.table("patients").update({"full_name": en, "phone_number": ep}).eq("id", p['id']).execute(); st.rerun()
        else: st.info("لا توجد بيانات.")

    # --- تبويب الإضافة والدردشة (للمراكز فقط) ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            with st.form("add_new"):
                ca, cb = st.columns(2)
                with ca: n = st.text_input("الاسم الرباعي:"); a = st.text_input("العمر:"); ph = st.text_input("الهاتف:")
                with cb: ad = st.text_input("العنوان:"); i = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"]); t = st.selectbox("التقنية:", ["Strips", "ELISA", "PCR"])
                d = st.date_input("التاريخ:", value=date.today())
                if st.form_submit_button("حفظ"):
                    if n: supabase.table("patients").insert({"full_name":n,"age":a,"phone_number":ph,"address":ad,"infection_type":i,"test_device":t,"test_date":str(d),"entry_center":st.session_state.center}).execute(); st.success("✅ تم الحفظ"); st.rerun()
        with tabs[2]:
            manage_chat_silent_limit()
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(100).execute()
            for m in reversed(msgs.data):
                st.markdown(f'<div class="chat-bubble"><div style="color:#00a884; font-size:0.8em; font-weight:bold;">{m["username"]}</div>{m["message"]}</div>', unsafe_allow_html=True)
            with st.form("send_msg", clear_on_submit=True):
                txt = st.text_input("رسالتك...")
                if st.form_submit_button("إرسال") and txt:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": txt}).execute(); st.rerun()
