import sys
import time
from pathlib import Path

import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCUMENT_PROCESSING_DIR = ROOT_DIR / "document_processing"

if str(DOCUMENT_PROCESSING_DIR) not in sys.path:
    sys.path.insert(0, str(DOCUMENT_PROCESSING_DIR))

from document_processor import process_document


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SakshamAI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- General ---------- */

    .stApp {
        background: #f7f8fc;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }


    /* ---------- Sidebar ---------- */

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 5px 18px 5px;
        font-size: 24px;
        font-weight: 700;
    }

    .brand-icon {
        font-size: 30px;
    }

    .sidebar-subtitle {
        color: #6b7280;
        font-size: 13px;
        margin-top: -12px;
        margin-bottom: 20px;
    }


    /* ---------- Chat header ---------- */

    .chat-header {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 18px 24px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .chat-title {
        font-size: 25px;
        font-weight: 700;
        margin: 0;
    }

    .chat-status {
        color: #16a34a;
        font-size: 13px;
        font-weight: 600;
    }


    /* ---------- Welcome card ---------- */

    .welcome-card {
        background: linear-gradient(135deg, #5146e5, #7c3aed);
        color: white;
        border-radius: 20px;
        padding: 35px;
        margin-bottom: 25px;
    }

    .welcome-title {
        font-size: 32px;
        font-weight: 750;
        margin-bottom: 10px;
    }

    .welcome-text {
        font-size: 17px;
        opacity: 0.95;
        line-height: 1.6;
    }


    /* ---------- Feature cards ---------- */

    .feature-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 22px;
        min-height: 145px;
    }

    .feature-icon {
        font-size: 30px;
        margin-bottom: 10px;
    }

    .feature-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .feature-text {
        color: #6b7280;
        font-size: 14px;
        line-height: 1.5;
    }


    /* ---------- Document information ---------- */

    .info-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 18px;
        min-height: 105px;
    }

    .info-label {
        color: #6b7280;
        font-size: 13px;
        margin-bottom: 7px;
    }

    .info-value {
        font-size: 20px;
        font-weight: 700;
    }


    /* ---------- Chat messages ---------- */

    .user-message {
        background: #5146e5;
        color: white;
        padding: 13px 17px;
        border-radius: 18px 18px 4px 18px;
        margin: 10px 0 10px auto;
        max-width: 75%;
    }

    .assistant-message {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 13px 17px;
        border-radius: 18px 18px 18px 4px;
        margin: 10px auto 10px 0;
        max-width: 75%;
    }


    /* ---------- Footer ---------- */

    .footer {
        text-align: center;
        color: #9ca3af;
        font-size: 12px;
        padding: 30px 0 10px 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "New Chat"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "processed_document" not in st.session_state:
    st.session_state.processed_document = None

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None


# ============================================================
# SIDEBAR — CHAT STYLE MENU
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            <span class="brand-icon">🧠</span>
            <span>SakshamAI</span>
        </div>

        <div class="sidebar-subtitle">
            Assistive Learning Assistant
        </div>
        """,
        unsafe_allow_html=True,
    )

    # New chat
    if st.button(
        "＋  New Chat",
        use_container_width=True,
        type="primary" if st.session_state.page == "New Chat" else "secondary",
    ):
        st.session_state.page = "New Chat"
        st.session_state.messages = []
        st.rerun()

    st.markdown("###")

    st.caption("MENU")

    if st.button(
        "💬  Chat",
        use_container_width=True,
    ):
        st.session_state.page = "New Chat"
        st.rerun()

    if st.button(
        "📄  Documents",
        use_container_width=True,
    ):
        st.session_state.page = "Documents"
        st.rerun()

    if st.button(
        "📚  Study",
        use_container_width=True,
    ):
        st.session_state.page = "Study"
        st.rerun()

    if st.button(
        "♿  Accessibility",
        use_container_width=True,
    ):
        st.session_state.page = "Accessibility"
        st.rerun()

    st.markdown("---")

    st.caption("RECENT")

    if st.session_state.uploaded_file_name:
        st.write("📄 " + st.session_state.uploaded_file_name)
    else:
        st.caption("No documents yet")

    st.markdown("---")

    if st.button(
        "⚙️  Settings",
        use_container_width=True,
    ):
        st.session_state.page = "Settings"
        st.rerun()

    st.markdown(
        """
        <div class="footer">
            SakshamAI • Version 2
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# TOP HEADER
# ============================================================

st.markdown(
    """
    <div class="chat-header">
        <div class="chat-title">SakshamAI</div>
        <div class="chat-status">● Ready</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# NEW CHAT
# ============================================================

if st.session_state.page == "New Chat":

    st.markdown(
        """
        <div class="welcome-card">
            <div class="welcome-title">
                👋 Welcome to SakshamAI
            </div>
            <div class="welcome-text">
                Your accessible learning assistant for understanding
                educational documents in a simpler way.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("What would you like to do?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📄</div>
                <div class="feature-title">Upload Document</div>
                <div class="feature-text">
                    Upload a PDF or image and prepare it for accessible learning.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📄 Upload Document", use_container_width=True):
            st.session_state.page = "Documents"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📚</div>
                <div class="feature-title">Study Support</div>
                <div class="feature-text">
                    Use your learning material for notes, revision and study.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📚 Open Study", use_container_width=True):
            st.session_state.page = "Study"
            st.rerun()

    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">♿</div>
                <div class="feature-title">Accessibility</div>
                <div class="feature-text">
                    Learning features designed with accessibility in mind.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("♿ Accessibility", use_container_width=True):
            st.session_state.page = "Accessibility"
            st.rerun()

    st.markdown("---")

    st.subheader("💬 Start a conversation")

    for message in st.session_state.messages:

        if message["role"] == "user":
            st.markdown(
                f"""
                <div class="user-message">
                    {message["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f"""
                <div class="assistant-message">
                    🧠 {message["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

    user_question = st.chat_input(
        "Ask SakshamAI about your study material..."
    )

    if user_question:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_question,
            }
        )

        # ----------------------------------------------------
        # Chatbot integration will be connected here later.
        # We don't generate fake answers.
        # ----------------------------------------------------

        if st.session_state.processed_document:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "Your document is loaded. "
                        "The document-grounded AI chatbot can be connected here."
                    ),
                }
            )

        else:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "Please upload a study document first. "
                        "Then you can ask questions about it."
                    ),
                }
            )

        st.rerun()


# ============================================================
# DOCUMENTS
# ============================================================

elif st.session_state.page == "Documents":

    st.title("📄 Documents")

    st.write(
        "Upload a PDF or image containing your educational material."
    )

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Upload educational PDFs or images.",
    )

    if uploaded_file:

        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name

        st.session_state.uploaded_file_name = file_name

        st.markdown("### Document Information")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="info-label">File Name</div>
                    <div class="info-value">{file_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="info-label">File Type</div>
                    <div class="info-value">{uploaded_file.type}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            size_mb = len(file_bytes) / (1024 * 1024)

            st.markdown(
                f"""
                <div class="info-card">
                    <div class="info-label">File Size</div>
                    <div class="info-value">{size_mb:.2f} MB</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        process_button = st.button(
            "⚡ Process Document",
            type="primary",
            use_container_width=True,
        )

        if process_button:

            progress = st.progress(0)
            status_text = st.empty()

            try:

                status_text.info("Preparing document...")
                progress.progress(20)

                start_time = time.time()

                status_text.info("Processing document...")
                progress.progress(45)

                result = process_document(
                    file_bytes,
                    file_name,
                )

                progress.progress(90)

                processing_time = time.time() - start_time

                progress.progress(100)
                status_text.success(
                    "✅ Document processed successfully!"
                )

                st.session_state.processed_document = result

                st.markdown("---")

                st.subheader("📊 Processing Result")

                # ------------------------------------------------
                # Extract result information safely
                # ------------------------------------------------

                if isinstance(result, dict):

                    status = result.get(
                        "status",
                        result.get("success", "Success")
                    )

                    file_type = result.get(
                        "file_type",
                        "PDF" if file_name.lower().endswith(".pdf")
                        else "Image"
                    )

                    pages = result.get(
                        "pages",
                        result.get(
                            "page_count",
                            result.get("num_pages", "-")
                        )
                    )

                    extracted_text = result.get(
                        "text",
                        result.get(
                            "extracted_text",
                            result.get("full_text", "")
                        )
                    )

                    warnings = result.get(
                        "warnings",
                        []
                    )

                    page_results = result.get(
                        "pages_data",
                        result.get("page_results", [])
                    )

                else:

                    status = "Success"
                    file_type = (
                        "PDF"
                        if file_name.lower().endswith(".pdf")
                        else "Image"
                    )

                    pages = "-"
                    extracted_text = str(result)
                    warnings = []
                    page_results = []

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Status",
                        "Success"
                        if status is True or status == "success"
                        else str(status),
                    )

                with col2:
                    st.metric(
                        "File Type",
                        str(file_type).upper(),
                    )

                with col3:
                    st.metric(
                        "Pages",
                        pages,
                    )

                with col4:
                    st.metric(
                        "Processing Time",
                        f"{processing_time:.2f}s",
                    )

                # ------------------------------------------------
                # Extracted text
                # ------------------------------------------------

                st.markdown("---")

                st.subheader("📖 Extracted Text")

                if extracted_text:

                    st.text_area(
                        "Document content",
                        value=str(extracted_text),
                        height=450,
                        label_visibility="collapsed",
                    )

                elif page_results:

                    for index, page in enumerate(page_results):

                        if isinstance(page, dict):

                            page_text = page.get(
                                "text",
                                page.get("extracted_text", "")
                            )

                        else:
                            page_text = str(page)

                        with st.expander(
                            f"📄 Page {index + 1}"
                        ):
                            st.write(page_text)

                else:

                    st.info(
                        "The document was processed, but no extracted "
                        "text was returned."
                    )

                # ------------------------------------------------
                # Warnings
                # ------------------------------------------------

                if warnings:

                    st.markdown("---")

                    st.subheader("⚠️ Warnings")

                    if isinstance(warnings, list):

                        for warning in warnings:
                            st.warning(str(warning))

                    else:
                        st.warning(str(warnings))

            except Exception as error:

                progress.empty()

                st.error(
                    "❌ Document processing failed."
                )

                st.exception(error)


# ============================================================
# STUDY
# ============================================================

elif st.session_state.page == "Study":

    st.title("📚 Study")

    if st.session_state.processed_document:

        st.success(
            f"Study material loaded: "
            f"{st.session_state.uploaded_file_name}"
        )

        st.write(
            "Your document is ready for study features."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("📝\n\n**Notes**\n\nAI-generated simplified notes will appear here.")

        with col2:
            st.info("🧠\n\n**Flashcards**\n\nImportant concepts can be converted into flashcards.")

        with col3:
            st.info("❓\n\n**Quiz**\n\nA quiz can be generated from the document.")

    else:

        st.info(
            "📄 Upload and process a document first to start studying."
        )

        if st.button("📄 Upload Document", use_container_width=True):
            st.session_state.page = "Documents"
            st.rerun()


# ============================================================
# ACCESSIBILITY
# ============================================================

elif st.session_state.page == "Accessibility":

    st.title("♿ Accessibility")

    st.write(
        "SakshamAI is designed to make educational material easier "
        "to access and understand."
    )

    st.markdown("### Accessibility Features")

    col1, col2 = st.columns(2)

    with col1:

        st.checkbox(
            "🔊 Speech / Voice Mode",
            disabled=True,
            help="Voice integration will be connected with the chatbot module.",
        )

        st.checkbox(
            "🔠 Large Text",
        )

    with col2:

        st.checkbox(
            "🎨 High Contrast",
        )

        st.checkbox(
            "📖 Simplified Reading",
        )

    st.info(
        "Some accessibility controls will be connected to the "
        "AI and voice modules in the next integration stage."
    )


# ============================================================
# SETTINGS
# ============================================================

elif st.session_state.page == "Settings":

    st.title("⚙️ Settings")

    st.subheader("SakshamAI Settings")

    st.selectbox(
        "Language",
        [
            "English",
            "Hindi",
            "Marathi",
        ],
    )

    st.selectbox(
        "Interface",
        [
            "Standard",
            "Accessible",
        ],
    )

    st.checkbox(
        "Show processing information",
        value=True,
    )

    st.info(
        "Settings are currently UI-level options. "
        "They can be connected to the AI and accessibility modules later."
    )


# ============================================================
# END
# ============================================================

st.markdown(
    """
    <div class="footer">
        SakshamAI • Assistive Learning Tools for Differently-Abled Students
    </div>
    """,
    unsafe_allow_html=True,
)