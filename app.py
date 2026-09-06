import datetime
import hashlib
import os
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CareerFlow",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        direction: rtl;
        background-color: #f7f8fc;
    }

    .main .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, h4 {
        font-weight: 700 !important;
        color: #171923;
    }

    p, label, span, div {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial, sans-serif;
    }


    /* ---------- SIDEBAR ---------- */

    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-left: 1px solid #1f2937;
    }

    section[data-testid="stSidebar"] * {
        color: #f9fafb;
    }

    section[data-testid="stSidebar"] .stButton button {
        background-color: transparent;
        border: 1px solid #374151;
        color: #f9fafb;
        border-radius: 8px;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #1f2937;
        border-color: #4b5563;
    }

    .sidebar-logo {
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .sidebar-subtitle {
        color: #9ca3af !important;
        font-size: 13px;
        margin-bottom: 30px;
    }

    .sidebar-user {
        background-color: #1f2937;
        padding: 14px;
        border-radius: 10px;
        margin-bottom: 20px;
    }

    .sidebar-user-label {
        color: #9ca3af !important;
        font-size: 12px;
    }

    .sidebar-user-name {
        font-size: 15px;
        font-weight: 600;
        margin-top: 4px;
    }


    /* ---------- LOGIN ---------- */

    .login-wrapper {
        max-width: 440px;
        margin: 8vh auto 0 auto;
    }

    .login-brand {
        text-align: center;
        margin-bottom: 35px;
    }

    .login-logo {
        font-size: 38px;
        font-weight: 800;
        color: #111827;
    }

    .login-tagline {
        color: #6b7280;
        font-size: 15px;
        margin-top: 6px;
    }

    .login-card {
        background: white;
        padding: 35px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    }


    /* ---------- HEADER ---------- */

    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
    }

    .page-title {
        font-size: 30px;
        font-weight: 800;
        color: #111827;
    }

    .page-subtitle {
        color: #6b7280;
        margin-top: 4px;
        font-size: 14px;
    }


    /* ---------- KPI CARDS ---------- */

    .kpi-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 22px;
        min-height: 125px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }

    .kpi-label {
        color: #6b7280;
        font-size: 13px;
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: 800;
        color: #111827;
    }

    .kpi-description {
        font-size: 12px;
        color: #9ca3af;
        margin-top: 5px;
    }


    /* ---------- SECTION ---------- */

    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 35px;
        margin-bottom: 15px;
    }

    .section-title {
        font-size: 19px;
        font-weight: 700;
        color: #111827;
    }

    .section-description {
        color: #6b7280;
        font-size: 13px;
    }


    /* ---------- STATUS BADGES ---------- */

    .status-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    .status-applied {
        background-color: #eef2ff;
        color: #4338ca;
    }

    .status-phone {
        background-color: #ecfeff;
        color: #0e7490;
    }

    .status-interview {
        background-color: #eff6ff;
        color: #1d4ed8;
    }

    .status-test {
        background-color: #fef3c7;
        color: #92400e;
    }

    .status-offer {
        background-color: #dcfce7;
        color: #166534;
    }

    .status-rejected {
        background-color: #fee2e2;
        color: #991b1b;
    }


    /* ---------- JOB CARD ---------- */

    .job-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 10px;
    }

    .job-company {
        font-size: 15px;
        font-weight: 700;
        color: #111827;
    }

    .job-position {
        font-size: 13px;
        color: #6b7280;
        margin-top: 3px;
    }

    .job-date {
        font-size: 12px;
        color: #9ca3af;
    }


    /* ---------- BUTTONS ---------- */

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 40px;
    }

    .stFormSubmitButton > button {
        border-radius: 8px;
        font-weight: 600;
    }


    /* ---------- INPUTS ---------- */

    input, textarea, select {
        border-radius: 8px !important;
    }


    /* ---------- DIVIDERS ---------- */

    hr {
        border-color: #e5e7eb !important;
    }


    /* ---------- EMPTY STATE ---------- */

    .empty-state {
        background: white;
        border: 1px dashed #d1d5db;
        border-radius: 14px;
        padding: 50px;
        text-align: center;
        color: #6b7280;
    }

    .empty-state-title {
        font-size: 18px;
        font-weight: 700;
        color: #374151;
        margin-bottom: 6px;
    }

    .empty-state-text {
        font-size: 13px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE
# ============================================================

DB_FILE = "tracker.db"

STATUS_OPTIONS = [
    "נשלח קורות חיים",
    "ראיון טלפוני",
    "ראיון מקצועי",
    "מבחן בית",
    "הצעה",
    "דחייה"
]


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
                FOREIGN KEY (username)
                    REFERENCES users(username)
            )
        """)

        conn.commit()


init_db()


# ============================================================
# AUTHENTICATION
# ============================================================

def hash_password(password: str, salt: bytes = None):

    if salt is None:
        salt = os.urandom(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )

    return hashed.hex(), salt.hex()


def verify_password(password: str, stored_hash: str, salt_hex: str):

    salt = bytes.fromhex(salt_hex)

    hashed_input = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    ).hex()

    return hashed_input == stored_hash


def register_user(username: str, password: str):

    username = username.strip().lower()

    if not username or not password:
        return False, "נא למלא את כל השדות."

    password_hash, salt = hash_password(password)

    try:

        with get_db_connection() as conn:

            conn.execute(
                """
                INSERT INTO users
                (username, password_hash, salt)
                VALUES (?, ?, ?)
                """,
                (username, password_hash, salt)
            )

            conn.commit()

        return True, "החשבון נוצר בהצלחה."

    except sqlite3.IntegrityError:

        return False, "שם המשתמש כבר קיים במערכת."

    except Exception:

        return False, "אירעה שגיאה ביצירת החשבון."


def authenticate_user(username: str, password: str):

    username = username.strip().lower()

    with get_db_connection() as conn:

        user = conn.execute(
            """
            SELECT password_hash, salt
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

    if user:

        return verify_password(
            password,
            user["password_hash"],
            user["salt"]
        )

    return False


# ============================================================
# JOB FUNCTIONS
# ============================================================

def get_user_jobs(username: str):

    with get_db_connection() as conn:

        query = """
            SELECT
                id,
                apply_date,
                company,
                position,
                status,
                link,
                notes
            FROM jobs
            WHERE username = ?
            ORDER BY apply_date DESC, id DESC
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(username,)
        )

    df.rename(
        columns={
            "id": "מזהה",
            "apply_date": "תאריך",
            "company": "שם החברה",
            "position": "תפקיד",
            "status": "סטאטוס",
            "link": "קישור",
            "notes": "הערות"
        },
        inplace=True
    )

    return df


def insert_job(
    username,
    apply_date,
    company,
    position,
    status,
    link,
    notes
):

    with get_db_connection() as conn:

        conn.execute(
            """
            INSERT INTO jobs
            (
                username,
                apply_date,
                company,
                position,
                status,
                link,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                apply_date,
                company,
                position,
                status,
                link,
                notes
            )
        )

        conn.commit()


def update_jobs_batch(username, edited_df):

    with get_db_connection() as conn:

        cursor = conn.cursor()

        delete_ids = edited_df[
            edited_df["למחיקה?"] == True
        ]["מזהה"].tolist()

        if delete_ids:

            placeholders = ",".join(
                "?" for _ in delete_ids
            )

            cursor.execute(
                f"""
                DELETE FROM jobs
                WHERE id IN ({placeholders})
                AND username = ?
                """,
                (*delete_ids, username)
            )

        active_rows = edited_df[
            edited_df["למחיקה?"] == False
        ]

        for _, row in active_rows.iterrows():

            cursor.execute(
                """
                UPDATE jobs

                SET
                    company = ?,
                    position = ?,
                    status = ?,
                    link = ?,
                    notes = ?

                WHERE id = ?
                AND username = ?
                """,
                (
                    row["שם החברה"],
                    row["תפקיד"],
                    row["סטאטוס"],
                    row["קישור"],
                    row["הערות"],
                    row["מזהה"],
                    username
                )
            )

        conn.commit()


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div class="login-wrapper">

            <div class="login-brand">

                <div class="login-logo">
                    CareerFlow
                </div>

                <div class="login-tagline">
                    ניהול חכם ופשוט של תהליך חיפוש העבודה
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    col_left, col_center, col_right = st.columns(
        [1, 2, 1]
    )

    with col_center:

        st.markdown(
            '<div class="login-card">',
            unsafe_allow_html=True
        )

        tab_login, tab_register = st.tabs(
            ["התחברות", "יצירת חשבון"]
        )

        # ---------------- LOGIN ----------------

        with tab_login:

            st.markdown(
                "### ברוכה הבאה",
                unsafe_allow_html=True
            )

            st.caption(
                "התחברי כדי להמשיך לניהול המועמדויות שלך."
            )

            with st.form("login_form"):

                login_user = st.text_input(
                    "שם משתמש"
                ).strip().lower()

                login_pass = st.text_input(
                    "סיסמה",
                    type="password"
                )

                submit_login = st.form_submit_button(
                    "התחברות",
                    use_container_width=True,
                    type="primary"
                )

                if submit_login:

                    if authenticate_user(
                        login_user,
                        login_pass
                    ):

                        st.session_state.logged_in = True
                        st.session_state.username = login_user

                        st.rerun()

                    else:

                        st.error(
                            "שם המשתמש או הסיסמה אינם תקינים."
                        )

        # ---------------- REGISTER ----------------

        with tab_register:

            st.markdown(
                "### יצירת חשבון",
                unsafe_allow_html=True
            )

            st.caption(
                "צרי חשבון חדש והתחילי לנהל את חיפוש העבודה שלך."
            )

            with st.form("register_form"):

                reg_user = st.text_input(
                    "שם משתמש"
                ).strip().lower()

                reg_pass = st.text_input(
                    "סיסמה",
                    type="password"
                )

                reg_pass_confirm = st.text_input(
                    "אימות סיסמה",
                    type="password"
                )

                submit_register = st.form_submit_button(
                    "יצירת חשבון",
                    use_container_width=True,
                    type="primary"
                )

                if submit_register:

                    if not reg_user or not reg_pass:

                        st.error(
                            "נא למלא את כל השדות."
                        )

                    elif reg_pass != reg_pass_confirm:

                        st.error(
                            "הסיסמאות אינן תואמות."
                        )

                    elif len(reg_pass) < 6:

                        st.error(
                            "הסיסמה חייבת להכיל לפחות 6 תווים."
                        )

                    else:

                        success, message = register_user(
                            reg_user,
                            reg_pass
                        )

                        if success:

                            st.success(message)

                        else:

                            st.error(message)

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


# ============================================================
# MAIN APPLICATION
# ============================================================

else:

    current_user = st.session_state.username

    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.markdown(
            """
            <div class="sidebar-logo">
                CareerFlow
            </div>

            <div class="sidebar-subtitle">
                Career Management Platform
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="sidebar-user">

                <div class="sidebar-user-label">
                    משתמש מחובר
                </div>

                <div class="sidebar-user-name">
                    {current_user}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### חיפוש וסינון")

        search_term = st.text_input(
            "חיפוש",
            placeholder="חברה או תפקיד..."
        )

        status_filter = st.multiselect(
            "סטאטוס",
            STATUS_OPTIONS
        )

        st.divider()

        if st.button(
            "התנתקות",
            use_container_width=True
        ):

            st.session_state.logged_in = False
            st.session_state.username = ""

            st.rerun()


    # ========================================================
    # LOAD DATA
    # ========================================================

    df = get_user_jobs(current_user)

    filtered_df = df.copy()

    if search_term and not filtered_df.empty:

        filtered_df = filtered_df[
            filtered_df["שם החברה"].str.contains(
                search_term,
                case=False,
                na=False
            )
            |
            filtered_df["תפקיד"].str.contains(
                search_term,
                case=False,
                na=False
            )
        ]

    if status_filter and not filtered_df.empty:

        filtered_df = filtered_df[
            filtered_df["סטאטוס"].isin(status_filter)
        ]


    # ========================================================
    # HEADER
    # ========================================================

    st.markdown(
        """
        <div class="page-header">

            <div>

                <div class="page-title">
                    לוח הבקרה
                </div>

                <div class="page-subtitle">
                    סקירה מרכזית של תהליך חיפוש העבודה שלך
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # KPI CALCULATIONS
    # ========================================================

    total_jobs = len(df)

    in_progress = len(
        df[
            df["סטאטוס"].isin(
                [
                    "ראיון טלפוני",
                    "ראיון מקצועי",
                    "מבחן בית",
                    "הצעה"
                ]
            )
        ]
    )

    applications = len(
        df[
            df["סטאטוס"] == "נשלח קורות חיים"
        ]
    )

    offers = len(
        df[
            df["סטאטוס"] == "הצעה"
        ]
    )


    # ========================================================
    # KPI CARDS
    # ========================================================

    k1, k2, k3, k4 = st.columns(4)

    with k1:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    סה"כ מועמדויות
                </div>

                <div class="kpi-value">
                    {total_jobs}
                </div>

                <div class="kpi-description">
                    כלל המשרות שנוספו למערכת
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with k2:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    בתהליכי מיון
                </div>

                <div class="kpi-value">
                    {in_progress}
                </div>

                <div class="kpi-description">
                    מועמדויות הנמצאות בתהליך
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with k3:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    מועמדויות פעילות
                </div>

                <div class="kpi-value">
                    {applications}
                </div>

                <div class="kpi-description">
                    ממתינות לשלב הבא
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with k4:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-label">
                    הצעות עבודה
                </div>

                <div class="kpi-value">
                    {offers}
                </div>

                <div class="kpi-description">
                    הצעות שהתקבלו
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # ADD JOB
    # ========================================================

    st.markdown(
        """
        <div class="section-header">

            <div>

                <div class="section-title">
                    הוספת מועמדות חדשה
                </div>

                <div class="section-description">
                    שמרי את פרטי המשרה כדי לעקוב אחר התהליך.
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander(
        "＋ הוספת משרה",
        expanded=False
    ):

        with st.form(
            "job_form",
            clear_on_submit=True
        ):

            c1, c2 = st.columns(2)

            with c1:

                company = st.text_input(
                    "שם החברה *",
                    placeholder="לדוגמה: Microsoft"
                )

                position = st.text_input(
                    "תפקיד *",
                    placeholder="לדוגמה: Data Analyst"
                )

                status = st.selectbox(
                    "סטאטוס",
                    STATUS_OPTIONS
                )

            with c2:

                apply_date = st.date_input(
                    "תאריך הגשה",
                    datetime.date.today()
                )

                link = st.text_input(
                    "קישור למשרה",
                    placeholder="https://..."
                )

                notes = st.text_input(
                    "הערות",
                    placeholder="לדוגמה: ראיון ביום ראשון"
                )

            submitted = st.form_submit_button(
                "שמירת מועמדות",
                use_container_width=True,
                type="primary"
            )

            if submitted:

                if not company.strip() or not position.strip():

                    st.error(
                        "יש למלא שם חברה ותפקיד."
                    )

                else:

                    insert_job(
                        current_user,
                        apply_date.strftime("%Y-%m-%d"),
                        company.strip(),
                        position.strip(),
                        status,
                        link.strip(),
                        notes.strip()
                    )

                    st.success(
                        "המועמדות נוספה בהצלחה."
                    )

                    st.rerun()


    # ========================================================
    # APPLICATION TABLE
    # ========================================================

    st.markdown(
        """
        <div class="section-header">

            <div>

                <div class="section-title">
                    המועמדויות שלי
                </div>

                <div class="section-description">
                    ניהול, עדכון ומעקב אחר כל תהליכי הגיוס.
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if not filtered_df.empty:

        display_df = filtered_df.copy()

        display_df.insert(
            0,
            "למחיקה?",
            False
        )

        edited_df = st.data_editor(

            display_df,

            column_config={

                "למחיקה?":
                    st.column_config.CheckboxColumn(
                        "מחיקה",
                        default=False,
                        width="small"
                    ),

                "מזהה":
                    None,

                "קישור":
                    st.column_config.LinkColumn(
                        "משרה",
                        display_text="פתיחת משרה"
                    ),

                "סטאטוס":
                    st.column_config.SelectboxColumn(
                        "סטאטוס",
                        options=STATUS_OPTIONS,
                        required=True
                    ),

                "תאריך":
                    st.column_config.TextColumn(
                        "תאריך",
                        disabled=True
                    ),

                "שם החברה":
                    st.column_config.TextColumn(
                        "חברה"
                    ),

                "תפקיד":
                    st.column_config.TextColumn(
                        "תפקיד"
                    ),

                "הערות":
                    st.column_config.TextColumn(
                        "הערות"
                    )
            },

            use_container_width=True,
            hide_index=True,
            key="jobs_data_editor"
        )

        st.write("")

        if st.button(
            "שמירת שינויים",
            type="primary"
        ):

            update_jobs_batch(
                current_user,
                edited_df
            )

            st.success(
                "השינויים נשמרו בהצלחה."
            )

            st.rerun()

    else:

        st.markdown(
            """
            <div class="empty-state">

                <div class="empty-state-title">
                    עדיין אין מועמדויות
                </div>

                <div class="empty-state-text">
                    הוסיפי את המשרה הראשונה שלך כדי להתחיל לעקוב
                    אחר תהליך חיפוש העבודה.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # ANALYTICS
    # ========================================================

    if not df.empty:

        st.markdown(
            """
            <div class="section-header">

                <div>

                    <div class="section-title">
                        Analytics
                    </div>

                    <div class="section-description">
                        תמונת מצב של התקדמות המועמדויות.
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        chart_col, summary_col = st.columns(
            [2, 1]
        )


        # ----------------------------------------------------
        # BAR CHART
        # ----------------------------------------------------

        with chart_col:

            counts = (
                df["סטאטוס"]
                .value_counts()
                .reindex(
                    STATUS_OPTIONS,
                    fill_value=0
                )
                .reset_index()
            )

            counts.columns = [
                "סטאטוס",
                "כמות"
            ]

            fig = px.bar(
                counts,
                x="סטאטוס",
                y="כמות",
                text="כמות"
            )

            fig.update_layout(

                showlegend=False,

                height=380,

                margin=dict(
                    l=20,
                    r=20,
                    t=30,
                    b=20
                ),

                plot_bgcolor="white",
                paper_bgcolor="white",

                xaxis=dict(
                    title="",
                    showgrid=False
                ),

                yaxis=dict(
                    title="מספר מועמדויות",
                    gridcolor="#eef0f4"
                )
            )

            fig.update_traces(
                textposition="outside"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        with summary_col:

            st.markdown(
                """
                <div class="job-card">

                    <div class="section-title">
                        סיכום
                    </div>

                    <br>

                """,
                unsafe_allow_html=True
            )

            rejection_rate = (
                len(
                    df[
                        df["סטאטוס"] == "דחייה"
                    ]
                )
                / total_jobs
                * 100
                if total_jobs
                else 0
            )

            progress_rate = (
                in_progress
                / total_jobs
                * 100
                if total_jobs
                else 0
            )

            st.metric(
                "שיעור בתהליכי מיון",
                f"{progress_rate:.0f}%"
            )

            st.metric(
                "שיעור דחיות",
                f"{rejection_rate:.0f}%"
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )


    # ========================================================
    # RECENT APPLICATIONS
    # ========================================================

    if not df.empty:

        st.markdown(
            """
            <div class="section-header">

                <div>

                    <div class="section-title">
                        מועמדויות אחרונות
                    </div>

                    <div class="section-description">
                        הפעילות האחרונה במערכת.
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        recent_jobs = df.head(5)

        for _, row in recent_jobs.iterrows():

            st.markdown(
                f"""
                <div class="job-card">

                    <div class="job-company">
                        {row["שם החברה"]}
                    </div>

                    <div class="job-position">
                        {row["תפקיד"]}
                    </div>

                    <div class="job-date">
                        {row["תאריך"]} · {row["סטאטוס"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )
