import datetime
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Job Tracker Pro", layout="wide")

FILE_PATH = "jobs.csv"

# הגדרת העמודות הראשיות שיישמרו ב-CSV
DATA_COLUMNS = [
    "תאריך",
    "שם החברה",
    "תפקיד",
    "סטאטוס",
    "קישור",
    "הערות",
]

# טעינת נתונים מקובץ CSV או יצירת DataFrame חדש
if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH)
    # לוודא שכל העמודות הנדרשות קיימות
    for col in DATA_COLUMNS:
        if col not in df.columns:
            df[col] = ""
else:
    df = pd.DataFrame(columns=DATA_COLUMNS)

st.title("💼 מערכת מעקב משרות מתקדמת - Job Tracker Pro")

# --- חלק 1: מדדים וסטטיסטיקות ---
st.markdown("### 📊 תמונת מצב")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

total_jobs = len(df)
in_progress = len(
    df[
        df["סטאטוס"].isin(
            ["ראיון טלפוני", "ראיון מקצועי", "מבחן בית", "הצעה"]
        )
    ]
)
applied = len(df[df["סטאטוס"] == "נשלח קורות חיים"])
rejected = len(df[df["סטאטוס"] == "דחייה"])

col_m1.metric('סה"כ משרות', total_jobs)
col_m2.metric("בתהליך מתקדם", in_progress)
col_m3.metric('נשלחו קו"ח', applied)
col_m4.metric("דחיות", rejected)

st.markdown("---")

# --- חלק 2: טופס הוספת משרה ---
with st.expander("➕ הוספת משרה חדשה", expanded=True):
    with st.form("job_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            company = st.text_input("שם החברה *")
            position = st.text_input("תפקיד *")
        with c2:
            status = st.selectbox(
                "סטאטוס",
                [
                    "נשלח קורות חיים",
                    "ראיון טלפוני",
                    "ראיון מקצועי",
                    "מבחן בית",
                    "הצעה",
                    "דחייה",
                ],
            )
            apply_date = st.date_input("תאריך הגשה", datetime.date.today())
        with c3:
            link = st.text_input("קישור למשרה")
            notes = st.text_area("הערות", height=68)

        submitted = st.form_submit_button("שמור משרה")

        if submitted:
            if company and position:
                new_row = pd.DataFrame(
                    [
                        {
                            "תאריך": apply_date.strftime("%Y-%m-%d"),
                            "שם החברה": company,
                            "תפקיד": position,
                            "סטאטוס": status,
                            "קישור": link,
                            "הערות": notes,
                        }
                    ]
                )
                df = pd.concat([df, new_row], ignore_index=True)
                df[DATA_COLUMNS].to_csv(FILE_PATH, index=False)
                st.success(f"המשרה {position} בחברת {company} נשמרה!")
                st.rerun()
            else:
                st.error("יש למלא שדות חובה (שם חברה ותפקיד).")

st.markdown("---")

# --- חלק 3: סיידבאר לסינון וחיפוש ---
st.sidebar.header("🔍 סינון וחיפוש")
search_term = st.sidebar.text_input("חיפוש לפי חברה / תפקיד")
status_filter = st.sidebar.multiselect(
    "סינון לפי סטאטוס", options=list(df["סטאטוס"].unique()) if not df.empty else []
)

filtered_df = df.copy()

if search_term and not filtered_df.empty:
    filtered_df = filtered_df[
        filtered_df["שם החברה"].astype(str).str.contains(search_term, case=False, na=False)
        | filtered_df["תפקיד"].astype(str).str.contains(search_term, case=False, na=False)
    ]

if status_filter and not filtered_df.empty:
    filtered_df = filtered_df[filtered_df["סטאטוס"].isin(status_filter)]

# --- חלק 4: טבלאות ועריכה בזמן אמת ---
st.subheader("📋 ניהול ועריכת משרות")
st.caption(
    "ניתן לערוך נתונים ישירות בטבלה, לסמן תיבת 'למחיקה?' בשורות שתרצי להסיר, וללחוץ על 'שמור שינויים'."
)

if not filtered_df.empty:
    # יצירת עמודת מחיקה בוליאנית נקייה בזיכרון
    display_df = filtered_df.copy()
    display_df.insert(0, "למחיקה?", False)

    edited_df = st.data_editor(
        display_df,
        column_config={
            "למחיקה?": st.column_config.CheckboxColumn("למחיקה?", default=False),
            "קישור": st.column_config.LinkColumn("קישור למשרה"),
            "סטאטוס": st.column_config.SelectboxColumn(
                "סטאטוס",
                options=[
                    "נשלח קורות חיים",
                    "ראיון טלפוני",
                    "ראיון מקצועי",
                    "מבחן בית",
                    "הצעה",
                    "דחייה",
                ],
                required=True,
            ),
        },
        disabled=["תאריך"],
        use_container_width=True,
        num_rows="dynamic",
        key="data_editor_widget",
    )

    if st.button("💾 שמור שינויים ועדכן"):
        # סינון שורות שסומנו למחיקה
        keep_rows = edited_df[edited_df["למחיקה?"] == False]
        
        # שמירת רק העמודות המקוריות ל-CSV
        save_df = keep_rows[DATA_COLUMNS]
        save_df.to_csv(FILE_PATH, index=False)
        
        st.success("השינויים נשמרו בהצלחה!")
        st.rerun()
else:
    st.info("אין משרות להצגה כרגע. תוכל/י להוסיף משרה חדשה בטופס למעלה.")

st.markdown("---")

# --- חלק 5: ויזואליזציית נתונים ---
if not df.empty:
    st.subheader("📈 ניתוח התפלגות המשרות")
    status_counts = df["סטאטוס"].value_counts().reset_index()
    status_counts.columns = ["סטאטוס", "כמות"]

    fig = px.bar(
        status_counts,
        x="סטאטוס",
        y="כמות",
        text="כמות",
        color="סטאטוס",
        title="חלוקת משרות לפי סטאטוס",
    )
    st.plotly_chart(fig, use_container_width=True)
