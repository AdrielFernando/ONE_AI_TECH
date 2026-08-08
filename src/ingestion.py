"""
Módulo de ingestão de documentos.

Responsável por ler documentos em múltiplos formatos (PDF, Markdown, CSV,
e futuramente Word, Excel, PowerPoint, JSON e HTML) e transformá-los em
uma lista de objetos Document do LangChain, prontos para serem divididos
em chunks e indexados no vector store.

Cada Document carrega metadados úteis para rastreabilidade e para futuros
filtros de busca (ex: filtrar respostas apenas em documentos de uma
categoria específica).
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
)

from config import DOCS_DIR


# Mapeamento categoria -> nome de arquivo (metadado de negócio).
# Em um cenário real, isso viria de um sistema de gestão documental;
# aqui é mantido simples e explícito para fins do desafio.

CATEGORIA_POR_ARQUIVO = {
    "politica-privacidade.pdf": "Legal e Compliance",
    "termos-uso.pdf": "Legal e Compliance",
    "politica-seguranca-fraude.pdf": "Segurança",
    "faq-transacoes-limites.md": "Atendimento e Suporte",
    "tarifas-comissoes.csv": "Financeiro e Comercial",
}


def _carregar_pdf(caminho: Path) -> List[Document]:
    loader = PyPDFLoader(str(caminho))
    return loader.load()


def _carregar_markdown(caminho: Path) -> List[Document]:
    loader = TextLoader(str(caminho), encoding="utf-8")
    return loader.load()


def _carregar_csv(caminho: Path) -> List[Document]:
    # Cada linha do CSV vira um Document — ótimo para tabelas de tarifas,
    # onde cada linha é uma unidade de informação independente.
    loader = CSVLoader(str(caminho), encoding="utf-8")
    return loader.load()


# Roteador simples por extensão. Novos formatos (docx, xlsx, pptx, json,
# html) podem ser plugados aqui seguindo o mesmo padrão.

LOADERS_POR_EXTENSAO = {
    ".pdf": _carregar_pdf,
    ".md": _carregar_markdown,
    ".csv": _carregar_csv,
}


def carregar_documentos(pasta: Path = DOCS_DIR) -> List[Document]:
    """
    Percorre a pasta de documentos, carrega cada arquivo suportado
    e enriquece os metadados com a categoria de negócio correspondente.
    """
    documentos: List[Document] = []

    for arquivo in sorted(pasta.iterdir()):
        if not arquivo.is_file():
            continue

        loader_fn = LOADERS_POR_EXTENSAO.get(arquivo.suffix.lower())

        if loader_fn is None:
            print(
                f"[ingestion] Formato não suportado, ignorando: {arquivo.name}"
            )
            continue

        docs = loader_fn(arquivo)

        categoria = CATEGORIA_POR_ARQUIVO.get(
            arquivo.name,
            "Não categorizado"
        )

        for doc in docs:
            doc.metadata["arquivo_origem"] = arquivo.name
            doc.metadata["categoria"] = categoria

        documentos.extend(docs)

        print(
            f"[ingestion] {arquivo.name}: "
            f"{len(docs)} documento(s) carregado(s) — "
            f"categoria '{categoria}'"
        )

    print(
        f"[ingestion] Total de documentos carregados: "
        f"{len(documentos)}"
    )

    return documentos


if __name__ == "__main__":
    # Execução standalone para testar a ingestão isoladamente:
    # python -m src.ingestion

    docs = carregar_documentos()

    for d in docs[:3]:
        print("---")
        print(d.metadata)
        print(d.page_content[:200])

