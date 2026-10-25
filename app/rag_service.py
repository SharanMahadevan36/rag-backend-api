from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

CHROMA_DIR = "chroma_store"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "llama3.2:1b"

_embeddings = None
_llm = None

PROMPT = ChatPromptTemplate.from_template("""
You are a knowledgeable assistant answering questions about
the document(s) provided below.

Guidelines:
- Answer using the context provided. If the user asks for a
  summary, overview, or general explanation, synthesize the
  key points across the retrieved context.
- Match your answer length to what is asked: a simple factual
  question gets 1-2 sentences; a request for an explanation,
  summary, details, or overview gets a fuller response.
- If the user specifies an exact number of lines or sentences,
  follow that instruction as closely as possible.
- Only say "I cannot find this information in the uploaded
  documents" if the context truly has nothing relevant.

Context:
{context}

Question:
{question}

Answer:
""")


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings


def _get_llm():
    global _llm
    if _llm is None:
        _llm = OllamaLLM(model=LLM_MODEL, temperature=0.3)
    return _llm


def _get_store(user_id: int):
    return Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=_get_embeddings(),
        persist_directory=CHROMA_DIR,
    )


def ingest_pdf(pdf_path: str, user_id: int) -> int:
    docs = PyPDFLoader(pdf_path).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    if not chunks:
        return 0
    _get_store(user_id).add_documents(chunks)
    return len(chunks)


def get_rag_answer(question: str, user_id: int) -> str:
    retriever = _get_store(user_id).as_retriever(search_kwargs={"k": 3})
    results = retriever.invoke(question)

    if not results:
        return "No documents are indexed for your account yet. Upload a PDF with POST /upload first."

    context = "\n\n---\n\n".join(doc.page_content for doc in results)
    prompt = PROMPT.format(context=context, question=question)
    return _get_llm().invoke(prompt)