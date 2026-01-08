# Async Signals

A type-safe asynchronous signal/slot implementation for Python 3.13+ with modern type hints and zero dependencies.

## Features

- 🧬 Type-safe callbacks: Generic type parameters ensure callback arguments match signal emissions
- ⚡ Async-first: Built for modern async/await patterns with asyncio integration
- 🔒 Thread-safe: Uses asyncio locks for safe concurrent operations
- 🚀 Concurrent execution: Callbacks run concurrently using asyncio.gather()
- 🔄 Duplicate prevention: Prevents connecting the same callback multiple times
- 📏 Clean API: Simple, intuitive methods with clear semantics
- 🔍 Type hints: Full support for Python 3.13+ type system including *A type variables
- 📦 Zero dependencies: Pure Python, nothing else required

## Requirements

- Python 3.13 or higher
- No external dependencies

## License

MIT License - see LICENSE file for details.

## Installation

```bash
pip install asignals
```

Or install from source:

```bash
git clone https://github.com/xmarlon30x2/asignals.git
cd asignals
pip install -e .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a Pull Request

## Support

If you find a bug or have a feature request, please open an issue.

## Quick Start

```python
import asyncio
from asignals import Signal

# Create a signal with specific argument types
data_signal = Signal[str, int]()

# Define async callbacks
async def log_data(name: str, value: int):
    print(f"📊 Data received: {name} = {value}")

async def process_data(name: str, value: int):
    await asyncio.sleep(0.1)  # Simulate some work
    print(f"⚙️ Processing: {name.upper()}")

# Connect callbacks
async def main():
    await data_signal.connect(log_data)
    await data_signal.connect(process_data)
    
    # Emit signal (triggers all callbacks concurrently)
    await data_signal.emit("temperature", 25)
    
    # Check connections
    print(f"Connected callbacks: {len(data_signal)}")
    
    # Disconnect a callback
    await data_signal.disconnect(log_data)
    
    # Check if callback is still connected
    if log_data not in data_signal:
        print("Logger disconnected successfully")

asyncio.run(main())
```

## API Reference

Signal[*A]

Main signal class with generic type parameters for callback arguments.

### Methods:

async connect(callback: Callback[*A]) -> None

Connect an async callback to the signal.

- callback: Async function to call when signal is emitted
- Duplicate prevention: If the same callback is already connected, it won't be added again

async disconnect(callback: Callback[*A]) -> None

Disconnect a specific callback from the signal.

- callback: Async function to disconnect
- Safe: If callback isn't connected, does nothing

async disconnect_all() -> None

Disconnect all callbacks from the signal.

- Cleanup: Useful for resetting signal state or cleanup operations

async emit(*args: *A) -> None

Emit the signal with given arguments.

- args: Arguments passed to all connected callbacks
- Concurrent execution: All callbacks run concurrently via asyncio.gather()
- Exception propagation: If any callback raises an exception, it propagates

### Special Methods:

__len__() -> int

Returns the number of connected callbacks.

```python
count = len(signal)
```

__bool__() -> bool

Returns True if any callbacks are connected, False otherwise.

```python
if signal:
    print("Signal has callbacks")
```

__contains__(callback: Callback[*A]) -> bool

Checks if a specific callback is connected.

```python
if my_handler in signal:
    print("Handler is connected")
```

### Type Alias

Callback[*A]

Type alias for async callback functions: Callable[[*A], CoroutineType]

### Advanced Examples

Multiple Signal Types

```python
from asignals import Signal

# Signal with no arguments
click_signal = Signal()

# Signal with one argument
message_signal = Signal[str]()

# Signal with multiple arguments
data_signal = Signal[str, int, float]()

# Signal with complex types
user_signal = Signal[dict, list[str]]()
```

### Complete Workflow

```python
import asyncio
from asignals import Signal

class EventManager:
    def __init__(self):
        self.message_received = Signal[str, str]()  # (user, message)
        self.user_joined = Signal[str]()  # username
        self.user_left = Signal[str, str]()  # (username, reason)
        
        self._setup_handlers()
    
    async def _setup_handlers(self):
        await self.message_received.connect(self._log_message)
        await self.message_received.connect(self._notify_admins)
        await self.user_joined.connect(self._welcome_user)
    
    async def _log_message(self, user: str, message: str):
        print(f"[LOG] {user}: {message}")
    
    async def _notify_admins(self, user: str, message: str):
        if "urgent" in message.lower():
            print(f"[ADMIN] Urgent message from {user}")
    
    async def _welcome_user(self, username: str):
        print(f"Welcome, {username}!")
    
    async def broadcast_message(self, user: str, message: str):
        await self.message_received.emit(user, message)

async def main():
    manager = EventManager()
    
    # Simulate events
    await manager.broadcast_message("alice", "Hello everyone!")
    await manager.broadcast_message("bob", "URGENT: Server restart needed")
    
    # User joins
    await manager.user_joined.emit("charlie")
    
    # Check signal status
    print(f"Message signal has {len(manager.message_received)} callbacks")
    
    # Cleanup
    await manager.message_received.disconnect_all()
    print(f"After cleanup: {len(manager.message_received)} callbacks")

asyncio.run(main())
```

### Error Handling

```python
import asyncio
from asignals import Signal

async def safe_emit(signal: Signal, *args):
    """Safely emit a signal, catching exceptions from callbacks."""
    try:
        await signal.emit(*args)
    except Exception as e:
        print(f"Error in signal callbacks: {e}")
        # Optionally re-raise or handle differently

async def main():
    signal = Signal[str]()
    
    async def bad_callback(msg: str):
        raise ValueError(f"Failed to process: {msg}")
    
    async def good_callback(msg: str):
        print(f"Success: {msg}")
    
    await signal.connect(bad_callback)
    await signal.connect(good_callback)
    
    # This will raise ValueError
    try:
        await signal.emit("test")
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Or use safe wrapper
    await safe_emit(signal, "another test")

asyncio.run(main())
```

### Testing Signals

The package includes comprehensive tests. To run them:

```bash
# Run tests
python -m unittest -v -s ./tests -p test_*.py
```

### Best Practices

1. Type Hints

Always specify signal types for better type checking:

```python
# Good
signal = Signal[str, int]()

# Avoid
signal = Signal()  # Less type safety
```

2. Callback Design

Keep callbacks focused and independent:

```python
# Good - focused callback
async def save_to_database(data: str):
    await db.save(data)

# Avoid - doing too much
async def handle_data(data: str):
    await db.save(data)
    await notify_users(data)
    await log_activity(data)
    # Better to split into separate callbacks
```

3. Cleanup

Always disconnect callbacks when they're no longer needed:

```python
async def setup():
    signal = Signal[str]()
    await signal.connect(handler)
    
    try:
        # Use signal...
        await signal.emit("data")
    finally:
        await signal.disconnect(handler)  # Clean up
```

4. Exception Handling

Consider how to handle callback exceptions:

```python
# Option 1: Let exceptions propagate
try:
    await signal.emit(data)
except Exception as e:
    # Handle error from any callback
    handle_error(e)

# Option 2: Wrap each callback
async def safe_callback(*args):
    try:
        await original_callback(*args)
    except Exception as e:
        logger.error(f"Callback failed: {e}")
```

---

Async Signals - Simple, type-safe async event handling for Python 3.13+
