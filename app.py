import streamlit as st
from supabase import create_client
from datetime import datetime, date
import time

# --- 1. إعدادات الاتصال المركزية ---
URL = "https://ngtkphoadvcvwqtuzawu.supabase.co"
KEY = "sb_publishable_2gEHqJ7SDmBVIYIl48a9Bg_XaNIz2za"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"فشل الاتصال بقاعدة البيانات: {e}")

# --- 2. التنسيق البصري (CSS) - حل مشكلة الخط الطولي والواجهة السوداء ---
st.set_page_config(page_title="نظام مختبرات حديثة", layout="wide")

st.markdown("""<style>
    /* الواجهة الداكنة */
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    
    /* منع التداخل والخطوط الطولية */
    .main .block-container { padding-top: 2rem; direction: rtl; text-align: right; }
    div[data-testid="stVerticalBlock"] > div { direction: rtl !important; }

    /* تنسيق الأزرار */
    .stButton>button { 
        width: 100%; border-radius: 10px; font-weight: bold; 
        background-color: #1e3a8a; color: white !important; height: 3.2em;
        border: none; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2563eb; transform: scale(1.02); }

    /* حقول الإدخال */
    .stTextInput input, .stSelectbox div { background-color: #1e293b !important; color: white !important; }

    /* إخفاء شعارات ستريمليت */
    #MainMenu, footer, header {visibility: hidden;}
    </style>""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية (Logic Functions) ---

def save_patient_data(name, addr, inf, dev, dt, note):
    """حفظ بيانات المراجع في السحابة"""
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

def push_chat_message(text):
    """إرسال رسالة للدردشة الفورية"""
    if text.strip():
        try:
            supabase.table("chat_messages").insert({
                "username": st.session_state.center, 
                "message": text
            }).execute()
            return True
        except:
            return False
    return False

# --- 4. نظام الحماية وتسجيل الدخول ---

if 'logged_in' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #3b82f6;'>🏥 نظام إدارة مختبرات قضاء حديثة</h1>", unsafe_allow_html=True)
    
    col_x, col_y, col_z = st.columns([1, 2, 1])
    with col_y:
        st.markdown("<div style='background: #1e293b; padding: 25px; border-radius: 15px; border: 1px solid #334155;'>", unsafe_allow_html=True)
        centers_list = [
            'مركز مستشفى حديثة للتبرع بالدم', 'مختبر مستشفى حديثة للفحوصات الفيروسية',
            'المركز التخصصي للاسنان', 'مركز صحي حديثة', 'مركز صحي بروانه', 
            'مركز صحي حقلانية', 'مركز صحي خفاجية', 'مركز صحي بني داهر',
            'مركز صحي الوس', 'مركز صحي السكران', 'أطباء الاختصاص'
        ]
        u_center = st.selectbox("اختر جهة العمل:", centers_list)
        u_code = st.text_input("رمز الدخول السري:", type="password")
        
        if st.button("تسجيل الدخول"):
            res = supabase.table("center_access").select("*").eq("center_name", u_center).eq("access_code", u_code).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.center = u_center
                st.session_state.is_doctor = "أطباء الاختصاص" in u_center
                st.rerun()
            else:
                st.error("⚠️ الرمز السري غير صحيح!")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. الواجهة التشغيلية (بعد النجاح في الدخول) ---

else:
    # القائمة الجانبية
    with st.sidebar:
        st.markdown(f"### 🏢 {st.session_state.center}")
        st.write("---")
        if st.button("🔴 تسجيل الخروج"):
            st.session_state.clear()
            st.rerun()
        st.caption("نظام الربط المختبري v3.0")

    # تحديد التبويبات بناءً على هوية المستخدم
    if st.session_state.is_doctor:
        # الطبيب لا يرى الدردشة ولا الإضافة، فقط السجل
        main_tabs = st.tabs(["🔍 السجل العام والبحث المركزي"])
    else:
        # المراكز المختبرية ترى كل شيء
        main_tabs = st.tabs(["📝 تسجيل مراجع جديد", "🔍 السجل العام والبحث", "💬 التواصل المباشر"])

    # --- أ: تبويب الإضافة (للمراكز فقط) ---
    if not st.session_state.is_doctor:
        with main_tabs[0]:
            st.markdown("### 📝 إدخال بيانات إصابة جديدة")
            with st.form("entry_form", clear_on_submit=True):
                r1, r2 = st.columns(2)
                with r1:
                    name = st.text_input("الاسم الرباعي للمراجع:")
                    address = st.text_input("عنوان السكن:")
                    inf_type = st.selectbox("نوع الإصابة:", ["HCV", "HBsAg", "HIV", "Syphilis"])
                with r2:
                    dev_type = st.selectbox("جهاز الفحص:", ["Strips", "ELISA", "PCR", "VITEK"])
                    t_date = st.date_input("تاريخ الفحص:", value=date.today())
                    notes = st.text_input("ملاحظات إضافية:")
                
                if st.form_submit_button("حفظ وإرسال"):
                    if name and address:
                        if save_patient_data(name, address, inf_type, dev_type, t_date, notes):
                            st.success(f"✅ تم حفظ السجل بنجاح لـ: {name}")
                        else:
                            st.error("❌ فشل الاتصال بالسيرفر")
                    else:
                        st.warning("⚠️ يرجى كتابة الاسم والعنوان")

    # --- ب: تبويب السجل والبحث (متاح للكل - يعرض الكل تلقائياً) ---
    search_idx = 0 if st.session_state.is_doctor else 1
    with main_tabs[search_idx]:
        st.markdown("### 🔍 أرشيف المرضى المركزي")
        search_term = st.text_input("بحث بالاسم (اتركه فارغاً لعرض كل السجلات):")
        
        # جلب البيانات
        if search_term:
            p_res = supabase.table("patients").select("*").ilike("full_name", f"%{search_term}%").order("created_at", desc=True).execute()
        else:
            p_res = supabase.table("patients").select("*").order("created_at", desc=True).execute()
        
        if p_res.data:
            st.info(f"📊 عدد المراجعين المسجلين: {len(p_res.data)}")
            for p in p_res.data:
                with st.container():
                    st.markdown(f"<div style='background:#1e293b; padding:15px; border-radius:10px; margin-bottom:10px; border-right: 5px solid #3b82f6;'>", unsafe_allow_html=True)
                    st.markdown(f"#### 👤 {p['full_name']}")
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"📍 **السكن:** {p['address']}")
                    c2.write(f"🔬 **التشخيص:** {p['infection_type']}")
                    c3.write(f"📅 **التاريخ:** {p['test_date']}")
                    st.markdown(f"<small>🏢 جهة الإدخال: {p['entry_center']} | 📝 ملاحظات: {p['pcr_result']}</small>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("🔎 لا توجد نتائج مطابقة.")

    # --- ج: تبويب الدردشة والمتصلين (مخفي عن الأطباء) ---
    if not st.session_state.is_doctor:
        with main_tabs[2]:
            st.markdown("### 💬 غرفة التنسيق المختبري")
            
            # معرفة المراكز المتصلة (التي أرسلت رسائل مؤخراً)
            recent_chats = supabase.table("chat_messages").select("username").order("created_at", desc=True).limit(50).execute()
            online_now = list(set([m['username'] for m in recent_chats.data]))
            
            # عرض عداد المتصلين
            st.markdown(f"🟢 **المراكز النشطة الآن ({len(online_now)}):** " + " ، ".join(online_now))
            st.write("---")

            # عرض المحادثة باستخدام نظام الفقاعات الرسمي
            chat_data = supabase.table("chat_messages").select("*").order("created_at", desc=True).limit(30).execute()
            for m in reversed(chat_data.data):
                with st.chat_message("user", avatar="🏢"):
                    st.write(f"**{m['username']}**")
                    st.write(m['message'])
                    st.caption(f"🕒 {m['created_at'][11:16]}")

            # مدخل الرسائل
            with st.form("chat_form", clear_on_submit=True):
                mc, bc = st.columns([5, 1])
                new_msg = mc.text_input("اكتب رسالة للمختبرات...", label_visibility="collapsed")
                if bc.form_submit_button("إرسال") and new_msg:
                    if push_chat_message(new_msg):
                        st.rerun()
