"""
Signal implementation for asynchronous event handling.

This module provides a type-safe Signal class that supports async callbacks
with proper locking to ensure thread safety in async contexts.
"""

from asyncio import Lock, create_task, gather
from types import CoroutineType
from typing import Callable

__all__ = ["Signal", "Callback"]


type Callback[*A] = Callable[[*A], CoroutineType]
"""
Type alias for async callback functions.

Generic type that represents an asynchronous callback function that accepts
a variable number of arguments and returns a coroutine.

Type Parameters:
    *A: Type variables representing the argument types of the callback.

Example:
    >>> Callback[str, int]  # Represents async def callback(s: str, n: int) -> Any
"""

class Signal[*A = *tuple[()]]:
    """
    Asynchronous signal for event-driven programming with type-safe callbacks.

    A Signal allows multiple async callbacks to be connected and executed
    concurrently when the signal is emitted. All operations are thread-safe
    using an async lock.

    Type Parameters:
        *A: Type variables representing the argument types for emit().

    Attributes:
        _lock (Lock): Async lock for thread-safe operations.
        _callbacks (list[Callback[*A]]): List of connected callbacks.

    Example:
        >>> signal = Signal[str, int]()
        >>>
        >>> async def on_event(name: str, value: int):
        ...     print(f"Event: {name}={value}")
        >>>
        >>> async def main():
        ...     await signal.connect(on_event)
        ...     await signal.emit("test", 42)  # Calls on_event("test", 42)
    """

    def __init__(self):
        """
        Initialize a new Signal instance.

        Creates an empty callback list and an async lock for thread safety.
        """
        self._lock = Lock()
        self._callbacks: list[Callback[*A]] = []

    async def emit(self, *args: *A) -> None:
        """
        Emit the signal with the given arguments.

        Executes all connected callbacks concurrently with the provided
        arguments. Callbacks are executed as asyncio tasks and gathered
        to ensure all complete before returning.

        Args:
            *args: Arguments to pass to each connected callback. Must match
                   the type parameters specified when creating the Signal.

        Raises:
            Exception: If any callback raises an exception, it will propagate.
                      Other callbacks will still complete unless they depend
                      on the failed one.

        Example:
            >>> await signal.emit("data", 100)
            >>> # All connected callbacks receive ("data", 100)
        """
        async with self._lock:
            tasks = (
                create_task(callback(*args))
                for callback in self._callbacks
            )
        await gather(*tasks)

    async def connect(self, callback: Callback[*A]) -> None:
        """
        Connect a callback to this signal.

        Adds the callback to the list of callbacks to be executed when the
        signal is emitted. If the callback is already connected, it will not
        be added again (prevents duplicate connections).

        Args:
            callback: Async callback function to connect. Must accept the
                     same argument types as the Signal's type parameters.

        Example:
            >>> await signal.connect(my_async_handler)
        """
        async with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    async def disconnect(self, callback: Callback[*A]) -> None:
        """
        Disconnect a callback from this signal.

        Removes the callback from the list of connected callbacks. If the
        callback is not connected, this method does nothing.

        Args:
            callback: Async callback function to disconnect.

        Example:
            >>> await signal.disconnect(my_async_handler)
        """
        async with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    async def disconnect_all(self) -> None:
        """
        Disconnect all callbacks from this signal.

        Removes all connected callbacks in one operation. Useful for cleanup
        or when you need to reset the signal's state.

        Example:
            >>> await signal.disconnect_all()
            >>> assert len(signal) == 0
        """
        async with self._lock:
            self._callbacks.clear()

    def __len__(self) -> int:
        """
        Return the number of connected callbacks.

        Returns:
            Number of callbacks currently connected to this signal.
        """
        return len(self._callbacks)

    def __bool__(self) -> bool:
        """
        Check if any callbacks are connected.

        Returns:
            True if at least one callback is connected, False otherwise.
        """
        return len(self._callbacks) > 0

    def __contains__(self, callback: Callback[*A]) -> bool:
        """
        Check if a specific callback is connected.

        Args:
            callback: Callback function to check for.

        Returns:
            True if the callback is connected, False otherwise.

        Example:
            >>> if my_handler in signal:
            ...     print("Handler is connected")
        """
        return callback in self._callbacks
