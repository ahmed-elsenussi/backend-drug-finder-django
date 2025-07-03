import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.text_splitter import CharacterTextSplitter
from supabase import create_client

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Check environment
if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(" Please set SUPABASE_URL and SUPABASE_KEY in your .env file.")

# Create Supabase client
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# File path (update this path as needed)
file_path = "C:/Users/ALL IN ONE/Desktop/Django_course/prject-information.pdf"

# Load document
if file_path.endswith(".txt"):
    loader = TextLoader(file_path, encoding="utf-8")
elif file_path.endswith(".pdf"):
    loader = PyMuPDFLoader(file_path)
else:
    raise ValueError(" Unsupported file format. Please use .txt or .pdf")

documents = loader.load()

# Split into chunks
splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_docs = splitter.split_documents(documents)

# Create or connect to Supabase vector store
vectorstore = SupabaseVectorStore(
    client=supabase_client,
    embedding=embedding_model,
    table_name="documents",       # Must match your Supabase table
    query_name="match_documents"  # Must match your Supabase RPC
)

# Upload to Supabase
vectorstore.add_documents(split_docs)

print(f"Successfully ingested {len(split_docs)} chunks to Supabase.")
