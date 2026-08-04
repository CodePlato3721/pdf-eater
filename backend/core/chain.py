from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores import VectorStore
from config import MODEL_NAME
from core.http_logging import create_logging_http_client
from core.hyde_retriever import HydeRetriever

# LangChain's default stuff-QA prompt only says "if you don't know, say you
# don't know" — it never forbids the model from falling back on its own
# training knowledge. That lets the LLM answer confidently from outside
# knowledge even when the retrieved context has nothing relevant, producing
# an answer the citation layer then (correctly) can't support.
#
# Two more wording choices matter here (PD-09): the retrieved text is called
# "the document" rather than "the context" — labelling it "context" invited
# the model to describe its own prompt input back to the user (e.g. "at the
# beginning of the context provided") instead of answering the question, even
# when the retrieved text plainly contained the answer. The model is also
# told to answer with a specific fact/quote rather than describing the
# document, for the same reason.
NOT_FOUND_ANSWER = "I don't know based on the provided document."
QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "Answer the question using ONLY the information in the document below. "
        "Do not use any outside or prior knowledge, even if you already know the answer. "
        "Answer with the specific fact or detail from the document, quoting or paraphrasing "
        "the relevant passage, rather than describing the document itself. "
        f'If the document does not contain the answer, respond exactly with "{NOT_FOUND_ANSWER}"\n\n'
        "Document:\n{context}\n\n"
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
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0, http_client=create_logging_http_client("LLM"))
    retriever = HydeRetriever(vectorstore=vectorstore, llm=llm)
    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        return_generated_question=True,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
    )
    return qa
