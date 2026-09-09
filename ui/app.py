from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nicegui import run, ui

from ui.db import (
    create_user,
    get_accessibility_profile,
    init_db,
    update_accessibility_profile,
    verify_login,
)
from ui.state.session_state import app_state
from ui.services.document_service import process_uploaded_document
from ui.services.chatbot_service import ask_question, build_chatbot
from ui.services.study_service import (
    generate_flashcards,
    generate_flashcards_for_topic,
    generate_notes,
    generate_notes_for_topic,
    generate_quiz,
    generate_quiz_for_topic,
)
from ui.services.voice_service import record_question, speak, transcribe


SESSION_SECONDS = 8 * 60 * 60
ACCESSIBILITY_OPTIONS = {
    'Visual impairment': 'visual_impairment',
    'Hearing impairment': 'hearing_impairment',
    'Motor or mobility': 'motor_impairment',
    'Speech difficulty': 'speech_difficulty',
    'Cognitive or learning difficulty': 'cognitive_learning_difficulty',
}

init_db()

NAV_ITEMS = [
    ("home", "Home", "⌂"),
    ("documents", "Documents", "↥"),
    ("chat", "Chat", "◌"),
    ("notes", "Notes", "✦"),
    ("quiz", "Quiz", "?"),
    ("flashcards", "Flashcards", "▣"),
    ("accessibility", "Accessibility Settings", "♿"),
]


ui.add_head_html('''
<style>
    :root {
        --bg: #f4f7fb;
        --bg-soft: #edf4ff;
        --panel: #ffffff;
        --panel-strong: #f8fafc;
        --ink: #172033;
        --muted: #5d6b82;
        --line: #dfe7f2;
        --primary: #4f46e5;
        --primary-strong: #3730a3;
        --success: #137a55;
        --warning: #b45309;
        --shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
    }

    html, body {
        background: var(--bg);
        color: var(--ink);
        font-family: "Segoe UI", sans-serif;
    }

    .saksham-shell {
        min-height: 100vh;
        background: var(--bg);
    }

    .saksham-sidebar {
        min-height: 100vh;
        background: linear-gradient(180deg, #0f172a 0%, #13213d 100%);
        color: #eef4ff;
        padding: 1.1rem 0.8rem;
        border-right: 1px solid rgba(148, 163, 184, 0.15);
    }

    .saksham-logo {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 0.9rem;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, #7c6af7 0%, #4f9fff 100%);
        box-shadow: 0 10px 26px rgba(88, 96, 255, 0.3);
        font-size: 1.3rem;
        font-weight: 800;
    }

    .saksham-brand {
        font-size: 1.35rem;
        letter-spacing: -0.05em;
        font-weight: 800;
    }

    .saksham-tagline {
        color: #b7c9ef;
        font-size: 0.78rem;
        margin: 0.15rem 0 1.1rem;
    }

    .saksham-nav-section {
        color: #90a3c8;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 800;
        padding: 0.9rem 0.6rem 0.4rem;
    }

    .saksham-nav-button {
        width: 100%;
        display: flex !important;
        justify-content: flex-start !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #edf4ff !important;
        border-radius: 0.9rem !important;
        margin: 0.18rem 0 !important;
        height: 2.65rem !important;
    }

    .saksham-nav-button.active {
        background: rgba(122, 155, 255, 0.12) !important;
        border-color: rgba(163, 179, 255, 0.18) !important;
    }

    .saksham-main {
        min-height: 100vh;
        padding: 1.25rem 1.35rem 2rem;
        background: var(--bg);
    }

    .saksham-main.profile-large-text { font-size: 1.08rem; }
    .saksham-main.profile-large-text .saksham-subtitle,
    .saksham-main.profile-large-text .saksham-message { font-size: 1.08rem; }
    .saksham-main.profile-motor button { min-height: 3.2rem; }
    .saksham-main.profile-motor input,
    .saksham-main.profile-motor textarea { min-height: 3rem; }
    .saksham-main.profile-contrast .saksham-card,
    .saksham-main.profile-contrast .saksham-composer,
    .saksham-main.profile-contrast .saksham-topbar { border-width: 2px; border-color: #172033; }

    .saksham-topbar {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid var(--line);
        border-radius: 1rem;
        padding: 0.8rem 1rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.1rem;
    }

    .saksham-status {
        background: #ecfdf5;
        color: var(--success);
        border: 1px solid #b9f5d2;
        border-radius: 999px;
        padding: 0.42rem 0.7rem;
        font-size: 0.72rem;
        font-weight: 800;
    }

    .saksham-page-title {
        font-size: clamp(1.7rem, 2.8vw, 2.5rem);
        letter-spacing: -0.06em;
        font-weight: 800;
        margin: 0.2rem 0 0.35rem;
    }

    .saksham-subtitle {
        color: var(--muted);
        font-size: 0.98rem;
        margin-bottom: 1rem;
    }

    .saksham-hero {
        background: linear-gradient(135deg, #ffffff 0%, #eef5ff 100%);
        border: 1px solid rgba(79, 70, 229, 0.12);
        border-radius: 1.2rem;
        padding: 1.15rem 1.2rem 1.05rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
    }

    .saksham-hero::after {
        content: "";
        position: absolute;
        width: 220px;
        height: 220px;
        border-radius: 50%;
        top: -90px;
        right: -40px;
        background: rgba(79, 70, 229, 0.07);
    }

    .saksham-pill {
        display: inline-flex;
        padding: 0.46rem 0.7rem;
        border-radius: 999px;
        background: rgba(79, 70, 229, 0.08);
        border: 1px solid rgba(79, 70, 229, 0.12);
        color: var(--primary-strong);
        font-size: 0.74rem;
        font-weight: 700;
        margin: 0.2rem 0.5rem 0 0;
    }

    .saksham-card {
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid var(--line);
        border-radius: 1rem;
        box-shadow: var(--shadow);
        padding: 1rem;
    }

    .saksham-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.8rem;
        border-radius: 999px;
        background: #ebf8f1;
        border: 1px solid rgba(22, 107, 71, 0.12);
        color: #166b47;
        font-weight: 700;
        font-size: 0.74rem;
    }

    .saksham-block {
        border: 1px solid var(--line);
        border-radius: 1rem;
        padding: 1rem;
        background: var(--panel);
        box-shadow: var(--shadow);
    }

    .saksham-metric {
        background: #eef5ff;
        border: 1px solid rgba(59, 130, 246, 0.14);
        padding: 0.75rem 0.8rem;
        border-radius: 0.8rem;
    }

    .saksham-metric-label {
        color: #5d7188;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 800;
    }

    .saksham-metric-value {
        margin-top: 0.35rem;
        font-size: 1.06rem;
        font-weight: 800;
        word-break: break-word;
    }

    .saksham-message {
        max-width: 76%;
        padding: 0.85rem 0.95rem;
        border-radius: 1rem;
        line-height: 1.55;
        white-space: pre-wrap;
        word-break: break-word;
    }

    .saksham-message.user {
        background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
        color: white;
        border-radius: 1rem 1rem 0.35rem 1rem;
        box-shadow: 0 10px 18px rgba(79, 70, 229, 0.2);
    }

    .saksham-message.assistant {
        background: #f3f7ff;
        color: var(--ink);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 1rem 1rem 1rem 0.35rem;
    }

    .saksham-composer {
        border: 1px solid rgba(148, 163, 184, 0.2);
        background: rgba(255, 255, 255, 0.96);
        border-radius: 1.05rem;
        padding: 0.55rem 0.7rem;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
        margin-top: 0.8rem;
        margin-bottom: 0.5rem;
    }

    .saksham-upload-box {
        background: rgba(239, 246, 255, 0.6);
        border-radius: 1rem;
        border: 1.5px dashed rgba(96, 111, 145, 0.45);
        padding: 1rem;
        min-height: 120px;
    }

    .saksham-section-title {
        font-size: 1.1rem;
        font-weight: 800;
        margin: 1.1rem 0 0.45rem;
    }

    .saksham-chat-scroll {
        max-height: 58vh;
        overflow-y: auto;
        padding-right: 0.15rem;
    }

    .auth-screen {
        min-height: 100vh;
        display: grid;
        grid-template-columns: minmax(0, 1.08fr) minmax(25rem, 0.92fr);
        background: #f6f3ff;
        color: #1f1736;
        overflow: hidden;
    }

    .auth-brand-panel {
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: clamp(2rem, 7vw, 7rem);
        background: linear-gradient(145deg, #25154f 0%, #4d2e9f 58%, #755fe0 100%);
        color: #fff;
        isolation: isolate;
    }

    .auth-brand-panel::before,
    .auth-brand-panel::after {
        content: '';
        position: absolute;
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 50%;
        z-index: -1;
    }

    .auth-brand-panel::before { width: 28rem; height: 28rem; right: -10rem; top: 8%; }
    .auth-brand-panel::after { width: 16rem; height: 16rem; right: 5%; bottom: 8%; }

    .auth-brand-mark {
        width: 3.5rem;
        height: 3.5rem;
        display: grid;
        place-items: center;
        border: 1px solid rgba(255, 255, 255, 0.36);
        border-radius: 1.1rem;
        background: rgba(255, 255, 255, 0.14);
        box-shadow: 0 1rem 2.5rem rgba(24, 10, 66, 0.25);
        font-size: 1.65rem;
    }

    .auth-brand-name { margin-top: 1.3rem; font-size: clamp(2.4rem, 5vw, 4.8rem); line-height: 0.98; letter-spacing: -0.07em; font-weight: 850; }
    .auth-brand-copy { max-width: 34rem; margin-top: 1.2rem; color: #eee9ff; font-size: 1.08rem; line-height: 1.7; }
    .auth-brand-points { display: flex; flex-wrap: wrap; gap: 0.65rem; margin-top: 2rem; }
    .auth-brand-point { padding: 0.55rem 0.8rem; border: 1px solid rgba(255, 255, 255, 0.24); border-radius: 999px; background: rgba(255, 255, 255, 0.1); color: #fff; font-size: 0.78rem; font-weight: 750; }

    .auth-form-panel { display: flex; align-items: center; justify-content: center; padding: clamp(1.2rem, 5vw, 5rem); background: #f6f3ff; }
    .auth-card { width: min(100%, 34rem); padding: clamp(1.4rem, 4vw, 2.7rem); border: 1px solid #e4dcff; border-radius: 1.5rem; background: rgba(255, 255, 255, 0.94); box-shadow: 0 1.8rem 4rem rgba(55, 35, 119, 0.16); animation: auth-card-enter 260ms ease-out both; }
    .auth-card.signup { width: min(100%, 39rem); }
    .auth-kicker { color: #6a4bc2; font-size: 0.72rem; font-weight: 850; letter-spacing: 0.16em; text-transform: uppercase; }
    .auth-title { margin-top: 0.55rem; color: #21113e; font-size: clamp(1.9rem, 3vw, 2.55rem); font-weight: 850; letter-spacing: -0.055em; }
    .auth-subtitle { margin-top: 0.6rem; color: #5d5372; line-height: 1.55; }
    .auth-field { margin-top: 0.85rem; }
    .auth-field .q-field__control { min-height: 3.45rem; border-radius: 0.9rem; background: #fff; transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease; }
    .auth-field .q-field__label { color: #6d6382; transition: color 180ms ease, transform 180ms ease; }
    .auth-field.q-field--focused .q-field__control { border-color: #6846d8; box-shadow: 0 0 0 0.22rem rgba(104, 70, 216, 0.18); transform: translateY(-1px); }
    .auth-field.q-field--focused .q-field__label { color: #5b35c0; }
    .auth-field input:focus-visible, .auth-field textarea:focus-visible { outline: none; }
    .auth-primary { min-height: 3.3rem; margin-top: 1.2rem; border-radius: 0.9rem !important; background: #5b35c0 !important; color: #fff !important; box-shadow: 0 0.8rem 1.5rem rgba(91, 53, 192, 0.22); font-weight: 800; transition: transform 160ms ease, opacity 160ms ease, box-shadow 160ms ease; }
    .auth-primary:hover { background: #4825a9 !important; transform: translateY(-2px); box-shadow: 0 1rem 1.8rem rgba(91, 53, 192, 0.28); }
    .auth-primary:active { transform: scale(0.98); opacity: 0.9; }
    .auth-primary:focus-visible, .auth-link:focus-visible, .auth-skip:focus-visible { outline: 3px solid #b79cff !important; outline-offset: 3px; }
    .auth-link { color: #5832bc !important; font-weight: 800; text-decoration: underline; text-underline-offset: 0.18em; }
    .auth-link:hover { color: #351681 !important; }
    .auth-footer { justify-content: center; margin-top: 1.2rem; color: #665b79; font-size: 0.92rem; }
    .auth-error { min-height: 0; margin-top: 0.8rem; color: #a12845; font-size: 0.88rem; font-weight: 700; }
    .auth-error-visible { padding: 0.7rem 0.8rem; border: 1px solid #e8a5b4; border-radius: 0.7rem; background: #fff2f5; animation: auth-error-shake 220ms ease-out both; }
    .auth-helper { margin-top: 0.8rem; color: #665b79; font-size: 0.82rem; line-height: 1.5; }
    .auth-profile-box { margin-top: 1.4rem; padding-top: 1.2rem; border-top: 1px solid #e7e0f4; }
    .auth-profile-box .q-field__control { background: #fcfaff; }
    .auth-skip { color: #352250; font-weight: 700; }
    .auth-password-note { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

    @keyframes auth-card-enter { from { opacity: 0; transform: translateY(0.7rem); } to { opacity: 1; transform: translateY(0); } }
    @keyframes auth-error-shake { 0%, 100% { transform: translateX(0); } 35% { transform: translateX(-0.25rem); } 70% { transform: translateX(0.25rem); } }

    @media (max-width: 900px) {
        .auth-screen { display: block; overflow: visible; }
        .auth-brand-panel { min-height: 15rem; padding: 2rem 1.4rem 2.4rem; }
        .auth-brand-name { font-size: 2.8rem; }
        .auth-brand-copy { font-size: 0.96rem; }
        .auth-form-panel { min-height: calc(100vh - 15rem); padding: 1.2rem; }
        .auth-brand-panel::before { width: 18rem; height: 18rem; right: -8rem; top: -6rem; }
    }

    @media (prefers-reduced-motion: reduce) {
        .auth-card, .auth-error-visible { animation: none; }
        .auth-field .q-field__control, .auth-primary { transition: none; }
    }

    @media (max-width: 860px) {
        .saksham-main {
            padding: 0.8rem;
        }
    }
</style>
''')


def apply_accessibility_profile(profile: dict[str, object]) -> None:
    """Turn disclosed functional needs into reversible session defaults."""
    app_state.accessibility_profile = profile
    disclosed = bool(profile.get('disclosed'))
    if not disclosed:
        app_state.voice_mode = False
        app_state.stt_phrase_seconds = 12
        return

    visual = bool(profile.get('visual_impairment'))
    extended_listening = bool(
        profile.get('motor_impairment') or profile.get('speech_difficulty')
    )
    speech_difficulty = bool(profile.get('speech_difficulty'))
    app_state.voice_mode = visual and not speech_difficulty
    app_state.stt_phrase_seconds = 20 if extended_listening else 12
    if visual:
        app_state.preferences.text_size = 'large'
        app_state.preferences.theme = 'contrast'


def establish_session(user: dict[str, object]) -> None:
    app_state.authenticated = True
    app_state.auth_user_id = int(user['id'])
    app_state.username = str(user['username'])
    app_state.auth_expires_at = time.time() + SESSION_SECONDS
    apply_accessibility_profile(get_accessibility_profile(app_state.auth_user_id))


def logout() -> None:
    app_state.clear_authentication()
    app_state.start_fresh()
    render_application()


def _profile_values(selected: list[str], other_notes: str) -> dict[str, object]:
    skipped = 'Prefer not to say / Skip' in selected
    values = {
        key: label in selected for label, key in ACCESSIBILITY_OPTIONS.items()
    }
    values['other_notes'] = other_notes if not skipped else ''
    values['disclosed'] = bool(selected) and not skipped
    return values


def render_auth() -> None:
    with ui.element('div').classes('auth-screen'):
        with ui.element('section').classes('auth-brand-panel').props('aria-label="SakshamAI introduction"'):
            ui.label('✦').classes('auth-brand-mark').props('aria-label="SakshamAI mark"')
            ui.label('SakshamAI').classes('auth-brand-name')
            ui.label('Learn at your pace, with support that adapts to you.').classes('auth-brand-copy')
            with ui.row().classes('auth-brand-points'):
                ui.label('Document-grounded learning').classes('auth-brand-point')
                ui.label('Clearer study tools').classes('auth-brand-point')
                ui.label('Built for access').classes('auth-brand-point')

        with ui.element('main').classes('auth-form-panel'):
            card_class = 'auth-card signup' if app_state.auth_mode == 'signup' else 'auth-card'
            with ui.card().classes(card_class):
                ui.label('YOUR LEARNING SPACE').classes('auth-kicker')
                if app_state.auth_mode == 'login':
                    ui.label('Welcome back').classes('auth-title')
                    ui.label('Pick up where you left off in your study space.').classes('auth-subtitle')
                    username = ui.input('Username or email').classes('auth-field w-full').props('outlined autocomplete=username')
                    password = ui.input('Password', password=True, password_toggle_button=True).classes('auth-field w-full').props('outlined autocomplete=current-password')
                    ui.label('Password visibility can be changed with the eye control.').classes('auth-password-note')
                    error_label = ui.label('').classes('auth-error')

                    async def submit_login() -> None:
                        login_button.props('loading').disable()
                        user = await run.io_bound(verify_login, username.value or '', password.value or '')
                        if not user:
                            error_label.set_text('⚠ Invalid username or password. Please check both fields and try again.')
                            error_label.classes('auth-error-visible')
                            login_button.enable().props(remove='loading')
                            return
                        establish_session(user)
                        render_application()

                    login_button = ui.button('Log In', on_click=submit_login).classes('auth-primary w-full')
                    with ui.row().classes('auth-footer w-full'):
                        ui.label("Don't have an account?")
                        ui.button('Create an account', on_click=lambda: switch_auth_mode('signup')).props('flat').classes('auth-link')
                else:
                    ui.label('Create your account').classes('auth-title')
                    ui.label('Start a private study space that can adapt to how you learn.').classes('auth-subtitle')
                    username = ui.input('Username or email').classes('auth-field w-full').props('outlined autocomplete=username')
                    password = ui.input('Password (at least 8 characters)', password=True, password_toggle_button=True).classes('auth-field w-full').props('outlined autocomplete=new-password')
                    confirm = ui.input('Confirm password', password=True, password_toggle_button=True).classes('auth-field w-full').props('outlined autocomplete=new-password')
                    ui.label('Password visibility can be changed with the eye control.').classes('auth-password-note')
                    error_label = ui.label('').classes('auth-error')

                    with ui.element('section').classes('auth-profile-box'):
                        ui.label('Optional accessibility profile').classes('text-xl font-bold text-[#291743]')
                        ui.label('Accessibility questions are optional. They help us turn on the right features automatically, and you can skip them or change them anytime in Accessibility Settings.').classes('auth-helper')
                        ui.label('Choose broad functional categories only. This is not a medical form.').classes('auth-helper')
                        selected = ui.select(
                            [*ACCESSIBILITY_OPTIONS.keys(), 'Other', 'Prefer not to say / Skip'],
                            multiple=True,
                            label='Accessibility needs (optional)',
                        ).classes('auth-field w-full').props('outlined use-chips')
                        ui.label('Prefer not to say / Skip is equally valid and keeps this unanswered.').classes('auth-skip auth-helper')
                        other_notes = ui.textarea('Other (optional)').classes('auth-field w-full').props('outlined')

                    async def submit_signup() -> None:
                        if password.value != confirm.value:
                            error_label.set_text('⚠ Passwords do not match. Please re-enter the same password.')
                            error_label.classes('auth-error-visible')
                            return
                        if len(password.value or '') < 8:
                            error_label.set_text('⚠ Use a password with at least 8 characters.')
                            error_label.classes('auth-error-visible')
                            return
                        choices = list(selected.value or [])
                        if 'Prefer not to say / Skip' in choices and len(choices) > 1:
                            error_label.set_text('⚠ Choose accessibility categories or Prefer not to say / Skip, not both.')
                            error_label.classes('auth-error-visible')
                            return
                        signup_button.props('loading').disable()
                        try:
                            user_id = await run.io_bound(create_user, username.value or '', password.value or '')
                            profile = _profile_values(choices, other_notes.value or '')
                            await run.io_bound(update_accessibility_profile, user_id, **profile)
                            user = await run.io_bound(verify_login, username.value or '', password.value or '')
                            if user:
                                establish_session(user)
                                render_application()
                        except ValueError as error:
                            error_label.set_text(f'⚠ {error}')
                            error_label.classes('auth-error-visible')
                            signup_button.enable().props(remove='loading')

                    signup_button = ui.button('Create Account', on_click=submit_signup).classes('auth-primary w-full')
                    with ui.row().classes('auth-footer w-full'):
                        ui.label('Already have an account?')
                        ui.button('Back to Login', on_click=lambda: switch_auth_mode('login')).props('flat').classes('auth-link')


def switch_auth_mode(mode: str) -> None:
    app_state.auth_mode = mode
    render_application()


def change_page(page: str) -> None:
    app_state.page = page
    render_page()


def render_page() -> None:
    content.clear()
    with content:
        with ui.row().classes('w-full items-center justify-between saksham-topbar'):
            ui.label(app_state.page.title()).classes('font-bold text-lg text-slate-800')
            ui.label('● Ready to learn').classes('saksham-status')

        if app_state.page == 'home':
            render_home()
        elif app_state.page == 'documents':
            render_documents()
        elif app_state.page == 'chat':
            render_chat()
        elif app_state.page == 'notes':
            render_notes()
        elif app_state.page == 'quiz':
            render_quiz()
        elif app_state.page == 'flashcards':
            render_flashcards()
        elif app_state.page == 'accessibility':
            render_accessibility_settings()


def render_home() -> None:
    with ui.column().classes('w-full h-full min-h-[calc(100vh-150px)] justify-between gap-4'):
        with ui.column().classes('w-full gap-4'):
            with ui.element('div').classes('saksham-hero'):
                ui.label('Accessible learning assistant').classes('text-xs uppercase tracking-[0.2em] text-indigo-700 font-bold')
                ui.label('Your study material, made clearer.').classes('saksham-page-title mt-2')
                ui.label('Bring in a document, ask questions in plain language, then turn it into notes, flashcards and a quiz whenever you are ready.').classes('saksham-subtitle mt-2 max-w-3xl')
                with ui.row().classes('wrap gap-2 mt-3'):
                    for tag in ['Document-grounded answers', 'Simple explanations', 'Built for focus']:
                        ui.label(tag).classes('saksham-pill')

        with ui.row().classes('w-full gap-3 items-center saksham-composer mt-auto'):
            with ui.button(icon='add', color='primary').classes('!min-w-12 !w-12 !h-12 rounded-full shadow-md'):
                with ui.menu() as menu:
                    ui.menu_item('Upload document', on_click=lambda: change_page('documents'))
                    ui.menu_item('Quiz', on_click=lambda: change_page('quiz'))
                    ui.menu_item('Flashcards', on_click=lambda: change_page('flashcards'))
            question_input = ui.input('Ask SakshamAI anything...').classes('flex-1').props('outlined')
            ui.button('Send', on_click=lambda: send_chat_message(question_input.value)).classes('bg-indigo-600 text-white rounded-full px-5')


def render_documents() -> None:
    ui.label('Document workspace').classes('saksham-page-title')
    ui.label('Upload a clear PDF, image, or text file. SakshamAI extracts the text and keeps it ready for chat and study tools.').classes('saksham-subtitle')

    with ui.card().classes('saksham-card mt-4'):
        ui.label('Drop your document here').classes('font-bold text-lg')
        ui.upload(on_upload=handle_upload, auto_upload=True).props('multiple=False').classes('w-full mt-2')

    if app_state.document_result:
        with ui.card().classes('saksham-card mt-4'):
            ui.label('Current document').classes('font-bold text-lg')
            ui.label(app_state.document_name).classes('text-slate-700 mt-2')
            ui.label(f'{len(app_state.document_text):,} characters extracted').classes('text-sm text-slate-600 mt-1')
            with ui.expander('Preview extracted text'):
                ui.textarea(value=app_state.document_text).props('readonly autogrow')


async def handle_upload(event) -> None:
    """Process the file supplied by NiceGUI's single-file upload event."""
    file = event.file
    try:
        ui.notify('Preparing your document...', type='ongoing')
        result = process_uploaded_document(await file.read(), file.name)
        app_state.document_result = result
        app_state.document_name = result.filename
        app_state.document_text = result.full_text
        app_state.chat_history = []
        app_state.notes = ''
        app_state.quiz = ''
        app_state.flashcards = ''
        app_state.page = 'chat'
        render_page()
        ui.notify('Document ready. You can ask questions now.', type='positive')
    except Exception as exc:
        app_state.last_error = str(exc)
        ui.notify(f'We could not process that file: {exc}', type='negative')


def render_chat() -> None:
    if not app_state.document_text:
        ui.label('Ask your document').classes('saksham-page-title')
        ui.label('Add and process a document first, then SakshamAI can answer using your material.').classes('saksham-subtitle')
        ui.button('Add document', on_click=lambda: change_page('documents')).classes('bg-indigo-600 text-white')
        return

    ui.label('Ask your document').classes('saksham-page-title')
    ui.label(f'📄 {app_state.document_name}').classes('saksham-badge')

    with ui.card().classes('saksham-card mt-4'):
        with ui.column().classes('w-full gap-3 saksham-chat-scroll'):
            for item in app_state.chat_history:
                with ui.row().classes('w-full justify-end' if item['role'] == 'user' else 'w-full justify-start'):
                    ui.label(item['content']).classes(
                        'saksham-message user'
                        if item['role'] == 'user'
                        else 'saksham-message assistant'
                    )

    with ui.row().classes('w-full gap-3 mt-4 items-center saksham-composer'):
        ui.button('+', on_click=lambda: ui.notify('Upload or attach features are available in the document workflow.', type='info')).classes('bg-slate-200 text-slate-900 min-w-12')
        question_input = ui.input('Ask SakshamAI anything...').classes('flex-1').props('outlined')
        ui.button('Send', on_click=lambda: send_chat_message(question_input.value)).classes('bg-indigo-600 text-white')
        voice_label = '🎙 Voice mode on' if app_state.voice_mode else '🎙 Voice'
        ui.button(voice_label, on_click=handle_voice_question).classes('bg-slate-200 text-slate-900 min-w-12')


async def handle_voice_question() -> None:
    """Use the profile-selected listening duration and always keep text visible."""
    if not app_state.document_text:
        ui.notify('Add and process a document before using voice mode.', type='warning')
        return
    try:
        app_state.voice.phase = 'listening'
        ui.notify(f'Listening for up to {app_state.stt_phrase_seconds} seconds...', type='ongoing')
        audio_path = await run.io_bound(record_question, app_state.stt_phrase_seconds)
        app_state.voice.phase = 'transcribing'
        question = await run.io_bound(transcribe, audio_path)
        app_state.voice.heard = question
        if app_state.chatbot is None:
            app_state.chatbot = build_chatbot(app_state.document_text, app_state.document_name)
        app_state.chat_history.append({'role': 'user', 'content': question})
        app_state.voice.phase = 'thinking'
        answer = await run.io_bound(ask_question, app_state.chatbot, question)
        app_state.chat_history.append({'role': 'assistant', 'content': answer})
        app_state.voice.answer = answer
        app_state.voice.phase = 'speaking' if app_state.voice_mode else 'idle'
        if app_state.voice_mode and app_state.preferences.speak_replies:
            await run.io_bound(speak, answer)
        app_state.voice.phase = 'idle'
        render_page()
    except Exception as error:
        app_state.voice.phase = 'error'
        app_state.voice.message = str(error)
        ui.notify(f'Voice mode could not complete: {error}', type='negative')


def send_chat_message(question: str | None) -> None:
    value = (question or '').strip()
    if not value:
        ui.notify('Please enter a question.', type='warning')
        return
    if app_state.chatbot is None:
        app_state.chatbot = build_chatbot(app_state.document_text, app_state.document_name)
    app_state.chat_history.append({'role': 'user', 'content': value})
    try:
        ui.notify('SakshamAI is thinking...', type='ongoing')
        answer = ask_question(app_state.chatbot, value)
        app_state.chat_history.append({'role': 'assistant', 'content': answer})
        render_page()
    except Exception as exc:
        app_state.last_error = str(exc)
        ui.notify(f'Something went wrong: {exc}', type='negative')


def render_notes() -> None:
    ui.label('Study notes').classes('saksham-page-title')
    ui.label('Create a concise study guide from a document or a topic you choose.').classes('saksham-subtitle')
    if not app_state.notes:
        render_material_start('notes', 'Create notes')
    else:
        with ui.card().classes('saksham-card mt-4'):
            ui.markdown(app_state.notes)


def render_quiz() -> None:
    ui.label('Practice quiz').classes('saksham-page-title')
    ui.label('Enter a topic for a 5-question quiz, or use your current document.').classes('saksham-subtitle')
    if not app_state.quiz:
        render_material_start('quiz', 'Generate 5-question quiz')
    else:
        with ui.card().classes('saksham-card mt-4'):
            ui.markdown(app_state.quiz)


def render_flashcards() -> None:
    ui.label('Flashcards').classes('saksham-page-title')
    ui.label('Create flashcards from a topic or from your current document.').classes('saksham-subtitle')
    if not app_state.flashcards:
        render_material_start('flashcards', 'Create flashcards')
    else:
        with ui.card().classes('saksham-card mt-4'):
            ui.markdown(app_state.flashcards)


def render_accessibility_settings() -> None:
    """Private, editable accessibility settings for the signed-in student."""
    profile = app_state.accessibility_profile
    ui.label('Accessibility Settings').classes('saksham-page-title')
    ui.label('These choices only change how SakshamAI responds in your session. They are optional, private to your account, and can be changed or cleared at any time.').classes('saksham-subtitle')
    if profile.get('cognitive_learning_difficulty'):
        ui.label('A simplified-layout mode is planned as a future enhancement; no cognitive or learning need is inferred from an unanswered profile.').classes('text-slate-600 mb-3')
    with ui.card().classes('saksham-card mt-4 w-full max-w-3xl'):
        ui.label('Your accessibility profile').classes('text-xl font-bold')
        ui.label('Choose broad functional categories only. You can select more than one, or choose Prefer not to say / Skip.').classes('text-slate-600 mt-1')
        checks = {
            label: ui.checkbox(label, value=bool(profile.get(key)))
            for label, key in ACCESSIBILITY_OPTIONS.items()
        }
        other = ui.checkbox('Other', value=bool(profile.get('other_notes')))
        skip = ui.checkbox('Prefer not to say / Skip', value=not bool(profile.get('disclosed')))
        other_notes = ui.textarea('Other (optional)', value=str(profile.get('other_notes') or '')).classes('w-full mt-2').props('outlined')

        def save_profile() -> None:
            selected = [label for label, checkbox in checks.items() if checkbox.value]
            if other.value:
                selected.append('Other')
            if skip.value:
                values = _profile_values(['Prefer not to say / Skip'], '')
            else:
                values = _profile_values(selected, other_notes.value or '')
            update_accessibility_profile(app_state.auth_user_id, **values)
            apply_accessibility_profile(get_accessibility_profile(app_state.auth_user_id))
            ui.notify('Accessibility settings updated. Adapted behavior changed for this session.', type='positive')
            render_page()

        def clear_profile() -> None:
            update_accessibility_profile(app_state.auth_user_id)
            apply_accessibility_profile(get_accessibility_profile(app_state.auth_user_id))
            ui.notify('Accessibility profile cleared. SakshamAI has returned to its standard behavior.', type='positive')
            render_application()

        with ui.row().classes('gap-3 mt-4'):
            ui.button('Save settings', on_click=save_profile).classes('bg-indigo-600 text-white')
            ui.button('Clear profile', on_click=clear_profile).props('outline color=negative')


def render_material_start(kind: str, label: str) -> None:
    """Offer a document source when present, otherwise ask for a study topic."""
    if app_state.document_text:
        ui.button(f'{label} from document', on_click=lambda: generate_material(kind)).classes('bg-indigo-600 text-white')
        ui.label('Or choose a different topic').classes('text-sm text-slate-600 mt-4')
    topic = ui.input('Topic', placeholder='For example: photosynthesis, algebra, or the French Revolution').classes('w-full max-w-xl mt-2').props('outlined')
    ui.button(label, on_click=lambda: generate_material(kind, topic.value)).classes('bg-indigo-600 text-white mt-2')


def generate_material(kind: str, topic: str | None = None) -> None:
    source_topic = (topic or '').strip()
    if not app_state.document_text and not source_topic:
        ui.notify('Enter a topic to get started.', type='warning')
        return
    try:
        ui.notify(f'Creating {kind}...', type='ongoing')
        if kind == 'notes':
            app_state.notes = generate_notes_for_topic(source_topic) if source_topic else generate_notes(app_state.document_text)
        elif kind == 'quiz':
            app_state.quiz = generate_quiz_for_topic(source_topic) if source_topic else generate_quiz(app_state.document_text)
        elif kind == 'flashcards':
            app_state.flashcards = generate_flashcards_for_topic(source_topic) if source_topic else generate_flashcards(app_state.document_text)
        render_page()
        ui.notify(f'{kind.title()} ready.', type='positive')
    except Exception as exc:
        app_state.last_error = str(exc)
        ui.notify(f'Could not create {kind}: {exc}', type='negative')


app_root = ui.column().classes('w-full')
content = None


def render_workspace_shell() -> None:
    global content
    app_root.clear()
    with app_root:
        with ui.row().classes('saksham-shell no-wrap w-full'):
            with ui.column().classes('saksham-sidebar w-72'):
                with ui.row().classes('items-center gap-3 px-2'):
                    ui.label('✦').classes('saksham-logo')
                    ui.label('SakshamAI').classes('saksham-brand')
                ui.label('Accessible study workspace').classes('saksham-tagline')

                ui.label('Workspace').classes('saksham-nav-section')
                for key, label, icon in NAV_ITEMS:
                    button = ui.button(f'{icon} {label}', on_click=lambda key=key: change_page(key)).classes('saksham-nav-button')
                    if app_state.page == key:
                        button.classes('active')
                ui.button('Log out', on_click=logout).classes('saksham-nav-button mt-4')

                ui.label('Current material').classes('saksham-nav-section')
                ui.label(app_state.document_name or 'Nothing loaded yet').classes('text-sm text-slate-200 px-2')
                ui.label(f'Signed in as {app_state.username}').classes('text-xs text-slate-300 px-2 mt-3')

            main_classes = 'saksham-main flex-1'
            if app_state.preferences.text_size in {'large', 'larger'}:
                main_classes += ' profile-large-text'
            if app_state.preferences.theme == 'contrast':
                main_classes += ' profile-contrast'
            if app_state.accessibility_profile.get('motor_impairment'):
                main_classes += ' profile-motor'
            with ui.column().classes(main_classes):
                content = ui.column().classes('w-full')
    render_page()


def render_application() -> None:
    if app_state.authenticated and app_state.auth_expires_at <= time.time():
        app_state.clear_authentication()
        ui.notify('Your session expired. Please log in again.', type='warning')
    app_root.clear()
    if app_state.authenticated:
        render_workspace_shell()
    else:
        render_auth()


render_application()

APP_PORT = int(os.getenv('SAKSHAM_PORT', '8010'))
ui.run(title='SakshamAI 2.0', favicon='✦', host='127.0.0.1', port=APP_PORT, reload=False)
