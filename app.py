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

# --- 2. التصميم (CSS) ---
st.set_page_config(page_title="أرشيف حديثة الموحد", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; padding: 1rem 2rem !important; }
    .patient-card { background: #1e293b; padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; border-right: 4px solid #3b82f6; cursor: pointer; }
    .p-title { font-size: 13px; font-weight: bold; color: #f8fafc; }
    .p-info { font-size: 11px; color: #94a3b8; margin-right: 8px; }
    .chat-bubble { background: #202c33; padding: 10px; border-radius: 8px; margin-bottom: 5px; border-right: 3px solid #00a884; width: fit-content; max-width: 85%; }
    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer, header { visibility: hidden; }
</style>""", unsafe_allow_html=True)

# --- 3. نظام التزامن والنشاط ---
def sync_activity():
    if 'center' in st.session_state:
        try:
            # تسجيل النشاط الحالي
            supabase.table("active_sessions").upsert({
                "center_name": st.session_state.center,
                "last_active": datetime.utcnow().isoformat(),
                "is_doctor": st.session_state.get('is_doctor', False)
            }).execute()
        except: pass

def get_live_status():
    """جلب حالة المتصلين الآن من السيرفر مباشرة"""
    try:
        # نعتبر الشخص متصلاً إذا كان آخر نشاط له خلال الـ 5 دقائق الماضية
        time_threshold = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        res = supabase.table("active_sessions").select("*").gt("last_active", time_threshold).execute()
        return res.data if res.data else []
    except: return []

# --- 4. الدخول والرموز ---
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
                sync_activity()
                st.rerun()
            else: st.error("❌ الرمز غير صحيح")
else:
    sync_activity()
    
    # --- قسم الترس (الإعدادات والنشاط المباشر) ---
    with st.expander(f"⚙️ إعدادات المتصل: {st.session_state.center}"):
        live_data = get_live_status() # جلب البيانات فور فتح الترس
        
        # تصفية المراكز والأطباء
        active_centers = list(set([s['center_name'] for s in live_data if not s['is_doctor']]))
        active_doctors = sum(1 for s in live_data if s['is_doctor'])
        
        c_col, d_col = st.columns(2)
        with c_col:
            st.write(f"🟢 **المراكز النشطة ({len(active_centers)}):**")
            if active_centers:
                for c in active_centers: st.write(f"- {c}")
            else: st.write("لا توجد مراكز أخرى")
        with d_col:
            st.write(f"👨‍⚕️ **أطباء الاختصاص:** {active_doctors}")
            
        st.divider()
        if st.button("🔴 تسجيل خروج نهائي"):
            supabase.table("active_sessions").delete().eq("center_name", st.session_state.center).execute()
            st.session_state.clear(); st.rerun()

    # التبويبات
    tabs = st.tabs(["🔍 السجل الموحد"]) if st.session_state.is_doctor else st.tabs(["🔍 السجل الموحد", "📝 إضافة مصاب", "💬 الدردشة"])

    # --- تبويب السجل ---
    with tabs[0]:
        search_q = st.text_input("🔍 ابحث عن اسم:")
        data = supabase.table("patients").select("*").ilike("full_name", f"%{search_q}%").order("created_at", desc=True).execute()
        if data.data:
            for p in data.data:
                st.markdown(f'<div class="patient-card"><span class="p-title">👤 {p["full_name"]}</span><span class="p-info">| 🔬 {p["infection_type"]}</span><span class="p-info">| 🏢 {p["entry_center"]}</span></div>', unsafe_allow_html=True)
                with st.expander(f"فتح تفاصيل: {p['full_name']}"):
                    st.write(f"🎂 العمر: {p.get('age','--')} | 📱 الهاتف: {p.get('phone_number','--')}")
                    st.write(f"📍 العنوان: {p.get('address','--')} | ⚙️ الجهاز: {p['test_device']}")
                    if not st.session_state.is_doctor:
                        if st.session_state.is_admin or p['entry_center'] == st.session_state.center:
                            st.divider()
                            col_d, col_e = st.columns(2)
                            with col_d:
                                if st.button("🗑️ حذف السجل", key=f"del_{p['id']}"):
                                    supabase.table("patients").delete().eq("id", p['id']).execute(); st.rerun()
                            with col_e:
                                with st.form(f"edit_{p['id']}"):
                                    en = st.text_input("الاسم:", value=p['full_name'])
                                    ep = st.text_input("الهاتف:", value=p.get('phone_number'))
                                    if st.form_submit_button("حفظ"):
                                        supabase.table("patients").update({"full_name": en, "phone_number": ep}).eq("id", p['id']).execute(); st.rerun()
        else: st.info("لا توجد سجلات.")

    # --- تبويب الإضافة (مع تصفير الخانات) ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            with st.form("add_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1: n = st.text_input("الاسم الرباعي:"); a = st.text_input("العمر:"); ph = st.text_input("الهاتف:")
                with c2: ad = st.text_input("العنوان:"); i = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"]); t = st.selectbox("الجهاز:", ["Strips", "ELISA", "PCR"])
                dt = st.date_input("التاريخ:", value=date.today())
                if st.form_submit_button("🚀 إرسال إلى قاعدة البيانات المركزية"):
                    if n:
                        supabase.table("patients").insert({"full_name":n,"age":a,"phone_number":ph,"address":ad,"infection_type":i,"test_device":t,"test_date":str(dt),"entry_center":st.session_state.center}).execute()
                        st.success("✅ تم الإرسال بنجاح!"); st.balloons()
        
        # --- الدردشة ---
        with tabs[2]:
            # نظام الـ 100 رسالة
            res_m = supabase.table("chat_messages").select("id").order("created_at", desc=True).execute()
            if len(res_m.data) > 100:
                cutoff = res_m.data[99]['id']
                supabase.table("chat_messages").delete().lt("id", cutoff).execute()
                
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(100).execute()
            for m in reversed(msgs.data):
                st.markdown(f'<div class="chat-bubble"><small style="color:#00a884;">{m["username"]}</small><br>{m["message"]}</div>', unsafe_allow_html=True)
            with st.form("send_msg", clear_on_submit=True):
                txt = st.text_input("رسالة...")
                if st.form_submit_button("إرسال") and txt:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": txt}).execute(); st.rerun()
