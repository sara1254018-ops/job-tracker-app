import datetime
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Job Tracker Pro", layout="wide")

FILE_PATH = "jobs.csv"

# טעינת נתונים מקובץ CSV או יצירת DataFrame חדש
if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH)
else:
    df = pd.DataFrame(
        columns=[
            "מחיקה",
            "תאריך",
            "שם החברה",
            "תפקיד",
            "סטאטוס",
            "קישור",
            "הערות",
        ]
    )

# ודאות שקיימת עמודת מחיקה במבנה הנתונים ושהיא מסוג Boolean
if "מחיקה" not in df.columns:
    df.insert(0, "מחיקה", False)

df["מחיקה"] = df["מחיקה"].astype(bool)

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
                            "מחיקה": False,
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
                df.to_csv(FILE_PATH, index=False)
                st.success(f"המשרה {position} בחברת {company} נשמרה!")
                st.rerun()
            else:
                st.error("יש למלא שדות חובה (שם חברה ותפקיד).")

st.markdown("---")

# --- חלק 3: סיידבאר לסינון וחיפוש ---
st.sidebar.header("🔍 סינון וחיפוש")
search_term = st.sidebar.text_input("חיפוש לפי חברה / תפקיד")
status_filter = st.sidebar.multiselect(
    "סינון לפי סטאטוס", options=list(df["סטאטוס"].unique())
)

filtered_df = df.copy()
filtered_df["מחיקה"] = filtered_df["מחיקה"].astype(bool)

if search_term:
    filtered_df = filtered_df[
        filtered_df["שם החברה"].str.contains(search_term, case=False, na=False)
        | filtered_df["תפקיד"].str.contains(search_term, case=False, na=False)
    ]

if status_filter:
    filtered_df = filtered_df[filtered_df["סטאטוס"].isin(status_filter)]

# --- חלק 4: טבלאות ועריכה בזמן אמת ---
st.subheader("📋 ניהול ועריכת משרות")
st.caption(
    "ניתן לערוך נתונים ישירות בטבלה, לסמן תיבת 'מחיקה' בשורות שתרצי להסיר, וללחוץ על 'שמור שינויים'."
)

if not filtered_df.empty:
    edited_df = st.data_editor(
        filtered_df,
        column_config={
            "מחיקה": st.column_config.CheckboxColumn("למחיקה?"),
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
    )

    if st.button("💾 שמור שינויים ועדכן"):
        # הסרת שורות שסומנו למחיקה
        final_df = edited_df[edited_df["מחיקה"] == False]
        final_df.to_csv(FILE_PATH, index=False)
        st.success("השינויים נשמרו בהצלחה!")
        st.rerun()
else:
    st.info("לא נמצאו משרות תואמות.")

st.markdown("---")

# --- חלק 5: ויזואליזציה נתונים ---
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
