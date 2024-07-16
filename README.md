# FOODSAFETY Bot
This app serves as food safety bot to give answer about specific questions conected to import of food from Thailand to USA. The main two parts is the model and small app to manage users.
## QA model
Simply RAG (retrieval-augmented generation) method is implemented. As a main framework is used Langchain wich take care of all data flowing through. As a knoledge database FAISS is used. To prepare it put your PDF files to ./data folder and run ./tools/ingest.py. Currently GEMINI is used as a main LLM to give human-like answers.   
Chainlit framework is used to handle all frontend and displaying as it is very easy. Literal AI works as store for conversations and also enables its presistance.
## User management
As this framework doesn't provide any user management, small Flask app was developed to server users to singup and also to admins to add new addresses and manage users. Navigate to routes folder routes to see what exactly is the app capable of. Frontend is written in simple HTML, CSS, JS style just to serve its purpouse.