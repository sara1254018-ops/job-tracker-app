import datetime
import hashlib
import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Job Tracker Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "tracker.db"
STATUS_OPTIONS = [
    "נשלח קורות חיים",
    "ראיון טלפוני",
    "ראיון מקצועי",
    "מבחן בית",
    "הצעה",
    "דחייה"
]

# ==========================================
# שכבת מסד הנתונים (Database Layer)
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                apply_date TEXT NOT NULL,
                company TEXT NOT NULL,
                position TEXT NOT NULL,
                status TEXT NOT NULL,
                link TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        conn.commit()

init_db()

# ==========================================
# ניהול משתמשים ואבטחה
# ==========================================
def hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return hashed.hex(), salt.hex()

def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    hashed_input = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000).hex()
    return hashed_input == stored_hash

def register_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()
    if not username or not password:
        return False, "נא למלא את כל השדות."
    
    password_hash, salt = hash_password(password)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (username, password_hash, salt)
            )
            conn.commit()
            return True, "החשבון נוצר בהצלחה! כעת ניתן להתחבר."
    except sqlite3.IntegrityError:
        return False, "שם המשתמש כבר קיים במערכת."
    except Exception as e:
        return False, f"שגיאה ביצירת משתמש: {str(e)}"

def authenticate_user(username: str, password: str) -> bool:
    username = username.strip().lower()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and verify_password(password, user["password_hash"], user["salt"]):
            return True
    return False

# ==========================================
# ניהול משרות
# ==========================================
def get_user_jobs(username: str) -> pd.DataFrame:
    with get_db_connection() as conn:
        query = """
            SELECT id, apply_date, company, position, status, link, notes 
            FROM jobs 
            WHERE username = ? 
            ORDER BY apply_date DESC, id DESC
        """
        df = pd.read_sql_query(query, conn, params=(username,))
        df.rename(columns={
            "id": "מזהה",
            "apply_date": "תאריך",
            "company": "שם החברה",
            "position": "תפקיד",
            "status": "סטאטוס",
            "link": "קישור",
            "notes": "הערות"
        }, inplace=True)
        return df

def insert_job(username: str, apply_date: str, company: str, position: str, status: str, link: str, notes: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (username, apply_date, company, position, status, link, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, apply_date, company, position, status, link, notes))
        conn.commit()

def update_jobs_batch(username: str, edited_df: pd.DataFrame):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. מחיקת שורות שסומנו למחיקה
        delete_ids = edited_df[edited_df["למחיקה?"] == True]["מזהה"].tolist()
        if delete_ids:
            placeholders = ",".join("?" for _ in delete_ids)
            cursor.execute(f"DELETE FROM jobs WHERE id IN ({placeholders}) AND username = ?", (*delete_ids, username))

        # 2. עדכון שורות קיימות שלא נמחקו
        active_rows = edited_df[edited_df["למחיקה?"] == False]
        for _, row in active_rows.iterrows():
            cursor.execute("""
                UPDATE jobs 
                SET company = ?, position = ?, status = ?, link = ?, notes = ?
                WHERE id = ? AND username = ?
            """, (
                row["שם החברה"],
                row["תפקיד"],
                row["סטאטוס"],
                row["קישור"],
                row["הערות"],
                row["מזהה"],
                username
            ))
        conn.commit()

# ==========================================
# ניהול State
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ==========================================
# מסך התחברות והרשמה
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>💼 Job Tracker Pro</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>מערכת ארגונית לניהול תהליכי גיוס וקריירה</p>", unsafe_allow_html=True)
    
    col_spacer_l, col_main, col_spacer_r = st.columns([1, 2, 1])
    
    with col_main:
        tab_login, tab_register = st.tabs(["🔐 התחברות", "📝 יצירת חשבון חדש"])

        with tab_login:
            with st.form("login_form"):
                login_user = st.text_input("שם משתמש").strip().lower()
                login_pass = st.text_input("סיסמה", type="password")
                submit_login = st.form_submit_button("התחבר למערכת", use_container_width=True)

                if submit_login:
                    if authenticate_user(login_user, login_pass):
                        st.session_state.logged_in = True
                        st.session_state.username = login_user
                        st.rerun()
                    else:
                        st.error("שם משתמש או סיסמה אינם תקינים.")

        with tab_register:
            with st.form("register_form"):
                reg_user = st.text_input("בחר שם משתמש").strip().lower()
                reg_pass = st.text_input("בחר סיסמה", type="password")
                reg_pass_confirm = st.text_input("אימות סיסמה", type="password")
                submit_reg = st.form_submit_button("פתח חשבון", use_container_width=True)

                if submit_reg:
                    if reg_pass != reg_pass_confirm:
                        st.error("הסיסמאות אינן תואמות.")
                    elif len(reg_pass) < 6:
                        st.error("על הסיסמה להכיל לפחות 6 תווים.")
                    else:
                        success, message = register_user(reg_user, reg_pass)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

# ==========================================
# המערכת הראשית (משתמש מחובר)
# ==========================================
else:
    current_user = st.session_state.username

    # Sidebar: פרטי משתמש והתנתקות
    st.sidebar.markdown(f"**שלום, {current_user}**")
    if st.sidebar.button("🚪 התנתק", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.sidebar.divider()

    # טעינת נתונים
    df = get_user_jobs(current_user)

    # כותרת ראשית
    st.title("💼 מערכת מעקב מועמדויות")

    # חלק 1: KPI Metrics
    total_jobs = len(df)
    in_progress = len(df[df["סטאטוס"].isin(["ראיון טלפוני", "ראיון מקצועי", "מבחן בית", "הצעה"])])
    applied = len(df[df["סטאטוס"] == "נשלח קורות חיים"])
    rejected = len(df[df["סטאטוס"] == "דחייה"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric('סה"כ מועמדויות', total_jobs)
    col2.metric("בתהליכי מיון", in_progress)
    col3.metric('קו"ח שנשלחו', applied)
    col4.metric("דחיות", rejected)

    st.divider()

    # חלק 2: הוספת משרה חדשה
    with st.expander("➕ הוספת משרה חדשה לרשימה", expanded=False):
        with st.form("job_form", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            with fc1:
                company = st.text_input("שם החברה *")
                position = st.text_input("תפקיד *")
                status = st.selectbox("סטאטוס נוכחי", STATUS_OPTIONS)
            with fc2:
                apply_date = st.date_input("תאריך הגשה", datetime.date.today())
                link = st.text_input("קישור למשרה / מודעה")
                notes = st.text_input("הערות ראשוניות")

            submit_job = st.form_submit_button("שמור משרה", use_container_width=True)
            if submit_job:
                if company.strip() and position.strip():
                    insert_job(
                        username=current_user,
                        apply_date=apply_date.strftime("%Y-%m-%d"),
                        company=company.strip(),
                        position=position.strip(),
                        status=status,
                        link=link.strip(),
                        notes=notes.strip()
                    )
                    st.success(f"המשרה '{position}' בחברת '{company}' נשמרה בהצלחה!")
                    st.rerun()
                else:
                    st.error("חובה למלא שם חברה ותפקיד.")

    # חלק 3: סינונים (Sidebar)
    st.sidebar.subheader("🔍 סינון וחיפוש")
    search_term = st.sidebar.text_input("חיפוש חופשי (חברה / תפקיד)")
    status_filter = st.sidebar.multiselect("סינון לפי סטאטוס", options=STATUS_OPTIONS)

    filtered_df = df.copy()
    if search_term and not filtered_df.empty:
        filtered_df = filtered_df[
            filtered_df["שם החברה"].str.contains(search_term, case=False, na=False) |
            filtered_df["תפקיד"].str.contains(search_term, case=False, na=False)
        ]
    if status_filter and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df["סטאטוס"].isin(status_filter)]

    # חלק 4: טבלת עריכה וניהול משרות
    st.subheader("📋 רשימת משרות וניהול תהליכים")

    if not filtered_df.empty:
        display_df = filtered_df.copy()
        display_df.insert(0, "למחיקה?", False)

        edited_df = st.data_editor(
            display_df,
            column_config={
                "למחיקה?": st.column_config.CheckboxColumn("למחיקה?", default=False, width="small"),
                "מזהה": None,  # הסתרת ה-ID מהתצוגה, נשמר ברקע
                "קישור": st.column_config.LinkColumn("קישור למשרה", display_text="פתח משרה"),
                "סטאטוס": st.column_config.SelectboxColumn("סטאטוס", options=STATUS_OPTIONS, required=True),
                "תאריך": st.column_config.TextColumn("תאריך הגשה", disabled=True),
                "הערות": st.column_config.TextColumn("הערות", width="medium"),
            },
            use_container_width=True,
            hide_index=True,
            key="jobs_data_editor"
        )

        col_act1, col_act2 = st.columns([1, 4])
        with col_act1:
            if st.button("💾 שמור שינויים", type="primary", use_container_width=True):
                update_jobs_batch(current_user, edited_df)
                st.success("השינויים עודכנו במסד הנתונים בהצלחה!")
                st.rerun()
    else:
        st.info("לא נמצאו משרות התואמות לחיפוש או שעדיין לא הוזנו משרות.")

    # חלק 5: אנליטיקה וגרפים
    if not df.empty:
        st.divider()
        st.subheader("📈 ניתוח מצב מועמדויות")
        
        counts = df["סטאטוס"].value_counts().reset_index()
        counts.columns = ["סטאטוס", "כמות"]

        fig = px.bar(
            counts,
            x="סטאטוס",
            y="כמות",
            text="כמות",
            color="סטאטוס",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title='מספר משרות',
            margin=dict(l=20, r=20, t=30, b=20),
            height=350
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
