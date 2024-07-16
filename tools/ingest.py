"""This is for creating the embeding store based on the documents in the data folder
If not run on good GPU running google colab on TPU device is faster"""
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DATA_PATH = "data/"
DB_FAISS_PATH = "vectorstores/db_faiss"
HG_TOKEN = ...

def create_texts():
    loader = DirectoryLoader(DATA_PATH,
                             glob='*.pdf',
                             loader_cls=PyPDFLoader)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=64)
    texts = text_splitter.split_documents(documents)
    for text in texts:
        text.page_content = text.page_content.replace('\t', ' ').replace('\n', ' ')
        text.page_content = ' '.join(text.page_content.split())
        text.page_content = text.page_content.replace('\uf0b7', '\n')
        if text.page_content.endswith("PUBLIC VERSION"):
            text.page_content = text.page_content[:-len("PUBLIC VERSION")].rstrip()
    return texts


def create_vector_db():
    texts = create_texts()
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu', 'token': HG_TOKEN, "trust_remote_code": True})
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_FAISS_PATH)

if __name__ == "__main__":
    create_vector_db()