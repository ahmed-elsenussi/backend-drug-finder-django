import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.text_splitter import CharacterTextSplitter
from supabase import create_client

# 1. تحميل متغيرات البيئة
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 2. إعداد Supabase Client
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. إعداد Embedding Model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 4. تحديد اسم الملف الذي تريد تحميله
file_path = "C:/Users/ALL IN ONE/Desktop/Django_course/The-Top-25-Prescribed-Drugs-Submit.pdf"  # ← غيّريه حسب نوع الملف (pdf أو txt)

# 5. تحميل المستند المناسب بناءً على الامتداد
if file_path.endswith(".txt"):
    loader = TextLoader(file_path, encoding="utf-8")
elif file_path.endswith(".pdf"):
    loader = PyMuPDFLoader(file_path)
else:
    raise ValueError("❌ نوع الملف غير مدعوم. استخدمي .txt أو .pdf فقط")

documents = loader.load()

# 6. تقسيم المستند إلى أجزاء صغيرة
splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_docs = splitter.split_documents(documents)

# 7. إعداد VectorStore
vectorstore = SupabaseVectorStore(
    client=supabase_client,
    embedding=embedding_model,
    table_name="documents",      # تأكدي إنك أنشأتي الجدول بنفس الاسم
    query_name="match_documents" # ده اسم query function في Supabase
)

# 8. رفع المستندات إلى Supabase
vectorstore.add_documents(split_docs)

print("✅ تم رفع المستند إلى Supabase بنجاح.")
