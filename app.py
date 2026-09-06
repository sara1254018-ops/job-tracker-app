import datetime
import hashlib
import json
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Job Tracker Pro", layout="wide")

USERS_FILE = "users.json"
DATA_COLUMNS = [
    "תאריך",
    "שם החברה",
    "תפקיד",
    "סטאטוס",
    "קישור",
    "הערות",
]

# --- פונקציות ניהול משתמשים ---
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_file_path(username):
    # קובץ נפרד לכל משתמש
    safe_username = "".join(c for c in username if c.isalnum() or c in ("_", "-")).lower()
    return f"jobs_{safe_username}.csv"

def load_user_data(username):
    file_path = get_user_file_path(username)
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            for col in DATA_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            for col in DATA_COLUMNS:
                df[col] = df[col].fillna("").astype(str)
            return df[DATA_COLUMNS]
        except Exception:
            return pd.DataFrame(columns=DATA_COLUMNS)
    else:
        return pd.DataFrame(columns=DATA_COLUMNS)

def save_user_data(username, df):
    file_path = get_user_file_path(username)
    df[DATA_COLUMNS].to_csv(file_path, index=False)

# --- ניהול Session State להתחברות ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

users_db = load_users()

# --- מסך התחברות / הרשמה ---
if not st.session_state.logged_in:
    st.title("💼 Job Tracker Pro - התחברות למערכת")
    
    tab_login, tab_register = st.tabs(["🔐 התחברות", "📝 הרשמה למשתמש חדש"])

    with tab_login:
        with st.form("login_form"):
            login_user = st.text_input("שם משתמש").strip().lower()
            login_pass = st.text_input("סיסמה", type="password")
            submit_login = st.form_submit_button("התחבר")

            if submit_login:
                if not login_user or not login_pass:
                    st.error("נא למלא שם משתמש וסיסמה.")
                elif login_user in users_db and users_db[login_user] == hash_password(login_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.success(f"ברוך/ה הבא/ה, {login_user}!")
                    st.rerun()
                else:
                    st.error("שם משתמש או סיסמה שגויים.")

    with tab_register:
        with st.form("register_form"):
            reg_user = st.text_input("בחר שם משתמש (באנגלית/מספרים בלבד)").strip().lower()
            reg_pass = st.text_input("בחר סיסמה", type="password")
            reg_pass_confirm = st.text_input("אימות סיסמה", type="password")
            submit_reg = st.form_submit_button("צור חשבון חדש")

            if submit_reg:
                if not reg_user or not reg_pass:
                    st.error("נא למלא את כל השדות.")
                elif reg_pass != reg_pass_confirm:
                    st.error("הסיסמאות אינן תואמות.")
                elif reg_user in users_db:
                    st.error("שם המשתמש כבר תפוס, נא לבחור שם אחר.")
                else:
                    users_db[reg_user] = hash_password(reg_pass)
                    save_users(users_db)
                    st.success("החשבון נוצר בהצלחה! כעת ניתן להתחבר בלשונית 'התחברות'.")

else:
    # --- מסך המערכת הראשי (לאחר התחברות) ---
    current_user = st.session_state.username
    
    # סיידבאר עם התנתקות וסינון
    st.sidebar.write(f"👤 מחובר כ: **{current_user}**")
    if st.sidebar.button("🚪 התנתק"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.sidebar.markdown("---")

    df = load_user_data(current_user)

    st.title("💼 מערכת מעקב משרות - Job Tracker Pro")

    # --- חלק 1: מדדים ---
    st.markdown("### 📊 תמונת מצב אישית")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    total_jobs = len(df)
    in_progress = len(
        df[df["סטאטוס"].isin(["ראיון טלפוני", "ראיון מקצועי", "מבחן בית", "הצעה"])]
    )
    applied = len(df[df["סטאטוס"] == "נשלח קורות חיים"])
    rejected = len(df[df["סטאטוס"] == "דחייה"])

    col_m1.metric('סה"כ משרות', total_jobs)
    col_m2.metric("בתהליך מתקדם", in_progress)
    col_m3.metric('נשלחו קו"ח', applied)
    col_m4.metric("דחיות", rejected)

    st.markdown("---")

    # --- חלק 2: הוספת משרה ---
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
                    save_user_data(current_user, df)
                    st.success(f"המשרה {position} בחברת {company} נשמרה בהצלחה!")
                    st.rerun()
                else:
                    st.error("יש למלא שדות חובה (שם חברה ותפקיד).")

    st.markdown("---")

    # --- חלק 3: סינון וחיפוש ---
    st.sidebar.header("🔍 סינון וחיפוש")
    search_term = st.sidebar.text_input("חיפוש לפי חברה / תפקיד")
    status_options = list(df["סטאטוס"].unique()) if not df.empty else []
    status_filter = st.sidebar.multiselect("סינון לפי סטאטוס", options=status_options)

    filtered_df = df.copy()

    if search_term and not filtered_df.empty:
        filtered_df = filtered_df[
            filtered_df["שם החברה"].str.contains(search_term, case=False, na=False)
            | filtered_df["תפקיד"].str.contains(search_term, case=False, na=False)
        ]

    if status_filter and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df["סטאטוס"].isin(status_filter)]

    # --- חלק 4: ניהול ועריכת משרות ---
    st.subheader("📋 ניהול ועריכת משרות")

    if not filtered_df.empty:
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
            key="editor_table",
        )

        if st.button("💾 שמור שינויים ועדכן"):
            keep_rows = edited_df[edited_df["למחיקה?"] == False]
            save_df = keep_rows[DATA_COLUMNS]
            save_user_data(current_user, save_df)
            st.success("השינויים נשמרו בהצלחה!")
            st.rerun()
    else:
        st.info("אין משרות להצגה. תוכל/י להוסיף משרה חדשה בטופס למעלה.")

    st.markdown("---")

    # --- חלק 5: גרף ---
    if not df.empty and len(df[df["סטאטוס"] != ""]) > 0:
        st.subheader("📈 ניתוח התפלגות המשרות שלך")
        status_counts = df[df["סטאטוס"] != ""]["סטאטוס"].value_counts().reset_index()
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
