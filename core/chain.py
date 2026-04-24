# core/chain.py
from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from config import MODEL_NAME, TOP_K

def create_chain(vectorstore):
    print(f"create_chain called, vectorstore: {vectorstore}")
    """
    Create a conversational retrieval chain from a vectorstore.
    """
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K}
    )
    qa = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model=MODEL_NAME, temperature=0),
        retriever=retriever,
        return_source_documents=True,
        return_generated_question=True,
    )
    return qa