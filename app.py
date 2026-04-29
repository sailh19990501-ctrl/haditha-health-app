import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. إعدادات قاعدة البيانات والاتصال ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception:
    st.error("فشل الاتصال بالسيرفر")

# --- 2. التنسيق الظاهري (CSS) لإلغاء الكتابة الطولية وترتيب الدردشة ---
st.set_page_config(page_title="أرشيف المصابين", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; max-width: 100% !important; }
    
    /* بطاقة المريض - عريضة وواضحة */
    .patient-card {
        background: #1e293b; padding: 25px; border-radius: 12px;
        margin-bottom: 20px; border-right: 10px solid #3b82f6; width: 100%;
    }
    .patient-card h3 { color: #60a5fa; margin-bottom: 10px; }

    /* صندوق الدردشة (WhatsApp Style) */
    .chat-container {
        height: 450px; overflow-y: auto; 
        background: #0b141a; padding: 15px; border-radius: 12px;
        display: flex; flex-direction: column; gap: 12px;
        border: 1px solid #202c33; margin-bottom: 10px;
    }
    .chat-bubble {
        background: #202c33; color: white; padding: 10px 15px;
        border-radius: 12px; width: fit-content; max-width: 80%;
    }
    .chat-sender { color: #00a884; font-weight: bold; font-size: 0.85em; }

    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    #MainMenu, footer, header {visibility: hidden;}
</style>""", unsafe_allow_html=True)

# --- 3. بوابة الدخول مع الرموز السرية المحددة ---
if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🏥 أرشيف المصابين بالأمراض الانتقالية</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        access_map = {
            'مركز مصرف الدم الرئيسي': 'HAD-BLOOD-2026',
            'مختبر مستشفى حديثة للفحوصات الفيروسية': 'HAD-VIRUS-2026',
            'المركز التخصصي للاسنان': 'HAD-DENT-2026',
            'مركز صحي بروانه': 'BAR-HEALTH-2026',
            'أطباء الاختصاص (طبيب الاختصاص)': 'DOC-READ-2026'
        }
        u_center = st.selectbox("يرجى اختيار جهة العمل:", list(access_map.keys()))
        u_code = st.text_input("الرمز السري الخاص بالمركز:", type="password")
        
        if st.button("دخول للنظام"):
            if u_code == access_map[u_center]:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                # الأدمن (مصرف الدم والفيروسية)
                st.session_state.is_admin = u_center in ['مركز مصرف الدم الرئيسي', 'مختبر مستشفى حديثة للفحوصات الفيروسية']
                # الطبيب (مشاهد فقط)
                st.session_state.is_doctor = (u_center == 'أطباء الاختصاص (طبيب الاختصاص)')
                st.rerun()
            else:
                st.error("❌ الرمز السري غير صحيح، حاول مرة أخرى.")

else:
    # --- التبويبات حسب الصلاحية ---
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 سجل المراجعين والبحث"])
    else:
        tabs = st.tabs(["🔍 السجل والبحث", "📝 إضافة إصابة جديدة", "💬 الدردشة الفورية"])

    # --- 1. تبويب السجل والبحث (متاح للكل، لكن التحكم للأدمن والمراكز) ---
    with tabs[0]:
        st.subheader("🔍 قاعدة بيانات المصابين")
        q = st.text_input("ابحث عن (اسم المصاب الرباعي):")
        
        # استعلام البيانات
        if q:
            res = supabase.table("patients").select("*").ilike("full_name", f"%{q}%").order("created_at", desc=True).execute()
        else:
            res = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if res.data:
            for p in res.data:
                # التحقق من صلاحية الحذف والتعديل
                can_manage = st.session_state.is_admin or (p['entry_center'] == st.session_state.center)
                
                st.markdown(f"""<div class="patient-card">
                    <h3>👤 {p['full_name']}</h3>
                    <p>📱 <b>رقم الهاتف:</b> {p.get('phone_number', 'غير متوفر')} | 📍 <b>العنوان:</b> {p.get('address', 'غير محدد')}</p>
                    <p>🔬 <b>نوع الإصابة:</b> {p['infection_type']} | ⚙️ <b>التقنية:</b> {p['test_device']}</p>
                    <p>📅 <b>تاريخ الفحص:</b> {p['test_date']} | 🏥 <b>جهة الإدخال:</b> {p['entry_center']}</p>
                    <p>📝 <b>الملاحظات:</b> {p['pcr_result']}</p>
                </div>""", unsafe_allow_html=True)
                
                # إذا لم يكن طبيباً، وعنده صلاحية
                if not st.session_state.is_doctor and can_manage:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"🗑️ مسح السجل", key=f"del_{p['id']}"):
                            supabase.table("patients").delete().eq("id", p['id']).execute()
                            st.rerun()
                    with c2:
                        with st.expander("🛠️ تعديل البيانات"):
                            with st.form(f"edit_{p['id']}"):
                                en = st.text_input("الاسم الرباعي:", value=p['full_name'])
                                eph = st.text_input("رقم الهاتف:", value=p.get('phone_number', ''))
                                ead = st.text_input("العنوان:", value=p.get('address', ''))
                                ei = st.selectbox("الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"], index=0)
                                et = st.date_input("التاريخ:", value=datetime.strptime(p['test_date'], '%Y-%m-%d').date())
                                if st.form_submit_button("تحديث السجل"):
                                    supabase.table("patients").update({
                                        "full_name": en, "phone_number": eph, "address": ead,
                                        "infection_type": ei, "test_date": str(et)
                                    }).eq("id", p['id']).execute()
                                    st.rerun()
        else: st.info("لا توجد نتائج مطابقة.")

    # --- التبويبات الإضافية (تختفي عند الطبيب) ---
    if not st.session_state.is_doctor:
        with tabs[1]:
            st.subheader("📝 إدخال بيانات إصابة جديدة")
            with st.form("new_entry", clear_on_submit=True):
                col_x, col_y = st.columns(2)
                with col_x:
                    n_name = st.text_input("الاسم الرباعي للمراجع:")
                    n_phone = st.text_input("رقم الهاتف:")
                    n_addr = st.text_input("عنوان السكن بالتفصيل:")
                with col_y:
                    n_inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                    n_tech = st.selectbox("تقنية الفحص:", ["Strips", "ELISA", "PCR"])
                    n_date = st.date_input("تاريخ الفحص (تقويم):", value=date.today())
                
                n_note = st.text_area("ملاحظات إضافية:")
                if st.form_submit_button("حفظ البيانات وإرسال"):
                    if n_name:
                        supabase.table("patients").insert({
                            "full_name": n_name, "phone_number": n_phone, "address": n_addr,
                            "infection_type": n_inf, "test_device": n_tech, "test_date": str(n_date),
                            "pcr_result": n_note, "entry_center": st.session_state.center
                        }).execute()
                        st.success("✅ تم الحفظ بنجاح")
                    else: st.warning("يرجى كتابة الاسم")

        with tabs[2]:
            st.subheader("💬 منصة التواصل بين المراكز")
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            msgs = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(40).execute()
            for m in reversed(msgs.data):
                st.markdown(f'<div class="chat-bubble"><div class="chat-sender">{m["username"]}</div>{m["message"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            with st.form("chat_box", clear_on_submit=True):
                txt = st.text_input("اكتب رسالتك...")
                if st.form_submit_button("إرسال") and txt:
                    supabase.table("chat_messages").insert({"username": st.session_state.center, "message": txt}).execute()
                    st.rerun()

    st.sidebar.button("🔴 تسجيل خروج", on_click=lambda: st.session_state.clear())
