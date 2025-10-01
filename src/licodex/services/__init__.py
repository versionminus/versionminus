# Re-export primary service layer entry points for convenience.
from .user import (
    create_user,
    get_user_or_404,
    delete_user,
    update_user_email,
    list_users,
    UserNotFoundError,
    DuplicateEmailError,
)
from .thread import (
    create_thread,
    create_message as thread_create_message,  # deprecated alias; prefer services.message.create_message
    get_thread_or_404,
    get_message_or_404 as thread_get_message_or_404,
    get_thread_user,
    list_messages_per_thread,
    list_message_counts,
    ThreadNotFoundError,
    MessageNotFoundError as ThreadMessageNotFoundError,
)
from .message import (
    create_message,
    get_message_or_404,
    get_message_thread,
    MessageNotFoundError,
    ThreadNotFoundError as MessageThreadNotFoundError,
)

__all__ = [
    # user
    "create_user",
    "get_user_or_404",
    "delete_user",
    "update_user_email",
    "list_users",
    "UserNotFoundError",
    "DuplicateEmailError",
    # thread
    "create_thread",
    "thread_create_message",
    "get_thread_or_404",
    "thread_get_message_or_404",
    "get_thread_user",
    "list_messages_per_thread",
    "list_message_counts",
    "ThreadNotFoundError",
    "ThreadMessageNotFoundError",
    # message
    "create_message",
    "get_message_or_404",
    "get_message_thread",
    "MessageNotFoundError",
    "MessageThreadNotFoundError",
]
