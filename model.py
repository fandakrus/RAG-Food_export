import os
from dotenv import load_dotenv
from typing import List, Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    format_document,
)
from langchain_core.prompts.prompt import PromptTemplate    
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

import chainlit as cl

DB_FAISS_PATH = 'vectorstores/db_faiss'

def load_keys():
    """"
    Load the API keys from the .env file 
    GOOGLE - for gemini access
    HUGGING_FACE - for huggingface access to embeddings but I don't think it's necessary here
    """
    load_dotenv()
    gemini_key = os.getenv("GOOGLE_API_KEY")
    hf_token = os.getenv("HUGGING_FACE_TOKEN")
    os.environ['GOOGLE_API_KEY'] = gemini_key
    os.environ['HF_TOKEN'] = hf_token

def load_db():
    """
    Load the FAISS database from the local file
    """
    embeddings = HuggingFaceEmbeddings(model_name="Alibaba-NLP/gte-large-en-v1.5",
                                       model_kwargs={'device': 'cpu', 'trust_remote_code': True})
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    return db

load_keys()
# preparation of model and retriever I hope chain lint run this at server start and the Fiass is loaded once
llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash')
retriever = load_db().as_retriever()

def write_conversation_to_file(conversation):
    # export the conversation to a text file based named based on the first question
    if not conversation:
        return

    # Extract the first question to use as the filename
    filename = "conversations/" + conversation[0][0].replace(" ", "_") + ".txt"

    with open(filename, 'w') as file:
        for human_message, chatbot_message in conversation:
            file.write(f"HUMAN: {human_message}\n")
            file.write(f"CHATBOT: {chatbot_message}\n\n")

# ----------------------------------------------------------------------------------------------------------------------
# Prompts needed in furter code

# Condense a chat history and follow-up question into a standalone question
_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""  # noqa: E501
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

# RAG answer synthesis prompt - this one is the most important - change for prompt engineering
template = """You are an expert in food safety for importing food from Thailand to the United States.
            Answer the following question based on the context provided:
<context>
{context}
</context>
if you don't know the answer give as much relative information as possible and say you don't know."""
ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{question}"),
    ]
)

# Conversational Retrieval Chain
DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")

# ----------------------------------------------------------------------------------------------------------------------

def _combine_documents(
    docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)

# Just helper function to display retrieved documents from chain to terminal
def _display_documents(docs):
    print(docs)
    return docs

def _format_chat_history(chat_history: List[Tuple[str, str]]) -> List:
    buffer = []
    for human, ai in chat_history:
        buffer.append(HumanMessage(content=human))
        buffer.append(AIMessage(content=ai))
    return buffer

# this is actual switch where if first part of brackets is evaluated to True then the thing after the comma is executed
_search_query = RunnableBranch(
    # If input includes chat_history, we condense it with the follow-up question
    (
        RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
            run_name="HasChatHistoryCheck"
        ),  # Condense follow-up question and chat into a standalone_question
        RunnablePassthrough.assign(
            chat_history=lambda x: _format_chat_history(x["chat_history"])
        )
        | CONDENSE_QUESTION_PROMPT
        | llm
        | StrOutputParser(),
    ),
    # Else, we have no chat history, so just pass through the question
    RunnableLambda(lambda x: x["question"]),
)

# this takes a dictionary and provides it to each part seperatly
_inputs = RunnableParallel(
    {
        "question": lambda x: x["question"],
        "chat_history": lambda x: _format_chat_history(x["chat_history"]),
        "context": _search_query | retriever | _combine_documents | _display_documents,
    }
)

# this is the main chain that is executed
chain = _inputs | ANSWER_PROMPT | llm | StrOutputParser()

# set stuff on the beginning of the chat
@cl.on_chat_start
async def start():
    # chain = create_source_chain()
    msg = cl.Message(content="Starting the bot...")
    history = []
    await msg.send()
    msg.content = "Hi, Welcome to Food safety Bot. What is your query?"
    await msg.update()
    cl.user_session.set("history", history)
    cl.user_session.set("chain", chain)

# this is executed when the message is received
@cl.on_message
async def on_message(message: cl.Message):
    chain = cl.user_session.get("chain")
    history = cl.user_session.get("history")
    cb = cl.AsyncLangchainCallbackHandler(
        stream_final_answer=True, answer_prefix_tokens=["FINAL", "ANSWER"]
    )
    cb.answer_reached = True
    res = chain.invoke({"question": message.content, "chat_history": history})
    history.append((message.content, res))
    await cl.Message(content=res).send()

@cl.on_chat_end 
async def end():
    write_conversation_to_file(cl.user_session.get("history"))
    await cl.Message(content="Goodbye").send()