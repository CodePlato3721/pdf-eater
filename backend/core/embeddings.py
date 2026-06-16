from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


def create_vectorstore(docs):
    """
    Create a FAISS vectorstore from a list of documents.

    Args:
        docs: List of Document objects.

    Returns:
        FAISS vectorstore instance.
    """
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore


def save_vectorstore(vectorstore, path: str) -> None:
    """
    Persist a FAISS vectorstore to disk.

    Args:
        vectorstore: FAISS vectorstore instance.
        path: Directory path to save the index to.
    """
    vectorstore.save_local(path)


def load_vectorstore(path: str):
    """
    Load a FAISS vectorstore from disk.

    Args:
        path: Directory path where the index was saved.

    Returns:
        FAISS vectorstore instance.
    """
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
