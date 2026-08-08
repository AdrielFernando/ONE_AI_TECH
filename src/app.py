"""
Interface do agente ONE_AI_TECH em Streamlit.

Execução local: streamlit run src/app.py
"""
import streamlit as st
from rag_chain import construir_agente

st.set_page_config(
    page_title="NovaPay | Assistente Interno",
    page_icon="💬",
    layout="centered",
)

st.title("💬 Assistente Interno NovaPay")
st.caption(
    "Tire dúvidas sobre políticas de privacidade, termos de uso, segurança, "
    "tarifas e transações com base nos documentos internos da empresa."
)


@st.cache_resource(show_spinner="Carregando base de conhecimento...")
def carregar_agente():
    return construir_agente(forcar_reindexacao=False)

agente = carregar_agente()

if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {
            "role": "assistant",
            "content": "Olá! Sou o assistente interno da NovaPay. Pode me perguntar "
                       "sobre políticas, termos de uso, segurança, tarifas ou limites de transação. 😊",
        }
    ]

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Digite sua pergunta...")

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando os documentos..."):
            resposta = agente.invoke(pergunta)
            st.markdown(resposta)

    st.session_state.mensagens.append({"role": "assistant", "content": resposta})

with st.sidebar:
    st.header("Sobre")
    st.write(
        "Este agente utiliza RAG (Retrieval-Augmented Generation) para "
        "responder com base nos documentos internos da NovaPay, cobrindo as "
        "categorias: Legal e Compliance, Segurança, Atendimento e Financeiro."
    )
    if st.button("🔄 Reindexar documentos"):
        st.cache_resource.clear()
        st.rerun()