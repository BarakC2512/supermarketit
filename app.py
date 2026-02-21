import streamlit as st
import pandas as pd
import re
import plotly.express as px

# הגדרות דף בסיסיות
st.set_page_config(page_title="מנתח הקבלות המשפחתי", layout="centered")

# הזרקת CSS לעברית (RTL)
st.markdown("""
    <style>
    .reportview-container .main .block-container { direction: rtl; text-align: right; }
    div[data-testid="stText"] { direction: rtl; text-align: right; }
    h1, h2, h3, p, span { direction: rtl; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛒 סיכום קניות משפחתי")
st.write("הדביקו את טקסט הקבלה מ-Pairzon כאן למטה:")

# תיבת טקסט להזנת הנתונים
raw_text = st.text_area("הדבק כאן:", height=200, placeholder="תל אביב... סה\"כ 847.77...")

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

if st.button("נתח קבלה"):
    if raw_text:
        lines = raw_text.split('\n')
        data = []
        for i, line in enumerate(lines):
            if "₪" in line and i > 0:
                try:
                    # חילוץ המחיר מהשורה
                    price_match = re.search(r"₪\s?(\d+\.\d+)", line)
                    if price_match:
                        price = float(price_match.group(1))
                        # שם המוצר נמצא בדר"כ שורה או שתיים מעל
                        name = lines[i-1].strip()
                        if not name or name[0].isdigit():
                            name = lines[i-2].strip()
                        
                        # סינון שורות סיכום והנחות
                        if any(x in name for x in ["סה\"כ", "סכום לתשלום", "ב-", "הנחה", "ויזה", "מזומן"]):
                            continue
                            
                        data.append({"מוצר": name, "מחיר": price, "קטגוריה": categorize(name)})
                except:
                    continue
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            st.success(f"נמצאו {len(df)} מוצרים. סה\"כ זוהה: ₪{df['מחיר'].sum():.2f}")
            
            # תצוגת גרף עוגה
            fig = px.pie(df, values='מחיר', names='קטגוריה', hole=0.3, title="הוצאות לפי קטגוריה")
            st.plotly_chart(fig)
            
            # טבלה מפורטת
            st.subheader("פירוט מוצרים")
            st.dataframe(df[['קטגוריה', 'מוצר', 'מחיר']].sort_values(by='קטגוריה'), use_container_width=True)
        else:
            st.error("לא הצלחתי לקרוא מוצרים. וודאו שהדבקתם את כל הטקסט מהקבלה.")
