import datetime
import hashlib
import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# הגדרות עמוד עיקריות
# ==========================================
st.set_page_config(
    page_title="Job Tracker Pro | Enterprise Edition",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# עיצוב מותאם אישית (Custom CSS)
# ==========================================
st.markdown(
    """
    <style>
    /* הגדרת כיוון כללי מימין לשמאל */
    .stApp {
        direction: rtl;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* עיצוב כרטיסיות המדדים (KPI Cards) */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 0.9rem;
        color: #64748b;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
    }

    /* התאמת אלמנטים בסיידבאר */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-left: 1px solid #e2e8f0;
    }
    
    /* שיפור מראה הכפתורים */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""",
    unsafe_allow_html=True,
)

DB_FILE = "tracker.db"
STATUS_OPTIONS = [
    "נשלח קורות חיים",
    "ראיון טלפוני",
    "ראיון מקצועי",
    "מבחן בית",
    "הצעה",
    "דחייה",
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

        # 2. עדכון שורות קיימות
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
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l, col_main, col_r = st.columns([1, 2, 1])
    
    with col_main:
        st.markdown("<h1 style='text-align: center; color: #1e293b;'>💼 Job Tracker Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>פלטפורמה חכמה לניהול ומעקב תהליכי קריירה וגיוס</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 התחברות למערכת", "📝 פתיחת חשבון חדש"])

        with tab_login:
            with st.form("login_form"):
                login_user = st.text_input("שם משתמש").strip().lower()
                login_pass = st.text_input("סיסמה", type="password")
                submit_login = st.form_submit_button("התחבר למערכת", use_container_width=True, type="primary")

                if submit_login:
                    if authenticate_user(login_user, login_pass):
                        st.session_state.logged_in = True
                        st.session_state.username = login_user
                        st.rerun()
                    else:
                        st.error("שם המשתמש או הסיסמה אינם נכונים.")

        with tab_register:
            with st.form("register_form"):
                reg_user = st.text_input("בחר שם משתמש").strip().lower()
                reg_pass = st.text_input("בחר סיסמה", type="password")
                reg_pass_confirm = st.text_input("אימות סיסמה", type="password")
                submit_reg = st.form_submit_button("צור חשבון", use_container_width=True)

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

    # Sidebar: פרופיל וסיידבר
    st.sidebar.markdown(f"### 👤 משתמש מחובר")
    st.sidebar.markdown(f"**`{current_user}`**")
    if st.sidebar.button("🚪 התנתק", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.sidebar.divider()

    # טעינת נתונים
    df = get_user_jobs(current_user)

    # כותרת ראשית
    st.title("💼 לוח בקרה ומעקב מועמדויות")
    st.markdown("ניהול ריכוזי של כל המועמדויות והתהליכים הילווים")

    st.markdown("<br>", unsafe_allow_html=True)

    # חלק 1: KPI Metrics
    total_jobs = len(df)
    in_progress = len(df[df["סטאטוס"].isin(["ראיון טלפוני", "ראיון מקצועי", "מבחן בית", "הצעה"])])
    applied = len(df[df["סטאטוס"] == "נשלח קורות חיים"])
    rejected = len(df[df["סטאטוס"] == "דחייה"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">סה"כ מועמדויות</div>
                <div class="metric-value">{total_jobs}</div>
            </div>
        ''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title" style="color: #0284c7;">בתהליכי מיון</div>
                <div class="metric-value" style="color: #0284c7;">{in_progress}</div>
            </div>
        ''', unsafe_allow_html=True)
    with c3:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title" style="color: #eab308;">נשלחו קו"ח</div>
                <div class="metric-value" style="color: #ca8a04;">{applied}</div>
            </div>
        ''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title" style="color: #ef4444;">דחיות</div>
                <div class="metric-value" style="color: #dc2626;">{rejected}</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

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

            submit_job = st.form_submit_button("שמור משרה במערכת", use_container_width=True, type="primary")
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
                "מזהה": None,
                "קישור": st.column_config.LinkColumn("קישור למשרה", display_text="פתח משרה"),
                "סטאטוס": st.column_config.SelectboxColumn("סטאטוס", options=STATUS_OPTIONS, required=True),
                "תאריך": st.column_config.TextColumn("תאריך הגשה", disabled=True),
                "הערות": st.column_config.TextColumn("הערות", width="medium"),
            },
            use_container_width=True,
            hide_index=True,
            key="jobs_data_editor"
        )

        col_act1, _ = st.columns([1, 4])
        with col_act1:
            if st.button("💾 שמור שינויים", type="primary", use_container_width=True):
                update_jobs_batch(current_user, edited_df)
                st.success("השינויים עודכנו בהצלחה!")
                st.rerun()
    else:
        st.info("לא נמצאו משרות להצגה.")

    # חלק 5: אנליטיקה וגרפים מתקדמים
    if not df.empty:
        st.divider()
        st.subheader("📈 ניתוח מצב מועמדויות")
        
        col_g1, col_g2 = st.columns(2)

        counts = df["סטאטוס"].value_counts().reset_index()
        counts.columns = ["סטאטוס", "כמות"]

        with col_g1:
            fig_bar = px.bar(
                counts,
                y="סטאטוס",
                x="כמות",
                text="כמות",
                orientation="h",
                title="התפלגות לפי סטאטוס",
                color_discrete_sequence=["#3b82f6"]
            )
            fig_bar.update_layout(
                xaxis_title="מספר משרות",
                yaxis_title="",
                height=320,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            fig_pie = px.pie(
                counts,
                names="סטאטוס",
                values="כמות",
                hole=0.4,
                title="חלוקה באחוזים",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(
                height=320,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
