# app/services/__init__.py
from .auth import authenticate_user, get_user_by_email
from .user_service import create_user, get_users, get_user_by_id, update_user, delete_user, get_commercials
from .client_service import create_client, get_clients, get_client_by_id, update_client, delete_client, get_commercial_clients
from .call_service import create_call, get_calls, get_call_by_id, update_call, get_commercial_calls, get_calls_stats
from .file_upload import save_recording_file, get_recording_by_id, delete_recording_file

__all__ = [
    "authenticate_user", "get_user_by_email",
    "create_user", "get_users", "get_user_by_id", "update_user", "delete_user", "get_commercials",
    "create_client", "get_clients", "get_client_by_id", "update_client", "delete_client", "get_commercial_clients",
    "create_call", "get_calls", "get_call_by_id", "update_call", "get_commercial_calls", "get_calls_stats",
    "save_recording_file", "get_recording_by_id", "delete_recording_file"
]