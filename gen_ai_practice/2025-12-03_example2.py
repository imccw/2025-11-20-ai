import os
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=GEMINI_API_KEY
)

client = MongoClient(os.getenv("MONGODB_ATLAS_CLUSTER_URI"))

DB_NAME = "test_db"
COLLECTION_NAME = "test_collection"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "test-index-1"

MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

# To clear existing documents:
MONGODB_COLLECTION.delete_many({})

vector_store = MongoDBAtlasVectorSearch(
    collection=MONGODB_COLLECTION,
    embedding=embeddings,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine",
)

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=200,
    chunk_overlap=0
)

loader = TextLoader("media/facts.txt")
docs = loader.load_and_split(text_splitter=text_splitter)

vector_store.add_documents(docs)
print("Documents Added")

client.close()
