"""
Async Signals (asignals)

A type-safe asynchronous signal/slot implementation for Python.

This module provides a Signal class that allows for type-safe event handling
with async callbacks. Signals can be emitted asynchronously, and callbacks
are executed concurrently.

Example:
    >>> from asignals import Signal
    >>>
    >>> class MyComponent:
    ...     def __init__(self):
    ...         self.data_received = Signal[str, int]()
    ...
    ...     async def process_data(self, data: str, count: int):
    ...         # Emit signal to all connected callbacks
    ...         await self.data_received.emit(data, count)
    >>>
    >>> async def handler1(data: str, count: int):
    ...     print(f"Handler 1: {data} ({count})")
    >>>
    >>> async def handler2(data: str, count: int):
    ...     print(f"Handler 2: {data.upper()} ({count})")
    >>>
    >>> async def main():
    ...     component = MyComponent()
    ...     await component.data_received.connect(handler1)
    ...     await component.data_received.connect(handler2)
    ...     await component.process_data("hello", 5)
    ...
    >>> # Output:
    >>> # Handler 1: hello (5)
    >>> # Handler 2: HELLO (5)
"""

from .signal import Signal

__all__ = ["Signal"]
