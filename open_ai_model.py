from dotenv import load_dotenv
from langchain_openai import ChatOpenAI # This is to interact with OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
import chainlit as cl
from langchain_community.llms import CTransformers
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_google_genai import ChatGoogleGenerativeAI


DB_FAISS_PATH = 'vectorstores/db_faiss'

custom_prompt_template = """Use the following pieces of information to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}
Question: {question}

Only return the helpful answer below and nothing else.
Helpful answer:
"""

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)

source_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

def set_api_key():
    load_dotenv()
    api_key = os.getenv("OPEN_AI_KEY")
    os.environ["OPENAI_API_KEY"] = api_key

def create_prompt_template():
    return PromptTemplate(imput_variables=['context', 'question'], template=custom_prompt_template)

def load_db():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    return db

# def load_llm():
#     set_api_key()
#     llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
#     return llm

def load_llm():
    return ChatGoogleGenerativeAI(model='gemini-1.5-flash')

# def load_llm():
#     # Load the locally downloaded model here
#     llm = CTransformers(
#         model = "/home/frantisek/Documents/KMITL_IAAI/langchain/llama-2-7b-chat.ggmlv3.q8_0.bin",
#         model_type="llama",
#         max_new_tokens = 512,
#         temperature = 0.5
#     )
#     return llm

def format_docs(docs):
    for doc in docs:
        print(doc, end="\n\n")
    return "\n\n".join(doc.page_content for doc in docs)

def create_source_chain():
    llm = load_llm()
    db = load_db()
    retriever = db.as_retriever(search_kwargs={'k': 5})
    question_answer_chain = create_stuff_documents_chain(llm, source_prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    return rag_chain

def create_chain():
    db = load_db()  
    llm = load_llm()
    prompt = create_prompt_template()
    retriever = db.as_retriever(search_kwargs={'k': 5})
    rag_chain = ({"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain

@cl.on_chat_start
async def start():
    # chain = create_source_chain()
    chain = create_chain()
    msg = cl.Message(content="Starting the bot...")
    await msg.send()
    msg.content = "Hi, Welcome to Food safety Bot. What is your query?"
    await msg.update()
    cl.user_session.set("chain", chain)

@cl.on_message
async def on_message(message: cl.Message):
    chain = cl.user_session.get("chain")
    cb = cl.AsyncLangchainCallbackHandler(
        stream_final_answer=True, answer_prefix_tokens=["FINAL", "ANSWER"]
    )
    cb.answer_reached = True
    res = await chain.ainvoke(message.content, callbacks=[cb])
    # answer = res["answer"]
    # sources = "\n".join([str(doc) for doc in res["context"]])

    # if sources:
    #     answer += f"\nSources:" + str(sources)
    # else:
    #     answer += "\nNo sources found"

    await cl.Message(content=res).send()


