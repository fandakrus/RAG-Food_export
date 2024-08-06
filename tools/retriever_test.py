from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

DB_FAISS_PATH = 'vectorstores/db_faiss'

def load_db():
    """
    Load the FAISS database from the local file
    """
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu', 'trust_remote_code': True})
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    return db

retriever = load_db().as_retriever(search_kwargs={'k': 5})

def retrieve(query):
    """
    Retrieve the most similar documents to the query
    """
    return retriever.invoke(query)

print(retrieve("What do you know about MALEE GROUP PUBLIC COMPANY LIMITED"))