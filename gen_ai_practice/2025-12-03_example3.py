import os
from dotenv import load_dotenv

from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")

# LLM + Embeddings
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=GEMINI_API_KEY
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=GEMINI_API_KEY
)

# MongoDB Connection
client = MongoClient(MONGODB_URI)

DB_NAME = "test_db"
COLLECTION_NAME = "test_collection"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "test-index-1"

MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

# Vector store
vector_store = MongoDBAtlasVectorSearch(
    collection=MONGODB_COLLECTION,
    embedding=embeddings,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine",
)

retriever = vector_store.as_retriever()

# ==============================
# SYSTEM PROMPT (IMPORTANT PART)
# ==============================
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, say that you don't know."
    "\n\n"
    "{context}"
)


# Prompt setup
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

# Chains
document_chain = create_stuff_documents_chain(llm, prompt)
chain = create_retrieval_chain(retriever, document_chain)

# Invoke
ai_response = chain.invoke({"input": "list down 3 facts about the english word."})
print(ai_response["answer"])

client.close()
