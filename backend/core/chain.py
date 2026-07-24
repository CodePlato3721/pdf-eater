from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStore
from config import MODEL_NAME, TOP_K
from core.http_logging import create_logging_http_client

# LangChain's default stuff-QA prompt only says "if you don't know, say you
# don't know" — it never forbids the model from falling back on its own
# training knowledge. That lets the LLM answer confidently from outside
# knowledge even when the retrieved context has nothing relevant, producing
# an answer the citation layer then (correctly) can't support.
NOT_FOUND_ANSWER = "I don't know based on the provided document."
QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "Answer the question using ONLY the information in the context below. "
        "Do not use any outside or prior knowledge, even if you already know the answer. "
        f'If the context does not contain the answer, respond exactly with "{NOT_FOUND_ANSWER}"\n\n'
        "Context:\n{context}\n\n"
        "Question: {question}\n"
        "Answer:"
    ),
)


def create_chain(vectorstore: VectorStore):
    """
    Create a conversational retrieval chain from a vectorstore.

    Args:
        vectorstore: Any VectorStore instance (e.g. FAISS).

    Returns:
        ConversationalRetrievalChain instance.
    """
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )
    qa = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model=MODEL_NAME, temperature=0, http_client=create_logging_http_client("LLM")),
        retriever=retriever,
        return_source_documents=True,
        return_generated_question=True,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
    )
    return qa
