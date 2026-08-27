import sys
from pathlib import Path

import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

# Get the main SakshamAI project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add document_processing folder to Python path.
# This is needed because the existing document_processor.py
# imports document_models, pdf_processor and image_processor
# directly.
DOCUMENT_PROCESSING_PATH = PROJECT_ROOT / "document_processing"

if str(DOCUMENT_PROCESSING_PATH) not in sys.path:
    sys.path.insert(0, str(DOCUMENT_PROCESSING_PATH))


# Import your friend's existing document-processing function
from document_processor import process_document


# ============================================================
# PAGE CONFIGURATION
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

    /* Main page */
    .stApp {
        background-color: #f7f9fc;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        padding: 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 25px;
    }

    .main-header h1 {
        font-size: 42px;
        margin-bottom: 5px;
    }

    .main-header p {
        font-size: 18px;
        margin-top: 5px;
        opacity: 0.92;
    }

    /* Upload card */
    .upload-card {
        background: white;
        padding: 30px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

    /* Information cards */
    .info-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        min-height: 120px;
    }

    .info-title {
        color: #6b7280;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .info-value {
        color: #111827;
        font-size: 24px;
        font-weight: 700;
    }

    /* Success box */
    .success-box {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        color: #065f46;
        padding: 15px;
        border-radius: 12px;
        margin: 15px 0;
    }

    /* Error box */
    .error-box {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
        padding: 15px;
        border-radius: 12px;
        margin: 15px 0;
    }

    /* Feature cards */
    .feature-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        padding: 22px;
        text-align: center;
        min-height: 150px;
    }

    .feature-icon {
        font-size: 32px;
    }

    .feature-title {
        font-size: 18px;
        font-weight: 700;
        margin-top: 8px;
    }

    .feature-description {
        color: #6b7280;
        font-size: 14px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "processing_result" not in st.session_state:
    st.session_state.processing_result = None

if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🧠 SakshamAI")

    st.markdown(
        """
        **Assistive Learning Tools**

        Learn from your educational documents
        in a simpler and more accessible way.
        """
    )

    st.divider()

    menu = st.radio(
        "Navigation",
        [
            "🏠 Home",
            "📄 Upload Document",
            "📚 Study",
        ],
    )

    st.divider()

    st.caption("SakshamAI • Version 1")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="main-header">
        <h1>🧠 SakshamAI</h1>
        <p>Assistive Learning Tools for Differently-Abled Students</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HOME
# ============================================================

if menu == "🏠 Home":

    st.subheader("Welcome to SakshamAI 👋")

    st.write(
        "Upload your educational PDF or image and SakshamAI "
        "will prepare the document for accessible learning."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📄</div>
                <div class="feature-title">Upload Documents</div>
                <div class="feature-description">
                    Upload educational PDFs or images.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📝</div>
                <div class="feature-title">Study Support</div>
                <div class="feature-description">
                    Prepare your document for learning features.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">♿</div>
                <div class="feature-title">Accessible Learning</div>
                <div class="feature-description">
                    Designed with accessibility in mind.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.info(
        "Start by selecting **📄 Upload Document** from the sidebar."
    )


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

elif menu == "📄 Upload Document":

    st.subheader("📄 Upload Study Material")

    st.write(
        "Upload a PDF or image containing your educational material."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=[
            "pdf",
            "png",
            "jpg",
            "jpeg",
            "webp",
            "bmp",
            "tiff",
        ],
        help="Supported formats: PDF, PNG, JPG, JPEG, WEBP, BMP and TIFF",
    )

    if uploaded_file is not None:

        st.markdown("<br>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # File information
        # ----------------------------------------------------

        file_size_mb = uploaded_file.size / (1024 * 1024)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="info-title">File Name</div>
                    <div class="info-value" style="font-size:18px;">
                        {uploaded_file.name}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="info-title">File Type</div>
                    <div class="info-value">
                        {uploaded_file.type or "Unknown"}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="info-title">File Size</div>
                    <div class="info-value">
                        {file_size_mb:.2f} MB
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # Preview image
        # ----------------------------------------------------

        file_extension = Path(uploaded_file.name).suffix.lower()

        if file_extension in {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".bmp",
            ".tiff",
        }:

            st.subheader("🖼️ Image Preview")

            st.image(
                uploaded_file,
                caption=uploaded_file.name,
                width="stretch",
            )

        elif file_extension == ".pdf":

            st.info(
                "📄 PDF selected. The document will be processed "
                "when you click the button below."
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # Process button
        # ----------------------------------------------------

        process_button = st.button(
            "⚡ Process Document",
            type="primary",
            use_container_width=True,
        )

        if process_button:

            try:

                file_bytes = uploaded_file.getvalue()

                if not file_bytes:
                    st.error("The uploaded file is empty.")
                    st.stop()

                # --------------------------------------------
                # Processing
                # --------------------------------------------

                with st.spinner(
                    "Processing your document... Please wait."
                ):

                    result = process_document(
                        file_bytes,
                        uploaded_file.name,
                    )

                # Save result
                st.session_state.processing_result = result
                st.session_state.uploaded_filename = uploaded_file.name

                # --------------------------------------------
                # Result
                # --------------------------------------------

                if result.success:

                    st.markdown(
                        """
                        <div class="success-box">
                            ✅ Document processed successfully!
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.balloons()

                else:

                    st.markdown(
                        """
                        <div class="error-box">
                            ❌ Document processing failed.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if result.error:
                        st.error(result.error)

            except Exception as e:

                st.error(
                    "Something went wrong while processing the document."
                )

                st.exception(e)

    # ========================================================
    # DISPLAY PROCESSING RESULT
    # ========================================================

    result = st.session_state.processing_result

    if result is not None:

        st.divider()

        st.subheader("📊 Processing Result")

        # ----------------------------------------------------
        # Result statistics
        # ----------------------------------------------------

        result_col1, result_col2, result_col3, result_col4 = st.columns(4)

        with result_col1:
            st.metric(
                "Status",
                "Success" if result.success else "Failed",
            )

        with result_col2:
            st.metric(
                "File Type",
                result.file_type.upper(),
            )

        with result_col3:
            st.metric(
                "Pages",
                len(result.pages),
            )

        with result_col4:
            st.metric(
                "Processing Time",
                f"{result.processing_time_seconds:.2f}s",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # Extracted text
        # ----------------------------------------------------

        if result.success:

            st.subheader("📖 Extracted Text")

            if result.full_text:

                st.text_area(
                    "Document content",
                    value=result.full_text,
                    height=400,
                    disabled=True,
                    label_visibility="collapsed",
                )

                st.caption(
                    f"Characters extracted: {len(result.full_text):,}"
                )

            else:

                st.warning(
                    "The document was processed, but no text was extracted."
                )

            # ------------------------------------------------
            # Page information
            # ------------------------------------------------

            if result.pages:

                st.subheader("📑 Page Information")

                page_data = []

                for page in result.pages:

                    page_data.append(
                        {
                            "Page": page.page_number,
                            "Method": page.method,
                            "Characters": page.char_count,
                        }
                    )

                st.dataframe(
                    page_data,
                    use_container_width=True,
                    hide_index=True,
                )

            # ------------------------------------------------
            # Warnings
            # ------------------------------------------------

            if result.warnings:

                st.subheader("⚠️ Warnings")

                for warning in result.warnings:
                    st.warning(warning)

        else:

            st.error(
                result.error
                if result.error
                else "Unknown processing error."
            )


# ============================================================
# STUDY PAGE
# ============================================================

elif menu == "📚 Study":

    st.subheader("📚 Study Dashboard")

    if st.session_state.processing_result is None:

        st.info(
            "📄 Please upload and process a document first."
        )

    else:

        result = st.session_state.processing_result

        if result.success:

            st.success(
                f"Document ready: {result.filename}"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:

                st.markdown(
                    """
                    <div class="feature-card">
                        <div class="feature-icon">📝</div>
                        <div class="feature-title">
                            Simplified Notes
                        </div>
                        <div class="feature-description">
                            AI-generated study notes will appear here.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(
                    """
                    <div class="feature-card">
                        <div class="feature-icon">🗂️</div>
                        <div class="feature-title">
                            Flashcards
                        </div>
                        <div class="feature-description">
                            Revision flashcards will appear here.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:

                st.markdown(
                    """
                    <div class="feature-card">
                        <div class="feature-icon">❓</div>
                        <div class="feature-title">
                            Quiz
                        </div>
                        <div class="feature-description">
                            AI-generated quiz will appear here.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(
                    """
                    <div class="feature-card">
                        <div class="feature-icon">💬</div>
                        <div class="feature-title">
                            Ask Saksham
                        </div>
                        <div class="feature-description">
                            Document-based questions and answers.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            st.info(
                "These study features are UI placeholders for now. "
                "Your teammates can connect their Gemini and chatbot "
                "modules later."
            )

        else:

            st.warning(
                "The uploaded document could not be processed."
            )