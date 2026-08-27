import sys
import tempfile
from pathlib import Path

import streamlit as st


# ============================================================
# PATH SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHATBOT_PATH = PROJECT_ROOT / "chatbot-voice"

if str(CHATBOT_PATH) not in sys.path:
    sys.path.insert(0, str(CHATBOT_PATH))


# ============================================================
# IMPORT CHATBOT BACKEND
# ============================================================

try:
    from chatbot import DocumentChatbot, load_document_from_file

except ImportError as error:
    st.error(
        "Unable to load the SakshamAI chatbot backend.\n\n"
        f"Expected location:\n{CHATBOT_PATH / 'chatbot.py'}\n\n"
        f"Error: {error}"
    )
    st.stop()


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

    /* ================================
       GLOBAL
       ================================ */

    .stApp {
        background-color: #f7f8fc;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 1200px;
    }


    /* ================================
       SIDEBAR
       ================================ */

    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 4px 4px 4px;
    }

    .brand-icon {
        font-size: 30px;
    }

    .brand-name {
        font-size: 24px;
        font-weight: 700;
    }

    .brand-subtitle {
        color: #6b7280;
        font-size: 12px;
        margin: 2px 0 20px 43px;
    }


    /* ================================
       TOP HEADER
       ================================ */

    .top-header {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 15px 20px;
        margin-bottom: 20px;

        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .top-title {
        font-size: 23px;
        font-weight: 700;
    }

    .online-status {
        color: #16a34a;
        font-size: 13px;
        font-weight: 600;
    }


    /* ================================
       WELCOME
       ================================ */

    .welcome {
        text-align: center;
        padding: 55px 20px 35px 20px;
    }

    .welcome-icon {
        font-size: 52px;
    }

    .welcome-title {
        font-size: 32px;
        font-weight: 700;
        margin-top: 10px;
    }

    .welcome-text {
        color: #6b7280;
        font-size: 16px;
        max-width: 650px;
        margin: 10px auto;
        line-height: 1.6;
    }


    /* ================================
       DOCUMENT STATUS
       ================================ */

    .document-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 15px;
        margin-bottom: 15px;
    }

    .document-title {
        font-weight: 700;
        margin-bottom: 5px;
    }

    .document-info {
        color: #6b7280;
        font-size: 13px;
    }


    /* ================================
       FEATURE CARDS
       ================================ */

    .feature-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 18px;
        min-height: 120px;
    }

    .feature-icon {
        font-size: 27px;
    }

    .feature-title {
        font-weight: 700;
        margin-top: 8px;
    }

    .feature-text {
        color: #6b7280;
        font-size: 13px;
        margin-top: 4px;
    }


    /* ================================
       FOOTER
       ================================ */

    .footer {
        text-align: center;
        color: #9ca3af;
        font-size: 12px;
        margin-top: 40px;
        padding-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "chatbot" not in st.session_state:
    st.session_state.chatbot = DocumentChatbot()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

if "page" not in st.session_state:
    st.session_state.page = "Chat"


chatbot = st.session_state.chatbot


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            <span class="brand-icon">🧠</span>
            <span class="brand-name">SakshamAI</span>
        </div>

        <div class="brand-subtitle">
            Assistive Learning Assistant
        </div>
        """,
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "＋  New Chat",
        use_container_width=True,
        type="primary",
    ):

        st.session_state.messages = []

        chatbot.conversation_history = []

        st.session_state.page = "Chat"

        st.rerun()


    st.markdown("###")


    # --------------------------------------------------------
    # MAIN MENU
    # --------------------------------------------------------

    st.caption("MENU")


    if st.button(
        "💬  Chat",
        use_container_width=True,
    ):

        st.session_state.page = "Chat"
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


    # --------------------------------------------------------
    # CURRENT DOCUMENT
    # --------------------------------------------------------

    st.caption("CURRENT DOCUMENT")

    if chatbot.has_document():

        st.write(
            "📄 " + chatbot.document_name
        )

        st.caption(
            f"{len(chatbot.document_text):,} characters"
        )

    else:

        st.caption("No document loaded")


    # --------------------------------------------------------
    # DOCUMENT ACTIONS
    # --------------------------------------------------------

    if chatbot.has_document():

        if st.button(
            "🗑️ Clear Document",
            use_container_width=True,
        ):

            chatbot.clear_document()

            st.session_state.messages = []

            st.session_state.last_uploaded_file = None

            st.rerun()


    st.markdown("---")


    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    if st.button(
        "⚙️  Settings",
        use_container_width=True,
    ):

        st.session_state.page = "Settings"
        st.rerun()


# ============================================================
# TOP HEADER
# ============================================================

st.markdown(
    """
    <div class="top-header">

        <div class="top-title">
            🧠 SakshamAI
        </div>

        <div class="online-status">
            ● Ready
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CHAT PAGE
# ============================================================

if st.session_state.page == "Chat":

    # --------------------------------------------------------
    # WELCOME SCREEN
    # --------------------------------------------------------

    if not st.session_state.messages:

        st.markdown(
            """
            <div class="welcome">

                <div class="welcome-icon">
                    🧠
                </div>

                <div class="welcome-title">
                    Welcome to SakshamAI
                </div>

                <div class="welcome-text">
                    Your intelligent and accessible learning
                    assistant. Upload your study material and
                    ask questions in a simple conversational way.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


        # ----------------------------------------------------
        # FEATURE CARDS
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown(
                """
                <div class="feature-card">

                    <div class="feature-icon">
                        📄
                    </div>

                    <div class="feature-title">
                        Documents
                    </div>

                    <div class="feature-text">
                        Upload PDF, TXT or image study material.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


        with col2:

            st.markdown(
                """
                <div class="feature-card">

                    <div class="feature-icon">
                        🧠
                    </div>

                    <div class="feature-title">
                        Ask Questions
                    </div>

                    <div class="feature-text">
                        Ask questions about your learning material.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


        with col3:

            st.markdown(
                """
                <div class="feature-card">

                    <div class="feature-icon">
                        📚
                    </div>

                    <div class="feature-title">
                        Study Support
                    </div>

                    <div class="feature-text">
                        Get explanations and learning assistance.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


        st.markdown("<br>", unsafe_allow_html=True)


        # ----------------------------------------------------
        # DOCUMENT UPLOAD BUTTON
        # ----------------------------------------------------

        if st.button(
            "📄  Upload Study Document",
            use_container_width=True,
        ):

            st.session_state.page = "Documents"

            st.rerun()


    # --------------------------------------------------------
    # DOCUMENT STATUS ABOVE CHAT
    # --------------------------------------------------------

    if chatbot.has_document():

        st.markdown(
            f"""
            <div class="document-card">

                <div class="document-title">
                    📄 {chatbot.document_name}
                </div>

                <div class="document-info">
                    Document-assisted mode •
                    {len(chatbot.document_text):,} characters
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])


    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

    question = st.chat_input(
        "Message SakshamAI..."
    )


    if question:

        # ----------------------------------------------------
        # USER MESSAGE
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
            }
        )


        with st.chat_message("user"):

            st.markdown(question)


        # ----------------------------------------------------
        # AI RESPONSE
        # ----------------------------------------------------

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                try:

                    answer = chatbot.ask(question)

                except Exception as error:

                    answer = (
                        "Sorry, something went wrong while "
                        "processing your question.\n\n"
                        f"{error}"
                    )


            st.markdown(answer)


        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )


# ============================================================
# DOCUMENTS PAGE
# ============================================================

elif st.session_state.page == "Documents":

    st.title("📄 Documents")

    st.write(
        "Upload a PDF, TXT file, or image containing your "
        "study material."
    )


    uploaded_file = st.file_uploader(
        "Choose a document",
        type=[
            "pdf",
            "txt",
            "png",
            "jpg",
            "jpeg",
            "webp",
            "bmp",
            "tiff",
        ],
    )


    if uploaded_file:

        file_id = (
            uploaded_file.name,
            uploaded_file.size,
        )


        if st.session_state.last_uploaded_file != file_id:

            if st.button(
                "⚡ Process Document",
                type="primary",
                use_container_width=True,
            ):

                try:

                    with st.spinner(
                        "Processing your document..."
                    ):

                        suffix = Path(
                            uploaded_file.name
                        ).suffix


                        with tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=suffix,
                        ) as temp_file:

                            temp_file.write(
                                uploaded_file.getbuffer()
                            )

                            temp_path = temp_file.name


                        document_text, document_name = (
                            load_document_from_file(
                                temp_path
                            )
                        )


                        chatbot.set_document(
                            document_text,
                            document_name,
                        )


                        st.session_state.last_uploaded_file = (
                            file_id
                        )

                        st.session_state.messages = []


                    st.success(
                        "✅ Document processed successfully!"
                    )


                    # ------------------------------------------------
                    # DOCUMENT INFORMATION
                    # ------------------------------------------------

                    col1, col2, col3 = st.columns(3)


                    with col1:

                        st.metric(
                            "File",
                            document_name,
                        )


                    with col2:

                        st.metric(
                            "Characters",
                            f"{len(document_text):,}",
                        )


                    with col3:

                        st.metric(
                            "Mode",
                            "Document AI",
                        )


                    st.markdown("---")


                    st.subheader(
                        "📖 Extracted Text"
                    )


                    with st.expander(
                        "View extracted document text"
                    ):

                        st.text_area(
                            "Extracted text",
                            document_text,
                            height=400,
                            label_visibility="collapsed",
                        )


                    st.info(
                        "Your document is now loaded. "
                        "Go to Chat and ask questions about it."
                    )


                except Exception as error:

                    st.error(
                        "❌ Document processing failed."
                    )

                    st.exception(error)


# ============================================================
# STUDY PAGE
# ============================================================

elif st.session_state.page == "Study":

    st.title("📚 Study")

    if chatbot.has_document():

        st.success(
            f"Study material loaded: "
            f"{chatbot.document_name}"
        )


        st.write(
            "Your document is ready for study assistance."
        )


        col1, col2, col3 = st.columns(3)


        with col1:

            st.info(
                "📝\n\n"
                "**Notes**\n\n"
                "AI-generated notes can be connected "
                "to the Gemini core module."
            )


        with col2:

            st.info(
                "🧠\n\n"
                "**Flashcards**\n\n"
                "Flashcards can be connected to "
                "the Gemini core module."
            )


        with col3:

            st.info(
                "❓\n\n"
                "**Quiz**\n\n"
                "Quiz generation can be connected "
                "to the Gemini core module."
            )


        st.markdown("---")


        if st.button(
            "💬 Ask Questions About This Document",
            use_container_width=True,
        ):

            st.session_state.page = "Chat"

            st.rerun()


    else:

        st.info(
            "📄 Upload a document first to use "
            "study assistance."
        )


        if st.button(
            "📄 Upload Document",
            use_container_width=True,
        ):

            st.session_state.page = "Documents"

            st.rerun()


# ============================================================
# ACCESSIBILITY PAGE
# ============================================================

elif st.session_state.page == "Accessibility":

    st.title("♿ Accessibility")

    st.write(
        "Accessibility options for a more comfortable "
        "learning experience."
    )


    col1, col2 = st.columns(2)


    with col1:

        st.checkbox(
            "🔠 Larger Text"
        )

        st.checkbox(
            "🎨 High Contrast"
        )


    with col2:

        st.checkbox(
            "📖 Simplified Reading"
        )

        st.checkbox(
            "🔊 Voice Mode"
        )


    st.info(
        "These controls are currently UI options. "
        "Voice and advanced accessibility functionality "
        "can be connected to the voice module."
    )


# ============================================================
# SETTINGS PAGE
# ============================================================

elif st.session_state.page == "Settings":

    st.title("⚙️ Settings")


    language = st.selectbox(
        "Language",
        [
            "English",
            "Hindi",
            "Marathi",
        ],
    )


    interface = st.selectbox(
        "Interface",
        [
            "Standard",
            "Accessible",
        ],
    )


    st.write(
        f"Language: **{language}**"
    )

    st.write(
        f"Interface: **{interface}**"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        SakshamAI • Assistive Learning Tools for
        Differently-Abled Students
    </div>
    """,
    unsafe_allow_html=True,
)