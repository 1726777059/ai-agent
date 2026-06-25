import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
# Claude 批改时用 service_role key（不暴露给前端）
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
