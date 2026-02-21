import streamlit as st
import pandas as pd
import re
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import requests

def save_to_google_form(df, feedback):
    # כאן צריך להדביק את ה-URL של ה-Form (נמצא ב-"Get pre-filled link")
    # וגם את ה-IDs של השאלות. 
    # אם תרצה עזרה במציאתם, רק תגיד.
    
    # זהו קוד פשוט ששולח את הנתונים בבת אחת:
    form_url = "כאן_מדביקים_את_כתובת_הטופס/formResponse"
    
    for _, row in df.iterrows():
        payload = {
            "entry.123456": row['מוצר'],      # מספר ה-ID של שאלת מוצר
            "entry.789012": row['קטגוריה'],  # מספר ה-ID של שאלת קטגוריה
            "entry.345678": row['מחיר'],     # מספר ה-ID של שאלת מחיר
            "entry.901234": feedback         # מספר ה-ID של שאלת פידבק
        }
        requests.post(form_url, data=payload)
        
st.set_page_config(page_title="מנתח הקבלות המשפחתי", layout="centered")

# עיצוב RTL ושיפור נראות
st.markdown("""
    <style>
    .reportview-container .main .block-container { direction: rtl; text-align: right; }
    div[data-testid="stText"] { direction: rtl; text-align: right; }
    div[data-testid="stDataFrame"] { direction: rtl; }
    h1, h2, h3, p, span, label { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# חיבור לגוגל שיטס
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛒 סיכום קניות משפחתי")

if 'categories' not in st.session_state:
    st.session_state.categories = ['ירקות ופירות', 'בשר ודגים', 'חלביה', 'חטיפים ומתוקים', 'ניקיון וטואלטיקה', 'מזווה ובישול']

def categorize(name):
    cat_map = {
        'ירקות ופירות': ['עגבניה', 'מלפפון', 'בצל', 'לימון', 'חסה', 'אבוקדו', 'פטריות', 'בננות', 'אוכמניות', 'שום', 'תירס', 'פלפל'],
        'בשר ודגים': ['עוף', 'שניצל', 'כנפיים', 'חזה', 'עטרה'],
        'חלביה': ['גבינה', 'יוגורט', 'חמאה', 'שמנת', 'קשקבל', 'מנצגו', 'גאודה', 'פרוביוטי'],
        'חטיפים ומתוקים': ['במבה', 'ופל', 'כריות', 'נייטשר ואלי', 'נוגט', 'רבע לשבע', 'פתיבר'],
        'ניקיון וטואלטיקה': ['נייר טואלט', 'דאב', 'מטליות', 'פדים', 'טישו', 'ניקוי', 'לילי', 'קלינקס'],
        'מזווה ובישול': ['שומשום', 'קוקוס', 'ממרח', 'תבנית', 'שקית', 'מזרח']
    }
    for cat, keywords in cat_map.items():
        if any(key in name for key in keywords):
            return cat
    return 'שונות'

raw_text = st.text_area("הדבקו את טקסט הקבלה כאן:", height=150)

if st.button("נתח קבלה"):
    if raw_text:
        lines = raw_text.split('\n')
        data = []
        unknown_items = []
        for i, line in enumerate(lines):
            if "₪" in line and i > 0:
                try:
                    price_match = re.search(r"₪\s?(\d+\.\d+)", line)
                    if price_match:
                        price = float(price_match.group(1))
                        name = lines[i-1].strip()
                        if not name or name[0].isdigit(): name = lines[i-2].strip()
                        if any(x in name for x in ["סה\"כ", "סכום לתשלום", "ב-", "הנחה", "ויזה", "מזומן"]): continue
                        
                        cat = categorize(name)
                        data.append({"מוצר": name, "קטגוריה": cat, "מחיר": price})
                        if cat == 'שונות': unknown_items.append(name)
                except: continue
        st.session_state.df = pd.DataFrame(data)
        st.session_state.unknown_items = unknown_items

# טיפול במוצרים לא מזוהים
if 'unknown_items' in st.session_state and st.session_state.unknown_items:
    with st.expander("🔍 מצטער, לא הצלחתי לסווג את המוצרים הבאים, תוכל לעזור לי ללמוד?", expanded=True):
        for item in st.session_state.unknown_items:
            selected_cat = st.selectbox(f"סיווג עבור: {item}", st.session_state.categories + ["אחר..."], key=item)
            if selected_cat == "אחר...":
                new_cat = st.text_input(f"קטגוריה חדשה ל-{item}", key=f"new_{item}")
                if new_cat: selected_cat = new_cat
            st.session_state.df.loc[st.session_state.df['מוצר'] == item, 'קטגוריה'] = selected_cat
        
        if st.button("סיימתי לסווג, הצג דוח"):
            st.session_state.unknown_items = []
            st.rerun()

# הצגת הדוח
if 'df' in st.session_state and not st.session_state.df.empty:
    df = st.session_state.df
    st.success(f"סה\"כ לתשלום: ₪{df['מחיר'].sum():.2f}")
    
    # טבלה בסדר המבוקש
    st.table(df[['מוצר', 'קטגוריה', 'מחיר']])
    
    fig = px.pie(df, values='מחיר', names='קטגוריה', hole=0.3, title="התפלגות הוצאות")
    st.plotly_chart(fig)

    # משוב ושמירה
    st.divider()
    feedback = st.text_area("משוב למפתח (אופציונלי):")
    if st.button("שמור נתונים ושלח משוב"):
        save_to_google_form(df, feedback)
