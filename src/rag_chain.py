"""
Módulo de RAG (Retrieval-Augmented Generation).

Responsável por:
1. Dividir os documentos carregados em chunks (text splitting).
2. Gerar embeddings e indexar no vector store (Chroma, local).
3. Montar a cadeia de recuperação + geração que responde perguntas
   com base apenas nos documentos indexados.
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from config import (
    VECTORSTORE_DIR,
    COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
    LLM_MODEL,
    EMBEDDING_MODEL,
    GOOGLE_API_KEY,
)
from ingestion import carregar_documentos

SYSTEM_PROMPT = """Você é o assistente virtual interno da NovaPay, uma fintech.
Sua função é responder perguntas de colaboradores com base EXCLUSIVAMENTE
nos documentos internos fornecidos como contexto abaixo.

Regras importantes:
- Se a resposta não estiver no contexto fornecido, diga claramente que não
  encontrou essa informação nos documentos disponíveis. Não invente respostas.
- Sempre que possível, cite de qual documento a informação foi extraída
  (campo 'arquivo_origem' nos metadados do contexto).
- Seja direto e objetivo, mas mantenha um tom profissional e cordial.

Contexto recuperado dos documentos internos:
{context}
"""


def _formatar_contexto(documentos) -> str:
    """Formata os chunks recuperados incluindo a fonte, para citação."""
    blocos = []
    for doc in documentos:
        fonte = doc.metadata.get("arquivo_origem", "desconhecido")
        categoria = doc.metadata.get("categoria", "não categorizado")
        blocos.append(f"[Fonte: {fonte} | Categoria: {categoria}]\n{doc.page_content}")
    return "\n\n---\n\n".join(blocos)


def construir_vectorstore(forcar_reindexacao: bool = False) -> Chroma:
    """
    Cria (ou carrega, se já existir) o vector store persistido em disco.
    Use forcar_reindexacao=True sempre que os documentos em /docs mudarem.
    """
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)

    if VECTORSTORE_DIR.exists() and not forcar_reindexacao:
        print("[rag_chain] Carregando vector store existente...")
        return Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(VECTORSTORE_DIR),
        )

    print("[rag_chain] Indexando documentos do zero...")
    documentos = carregar_documentos()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documentos)
    print(f"[rag_chain] {len(documentos)} documento(s) divididos em {len(chunks)} chunk(s).")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTORSTORE_DIR),
    )
    return vectorstore


def construir_agente(forcar_reindexacao: bool = False):
    """
    Monta a chain completa: retriever (busca nos documentos) + LLM (geração
    da resposta). Retorna um objeto invocável: agente.invoke("pergunta").
    """
    vectorstore = construir_vectorstore(forcar_reindexacao=forcar_reindexacao)
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{pergunta}"),
    ])

    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0.2)

    agente = (
        {
            "context": retriever | _formatar_contexto,
            "pergunta": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return agente


if __name__ == "__main__":
    # Teste rápido via linha de comando: python -m src.rag_chain
    agente = construir_agente(forcar_reindexacao=True)
    while True:
        pergunta = input("\nPergunta (ou 'sair'): ")
        if pergunta.lower() in {"sair", "exit", "quit"}:
            break
        resposta = agente.invoke(pergunta)
        print(f"\nResposta: {resposta}")