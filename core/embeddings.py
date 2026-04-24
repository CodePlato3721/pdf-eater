# core/embeddings.py
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch

def create_vectorstore(docs):
    print(f"Creating vectorstore with {len(docs)} chunks...")
    embeddings = OpenAIEmbeddings()
    vectorstore = DocArrayInMemorySearch.from_documents(docs, embeddings)
    print("Vectorstore created successfully.")
    return vectorstore