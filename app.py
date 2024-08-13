import os
from typing import Dict, Optional
import sqlite3
import bcrypt

import chainlit as cl
from src.chain import chain, write_conversation_to_file

DATABASE_PATH = 'instance/users.db'

@cl.password_auth_callback
def auth_callback(email: str, password: str):
    """
    Authenticates the user based on the provided email and password.

    Args:
        email (str): The email to authenticate.
        password (str): The password to authenticate.

    Returns:
        cl.User or None: If the authentication is successful, returns a `cl.User` object
        with the user's identifier, role, and provider. Otherwise, returns None.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT email, password, role, email_verified FROM user WHERE email = ?", (email.lower(),))
        user = cursor.fetchone()

        if user is None:
            return None

        stored_email, stored_password_hash, role, email_verified = user

        if not email_verified:
            return None

        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            return cl.User(
                identifier=stored_email, metadata={"role": role, "provider": "credentials"}
            )
        else:
            return None
    except Exception as e:
        print(f"Error during authentication: {e}")
        return None
    finally:
        conn.close()

            
@cl.on_chat_start
async def start():
    """
    Starts the bot and initializes the necessary variables.
    History is for storing content of the conversation.
    Chain is in this code presistently set for each usersession.
    """
    msg = cl.Message(content="Starting the bot...")
    history = []
    await msg.send()
    msg.content = """Hi there! Welcome to the Food Safety Bot. Feel free to ask your questions—try to be as specific as you can. Please keep in mind that the information provided may not always be 100% accurate. For the best results, ask your questions in English."""
    await msg.update()
    cl.user_session.set("history", history)
    cl.user_session.set("chain", chain)

@cl.on_chat_resume
async def on_chat_resume(thread):
    """
    Resumes the chat conversation and updates the chat history and chain.

    Args:
        thread (dict): The chat thread containing the conversation steps.

    Returns:
        None
    """
    history = []
    root_messages = [m for m in thread["steps"] if m["parentId"] == None]
    for message in root_messages:
        if message["type"] == "user_message":
            history.append((message["output"], None))
        elif len(history) > 0:
            history[-1] = (history[-1][0], message["output"])
        else:
            pass
    cl.user_session.set("history", history)
    cl.user_session.set("chain", chain)


@cl.on_message
async def on_message(message: cl.Message):
    """
    Process incoming messages and generate a response.

    Args:
        message (cl.Message): The incoming message object.

    Returns:
        None
    """
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
    """
    Ends the chat conversation and writes the conversation history to a file.
    Not necessary needed as the history of conversation is available at Literal AI.
    """
    write_conversation_to_file(cl.user_session.get("history"))