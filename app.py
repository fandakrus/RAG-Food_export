import os
from typing import Dict, Optional

import chainlit as cl
from src.chain import chain, write_conversation_to_file


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    username_stored = os.environ.get("CHAINTLIT_USERNAME")
    password_stored = os.environ.get("CHAINTLIT_PASSWORD")

    if username_stored is None or password_stored is None:
        raise ValueError(
            "Username or password not set. Please set CHAINTLIT_USERNAME and "
            "CHAINTLIT_PASSWORD environment variables."
        )

    if (username, password) == (username_stored, password_stored):
        return cl.User(
            identifier="pawel", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None
    
@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
    ) -> Optional[cl.User]:
    return default_user

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