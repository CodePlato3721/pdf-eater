from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_core.vectorstores import VectorStore
from config import MODEL_NAME, TOP_K


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
        llm=ChatOpenAI(model=MODEL_NAME, temperature=0),
        retriever=retriever,
        return_source_documents=True,
        return_generated_question=True,
    )
    return qa
