import streamlit as st
from supabase import create_client
from datetime import datetime, date
import time

# --- 1. إعدادات الاتصال الآمن (Supabase) ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"فشل الاتصال: {e}")

# --- 2. التصميم (CSS) لمنع الخطوط الطولية وتحسين الواجهة ---
st.set_page_config(page_title="نظام مختبرات حديثة المتكامل", layout="wide")

st.markdown("""<style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .main .block-container { padding-top: 2rem; direction: rtl; text-align: right; }
    div[data-testid="stVerticalBlock"] > div { direction: rtl !important; }
    .stButton>button { 
        width: 100%; border-radius: 10px; font-weight: bold; 
        background-color: #1e3a8a; color: white !important; height: 3em;
    }
    /* إخفاء القوائم العلوية والسفلية لزيادة المساحة */
    #MainMenu, footer, header {visibility: hidden;}
    </style>""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية (Logic) ---

def save_new_entry(name, addr, inf, dev, dt, note):
    """دالة حفظ بيانات المريض"""
    try:
        data = {
            "full_name": name, "address": addr, "test_date": str(dt),
            "infection_type": inf, "test_device": dev, 
            "pcr_result": note, "entry_center": st.session_state.center
        }
        supabase.table("patients").insert(data).execute()
        return True
    except:
        return False

def post_chat(msg_text):
    """دالة إرسال رسالة دردشة"""
    if msg_text.strip():
        try:
            supabase.table("chat_messages").insert({
                "username": st.session_state.center, 
                "message": msg_text
            }).execute()
            return True
        except:
            return False
    return False

# --- 4. نظام تسجيل الدخول ---

if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>🏥 نظام مختبرات قضاء حديثة المركزية</h1>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        centers = [
            'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
            'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
            'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
            'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص'
        ]
        sel_center = st.selectbox("اختر الجهة المستخدمة:", centers)
        pass_key = st.text_input("كود الدخول السري:", type="password")
        
        if st.button("دخول للنظام"):
            res = supabase.table("center_access").select("*").eq("center_name", sel_center).eq("access_code", pass_key).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.center = sel_center
                st.session_state.is_doctor = "أطباء الاختصاص" in sel_center
                st.rerun()
            else:
                st.error("الكود غير صحيح")

# --- 5. الواجهة الرئيسية بعد الدخول ---

else:
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.center}")
        if st.button("🚪 خروج"):
            st.session_state.clear()
            st.rerun()

    # إنشاء التبويبات
    if st.session_state.is_doctor:
        tabs = st.tabs(["🔍 السجل العام والبحث", "💬 التواصل المباشر"])
    else:
        tabs = st.tabs(["📝 تسجيل مراجع جديد", "🔍 السجل العام والبحث", "💬 التواصل المباشر"])

    # --- تبويب الإدخال ---
    if not st.session_state.is_doctor:
        with tabs[0]:
            st.subheader("📝 تسجيل مراجع جديد")
            with st.form("entry_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    i_name = st.text_input("الاسم الرباعي للمراجع:")
                    i_addr = st.text_input("عنوان السكن:")
                    i_inf = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with c2:
                    i_dev = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    i_date = st.date_input("تاريخ الفحص:", value=date.today())
                    i_note = st.text_input("ملاحظات إضافية:")
                
                if st.form_submit_button("إرسال البيانات للقاعدة المركزية"):
                    if i_name and i_addr:
                        if save_new_entry(i_name, i_addr, i_inf, i_dev, i_date, i_note):
                            st.success(f"تم الحفظ بنجاح: {i_name}")
                        else:
                            st.error("فشل الحفظ")
                    else:
                        st.warning("يرجى ملء الحقول")

    # --- تبويب السجل العام والبحث (تعديل: عرض الكل تلقائياً) ---
    s_idx = 0 if st.session_state.is_doctor else 1
    with tabs[s_idx]:
        st.subheader("🔍 استعلام فوري عن مراجع")
        s_query = st.text_input("ادخل الاسم للبحث (اتركه فارغاً لعرض الكل):")
        
        if s_query:
            p_data = supabase.table("patients").select("*").ilike("full_name", f"%{s_query}%").order("created_at", desc=True).execute()
        else:
            # عرض الكل تلقائياً عند فتح التبويب
            p_data = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if p_data.data:
            st.write(f"📊 تم العثور على {len(p_data.data)} سجلات")
            for p in p_data.data:
                with st.container():
                    st.markdown(f"### 👤 {p['full_name']}")
                    ca, cb, cc = st.columns(3)
                    ca.markdown(f"📍 **السكن:** {p['address']}")
                    cb.markdown(f"🔬 **التشخيص:** {p['infection_type']}")
                    cc.markdown(f"📅 **التاريخ:** {p['test_date']}")
                    st.info(f"📝 **ملاحظات:** {p['pcr_result']} | 🏢 **المركز الموثق:** {p['entry_center']}")
                    st.divider()
        else:
            st.info("لا توجد سجلات مطابقة")

    # --- تبويب الدردشة (الحل النهائي لمنع ظهور الكود النصي) ---
    c_idx = 1 if st.session_state.is_doctor else 2
    with tabs[c_idx]:
        st.subheader("💬 منصة التواصل الفوري بين المختبرات")
        
        # جلب الرسائل
        chat_res = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
        
        # استخدام st.chat_message لعرض الرسائل بشكل احترافي ومنع ظهور كود HTML
        for m in reversed(chat_res.data):
            with st.chat_message("user", avatar="🏢"):
                st.write(f"**{m['username']}**")
                st.write(m['message'])
                st.caption(f"توقيت الإرسال: {m['created_at'][11:16]}")
        
        # حقل الإرسال
        with st.form("chat_input_form", clear_on_submit=True):
            chat_col, btn_col = st.columns([5, 1])
            with chat_col:
                new_m = st.text_input("اكتب رسالتك هنا...", label_visibility="collapsed")
            with btn_col:
                if st.form_submit_button("إرسال") and new_m:
                    if post_chat(new_m):
                        st.rerun()
