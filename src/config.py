"""
Configurações centrais do agente ONE_AI_TECH.

Todas as variáveis sensíveis (chaves de API, etc.) devem vir do arquivo .env
(nunca hardcode credenciais aqui). Veja .env.example para o modelo.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# --- Caminhos do projeto ---
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
VECTORSTORE_DIR = BASE_DIR / "data" / "chroma"

# Carrega o .env explicitamente a partir da raiz do projeto, independente
# de onde o comando "streamlit run" for executado.
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- LLM / Embeddings ---
# Usamos Google Gemini para desenvolvimento: possui free tier real (sem
# cartão de crédito, sem custo), roda em nuvem (sem exigir hardware
# potente) e é o que a Alura recomenda. Quando o deploy for feito na OCI,
# essas configurações podem ser trocadas pelo OCI Generative AI Service
# sem precisar alterar o restante do código (ingestion.py e app.py não mudam).
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Algumas bibliotecas do Google leem a chave diretamente de variáveis de
# ambiente específicas (GOOGLE_API_KEY e, em versões mais novas,
# GEMINI_API_KEY), não apenas do parâmetro passado nas classes do
# LangChain. Garantimos aqui que ambas estejam disponíveis, evitando
# erros de autenticação.
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    os.environ["GEMINI_API_KEY"] = GOOGLE_API_KEY
else:
    raise RuntimeError(
        "GOOGLE_API_KEY não encontrada. Verifique se o arquivo .env existe "
        f"em {BASE_DIR} e contém a linha GOOGLE_API_KEY=sua_chave_real."
    )

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")

# --- RAG ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "4"))

# --- Nome da collection no vector store ---
COLLECTION_NAME = "one_ai_tech_docs"