"""Standalone, accessible Streamlit login and signup views for app_v3."""

from __future__ import annotations

import html

import streamlit as st

from ui.auth_mongo import (
    create_user,
    get_accessibility_profile,
    update_accessibility_profile,
    verify_login,
)

ACCESSIBILITY_OPTIONS = {
    "Visual impairment": "visual_impairment",
    "Hearing impairment": "hearing_impairment",
    "Motor or mobility": "motor_impairment",
    "Speech difficulty": "speech_difficulty",
    "Cognitive or learning difficulty": "cognitive_learning_difficulty",
}


def inject_auth_css() -> None:
    """Keep auth styling local so it cannot affect the signed-in workspace."""
    st.markdown(
        """
        <style>
        :root {
            --auth-ink:#172038;
            --auth-muted:#5d667b;
            --auth-violet:#5b43c7;
            --auth-violet-dark:#432ca8;
            --auth-violet-soft:#eeeaff;
        }

        .stApp:has(.st-key-auth-shell) {
            background:
                radial-gradient(circle at 7% 8%, #eae6ff 0, transparent 26rem),
                radial-gradient(circle at 96% 92%, #def4ed 0, transparent 24rem),
                #f8f7fc;
        }

        .stApp:has(.st-key-auth-shell) .block-container {
            max-width:1240px;
            padding:clamp(22px, 4vw, 58px) clamp(16px, 4vw, 42px);
        }

        .st-key-auth-shell {
            overflow:hidden;
            border:1px solid #e1dcf4;
            border-radius:28px;
            background:#fff;
            box-shadow:0 24px 70px rgba(48,42,109,.16);
            animation:auth-card-in .36s ease both;
        }

        .st-key-auth-shell > div {
            gap:0 !important;
            align-items:stretch;
        }

        .st-key-auth-visual {
            height:100%;
            min-height:620px;
            padding:clamp(34px, 6vw, 82px);
            color:#fff;
            background:linear-gradient(145deg, #221343 0%, #5b43c7 61%, #72cbb7 120%);
            overflow:hidden;
        }

        .st-key-auth-visual > div {
            height:100%;
        }

        .auth-visual-copy {
            position:relative;
            display:flex;
            min-height:490px;
            height:100%;
            flex-direction:column;
            justify-content:center;
        }

        .auth-visual-copy::before {
            content:"";
            position:absolute;
            width:310px;
            height:310px;
            right:-140px;
            top:-105px;
            border:1px solid rgba(255,255,255,.28);
            border-radius:50%;
            box-shadow:
                0 0 0 42px rgba(255,255,255,.05),
                0 0 0 88px rgba(255,255,255,.035);
        }

        .auth-visual-copy::after {
            content:"✦";
            position:absolute;
            right:2%;
            bottom:-10%;
            color:rgba(255,255,255,.16);
            font-size:170px;
            line-height:1;
            transform:rotate(-12deg);
        }

        .auth-mark {
            display:grid;
            place-items:center;
            width:58px;
            height:58px;
            border:1px solid rgba(255,255,255,.34);
            border-radius:18px;
            background:rgba(255,255,255,.12);
            font-size:28px;
            box-shadow:0 10px 28px rgba(25,13,70,.18);
        }

        .auth-visual-copy h1 {
            max-width:500px;
            margin:25px 0 13px;
            color:#fff;
            font-size:clamp(38px, 4.7vw, 62px);
            line-height:1;
            letter-spacing:-2px;
        }

        .auth-visual-copy p {
            max-width:440px;
            margin:0;
            color:#f4f2ff;
            font-size:16px;
            line-height:1.7;
        }

        .auth-visual-detail {
            display:flex;
            align-items:center;
            gap:10px;
            margin-top:30px;
            color:#fff;
            font-size:13px;
            font-weight:700;
        }

        .auth-visual-detail span {
            display:grid;
            place-items:center;
            width:28px;
            height:28px;
            border-radius:50%;
            background:rgba(255,255,255,.17);
        }

        .st-key-auth-form {
            display:flex;
            align-items:center;
            padding:clamp(30px, 5vw, 72px);
            background:rgba(255,255,255,.96);
        }

        .st-key-auth-form > div {
            width:100%;
            max-width:440px;
            margin:auto;
        }

        .auth-kicker {
            margin:0 0 8px;
            color:var(--auth-violet);
            font-size:11px;
            font-weight:800;
            letter-spacing:1.5px;
            text-transform:uppercase;
        }

        .auth-heading {
            margin:0 0 8px;
            color:var(--auth-ink);
            font-size:clamp(30px, 3vw, 38px);
            line-height:1.1;
            letter-spacing:-1px;
        }

        .auth-copy {
            margin:0 0 26px;
            color:var(--auth-muted);
            font-size:15px;
            line-height:1.65;
        }

        .st-key-auth-form [data-testid="stForm"] {
            border:0;
            padding:0;
            background:transparent;
        }

        .st-key-auth-form [data-testid="stTextInput"],
        .st-key-auth-form [data-testid="stTextArea"],
        .st-key-auth-form [data-testid="stMultiSelect"] {
            position:relative;
            margin-bottom:17px;
        }

        .st-key-auth-form [data-testid="stTextInput"] label,
        .st-key-auth-form [data-testid="stTextArea"] label,
        .st-key-auth-form [data-testid="stMultiSelect"] label {
            position:relative;
            z-index:2;
            display:table;
            margin:0 0 -8px 12px;
            padding:0 5px;
            color:#4a4561 !important;
            background:#fff;
            font-size:12px !important;
            font-weight:750 !important;
            transition:color .18s ease, transform .18s ease;
        }

        .st-key-auth-form [data-testid="stTextInput"]:has(input:focus) label,
        .st-key-auth-form [data-testid="stTextArea"]:has(textarea:focus) label,
        .st-key-auth-form [data-testid="stMultiSelect"]:has(input:focus) label {
            color:var(--auth-violet) !important;
            transform:translateY(-2px);
        }

        .st-key-auth-form [data-testid="stTextInput"] input,
        .st-key-auth-form [data-testid="stTextArea"] textarea,
        .st-key-auth-form [data-testid="stMultiSelect"] > div {
            min-height:51px !important;
            border:1px solid #c9c1e8 !important;
            border-radius:13px !important;
            background:#fff !important;
            color:var(--auth-ink) !important;
            box-shadow:0 4px 12px rgba(48,42,109,.04);
            transition:border-color .2s ease, box-shadow .2s ease, transform .2s ease;
        }

        .st-key-auth-form [data-testid="stTextArea"] textarea {
            min-height:92px !important;
        }

        .st-key-auth-form [data-testid="stTextInput"] input:focus,
        .st-key-auth-form [data-testid="stTextArea"] textarea:focus,
        .st-key-auth-form [data-testid="stMultiSelect"]:has(input:focus) > div {
            border-color:var(--auth-violet) !important;
            box-shadow:0 0 0 4px rgba(91,67,199,.20), 0 9px 19px rgba(48,42,109,.08) !important;
            transform:translateY(-1px);
        }

        .st-key-auth-form button[kind="primary"] {
            min-height:50px;
            border:0 !important;
            border-radius:13px !important;
            background:var(--auth-violet) !important;
            color:#fff !important;
            font-size:15px !important;
            font-weight:800 !important;
            box-shadow:0 10px 22px rgba(91,67,199,.28);
            transition:background .18s ease, transform .18s ease, box-shadow .18s ease, opacity .18s ease;
        }

        .st-key-auth-form button[kind="primary"]:hover {
            background:var(--auth-violet-dark) !important;
            transform:translateY(-2px) scale(1.01);
            box-shadow:0 14px 27px rgba(67,44,168,.32);
        }

        .st-key-auth-form button[kind="primary"]:active {
            transform:translateY(0) scale(.985);
            opacity:.92;
        }

        .st-key-auth-form .stButton button:not([kind="primary"]) {
            min-height:44px;
            border:0 !important;
            border-radius:11px !important;
            background:transparent !important;
            color:var(--auth-violet) !important;
            font-weight:750 !important;
            text-decoration:underline;
            text-underline-offset:3px;
        }

        .st-key-auth-form .stButton button:not([kind="primary"]):hover {
            background:var(--auth-violet-soft) !important;
        }

        .st-key-auth-form button:focus-visible,
        .st-key-auth-form input:focus-visible,
        .st-key-auth-form textarea:focus-visible,
        .st-key-auth-form [data-testid="stMultiSelect"]:has(input:focus) > div {
            outline:3px solid #8d7df1 !important;
            outline-offset:2px !important;
        }

        .auth-skip-note {
            margin:0 0 16px;
            padding:12px 13px;
            border:1px solid #d8d0f2;
            border-radius:12px;
            background:#f5f2ff;
            color:#403958;
            font-size:13px;
            line-height:1.55;
        }

        .auth-form-note {
            margin:14px 0 0;
            color:#687187;
            font-size:12px;
            line-height:1.55;
        }

        .auth-error {
            margin:0 0 15px;
            padding:11px 13px;
            border:1px solid #c83248;
            border-radius:12px;
            background:#fff2f3;
            color:#8d1930;
            font-size:13px;
            font-weight:650;
            animation:auth-error .3s ease both;
        }

        @keyframes auth-card-in {
            from { opacity:0; transform:translateY(12px); }
            to { opacity:1; transform:translateY(0); }
        }

        @keyframes auth-error {
            0%,100% { transform:translateX(0); }
            30% { transform:translateX(-5px); }
            65% { transform:translateX(5px); }
        }

        @media (max-width:820px) {
            .st-key-auth-shell > div {
                flex-direction:column !important;
            }

            .st-key-auth-visual {
                min-height:260px;
                padding:34px;
            }

            .auth-visual-copy {
                min-height:190px;
            }

            .auth-visual-copy h1 {
                font-size:38px;
            }

            .st-key-auth-form {
                padding:34px 24px;
            }
        }

        @media (prefers-reduced-motion:reduce) {
            *, *::before, *::after {
                scroll-behavior:auto !important;
                animation-duration:.01ms !important;
                animation-iteration-count:1 !important;
                transition-duration:.01ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _profile_values(selected: list[str], other_notes: str) -> dict[str, object]:
    skipped = "Prefer not to say / Skip" in selected
    return {
        **{key: label in selected for label, key in ACCESSIBILITY_OPTIONS.items()},
        "other_notes": "" if skipped else other_notes,
        "disclosed": bool(selected) and not skipped,
    }


def _brand_panel() -> None:
    st.markdown(
        """
        <div class="auth-visual-copy">
            <div class="auth-mark" aria-label="SakshamAI">✦</div>
            <h1>Learn with room to breathe.</h1>
            <p>
                SakshamAI turns your material into clearer conversations, notes,
                flashcards, and quizzes. Your accessibility choices are optional
                and always yours to change.
            </p>
            <div class="auth-visual-detail">
                <span aria-hidden="true">⌁</span>
                Built to adapt to your way of learning
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _set_authenticated(user: dict[str, object]) -> None:
    st.session_state.authenticated = True
    st.session_state.auth_user_id = user["id"]
    st.session_state.username = user["username"]
    st.session_state.accessibility_profile = get_accessibility_profile(user["id"])


def _show_error() -> None:
    error = st.session_state.pop("auth_error", None)
    if error:
        st.markdown(
            f'<div class="auth-error" role="alert">⚠ {html.escape(str(error))}</div>',
            unsafe_allow_html=True,
        )


def render_login_page() -> bool:
    """Render one auth view at a time and return True after a successful login."""
    if st.session_state.get("authenticated"):
        return True

    inject_auth_css()
    st.session_state.setdefault("auth_view", "login")

    with st.container(key="auth-shell"):
        visual, form = st.columns((1.04, 0.96), gap="small")

        with visual:
            with st.container(key="auth-visual"):
                _brand_panel()

        with form:
            with st.container(key="auth-form"):
                if st.session_state.auth_view == "login":
                    _render_login_form()
                else:
                    _render_signup_form()

    return False


def _render_login_form() -> None:
    st.markdown(
        """
        <p class="auth-kicker">Your learning space</p>
        <h1 class="auth-heading">Welcome back</h1>
        <p class="auth-copy">Sign in to continue your study session.</p>
        """,
        unsafe_allow_html=True,
    )

    _show_error()

    with st.form("login_form"):
        username = st.text_input(
            "Username or email",
            key="login_username",
            autocomplete="username",
        )
        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button(
            "Log In",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        with st.spinner("Signing you in…"):
            try:
                user = verify_login(username, password)
            except Exception as error:
                st.session_state.auth_error = (
                    f"Could not connect to the account database: {error}"
                )
            else:
                if not user:
                    st.session_state.auth_error = (
                        "Invalid username or password. Please check both fields and try again."
                    )
                else:
                    _set_authenticated(user)
                    st.rerun()

        st.rerun()

    if st.button("Create an account", key="go_signup", use_container_width=True):
        st.session_state.auth_view = "signup"
        st.rerun()

    st.markdown(
        '<p class="auth-form-note">Your sign-in details stay private on this device.</p>',
        unsafe_allow_html=True,
    )


def _render_signup_form() -> None:
    st.markdown(
        """
        <p class="auth-kicker">Start gently</p>
        <h1 class="auth-heading">Create your account</h1>
        <p class="auth-copy">
            Make a private study space that can adapt to how you learn.
        </p>
        """,
        unsafe_allow_html=True,
    )

    _show_error()

    with st.form("signup_form"):
        username = st.text_input(
            "Username or email",
            key="signup_username",
            autocomplete="username",
        )
        password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
            autocomplete="new-password",
        )
        confirm = st.text_input(
            "Confirm password",
            type="password",
            key="signup_confirm",
            autocomplete="new-password",
        )

        st.markdown(
            """
            <div class="auth-skip-note">
                Accessibility questions are optional. They help us turn on the right
                features automatically. You can choose multiple broad categories,
                select <strong>Prefer not to say / Skip</strong>, or change
                everything later in Accessibility Settings.
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected = st.multiselect(
            "Accessibility needs (optional)",
            [*ACCESSIBILITY_OPTIONS, "Other", "Prefer not to say / Skip"],
            key="signup_accessibility",
        )

        other_notes = st.text_area("Other (optional)", key="signup_other_notes")

        submitted = st.form_submit_button(
            "Create Account",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if password != confirm:
            st.session_state.auth_error = "Passwords do not match."
        elif "Prefer not to say / Skip" in selected and len(selected) > 1:
            st.session_state.auth_error = (
                "Choose accessibility categories or Prefer not to say / Skip, not both."
            )
        else:
            with st.spinner("Creating your account…"):
                try:
                    user_id = create_user(username, password)
                    update_accessibility_profile(
                        user_id,
                        **_profile_values(selected, other_notes),
                    )
                    user = verify_login(username, password)
                except ValueError as error:
                    st.session_state.auth_error = str(error)
                except Exception as error:
                    st.session_state.auth_error = (
                        f"Could not connect to the account database: {error}"
                    )
                else:
                    _set_authenticated(user)
                    st.rerun()

        st.rerun()

    if st.button("Back to Login", key="go_login", use_container_width=True):
        st.session_state.auth_view = "login"
        st.rerun()