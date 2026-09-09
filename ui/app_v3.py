"""SakshamAI's accessible Streamlit interface.

Run from the project root with:
    streamlit run ui/app_v3.py
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent.parent
for folder in (ROOT, ROOT / "chatbot-voice", ROOT / "gemini-core"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from ui.services.bootstrap import BackendError, prepare_backend
from ui.services.chatbot_service import ask as ask_question
from ui.services.chatbot_service import attach_document, create_chatbot
from ui.services.document_service import (
    extract_document,
    load_document_library,
    save_document_to_library,
)
from ui.services.study_service import (
    generate_flashcards,
    generate_flashcards_for_topic,
    generate_notes,
    generate_notes_for_topic,
    generate_quiz,
    generate_quiz_for_topic,
    parse_quiz,
    parse_flashcards,
)
from ui.services.voice_service import microphone_available, record_question, speak, transcribe
from ui.auth_mongo import get_accessibility_profile, update_accessibility_profile
from ui.login_page import ACCESSIBILITY_OPTIONS, render_login_page

prepare_backend()


st.set_page_config("SakshamAI | Learn your way", "✦", layout="wide", initial_sidebar_state="expanded")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root { --bg:#f3f1ec; --ink:#172038; --muted:#7c8495; --line:#dedbd4; --violet:#6558e8; --light-purple:#e9e6ff; --mint:#e4f5ec; --navy:#151b31; }
        .stApp { background:var(--bg); color:var(--ink); }
        footer, #MainMenu { visibility:hidden; }
        header[data-testid="stHeader"] { visibility:visible; background:transparent; }
        [data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapseButton"] button, [data-testid="stExpandSidebarButton"] { visibility:visible!important; opacity:1!important; }
        [data-testid="stSidebarCollapseButton"] button, button[data-testid="stExpandSidebarButton"] { position:fixed!important; z-index:1100!important; width:34px!important; height:34px!important; min-height:34px!important; padding:0!important; border:1px solid #38405a!important; border-radius:10px!important; background:var(--navy)!important; color:#fff!important; box-shadow:0 8px 20px #14192d3d!important; }
        [data-testid="stSidebarCollapseButton"] button { left:40px!important; top:30px!important; }
        button[data-testid="stExpandSidebarButton"] { left:22px!important; top:30px!important; }
        [data-testid="stSidebarCollapseButton"] button:hover, button[data-testid="stExpandSidebarButton"]:hover, [data-testid="stSidebarCollapseButton"] button:focus-visible, button[data-testid="stExpandSidebarButton"]:focus-visible { background:#293251!important; color:#fff!important; outline:2px solid #9dcdff!important; outline-offset:2px; }
        [data-testid="stSidebarCollapseButton"] button > svg, button[data-testid="stExpandSidebarButton"] > svg { animation:corner-icon-breathe 2.2s ease-in-out infinite; transform-origin:center; }
        header[data-testid="stHeader"] { background:transparent; }
        .block-container { max-width:1280px; padding:28px 28px 120px 110px; }
        section[data-testid="stSidebar"] { position:fixed; left:22px; top:22px; bottom:22px; width:70px!important; min-width:70px!important; z-index:999; background:var(--navy); border:0; border-radius:28px; box-shadow:0 18px 45px #14192d24; overflow:hidden; cursor:default; user-select:none; }
        section[data-testid="stSidebar"] > div { padding:18px 9px; }
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] { overflow:hidden; }
        .sidebar-brand { display:flex; justify-content:center; margin-bottom:40px; cursor:default; user-select:none; }
        section[data-testid="stSidebar"] .stButton { margin:4px 0; }
        section[data-testid="stSidebar"] .stButton button { width:100%; color:#dce4ff!important; background:transparent; border:1px solid #263556; border-radius:10px; text-align:left; font-size:13px; font-weight:650; min-height:42px; padding:0 10px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; transition:background .18s ease, border-color .18s ease, transform .18s ease; }
        section[data-testid="stSidebar"] .stButton button:hover { background:#202e52; border-color:#3b4b78; color:white!important; transform:translateY(-1px); }
        section[data-testid="stSidebar"] .stButton button:active { background:#354b88; border-color:#a8bbff; }
        section[data-testid="stSidebar"] .stButton button:focus-visible { outline:3px solid #9dcdff; outline-offset:2px; }
        section[data-testid="stSidebar"] .stButton button p { display:flex; align-items:center; justify-content:flex-start; gap:6px; margin:0; white-space:nowrap; }
        section[data-testid="stSidebar"] .stButton button:first-letter { color:#a9b8ff; }
        .logo { flex:0 0 36px; width:36px; height:36px; display:inline-flex; align-items:center; justify-content:center; border-radius:11px; background:linear-gradient(135deg,#8d79ff,#5b54ef); color:#fff; font-size:19px; box-shadow:0 8px 22px #0004; cursor:default; user-select:none; }
        .brand, .side-note, .side-label, .sidebar-material { display:none; }
        section[data-testid="stSidebar"] .stButton { margin:6px 0; }
        section[data-testid="stSidebar"] .stButton button { width:44px; height:44px; min-height:44px; padding:0; color:#b8bfd2!important; background:transparent; border:0; border-radius:14px; font-size:0; cursor:pointer; user-select:none; transition:background .18s ease, color .18s ease, transform .18s ease; }
        section[data-testid="stSidebar"] .stButton button p { justify-content:center; font-size:20px; }
        section[data-testid="stSidebar"] .stButton button:hover, section[data-testid="stSidebar"] .stButton button:focus-visible { background:#293251; color:#fff!important; transform:translateY(-1px); outline:2px solid #9dcdff; outline-offset:2px; }
        section[data-testid="stSidebar"] .stButton button[kind="primary"] { background:#293251!important; color:#fff!important; }
        .nav-divider { width:34px; height:1px; background:#38405a; margin:30px auto 18px; }
        .top { display:flex; justify-content:space-between; align-items:center; margin:0 0 78px; animation:rise-in .45s ease both; }
        .crumb { color:var(--ink); font-size:16px; font-weight:750; }.app-name { color:var(--muted); font-size:10px; font-weight:750; letter-spacing:1.4px; margin-top:5px; }
        .status { border-radius:99px; padding:8px 13px; color:#24845d; background:var(--mint); font-size:11px; font-weight:750; }
        .welcome { position:relative; max-width:780px; margin:0; text-align:left; animation:rise-in .6s .08s ease both; }
        .welcome-kicker { color:var(--muted); font-size:10px; font-weight:750; letter-spacing:1.5px; text-transform:uppercase; }
        .welcome h1 { color:var(--ink); font-size:clamp(44px, 5vw, 58px); line-height:1; margin:18px 0 24px; letter-spacing:-2px; font-weight:700; }.welcome h1 span { color:var(--violet); }
        .welcome p { color:var(--muted); font-size:16px; line-height:1.65; margin:0; max-width:560px; }
        .document-status { display:inline-flex; align-items:center; gap:9px; margin-top:27px; padding:10px 15px; border:1px solid var(--line); background:#fff9; border-radius:20px; color:var(--muted); font-size:11px; font-weight:650; }.document-dot { width:7px; height:7px; border-radius:50%; background:#a9afbc; }
        .orbit { position:absolute; right:9%; top:285px; width:310px; height:310px; border:1px solid #bdb6ed; border-radius:50%; opacity:.8; animation:slow-float 12s ease-in-out infinite, orbit-breathe 3.2s ease-in-out infinite; }.orbit:before { content:""; position:absolute; inset:48px; border:1px solid #c9c5d8; border-radius:50%; animation:ring-breathe 3.2s ease-in-out infinite; }.orbit:after { content:""; position:absolute; width:24px; height:24px; left:143px; top:143px; border-radius:50%; background:var(--violet); box-shadow:0 0 0 10px #6558e814, 0 0 35px #6558e82e; animation:icon-breathe 2.2s ease-in-out infinite; }
        .section-title { font-size:24px; font-weight:750; margin:24px 0 4px; }.section-copy { font-size:14px; color:var(--muted); margin:0 0 15px; }
        .card { background:#fff; border:1px solid var(--line); min-height:170px; padding:21px; border-radius:8px; box-shadow:0 5px 18px #1b295009; }.card-icon { font-size:27px; }.card h3 { font-size:16px; margin:11px 0 7px; }.card p { color:var(--muted); font-size:13px; line-height:1.6; margin:0; }
        .st-key-study-topic { position:relative; max-width:900px; margin:30px 0 18px; padding:24px 24px 20px; overflow:hidden; background:linear-gradient(135deg,#ffffffef 0%,#f5f3ffed 72%,#edf9f6e8 100%); border:1px solid #ddd8f4; border-radius:20px; box-shadow:0 16px 40px #302a6d14; animation:study-rise .55s .08s ease both; }
        .st-key-study-topic::after { content:"✦"; position:absolute; top:20px; right:24px; display:grid; place-items:center; width:34px; height:34px; border:1px solid #d7d0fb; border-radius:50%; background:#fff9; color:#766be9; font-size:16px; animation:sparkle-breathe 2.8s ease-in-out infinite; }
        .st-key-study-topic [data-testid="stTextInput"] label { font-size:15px; font-weight:750; color:var(--ink)!important; }
        .st-key-study-topic [data-testid="stTextInput"] input { height:54px!important; background:#fff!important; border:1px solid #c5bef0!important; border-radius:13px!important; color:var(--ink)!important; font-size:15px!important; box-shadow:0 5px 14px #302a6d0a; transition:border-color .2s ease, box-shadow .2s ease, transform .2s ease; }
        .st-key-study-topic [data-testid="stTextInput"] input:focus { border-color:var(--violet)!important; box-shadow:0 0 0 4px #6558e82b, 0 8px 20px #302a6d14!important; transform:translateY(-1px); }
        .study-progress { margin:16px 2px 2px; color:#58627a; font-size:12px; font-weight:650; }
        .study-progress-head { display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:8px; }
        .study-progress-label { color:var(--ink); }
        .study-dots { color:#6558e8; letter-spacing:3px; animation:dots-pulse 1.6s ease-in-out infinite; }
        .study-progress-track { height:4px; overflow:hidden; border-radius:99px; background:#e5e2f5; }
        .study-progress-fill { width:62%; height:100%; border-radius:inherit; background:linear-gradient(90deg,#6558e8,#6fcab8); animation:progress-glide 2.8s ease-in-out infinite; transform-origin:left; }
        .study-options { margin:26px 0 30px; }
        [class*="st-key-study-option-"] { position:relative; min-height:156px; padding:20px 20px 14px; overflow:hidden; background:#fff; border:1px solid #dedfe8; border-radius:16px; box-shadow:0 8px 22px #1720380b; animation:study-rise .55s ease both; transition:transform .22s ease, box-shadow .22s ease, border-color .22s ease; }
        [class*="st-key-study-option-"]:hover { transform:translateY(-4px); border-color:#bdb5f0; box-shadow:0 16px 30px #302a6d18; }
        [class*="st-key-study-option-"]::before { content:""; position:absolute; inset:0 auto 0 0; width:4px; background:linear-gradient(180deg,#6558e8,#71c8b6); opacity:.35; transition:opacity .2s ease; }
        [class*="st-key-study-option-"]:hover::before { opacity:1; }
        .study-option-icon { display:grid; place-items:center; width:38px; height:38px; margin-bottom:14px; border-radius:12px; background:#f0edff; color:#5f54d8; font-size:19px; }
        .study-option-title { margin:0 0 5px; color:var(--ink); font-size:16px; font-weight:800; }
        .study-option-copy { min-height:34px; margin:0 0 11px; color:var(--muted); font-size:12px; line-height:1.45; }
        [class*="st-key-study-option-"] .stButton button { width:100%; min-height:38px; background:transparent!important; color:#554ac2!important; border:1px solid #d9d4f7!important; border-radius:9px!important; font-size:12px; font-weight:750; transition:background .2s ease, border-color .2s ease; }
        [class*="st-key-study-option-"] .stButton button:hover { background:#f0edff!important; border-color:#9d93ed!important; }
        [class*="st-key-study-option-"]:has(.study-option-check) { background:linear-gradient(135deg,#fff 0%,#f4f1ff 100%); border-color:#aaa0ed; }
        .study-option-check { position:absolute; top:14px; right:16px; display:grid; place-items:center; width:22px; height:22px; border-radius:50%; background:#6558e8; color:#fff; font-size:12px; font-weight:800; }
        .study-option:nth-child(2) { animation-delay:.08s; }.study-option:nth-child(3) { animation-delay:.16s; }
        .flashcard-deck { position:relative; width:min(620px,100%); height:390px; margin:28px auto 20px; perspective:1200px; }
        .flashcard-stack { position:absolute; inset:0; }
        .flashcard-stack-card { position:absolute; left:50%; width:92%; height:330px; transform:translateX(-50%); border:1px solid #d8d2f4; border-radius:22px; background:linear-gradient(145deg,#ffffff,#f1efff); box-shadow:0 16px 35px #17203812; opacity:.38; }
        .flashcard-stack-card.stack-one { top:22px; transform:translateX(-50%) rotate(2deg); opacity:.46; }
        .flashcard-stack-card.stack-two { top:12px; transform:translateX(-50%) rotate(-1.5deg); opacity:.62; }
        .flashcard-active { position:absolute; inset:0 0 32px; transform-style:preserve-3d; transition:transform .55s cubic-bezier(.2,.8,.2,1); }
        .flashcard-active.is-revealed { transform:rotateY(180deg); }
        .flashcard-face { position:absolute; inset:0; display:flex; flex-direction:column; backface-visibility:hidden; border:1px solid #c9c1f4; border-radius:22px; padding:28px 32px; background:linear-gradient(145deg,#fff 0%,#f8f7ff 68%,#eefaf7 100%); box-shadow:0 20px 45px #302a6d1c, 0 0 0 5px #aaa0ed12; }
        .flashcard-face.back { transform:rotateY(180deg); background:linear-gradient(145deg,#f3f0ff,#fff 65%,#e9f8f3); }
        .flashcard-meta { display:flex; align-items:center; justify-content:space-between; color:#6558e8; font-size:12px; font-weight:800; letter-spacing:.4px; }
        .flashcard-progress { color:#6f7a91; font-weight:700; }
        .flashcard-label { margin-top:38px; color:#6f7a91; font-size:11px; font-weight:800; letter-spacing:1.4px; text-transform:uppercase; }
        .flashcard-question, .flashcard-answer { margin:12px 0 0; color:var(--ink); font-size:clamp(20px,2.6vw,29px); line-height:1.25; font-weight:800; }
        .flashcard-answer { font-size:clamp(18px,2.2vw,25px); font-weight:700; }
        .flashcard-hint { margin-top:auto; color:#766be9; font-size:12px; font-weight:700; }
        .flashcard-controls { display:flex; justify-content:center; align-items:center; gap:12px; margin:8px auto 28px; }
        .flashcard-controls .stButton button { min-width:132px; min-height:44px; border:1px solid #d8d2f4!important; border-radius:12px!important; background:#fff!important; color:var(--ink)!important; font-weight:750; transition:transform .2s ease, box-shadow .2s ease, background .2s ease; }
        .flashcard-controls .stButton button:hover:not(:disabled) { transform:translateY(-2px); background:#f3f0ff!important; box-shadow:0 8px 18px #302a6d18; }
        .flashcard-controls .stButton button:disabled { opacity:.42; cursor:not-allowed; }
        .st-key-flashcard-flip-control .stButton button, .st-key-flashcard-controls .stButton button { min-height:44px!important; border:1px solid #d8d2f4!important; border-radius:12px!important; background:#fff!important; color:#172038!important; font-weight:750!important; opacity:1!important; }
        .st-key-flashcard-flip-control .stButton button p, .st-key-flashcard-flip-control .stButton button span, .st-key-flashcard-controls .stButton button p, .st-key-flashcard-controls .stButton button span { color:#172038!important; }
        .st-key-flashcard-flip-control .stButton button { background:var(--navy)!important; border-color:#38405a!important; color:#d9d2ff!important; }
        .st-key-flashcard-flip-control .stButton button p, .st-key-flashcard-flip-control .stButton button span { color:#d9d2ff!important; }
        .st-key-flashcard-flip-control .stButton button:hover { background:#242d49!important; border-color:#a99cff!important; color:#eeeaff!important; }
        .st-key-flashcard-flip-control .stButton button:hover p, .st-key-flashcard-flip-control .stButton button:hover span { color:#eeeaff!important; }
        .st-key-flashcard-controls .stButton button:hover:not(:disabled) { background:#f3f0ff!important; border-color:#9d93ed!important; color:#4438b4!important; }
        .st-key-flashcard-flip-control .stButton button:disabled, .st-key-flashcard-controls .stButton button:disabled { background:#eef0f5!important; color:#6f7a91!important; opacity:.65!important; }
        @media (max-width:650px) { .flashcard-deck { height:350px; margin-top:22px; }.flashcard-face { padding:22px; }.flashcard-label { margin-top:28px; }.flashcard-controls .stButton button { min-width:108px; } }
        section[data-testid="stMain"]::before, section[data-testid="stMain"]::after { content:""; position:fixed; z-index:-1; width:230px; height:230px; border-radius:50%; pointer-events:none; opacity:.11; filter:blur(2px); }
        section[data-testid="stMain"]::before { top:18%; right:4%; background:#aaa0ed; } section[data-testid="stMain"]::after { bottom:4%; left:12%; background:#71c8b6; }
        .home-composer { display:flex; align-items:center; gap:10px; }.home-composer-copy { color:var(--muted); font-size:14px; padding:0 8px; }
        section[data-testid="stMain"] { position:relative; min-height:100vh; }
        div[data-testid="stForm"] { background:transparent; border:0; padding:0; box-shadow:none; }
        div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]):has([data-testid="stForm"]) { position:fixed; left:calc(50% + 35px); bottom:30px; transform:translateX(-50%); z-index:1000; display:flex; align-items:center; gap:8px; width:min(880px, calc(100vw - 180px)); margin:0; padding:10px 12px 10px 14px; background:#fff; border:1px solid #dddadd; border-radius:25px; box-shadow:0 18px 50px #181d3021; animation:composer-in .7s .2s ease both; }
        div[data-testid="stForm"] { background:transparent; border:0; padding:0; box-shadow:none; }
        div[data-testid="stForm"] input { height:48px!important; border:0!important; background:transparent!important; color:var(--ink)!important; font-size:14px!important; box-shadow:none!important; }
        div[data-testid="stForm"] .stTextInput > div > div { background:transparent!important; border:0!important; }
        div[data-testid="stForm"] input::placeholder { color:#8a91a0!important; opacity:1!important; }
        div[data-testid="stFormSubmitButton"] button { width:auto; min-width:180px; height:48px; border:0!important; border-radius:15px!important; background:var(--violet)!important; color:#fff!important; font-size:15px!important; white-space:nowrap; }
        div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]):has([data-testid="stForm"]) div[data-testid="stFormSubmitButton"] button { width:48px; min-width:48px; font-size:19px!important; }
        div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]):has([data-testid="stForm"]) > [data-testid="stColumn"]:last-child button { background:var(--light-purple)!important; color:#5b52bd!important; border-color:transparent!important; }
        div[data-testid="stPopover"] button[data-testid="stPopoverButton"] { width:48px!important; min-width:48px!important; max-width:48px!important; height:48px; padding:0!important; background:var(--navy)!important; color:#fff!important; border:0!important; border-radius:15px!important; font-size:22px!important; box-shadow:none; }
        div[data-testid="stPopover"] button[data-testid="stPopoverButton"]:hover { background:#273453!important; color:#fff!important; }
        .metric { background:#fff; border:1px solid var(--line); padding:16px; border-radius:15px; }.metric-label { font-size:10px; font-weight:800; color:var(--muted); text-transform:uppercase; letter-spacing:.8px; }.metric-value { font-size:19px; font-weight:800; margin-top:5px; overflow:hidden; text-overflow:ellipsis; }
        .active-doc { background:var(--mint); color:#126c48; border-radius:13px; padding:11px 13px; font-size:13px; font-weight:650; margin:15px 0; }
        [data-testid="stChatMessage"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:12px 14px; margin:10px 0; box-shadow:0 3px 12px #18213b0b; }
        [data-testid="stChatMessage"] > div:last-child, [data-testid="stChatMessage"] p { color:var(--ink)!important; }
        [data-testid="stBottom"] { background:transparent!important; }
        [data-testid="stBottom"] > div { background:transparent!important; }
        [data-testid="stChatInput"] { position:fixed!important; left:calc(50% + 35px)!important; bottom:24px!important; transform:translateX(-50%)!important; z-index:1000!important; width:min(820px, calc(100vw - 100px))!important; background:#fff!important; border:1px solid #a99cff!important; border-radius:18px!important; box-shadow:0 16px 42px #18213b2b!important; }
        [data-testid="stChatInput"] textarea { color:var(--ink)!important; caret-color:var(--ink)!important; }
        [data-testid="stChatInput"] textarea::placeholder { color:#6b7280!important; opacity:1!important; }
        div[data-testid="stTextInput"] label, div[data-testid="stTextInput"] label p { color:var(--ink)!important; }
        div[data-testid="stTextInput"] input { background:#fff!important; color:var(--ink)!important; caret-color:var(--ink)!important; border:1px solid #b9c1d0!important; border-radius:10px!important; }
        div[data-testid="stTextInput"] input::placeholder { color:#6b7280!important; opacity:1!important; }
        div[data-testid="stTextInput"] input:focus { border-color:var(--violet)!important; box-shadow:0 0 0 2px #6558e833!important; }
        div[data-testid="stForm"]:has(input[placeholder*="Type A/B/C/D"]) { padding:8px!important; }
        div[data-testid="stForm"]:has(input[placeholder*="Type A/B/C/D"]) [class*="st-key-quiz-question-"] { background:#fff; border:1px solid #d9dce5; border-radius:12px; padding:18px; margin:12px 0; box-shadow:0 4px 14px #1720380c; }
        div[data-testid="stForm"]:has(input[placeholder*="Type A/B/C/D"]) input { background:var(--navy)!important; color:#d9d2ff!important; caret-color:#d9d2ff!important; border:1px solid #38405a!important; border-radius:10px!important; }
        div[data-testid="stForm"]:has(input[placeholder*="Type A/B/C/D"]) input::placeholder { color:#b8adff!important; opacity:1!important; }
        div[data-testid="stForm"]:has(input[placeholder*="Type A/B/C/D"]) input:focus { border-color:#a99cff!important; box-shadow:0 0 0 2px #a99cff55!important; }
        div[data-testid="stForm"]:has(input[placeholder*="Type A/B/C/D"]) label, div[data-testid="stForm"]:has(input[placeholder*="Type A/B/C/D"]) label p { color:var(--ink)!important; }
        [data-testid="stTextArea"] textarea { background:var(--navy)!important; color:#d9d2ff!important; caret-color:#d9d2ff!important; border:1px solid #38405a!important; }
        [data-testid="stTextArea"] textarea:focus { border-color:#a99cff!important; box-shadow:0 0 0 2px #a99cff55!important; }
        [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color:var(--ink)!important; }
        div[data-testid="stMarkdownContainer"] pre { background-color:transparent!important; border:1px solid #a99cff!important; border-radius:8px!important; box-shadow:none!important; padding:14px 16px!important; }
        div[data-testid="stMarkdownContainer"] pre code, div[data-testid="stMarkdownContainer"] code { background-color:transparent!important; box-shadow:none!important; }
        div[data-testid="stMarkdownContainer"] pre code { color:var(--ink)!important; }
        .stButton > button { border-radius:11px; min-height:43px; font-weight:700; border-color:#dce1ed; }.stButton > button[kind="primary"] { border:0; background:var(--violet); color:#fff; }
        [class*="st-key-open_saved_"] button { color:#b9adff!important; }
        [class*="st-key-open_saved_"] button:hover { color:#d9d2ff!important; }
        [data-testid="stTooltipContent"] { animation-duration:.08s!important; transition-duration:.08s!important; transition-delay:0s!important; }
        [data-testid="stFileUploader"] { margin:18px 0 24px; padding:18px!important; background:linear-gradient(135deg,#fff,#f7f5ff)!important; border:1px dashed #b9b2ee!important; border-radius:18px!important; box-shadow:0 10px 26px #302a6d0d; }
        [data-testid="stFileUploader"] section { min-height:112px; padding:16px!important; background:#fff!important; border:1px solid #e2e0ed!important; border-radius:13px!important; }
        [data-testid="stFileUploader"] section > div, [data-testid="stFileUploader"] section p, [data-testid="stFileUploader"] section span, [data-testid="stFileUploader"] section small { color:#59647b!important; opacity:1!important; }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"], [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] * { color:#59647b!important; opacity:1!important; }
        [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] label p, [data-testid="stFileUploader"] small { color:#59647b!important; opacity:1!important; }
        [data-testid="stFileUploader"] button { min-height:40px!important; padding:0 16px!important; background:var(--navy)!important; border:1px solid #38405a!important; border-radius:10px!important; color:#fff!important; font-weight:750!important; }
        [data-testid="stFileUploader"] button:hover { background:#293251!important; border-color:#a99cff!important; }
        [data-testid="stFileUploader"] svg { color:#6558e8!important; }
        .stChatInput { border-radius:15px; }
        @keyframes rise-in { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
        @keyframes composer-in { from { opacity:0; transform:translate(-50%, 12px); } to { opacity:1; transform:translate(-50%, 0); } }
        @keyframes composer-in-mobile { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
        @keyframes slow-float { 0%,100% { transform:translateY(0) rotate(0deg); } 50% { transform:translateY(-10px) rotate(4deg); } }
        @keyframes icon-breathe { 0%,100% { transform:scale(.82); box-shadow:0 0 0 7px #6558e814, 0 0 24px #6558e82e; } 50% { transform:scale(1.18); box-shadow:0 0 0 14px #6558e81c, 0 0 42px #6558e84d; } }
        @keyframes corner-icon-breathe { 0%,100% { transform:scale(.9); opacity:.8; } 50% { transform:scale(1.12); opacity:1; } }
        @keyframes orbit-breathe { 0%,100% { opacity:.55; } 50% { opacity:.95; } }
        @keyframes ring-breathe { 0%,100% { opacity:.45; transform:scale(.94); } 50% { opacity:.9; transform:scale(1.04); } }
        @keyframes study-rise { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
        @keyframes sparkle-breathe { 0%,100% { transform:rotate(-8deg) scale(.94); opacity:.72; } 50% { transform:rotate(8deg) scale(1.08); opacity:1; } }
        @keyframes dots-pulse { 0%,100% { opacity:.38; } 50% { opacity:1; } }
        @keyframes progress-glide { 0%,100% { transform:scaleX(.72); opacity:.65; } 50% { transform:scaleX(1); opacity:1; } }
        @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration:.01ms!important; animation-iteration-count:1!important; transition-duration:.01ms!important; } }
        @media (max-width:800px) { section[data-testid="stSidebar"][aria-expanded="false"] { width:0!important; min-width:0!important; pointer-events:none!important; } .block-container { padding:1rem 1rem 100px; }.top { margin-left:55px; margin-bottom:55px; }.welcome { margin-left:55px; }.welcome h1 { font-size:39px; }.orbit { display:none; } [data-testid="stChatInput"] { left:50%!important; width:calc(100vw - 32px)!important; } div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]):has([data-testid="stForm"]) { left:14px!important; right:14px!important; bottom:14px; width:auto!important; transform:none!important; } }
        @media (max-width:800px) { div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]):has([data-testid="stForm"]) { left:16px!important; right:9px!important; bottom:13px; padding:10px 12px 10px 13px; gap:8px; animation:composer-in-mobile .7s .2s ease both; } div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]):has([data-testid="stForm"]) > [data-testid="stColumn"]:first-child { flex:0 0 48px!important; width:48px!important; } div[data-testid="stHorizontalBlock"]:has([data-testid="stPopover"]):has([data-testid="stForm"]) > [data-testid="stColumn"]:last-child { flex:0 0 140px!important; width:140px!important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()

defaults = {
    "page": "Home", "messages": [], "result": None, "chatbot": None,
    "document_name": None, "notes": None, "flashcards": None, "quiz": None,
    "quiz_answers": {}, "quiz_checked": False, "flashcard_index": 0, "flashcard_revealed": False,
    "large_text": False, "high_contrast": False, "pending_question": None,
    "from_voice": False, "authenticated": False, "auth_user_id": None,
    "username": "", "accessibility_profile": {}, "auth_view": "login",
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)


if not render_login_page():
    st.stop()

profile = st.session_state.get("accessibility_profile", {})
if profile.get("disclosed") and profile.get("visual_impairment"):
    st.session_state.large_text = True
    st.session_state.high_contrast = True


def go(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def clean(value: object) -> str:
    return html.escape(str(value))


def normalize_quiz_choice(value: object) -> str | None:
    """Accept A/B/C/D, 1/2/3/4, or text like '1. Tiger is strong'."""
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    match = re.findall(r"(?i)\b([a-d]|[1-4])\b", text)
    if not match:
        return None

    token = match[0].lower()
    if token in {"a", "b", "c", "d"}:
        return token.upper()

    number = int(token)
    if 1 <= number <= 4:
        return "ABCD"[number - 1]

    return None


def quiz_topic_from_request(value: object) -> str | None:
    """Extract a topic from a natural-language request to create a quiz."""
    text = str(value or "").strip()
    match = re.search(
        r"\b(?:quiz|test)\s+(?:on|about|for)(?:\s+the\s+topic(?:\s+of)?|\s+the)?\s+(.+?)\s*[?.!]?$",
        text,
        re.IGNORECASE,
    )
    if match:
        topic = match.group(1).strip(" .?!")
        return topic or "general knowledge"

    if not re.search(r"\bquiz\b", text, re.IGNORECASE):
        return None

    topic_match = re.search(r"\bquiz\b(.*)$", text, re.IGNORECASE)
    topic = topic_match.group(1) if topic_match else ""
    topic = re.sub(r"^\s*(?:please\s+)?(?:make|create|generate|give|prepare|start)\s*", "", topic, flags=re.IGNORECASE)
    topic = re.sub(r"^\s*(?:a|an|the|on|about|for|of|topic)\s+", "", topic, flags=re.IGNORECASE)
    topic = topic.strip(" .?!")
    return topic or None


def get_quiz_items() -> list:
    payload = st.session_state.get("quiz")
    if not payload:
        return []
    if isinstance(payload, str):
        try:
            return parse_quiz(payload)
        except Exception:
            return []
    return list(payload)


def get_flashcard_items() -> list:
    payload = st.session_state.get("flashcards")
    if not payload:
        return []
    if isinstance(payload, str):
        try:
            return parse_flashcards(payload)
        except Exception:
            return []
    return list(payload)


def document_text() -> str:
    result = st.session_state.result
    return result.text if result else ""


def activate_document(document) -> None:
    st.session_state.result = document
    st.session_state.document_name = document.name
    st.session_state.chatbot = None
    st.session_state.notes = st.session_state.flashcards = st.session_state.quiz = None
    st.session_state.quiz_answers = {}
    st.session_state.quiz_checked = False
    st.session_state.flashcard_index = 0
    st.session_state.flashcard_revealed = False


def reset_session() -> None:
    for key in ("messages", "result", "chatbot", "document_name", "notes", "flashcards", "quiz"):
        st.session_state[key] = [] if key == "messages" else None
    st.session_state.quiz_answers = {}
    st.session_state.quiz_checked = False
    st.session_state.flashcard_index = 0
    st.session_state.flashcard_revealed = False
    st.session_state.from_voice = False


def card(icon: str, title: str, copy: str) -> None:
    st.markdown(f'<div class="card"><div class="card-icon">{icon}</div><h3>{title}</h3><p>{copy}</p></div>', unsafe_allow_html=True)


def topbar() -> None:
    title = st.session_state.page
    status = "Document ready" if st.session_state.result else "Ready to learn"
    st.markdown(f'<div class="top"><div><div class="crumb">SakshamAI</div><div class="app-name">YOUR LEARNING SPACE</div></div><div class="status">● {status}</div></div>', unsafe_allow_html=True)


with st.sidebar:
    st.markdown('<div class="sidebar-brand"><span class="logo">✦</span><span class="brand">SakshamAI</span></div>', unsafe_allow_html=True)
    for label, page, tip in (("⌂", "Home", "Overview"), ("▱", "Documents", "Documents"), ("◌", "Chat", "Ask your document"), ("✦", "Study", "Study studio")):
        if st.button(label, key=f"nav_{page}", help=tip, type="primary" if st.session_state.page == page else "secondary", use_container_width=True): go(page)
    st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)
    for label, page, tip in (("♿", "Accessibility", "Accessibility"), ("⚙", "Settings", "Settings")):
        if st.button(label, key=f"nav_{page}", help=tip, type="primary" if st.session_state.page == page else "secondary", use_container_width=True): go(page)

topbar()

if st.session_state.page == "Home":
    document_label = "No document loaded"
    if st.session_state.result:
        document_label = f"{clean(st.session_state.result.name)} · {st.session_state.result.page_count} pages · Ready"
    st.markdown(f'''<div class="welcome"><div class="welcome-kicker">What's on your mind?</div><h1>Learn at<br><span>your own pace.</span></h1><p>Bring in your material.<br>I'll help you understand it.</p><div class="document-status"><span class="document-dot"></span>{document_label}</div></div><div class="orbit" aria-hidden="true"></div>''', unsafe_allow_html=True)
    plus, composer, voice = st.columns((1, 7, 2))
    with plus:
        with st.popover("＋", use_container_width=True):
            if st.button("📄  Upload document", key="home_upload_menu", help="Open document upload", use_container_width=True):
                go("Documents")
            if st.button("📝  Generate notes", key="home_notes_menu", use_container_width=True):
                go("Study")
            if st.button("🧠  Create quiz", key="home_quiz_menu", use_container_width=True):
                go("Study")
            if st.button("🗂  Create flashcards", key="home_flashcards_menu", use_container_width=True):
                go("Study")
    with composer:
        with st.form("home_composer", clear_on_submit=True):
            prompt, send = st.columns((8, 1))
            with prompt:
                question = st.text_input("Ask SakshamAI", placeholder="Ask anything about your material...", label_visibility="collapsed")
            with send:
                submitted = st.form_submit_button("➤", use_container_width=True)
    with voice:
        voice_clicked = st.button("◉  Voice", help="Start voice mode", use_container_width=True)
    if voice_clicked:
        available, details = microphone_available()
        if not available:
            st.error(f"Voice mode is unavailable: {details}")
        else:
            try:
                with st.spinner("Listening…"):
                    voice_path = record_question()
                    voice_question = transcribe(voice_path)
                st.session_state.from_voice = True
                st.session_state.pending_question = voice_question
                go("Chat")
            except BackendError as error:
                st.error(str(error))
    if submitted and question.strip():
        st.session_state.pending_question = question.strip()
        go("Chat")

elif st.session_state.page == "Documents":
    st.markdown('<div class="section-title">Add learning material</div><p class="section-copy">Upload a clear PDF or image. SakshamAI extracts the text and keeps it ready for chat and study tools.</p>', unsafe_allow_html=True)
    saved_documents = load_document_library()
    if saved_documents:
        st.markdown('<div class="section-title" style="font-size:18px;margin-top:20px;">Your document library</div><p class="section-copy">Saved locally on this computer and available in future sessions.</p>', unsafe_allow_html=True)
        for saved_document in reversed(saved_documents):
            library_col, open_col = st.columns((7, 1))
            with library_col:
                st.markdown(
                    f'<div class="active-doc">📄 <strong>{clean(saved_document.name)}</strong> · {saved_document.page_count} pages · {saved_document.char_count:,} characters</div>',
                    unsafe_allow_html=True,
                )
            with open_col:
                if st.button("Open", key=f"open_saved_{saved_document.name}", use_container_width=True):
                    activate_document(saved_document)
                    st.success(f"Loaded {saved_document.name} from your local library.")

    file = st.file_uploader("Choose a PDF, PNG, JPG or JPEG", type=["pdf", "png", "jpg", "jpeg"])
    if file:
        x, y, z = st.columns(3)
        for column, label, value in ((x, "FILE", file.name), (y, "FORMAT", (file.type or "Unknown").split("/")[-1].upper()), (z, "SIZE", f"{file.size / 1024 / 1024:.2f} MB")):
            with column: st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{clean(value)}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Process document", type="primary", use_container_width=True):
            try:
                with st.spinner("Extracting readable study material..."):
                    result = extract_document(file.getvalue(), file.name)
                save_document_to_library(result)
                activate_document(result)
                st.success("Your material is ready. You can now ask questions or start revising.")
            except BackendError as error:
                st.error(str(error))
            except Exception as error:
                st.error(f"We could not process this document: {error}")
    if st.session_state.result:
        result = st.session_state.result
        st.markdown(f'<div class="active-doc">✓ {clean(result.name)} is ready · {result.char_count:,} characters extracted · {result.page_count} pages</div>', unsafe_allow_html=True)
        with st.expander("Preview extracted text"):
            st.text_area("Extracted text", result.text, height=300, label_visibility="collapsed")

elif st.session_state.page == "Chat":
    st.markdown('<div class="section-title">Ask SakshamAI</div><p class="section-copy">Ask anything, or ask questions grounded in your uploaded study material.</p>', unsafe_allow_html=True)
    if st.session_state.result:
        st.markdown(f'<div class="active-doc">📄 Using {clean(st.session_state.document_name)}</div>', unsafe_allow_html=True)
    else:
        st.caption("General chat is ready. Upload a document whenever you want grounded answers.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])
    question = st.chat_input("Ask SakshamAI anything…")
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
    if question:
        quiz_topic = quiz_topic_from_request(question)
        if quiz_topic:
            st.session_state.quiz_topic_request = quiz_topic
            go("Study")

        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    if st.session_state.chatbot is None:
                        bot = create_chatbot()
                        if st.session_state.result:
                            attach_document(bot, document_text(), st.session_state.document_name)
                        st.session_state.chatbot = bot
                    answer = ask_question(st.session_state.chatbot, question)
                except BackendError as error:
                    answer = str(error)
                except Exception as error:
                    answer = f"I couldn't answer that right now: {error}"
            st.markdown(answer)
            if st.session_state.from_voice:
                try:
                    speak(answer)
                except BackendError:
                    pass
                st.session_state.from_voice = False
        st.session_state.messages.append({"role": "assistant", "content": answer})

elif st.session_state.page == "Study":
    st.markdown('<div class="section-title">Study studio</div><p class="section-copy">Choose any topic or use your uploaded document to create notes, flashcards, and quizzes.</p>', unsafe_allow_html=True)

    requested_quiz_topic = st.session_state.pop("quiz_topic_request", "")
    with st.container(key="study-topic"):
        topic = st.text_input(
            "What do you want to study?",
            value=requested_quiz_topic,
            placeholder="Try photosynthesis, robotics engineering, algebra, or world history",
            help="Generate revision content from any topic, even without a document.",
        )

    if topic.strip():
        st.markdown(
            f'<div class="study-progress"><div class="study-progress-head"><span class="study-progress-label">Creating your study kit for {clean(topic.strip()).title()}</span><span class="study-dots">•••</span></div><div class="study-progress-track"><div class="study-progress-fill"></div></div></div>',
            unsafe_allow_html=True,
        )

    if st.session_state.result:
        st.markdown(f'<div class="active-doc">📄 Using {clean(st.session_state.document_name)}</div>', unsafe_allow_html=True)

    source_available = bool(topic.strip()) or bool(st.session_state.result) or bool(st.session_state.quiz)
    if not source_available:
        st.info("Add a document or enter a topic to generate study material.")
        if st.button("Add document →", type="primary"): go("Documents")

    if source_available:
        if requested_quiz_topic and not st.session_state.quiz:
            try:
                with st.spinner("Creating practice quiz…"):
                    st.session_state.quiz = generate_quiz_for_topic(requested_quiz_topic)
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_checked = False
            except Exception as error:
                st.error(f"Could not create the practice quiz: {error}")

        choices = (
            ("📝", "Smart notes", "A concise outline of the key ideas.", "notes", generate_notes if st.session_state.result else generate_notes_for_topic),
            ("▣", "Flashcards", "Quick revision prompts for memorizing facts.", "flashcards", generate_flashcards if st.session_state.result else generate_flashcards_for_topic),
            ("?", "Practice quiz", "A short multi-choice quiz for recall and revision.", "quiz", generate_quiz if st.session_state.result else generate_quiz_for_topic),
        )

        with st.container(key="study-options"):
            action_cols = st.columns(3)
            for col, (icon, title, copy, key, generator) in zip(action_cols, choices):
                with col:
                    with st.container(key=f"study-option-{key}"):
                        active_marker = '<span class="study-option-check">✓</span>' if st.session_state[key] else ""
                        st.markdown(
                            f'<div class="study-option-icon">{icon}</div><p class="study-option-title">{title}{active_marker}</p><p class="study-option-copy">{copy}</p>',
                            unsafe_allow_html=True,
                        )
                        if st.button(f"Open {title.lower()}", key=f"make_{key}", use_container_width=True):
                            try:
                                with st.spinner(f"Creating {title.lower()}…"):
                                    if st.session_state.result:
                                        st.session_state[key] = generator(document_text())
                                    else:
                                        st.session_state[key] = generator(topic.strip())
                                    if key == "quiz":
                                        st.session_state.quiz_answers = {}
                                        st.session_state.quiz_checked = False
                                    if key == "flashcards":
                                        st.session_state.flashcard_index = 0
                                        st.session_state.flashcard_revealed = False
                            except Exception as error:
                                st.error(f"Could not create {title.lower()}: {error}")

        for icon, title, key in (("📝", "Smart notes", "notes"), ("▣", "Flashcards", "flashcards"), ("?", "Practice quiz", "quiz")):
            if st.session_state[key]:
                st.markdown(f'<div class="section-title">{icon} {title}</div>', unsafe_allow_html=True)
                if key == "quiz":
                    quiz_items = get_quiz_items()
                    if quiz_items:
                        answers = {}
                        with st.form(f"quiz_check_form_{key}", clear_on_submit=False):
                            for item in quiz_items:
                                with st.container(border=True, key=f"quiz-question-{item.number}"):
                                    st.markdown(f"#### Question {item.number}")
                                    st.markdown(f"**{item.stem}**")
                                    for option_key, option_value in item.options.items():
                                        st.markdown(f"**{option_key}.** {option_value}")
                                    answers[item.number] = st.text_input(
                                        f"Your answer for Q{item.number}",
                                        key=f"quiz_answer_{item.number}",
                                        placeholder="Type A/B/C/D or 1/2/3/4",
                                    )
                            checked = st.form_submit_button("Check my answers")

                        if checked:
                            st.session_state.quiz_answers = dict(answers)
                            st.session_state.quiz_checked = True

                        if st.session_state.quiz_checked:
                            score = 0
                            st.markdown("### Your results")
                            for item in quiz_items:
                                user_text = st.session_state.quiz_answers.get(item.number, "")
                                chosen = normalize_quiz_choice(user_text)
                                correct = item.correct.upper()
                                with st.container(border=True):
                                    st.markdown(f"**Question {item.number}**")
                                    st.markdown(f"Your answer: **{user_text or 'No answer'}**")
                                    if chosen == correct:
                                        score += 1
                                        st.success(f"Correct: {correct}. {item.options[correct]}")
                                    else:
                                        st.error(f"Incorrect. Correct answer: {correct}. {item.options[correct]}")

                            st.markdown(f"### Final score: {score}/{len(quiz_items)}")
                    else:
                        st.error("This quiz could not be read safely. Please create it again.")
                else:
                    if key == "flashcards":
                        flashcard_items = get_flashcard_items()
                        if not flashcard_items:
                            st.error("These flashcards could not be read safely. Please create them again.")
                            continue

                        last_index = len(flashcard_items) - 1
                        index = max(0, min(st.session_state.flashcard_index, last_index))
                        st.session_state.flashcard_index = index
                        active_card = flashcard_items[index]
                        revealed = st.session_state.flashcard_revealed
                        stack_markup = ""
                        if index + 2 < len(flashcard_items):
                            stack_markup += '<div class="flashcard-stack-card stack-one"></div>'
                        if index + 1 < len(flashcard_items):
                            stack_markup += '<div class="flashcard-stack-card stack-two"></div>'
                        face_class = " is-revealed" if revealed else ""
                        st.markdown(
                            f'<div class="flashcard-deck"><div class="flashcard-stack">{stack_markup}</div><div class="flashcard-active{face_class}"><div class="flashcard-face front"><div class="flashcard-meta"><span>FLASHCARD {active_card.number}</span><span class="flashcard-progress">{index + 1} / {len(flashcard_items)}</span></div><div class="flashcard-label">Question</div><p class="flashcard-question">{clean(active_card.question)}</p><p class="flashcard-hint">Tap below to reveal the answer</p></div><div class="flashcard-face back"><div class="flashcard-meta"><span>FLASHCARD {active_card.number}</span><span class="flashcard-progress">{index + 1} / {len(flashcard_items)}</span></div><div class="flashcard-label">Answer</div><p class="flashcard-answer">{clean(active_card.answer)}</p><p class="flashcard-hint">Tap below to return to the question</p></div></div></div>',
                            unsafe_allow_html=True,
                        )

                        with st.container(key="flashcard-flip-control"):
                            if st.button("Show question" if revealed else "Tap to reveal answer", key="flashcard_flip", use_container_width=True):
                                st.session_state.flashcard_revealed = not revealed
                                st.rerun()

                        with st.container(key="flashcard-controls"):
                            previous, spacer, next_card = st.columns((1, 1, 1))
                            with previous:
                                if st.button("←  Previous", key="flashcard_previous", disabled=index == 0, use_container_width=True):
                                    st.session_state.flashcard_index = index - 1
                                    st.session_state.flashcard_revealed = False
                                    st.rerun()
                            with spacer:
                                st.markdown('<div style="text-align:center;color:#7c8495;font-size:12px;padding-top:13px;">Flip card</div>', unsafe_allow_html=True)
                            with next_card:
                                if st.button("Next  →", key="flashcard_next", disabled=index == last_index, use_container_width=True):
                                    st.session_state.flashcard_index = index + 1
                                    st.session_state.flashcard_revealed = False
                                    st.rerun()
                    else:
                        st.markdown(st.session_state[key])

elif st.session_state.page == "Accessibility":
    st.markdown('<div class="section-title">Make the workspace feel right</div><p class="section-copy">These preferences only change the interface, never your document or AI results.</p>', unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        card("Aa", "Reading comfort", "Increase text size to make headings, cards, and chat easier to scan.")
        st.session_state.large_text = st.toggle("Use larger text", value=st.session_state.large_text)
    with b:
        card("◐", "Visual clarity", "Use strong borders and colours that are easier to distinguish.")
        st.session_state.high_contrast = st.toggle("Use high contrast", value=st.session_state.high_contrast)

elif st.session_state.page == "Settings":
    st.markdown('<div class="section-title">Workspace settings</div><p class="section-copy">Choose how SakshamAI presents your learning space.</p>', unsafe_allow_html=True)
    a, b = st.columns(2)
    with a: st.selectbox("Preferred language", ["English", "Hindi", "Marathi"])
    with b: st.selectbox("Learning style", ["Standard", "Distraction-reduced"])
    st.caption("These are interface preferences. Your document remains private to this local session.")

if st.session_state.large_text:
    st.markdown('<style>.card p,.section-copy,.active-doc,.stChatMessage { font-size:16px!important; }.card h3 { font-size:19px!important; }</style>', unsafe_allow_html=True)
if st.session_state.high_contrast:
    st.markdown('<style>.stApp{background:#fff}.card,.metric,.top,[data-testid="stFileUploader"]{border:2px solid #111827!important}.section-copy,.card p{color:#111827!important}</style>', unsafe_allow_html=True)
