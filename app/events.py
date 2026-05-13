from typing import Callable, Any

EventPayload = dict[str, Any]
EventHandler = Callable[[str, EventPayload], None]

