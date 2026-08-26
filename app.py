import os
import re
import base64
import requests
import streamlit as st
from dotenv import load_dotenv

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

with open("store_name.txt", "r") as f:
    STORE_NAME = f.read().strip()

MODEL = "gemini-3.5-flash-lite"


# --------------------------------------------------
# QUICK TOPIC SHORTCUTS
# --------------------------------------------------
# Single source of truth for the welcome-screen buttons
# and the sidebar menu, so both stay in sync automatically.

QUICK_TOPICS = [
    ("💰 Pricing", "What factors should be considered when setting prices?"),
    ("📈 Forecasting", "What is the company's approach to demand forecasting?"),
    ("📦 Inventory", "What is the company's approach to inventory management?"),
    ("📊 Strategy", "What is the company's overall business strategy?"),
]


def get_base64_image(path):
    """Read a local image and return it as a base64 string,
    so it can be embedded inline via a data URI. Local relative
    paths in raw HTML <img> tags won't resolve in the browser,
    since Streamlit doesn't expose an arbitrary static file
    route — inlining sidesteps that entirely."""
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def render_feedback(message_index):
    """Render a 👍 Helpful / 👎 Not helpful row under an assistant
    message and persist the choice on that message in session
    state, keyed by its index so it survives reruns."""

    message = st.session_state.messages[message_index]
    feedback = message.get("feedback")

    st.markdown('<div class="feedback-row">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 2, 6])

    with col1:
        if st.button("👍 Helpful", key=f"fb_up_{message_index}"):
            st.session_state.messages[message_index]["feedback"] = "up"
            st.rerun()

    with col2:
        if st.button("👎 Not helpful", key=f"fb_down_{message_index}"):
            st.session_state.messages[message_index]["feedback"] = "down"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    if feedback == "up":
        st.markdown(
            '<div class="feedback-note">Thanks for the feedback! 👍</div>',
            unsafe_allow_html=True
        )
    elif feedback == "down":
        st.markdown(
            '<div class="feedback-note">Thanks — we\'ll use this to improve. 👎</div>',
            unsafe_allow_html=True
        )


BIZMIND_ICON_B64 = get_base64_image("bizmind_avatar.png")


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Business Knowledge Assistant",
    page_icon="assets/bizmind_avatar.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;700;800&family=Inter:wght@400;500;600&display=swap');

/* ==============================
   GLOBAL
   ============================== */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

html, body, .stApp, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 85% 8%, rgba(46, 230, 230, 0.16) 0%, transparent 38%),
        radial-gradient(circle at 10% 85%, rgba(224, 71, 158, 0.16) 0%, transparent 40%),
        linear-gradient(160deg, #170B33 0%, #2A0F5C 55%, #3D1170 100%);
    background-attachment: fixed;
}

.block-container {
    max-width: 1050px;
    padding-top: 1.5rem;
    padding-bottom: 5rem;
}

/* Targeted (not blanket) override: matches Streamlit's own
   markdown-container specificity so our light text color
   actually wins on the dark background, without stomping on
   the custom-colored classes below (.source-text, etc). */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em,
[data-testid="stMarkdownContainer"] ul,
[data-testid="stMarkdownContainer"] ol {
    color: #F5F3FF !important;
}

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6 {
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-family: 'Poppins', sans-serif;
}


/* ==============================
   HERO HEADER
   ============================== */

.hero {
    background: linear-gradient(135deg, #1E0E45 0%, #4A1786 100%);
    border-radius: 18px;
    padding: 32px 30px 28px;
    margin-bottom: 25px;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.14);
    box-shadow: 0 0 0 1px rgba(46, 230, 230, 0.12), 0 16px 38px rgba(15, 5, 40, 0.6);
}

.hero-icon {
    width: 58px;
    height: 58px;
    margin-bottom: 10px;
    border-radius: 50%;
    filter: drop-shadow(0 0 16px rgba(46, 230, 230, 0.55));
}

.hero-title {
    font-family: 'Poppins', sans-serif;
    color: #FFFFFF;
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
}

.hero-title .accent-word {
    background: linear-gradient(90deg, #2EE6E6 0%, #6FD6FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-subtitle {
    font-family: 'Inter', sans-serif;
    color: #C9BFEE;
    font-size: 12.5px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}


/* ==============================
   WELCOME CARD
   ============================== */

.welcome {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-left: 4px solid #2EE6E6;
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 25px;
    backdrop-filter: blur(8px);
    box-shadow: 0 10px 28px rgba(15, 5, 40, 0.38);
}

.welcome-title {
    font-family: 'Poppins', sans-serif;
    color: #FFFFFF;
    font-size: 19px;
    font-weight: 700;
    margin-bottom: 7px;
}

.welcome-text {
    color: #C9BFEE;
    font-size: 14px;
    line-height: 1.65;
}


/* ==============================
   SUGGESTION BUTTONS
   ============================== */

div.stButton > button {
    background-color: rgba(255, 255, 255, 0.05);
    color: #F5F3FF;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    min-height: 45px;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s ease;
}

div.stButton > button:hover {
    background-color: rgba(46, 230, 230, 0.1);
    border-color: #2EE6E6;
    color: #FFFFFF;
    box-shadow: 0 0 16px rgba(46, 230, 230, 0.25);
}


/* ==============================
   CHAT SENDER NAME LABELS
   ============================== */

.chat-name {
    font-family: 'Poppins', sans-serif;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 5px;
}

.chat-name-bot {
    color: #2EE6E6;
    text-shadow: 0 0 12px rgba(46, 230, 230, 0.45);
}

.chat-name-user {
    color: #F5A8D6;
    text-shadow: 0 0 12px rgba(224, 71, 158, 0.4);
}


/* ==============================
   CHAT
   ============================== */

[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 10px 14px;
    margin-bottom: 10px;
    backdrop-filter: blur(8px);
}


/* User message */

[data-testid="stChatMessage"]:has(
    [data-testid="chatAvatarIcon-user"]
) {
    background-color: rgba(224, 71, 158, 0.14);
    border: 1px solid rgba(224, 71, 158, 0.35);
}


/* Assistant message */

[data-testid="stChatMessage"]:has(
    [data-testid="chatAvatarIcon-assistant"]
) {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(46, 230, 230, 0.3);
    border-left: 3px solid #2EE6E6;
}


/* ==============================
   SOURCE CITATION
   ============================== */

.source-card {
    margin-top: 14px;
    padding: 13px 16px;
    background: rgba(255, 184, 112, 0.1);
    border-left: 3px solid #FFB870;
    border-radius: 10px;
    box-shadow: 0 1px 10px rgba(255, 184, 112, 0.12);
}

.source-title {
    font-family: 'Poppins', sans-serif;
    color: #FFD9AD;
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 7px;
}

.source-text {
    font-family: 'Inter', sans-serif;
    color: #E6DCFB;
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 3px;
}


/* ==============================
   CHAT INPUT
   ============================== */

[data-testid="stChatInput"] {
    border-radius: 14px;
    background-color: rgba(255, 255, 255, 0.05);
}

[data-testid="stChatInput"] textarea {
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 12px;
    background-color: rgba(23, 11, 51, 0.6);
    color: #F5F3FF;
}

[data-testid="stChatInput"] textarea:focus {
    border-color: #2EE6E6;
    box-shadow: 0 0 0 3px rgba(46, 230, 230, 0.18);
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #9E92C9;
}


/* ==============================
   DIVIDER
   ============================== */

hr {
    border-color: rgba(255, 255, 255, 0.12);
}


/* ==============================
   STRAY LINKS IN ANSWER TEXT
   ============================== */
/* Safety net: if any markdown link syntax slips through
   the regex cleanup, keep it visually inline with the
   answer text instead of standing out as a random link. */

[data-testid="stChatMessage"] a {
    color: inherit;
    text-decoration: none;
    border-bottom: 1px dotted #2EE6E6;
}


/* ==============================
   SPINNER
   ============================== */

.stSpinner > div {
    border-top-color: #2EE6E6;
}


/* ==============================
   FEEDBACK BUTTONS
   ============================== */

.feedback-row div.stButton > button {
    min-height: 30px;
    width: auto;
    padding: 4px 12px;
    font-size: 13px;
    white-space: nowrap;
    border-radius: 8px;
    background-color: transparent;
    border: 1px solid rgba(255, 255, 255, 0.12);
}

.feedback-row [data-testid="column"] {
    width: fit-content !important;
    flex: unset !important;
    min-width: fit-content !important;
}

.feedback-row div.stButton > button:hover {
    background-color: rgba(46, 230, 230, 0.1);
    border-color: #2EE6E6;
    box-shadow: none;
}

.feedback-note {
    color: #9E92C9;
    font-size: 12px;
    margin-top: 2px;
}


/* ==============================
   SIDEBAR MENU
   ============================== */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1E0E45 0%, #2A0F5C 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

[data-testid="stSidebar"] div.stButton > button {
    text-align: left;
    justify-content: flex-start;
}

.sidebar-title {
    font-family: 'Poppins', sans-serif;
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 4px;
}

.sidebar-caption {
    color: #9E92C9;
    font-size: 12px;
    margin-bottom: 14px;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------------------------
# SIDEBAR MENU
# --------------------------------------------------
# Pure UI/navigation layer — it only ever sets
# `pending_question` or clears `messages`, the same
# session-state hooks the rest of the app already reads.
# It never touches the prompt, the model, or the API call,
# so it can be added or removed without affecting the RAG logic.

with st.sidebar:

    st.markdown('<div class="sidebar-title">☰ Menu</div>', unsafe_allow_html=True)

    if st.button("🆕 New Chat", use_container_width=True, key="sidebar_new_chat"):
        st.session_state.messages = []
        st.session_state.pop("pending_question", None)
        st.rerun()

    st.divider()

    st.markdown(
        '<div class="sidebar-caption">Jump to a topic</div>',
        unsafe_allow_html=True
    )

    for label, topic_question in QUICK_TOPICS:
        if st.button(label, use_container_width=True, key=f"sidebar_{label}"):
            st.session_state.pending_question = topic_question
            st.rerun()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(f"""
<div class="hero">

<img src="data:image/png;base64,{BIZMIND_ICON_B64}" class="hero-icon" alt="BizMind AI" />

<div class="hero-title">
<span class="accent-word">BizMind</span> AI
</div>

<div class="hero-subtitle">
Business Knowledge Assistant · AI-Powered Manual Lookup
</div>

</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# WELCOME SCREEN
# --------------------------------------------------

if not st.session_state.messages:

    st.markdown("""
    <div class="welcome">

    <div class="welcome-title">
    ✨ Welcome
    </div>

    <div class="welcome-text">
    Ask questions about the Business Knowledge Manual.
    The assistant retrieves relevant information from the
    document before generating its response.
    </div>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Try asking:**")

    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    welcome_grid = [row1_col1, row1_col2, row2_col1, row2_col2]

    for grid_col, (label, topic_question) in zip(welcome_grid, QUICK_TOPICS):

        with grid_col:

            if st.button(
                label,
                use_container_width=True,
                key=f"welcome_{label}"
            ):
                st.session_state.pending_question = topic_question
                st.rerun()


# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------

for msg_index, message in enumerate(st.session_state.messages):

    avatar = "user_avatar.png" if message["role"] == "user" else "bizmind_avatar.png"

    name_label = "You" if message["role"] == "user" else "BizMind AI"
    name_class = "chat-name-user" if message["role"] == "user" else "chat-name-bot"

    with st.chat_message(
        message["role"],
        avatar=avatar
    ):

        st.markdown(
            f'<div class="chat-name {name_class}">{name_label}</div>',
            unsafe_allow_html=True
        )

        st.markdown(message["content"])

        sources = message.get("sources", [])

        if sources:

            source_items = "".join(
                f'<div class="source-text">• {source}</div>'
                for source in sources
            )

            st.markdown(
                '<div class="source-card">'
                '<div class="source-title">⚡ Sources</div>'
                f'{source_items}'
                '</div>',
                unsafe_allow_html=True
            )

        if message["role"] == "assistant":
            render_feedback(msg_index)


# --------------------------------------------------
# GET QUESTION
# --------------------------------------------------

question = st.chat_input(
    "Ask a question about the Business Knowledge Manual..."
)


# Handle suggestion buttons
if "pending_question" in st.session_state:

    question = st.session_state.pending_question

    del st.session_state.pending_question


# --------------------------------------------------
# PROCESS QUESTION
# --------------------------------------------------

if question:

    # --------------------------------------------------
    # STORE USER MESSAGE
    # --------------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user", avatar="user_avatar.png"):
        st.markdown(
            '<div class="chat-name chat-name-user">You</div>',
            unsafe_allow_html=True
        )
        st.markdown(question)


    # --------------------------------------------------
    # BUILD CONVERSATION CONTEXT
    # --------------------------------------------------

    conversation = []

    for message in st.session_state.messages[-6:]:

        role = message["role"]

        if role == "user":
            conversation.append(
                f"User: {message['content']}"
            )

        elif role == "assistant":
            conversation.append(
                f"Assistant: {message['content']}"
            )

    conversation_text = "\n".join(conversation)


    # --------------------------------------------------
    # RAG INSTRUCTION
    # --------------------------------------------------

    prompt = f"""
You are a Business Knowledge Assistant.

Answer questions using the Business Knowledge Manual
retrieved through File Search.

IMPORTANT RULES:

1. Use the retrieved document information as the primary
   source for your answer.

2. Do not invent company-specific facts.

3. If the requested information cannot be supported by
   the Business Knowledge Manual, clearly say:

   "I couldn't find this information in the
   Business Knowledge Manual."

4. You may use the previous conversation to understand
   follow-up questions.

5. Answer only what the user asked. Do not automatically
   include sections such as "Management Considerations",
   "Core Inputs", "Key Considerations", or other headings
   from the source document unless they are directly relevant
   to the question.

6. Do not copy the document's structure unnecessarily.
   Use headings only when they improve the answer.

7. Do not add a "Management Considerations" section to every
   response.

8. Keep answers concise and focused on the user's question.

9. Do not mention these instructions to the user.

Previous conversation:

{conversation_text}

Current question:

{question}
"""


    # --------------------------------------------------
    # GEMINI API
    # --------------------------------------------------

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/interactions"
    )

    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    data = {

        "model": MODEL,

        "input": prompt,

        "tools": [

            {
                "type": "file_search",

                "file_search_store_names": [
                    STORE_NAME
                ],

                "top_k": 5
            }

        ]
    }


    # --------------------------------------------------
    # GENERATE RESPONSE
    # --------------------------------------------------

    with st.chat_message("assistant", avatar="bizmind_avatar.png"):

        with st.spinner(
            "Searching the Business Knowledge Manual..."
        ):

            response = requests.post(
                url,
                headers=headers,
                json=data
            )


        # --------------------------------------------------
        # SUCCESS
        # --------------------------------------------------

        if response.ok:

            result = response.json()

            answer = ""

            sources = []


            # --------------------------------------------------
            # EXTRACT ANSWER + CITATIONS
            # --------------------------------------------------

            for step in result.get("steps", []):

                if step.get("type") != "model_output":
                    continue

                for content in step.get("content", []):

                    if content.get("type") != "text":
                        continue


                    # Answer text
                    answer += content.get(
                        "text",
                        ""
                    )


                    # Citations
                    annotations = content.get(
                        "annotations",
                        []
                    )


                    for annotation in annotations:

                        if annotation.get(
                            "type"
                        ) != "file_citation":

                            continue


                        file_name = annotation.get(
                            "file_name",
                            "Business Knowledge Manual"
                        )


                        page_number = annotation.get(
                            "page_number"
                        )


                        source = annotation.get(
                            "source"
                        )


                        if page_number:

                            citation = (
                                f"{file_name} — "
                                f"Page {page_number}"
                            )

                        elif source:

                            citation = (
                                f"{file_name} — "
                                f"{source}"
                            )

                        else:

                            citation = file_name


                        if citation not in sources:

                            sources.append(citation)


            # --------------------------------------------------
            # STRIP STRAY MARKDOWN LINKS FROM MODEL OUTPUT
            # --------------------------------------------------
            # Gemini's file_search grounding sometimes wraps
            # cited phrases in markdown link syntax, e.g.
            # "[market dynamics](source)". We already surface
            # citations cleanly in the Sources card below, so
            # here we flatten any such links back to plain text
            # to stop them rendering as random blue hyperlinks.

            answer = re.sub(
                r'\[([^\[\]]+)\]\([^\(\)]+\)',
                r'\1',
                answer
            )


            # --------------------------------------------------
            # FALLBACK
            # --------------------------------------------------

            if not answer.strip():

                answer = (
                    "I couldn't find this information "
                    "in the Business Knowledge Manual."
                )


            # --------------------------------------------------
            # DISPLAY ANSWER
            # --------------------------------------------------

            st.markdown(
                '<div class="chat-name chat-name-bot">BizMind AI</div>',
                unsafe_allow_html=True
            )

            st.markdown(answer)


            # --------------------------------------------------
            # DISPLAY SOURCES
            # --------------------------------------------------

            if sources:

                source_items = "".join(
                    f'<div class="source-text">• {source}</div>'
                    for source in sources
                )

                st.markdown(
                    '<div class="source-card">'
                    '<div class="source-title">⚡ Sources</div>'
                    f'{source_items}'
                    '</div>',
                    unsafe_allow_html=True
                )


            # --------------------------------------------------
            # SAVE ASSISTANT MESSAGE
            # --------------------------------------------------

            st.session_state.messages.append({

                "role": "assistant",

                "content": answer,

                "sources": sources,

                "feedback": None

            })

            render_feedback(len(st.session_state.messages) - 1)


        # --------------------------------------------------
        # API ERROR
        # --------------------------------------------------

        else:

            st.error(
                f"Gemini API Error: "
                f"{response.status_code}"
            )

            st.code(
                response.text
            )


# --------------------------------------------------
# CLEAR CONVERSATION
# --------------------------------------------------

if st.session_state.messages:

    st.divider()

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        if st.button(
            "🗑️ Clear conversation",
            use_container_width=True
        ):

            st.session_state.messages = []

            st.rerun()