import streamlit as st
from streamlit_chat import message as chat_message

from vocava import storage, entity
from vocava.service import Service

# ANTHROPIC_API_KEY = st.secrets["anthropic_api_key"]
# COHERE_API_KEY = st.secrets["cohere_api_key"]


import os
from dotenv import load_dotenv


# ANTHROPIC_API_KEY = st.secrets["anthropic_api_key"]
# COHERE_API_KEY = st.secrets["cohere_api_key"]
# openai.api_key = st.secrets["openai_api_key"]
# elevenlabs.set_api_key(st.secrets["eleven_labs_api_key"])

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

def main():
    st.title("Chatterbox")

    tutor = entity.get_tutor("Claude", key=ANTHROPIC_API_KEY)

    languages = list(entity.LANGUAGES)
    default_native_lang = st.session_state.get("user.native_lang", languages[0])
    default_target_lang = st.session_state.get("user.target_lang", languages[4])
    default_fluency = st.session_state.get("user.fluency", 3)
    native_language = st.sidebar.selectbox(
        "Native Language", options=entity.LANGUAGES,
        index=languages.index(default_native_lang),
    )
    target_language = st.sidebar.selectbox(
        "Choose Language", options=entity.LANGUAGES,
        index=languages.index(default_target_lang),
    )
    fluency = st.sidebar.slider("Fluency", min_value=1, max_value=10, step=1,
                                value=default_fluency)
    store = storage.VectorStore(COHERE_API_KEY)
    user = entity.User(
        native_language=native_language,
        target_language=target_language,
        fluency=fluency,
        db=store,
    )
    st.session_state["user.native_lang"] = native_language
    st.session_state["user.target_lang"] = target_language
    st.session_state["user.fluency"] = fluency

    view_native = st.sidebar.checkbox("Native View")
    user_input = st.text_input("Enter a Message")

    if "chatterbox.history" not in st.session_state:
        st.session_state["chatterbox.history"] = []

    if st.button("Send"):
        chatterbox = Service(
            name="chatterbox-native" if view_native else "chatterbox-target",
            user=user,
            tutor=tutor,
            max_tokens=300,
            native_mode=view_native,
        )
        history = st.session_state["chatterbox.history"]
        chat_history = "\n".join([
            f'USER: {interaction["user"][user.target_language_name()]}\n'
            f'TUTOR: {interaction["tutor"][user.target_language_name()]}'
            for interaction in history
        ])
        with st.spinner():
            data = chatterbox.run(
                history=chat_history,
                message=user_input,
                fluency=user.fluency(),
            )

        interaction = data["interaction"]
        st.session_state["chatterbox.history"].append(interaction)

    history = st.session_state["chatterbox.history"][::-1]
    if not history:
        return
    last_interaction = history[0]

    language = (user.native_language_name()
                if view_native else
                user.target_language_name())
    corrected = last_interaction["user"].get(
        f"{user.target_language_name()}_corrected"
    )
    explanation = last_interaction["user"].get(
        f"{user.native_language_name()}_explanation"
    )
    if corrected:
        st.warning(corrected)
        st.info(explanation)

    for i, interaction in enumerate(history):
        chat_message(interaction["tutor"][language], key=f"{i}")
        show_corrected = corrected and not view_native
        corrected_language = f"{language}_corrected" if show_corrected else language
        chat_message(interaction["user"][corrected_language],
                     is_user=True, key=f"{i}_user")


if __name__ == "__main__":
    main()
