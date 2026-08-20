from supabase import create_client, Client
from app.core.config import settings


def get_supabase() -> Client:
    """Admin client — uses service role key (server-side only)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_anon() -> Client:
    """Public anon client — for verifying user JWTs."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
