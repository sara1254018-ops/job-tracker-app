import datetime
import hashlib
import os
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CareerFlow",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    /* ---------- GENERAL ---------- */

    .stApp {
        background-color: #f6f7fb;
    }

    .main .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: #111827;
        font-weight: 700;
    }

    /* ---------- SIDEBAR ---------- */

    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: #f9fafb;
    }

    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] {
        background-color: #1f2937;
        border-color: #374151;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #374151;
    }

    /* ---------- BUTTONS ---------- */

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 40px;
    }

    /* ---------- INPUTS ---------- */

    .stTextInput input,
    .stTextArea textarea,
    .stDateInput input {
        border-radius: 8px;
    }

    /* ---------- METRICS ---------- */

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }

    div[data-testid="stMetricLabel"] {
        color: #6b7280;
        font-size: 13px;
    }

    div[data-testid="stMetricValue"] {
        color: #111827;
        font-size: 28px;
        font-weight: 700;
    }

    /* ---------- DATA EDITOR ---------- */

    div[data-testid="stDataEditor"] {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        overflow: hidden;
        background: white;
    }

    /* ---------- EXPANDER ---------- */

    div[data-testid="stExpander"] {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        background-color: white;
    }

    /* ---------- TABS ---------- */

    button[data-baseweb="tab"] {
        font-weight: 600;
    }

    /* ---------- ALERTS ---------- */

    div[data-testid="stAlert"] {
        border-radius: 8px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE CONFIGURATION
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


# ============================================================
# DATABASE LAYER
# ============================================================

def get_db_connection():
    conn = sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )
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


def verify_password(
    password: str,
    stored_hash: str,
    salt_hex: str
):

    salt = bytes.fromhex(salt_hex)

    hashed_input = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    ).hex()

    return hashed_input == stored_hash


def register_user(
    username: str,
    password: str
):

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
                (
                    username,
                    password_hash,
                    salt
                )
            )

            conn.commit()

        return True, "החשבון נוצר בהצלחה."

    except sqlite3.IntegrityError:

        return False, "שם המשתמש כבר קיים במערכת."

    except Exception:

        return False, "אירעה שגיאה ביצירת החשבון."


def authenticate_user(
    username: str,
    password: str
):

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
# JOB MANAGEMENT
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


def update_jobs_batch(
    username,
    edited_df
):

    with get_db_connection() as conn:

        cursor = conn.cursor()

        # Delete selected rows
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

        # Update remaining rows
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
# LOGIN / REGISTER SCREEN
# ============================================================

if not st.session_state.logged_in:

    st.write("")
    st.write("")
    st.write("")

    left, center, right = st.columns(
        [1.1, 1.4, 1.1]
    )

    with center:

        st.markdown(
            """
            <div style="
                text-align:center;
                margin-bottom:25px;
            ">
                <div style="
                    font-size:36px;
                    font-weight:800;
                    color:#111827;
                ">
                    CareerFlow
                </div>

                <div style="
                    color:#6b7280;
                    font-size:14px;
                    margin-top:6px;
                ">
                    ניהול חכם של תהליך חיפוש העבודה
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        tab_login, tab_register = st.tabs(
            [
                "התחברות",
                "יצירת חשבון"
            ]
        )

        # ---------------- LOGIN ----------------

        with tab_login:

            st.subheader("ברוכה הבאה")

            st.caption(
                "התחברי כדי להמשיך ללוח הבקרה שלך."
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

            st.subheader("יצירת חשבון")

            st.caption(
                "פתחי חשבון חדש כדי להתחיל לנהל את המועמדויות."
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
            <div style="
                font-size:25px;
                font-weight:800;
                margin-bottom:3px;
            ">
                CareerFlow
            </div>

            <div style="
                color:#9ca3af;
                font-size:12px;
                margin-bottom:28px;
            ">
                Career Management
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div style="
                background:#1f2937;
                border-radius:9px;
                padding:12px;
                margin-bottom:22px;
            ">

                <div style="
                    color:#9ca3af;
                    font-size:11px;
                ">
                    משתמש מחובר
                </div>

                <div style="
                    font-weight:600;
                    margin-top:3px;
                ">
                    {current_user}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("#### חיפוש וסינון")

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

    st.title("לוח הבקרה")

    st.caption(
        "סקירה מרכזית של תהליך חיפוש העבודה שלך"
    )


    # ========================================================
    # KPI METRICS
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

    rejected = len(
        df[
            df["סטאטוס"] == "דחייה"
        ]
    )


    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric(
            "סה״כ מועמדויות",
            total_jobs
        )

    with k2:
        st.metric(
            "בתהליכי מיון",
            in_progress
        )

    with k3:
        st.metric(
            "ממתינות למענה",
            applications
        )

    with k4:
        st.metric(
            "הצעות עבודה",
            offers
        )


    # ========================================================
    # ADD NEW JOB
    # ========================================================

    st.write("")

    st.subheader("הוספת מועמדות")

    with st.expander(
        "＋ הוספת משרה חדשה",
        expanded=False
    ):

        with st.form(
            "job_form",
            clear_on_submit=True
        ):

            col1, col2 = st.columns(2)

            with col1:

                company = st.text_input(
                    "שם החברה *",
                    placeholder="לדוגמה: Microsoft"
                )

                position = st.text_input(
                    "תפקיד *",
                    placeholder="לדוגמה: Data Analyst"
                )

                status = st.selectbox(
                    "סטאטוס נוכחי",
                    STATUS_OPTIONS
                )

            with col2:

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
                    placeholder="הערה קצרה..."
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
                        username=current_user,
                        apply_date=apply_date.strftime(
                            "%Y-%m-%d"
                        ),
                        company=company.strip(),
                        position=position.strip(),
                        status=status,
                        link=link.strip(),
                        notes=notes.strip()
                    )

                    st.success(
                        "המועמדות נוספה בהצלחה."
                    )

                    st.rerun()


    # ========================================================
    # APPLICATIONS TABLE
    # ========================================================

    st.write("")

    st.subheader("המועמדויות שלי")

    st.caption(
        f"מציג {len(filtered_df)} מתוך {len(df)} מועמדויות"
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

                "תאריך":
                    st.column_config.TextColumn(
                        "תאריך הגשה",
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

                "סטאטוס":
                    st.column_config.SelectboxColumn(
                        "סטאטוס",
                        options=STATUS_OPTIONS,
                        required=True
                    ),

                "קישור":
                    st.column_config.LinkColumn(
                        "קישור",
                        display_text="פתיחת משרה"
                    ),

                "הערות":
                    st.column_config.TextColumn(
                        "הערות",
                        width="medium"
                    )
            },

            use_container_width=True,
            hide_index=True,
            key="jobs_data_editor"
        )

        st.write("")

        col_save, col_space = st.columns(
            [1, 5]
        )

        with col_save:

            if st.button(
                "שמירת שינויים",
                type="primary",
                use_container_width=True
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

        if df.empty:

            st.info(
                "עדיין לא הוספת מועמדויות. "
                "הוסיפי את המשרה הראשונה שלך למעלה."
            )

        else:

            st.info(
                "לא נמצאו מועמדויות התואמות לסינון שבחרת."
            )


    # ========================================================
    # ANALYTICS
    # ========================================================

    if not df.empty:

        st.write("")
        st.write("")

        st.subheader("ניתוח מועמדויות")

        st.caption(
            "התפלגות המועמדויות לפי שלב בתהליך הגיוס"
        )

        chart_col, stats_col = st.columns(
            [2.2, 1]
        )


        # ----------------------------------------------------
        # CHART
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

                height=380,

                showlegend=False,

                plot_bgcolor="white",
                paper_bgcolor="white",

                margin=dict(
                    l=20,
                    r=20,
                    t=30,
                    b=30
                ),

                xaxis=dict(
                    title="",
                    showgrid=False
                ),

                yaxis=dict(
                    title="מספר מועמדויות",
                    gridcolor="#edf0f4"
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
        # STATISTICS
        # ----------------------------------------------------

        with stats_col:

            st.markdown("### סיכום")

            interview_count = len(
                df[
                    df["סטאטוס"].isin(
                        [
                            "ראיון טלפוני",
                            "ראיון מקצועי"
                        ]
                    )
                ]
            )

            interview_rate = (
                interview_count / total_jobs * 100
                if total_jobs
                else 0
            )

            rejection_rate = (
                rejected / total_jobs * 100
                if total_jobs
                else 0
            )

            st.metric(
                "הגיעו לראיון",
                interview_count
            )

            st.metric(
                "שיעור הגעה לראיון",
                f"{interview_rate:.0f}%"
            )

            st.metric(
                "שיעור דחיות",
                f"{rejection_rate:.0f}%"
            )


    # ========================================================
    # RECENT APPLICATIONS
    # ========================================================

    if not df.empty:

        st.write("")
        st.write("")

        st.subheader("מועמדויות אחרונות")

        recent_df = df.head(5).copy()

        recent_df = recent_df[
            [
                "תאריך",
                "שם החברה",
                "תפקיד",
                "סטאטוס"
            ]
        ]

        recent_df.columns = [
            "תאריך הגשה",
            "חברה",
            "תפקיד",
            "סטאטוס"
        ]

        st.dataframe(
            recent_df,
            use_container_width=True,
            hide_index=True
        )
