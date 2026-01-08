"""
Comprehensive test suite for the Signal class.

This module tests all functionality of the Signal class including
connection, emission, disconnection, and edge cases.
"""

import asyncio
from typing import List, Set, Tuple
from unittest.async_case import IsolatedAsyncioTestCase

from src.asignals import Signal


class TestSignal(IsolatedAsyncioTestCase):
    """Test basic Signal functionality."""

    async def test_emit_without_callbacks(self):
        """Signal emission with no callbacks should do nothing."""
        signal = Signal[str, int]()
        # This should not raise any errors
        await signal.emit("test", 42)
        self.assertEqual(len(signal), 0)
        self.assertFalse(signal)

    async def test_connect_and_emit(self):
        """Basic connection and emission should work."""
        signal = Signal[str]()
        calls: List[str] = []

        async def callback(data: str):
            calls.append(data)

        await signal.connect(callback)
        self.assertEqual(len(signal), 1)
        self.assertTrue(signal)

        await signal.emit("test_data")
        self.assertEqual(calls, ["test_data"])

    async def test_connect_multiple_callbacks(self):
        """Multiple callbacks should all be called on emit."""
        signal = Signal[int]()
        results: Set[int] = set()

        async def callback1(value: int):
            results.add(value * 2)

        async def callback2(value: int):
            results.add(value * 3)

        await signal.connect(callback1)
        await signal.connect(callback2)
        self.assertEqual(len(signal), 2)

        await signal.emit(5)
        self.assertEqual(results, {10, 15})

    async def test_connect_duplicate_callback(self):
        """Same callback should not be connected multiple times."""
        signal = Signal[str]()
        call_count = 0

        async def callback(data: str):
            nonlocal call_count
            call_count += 1

        # Connect twice
        await signal.connect(callback)
        await signal.connect(callback)

        self.assertEqual(len(signal), 1) # Should still be 1)

        await signal.emit("test")
        self.assertEqual(call_count, 1)  # Should be called only once

    async def test_disconnect(self):
        """Disconnecting a callback should remove it."""
        signal = Signal[str]()
        calls: List[str] = []

        async def callback1(data: str):
            calls.append(f"callback1: {data}")

        async def callback2(data: str):
            calls.append(f"callback2: {data}")

        await signal.connect(callback1)
        await signal.connect(callback2)
        self.assertEqual(len(signal), 2)

        await signal.disconnect(callback1)
        self.assertEqual(len(signal), 1)
        self.assertTrue(callback1 not in signal)
        self.assertTrue(callback2 in signal)

        await signal.emit("test")
        self.assertEqual(calls, ["callback2: test"])

    async def test_disconnect_nonexistent_callback(self):
        """Disconnecting a non-existent callback should do nothing."""
        signal = Signal[str]()

        async def callback1(data: str):
            pass

        async def callback2(data: str):
            pass

        await signal.connect(callback1)
        self.assertEqual(len(signal), 1)

        # Disconnect callback2 which was never connected
        await signal.disconnect(callback2)
        self.assertEqual(len(signal), 1) # Should still have callback1)
        self.assertTrue(callback1 in signal)

    async def test_disconnect_all(self):
        """disconnect_all should remove all callbacks."""
        signal = Signal[int]()
        calls: List[int] = []

        async def callback1(value: int):
            calls.append(value * 1)

        async def callback2(value: int):
            calls.append(value * 2)

        async def callback3(value: int):
            calls.append(value * 3)

        await signal.connect(callback1)
        await signal.connect(callback2)
        await signal.connect(callback3)
        self.assertEqual(len(signal), 3)
        self.assertTrue(signal)

        await signal.disconnect_all()
        self.assertEqual(len(signal), 0)
        self.assertFalse(signal)

        # Emit should not call any callbacks
        await signal.emit(10)
        self.assertEqual(len(calls), 0)

    async def test_disconnect_all_empty_signal(self):
        """disconnect_all on empty signal should do nothing."""
        signal = Signal[str]()
        self.assertEqual(len(signal), 0)

        await signal.disconnect_all()  # Should not raise
        self.assertEqual(len(signal), 0)

    async def test_emit_with_multiple_arguments(self):
        """Signal should handle multiple arguments correctly."""
        signal = Signal[str, int, float]()
        received_args: List[Tuple[str, int, float]] = []

        async def callback(s: str, i: int, f: float):
            received_args.append((s, i, f))

        await signal.connect(callback)
        await signal.emit("test", 42, 3.14)

        self.assertEqual(received_args, [("test", 42, 3.14)])

    async def test_emit_with_no_arguments(self):
        """Signal should work with no arguments."""
        signal = Signal()  # No type arguments
        call_count = 0

        async def callback():
            nonlocal call_count
            call_count += 1

        await signal.connect(callback)
        await signal.emit()  # No arguments

        self.assertEqual(call_count, 1)

    async def test_concurrent_connections(self):
        """Multiple connections in parallel should work correctly."""
        signal = Signal[int]()
        connection_count = 0

        async def make_callback(idx: int):
            async def callback(value: int):
                nonlocal connection_count
                connection_count += 1

            await signal.connect(callback)
            return callback

        # Create and connect 10 callbacks concurrently
        tasks = [make_callback(i) for i in range(10)]
        callbacks = await asyncio.gather(*tasks)

        self.assertEqual(len(signal), 10)

        # Emit and verify all were called
        await signal.emit(1)
        self.assertEqual(connection_count, 10)

        # Disconnect all concurrently
        disconnect_tasks = [signal.disconnect(cb) for cb in callbacks]
        await asyncio.gather(*disconnect_tasks)

        self.assertEqual(len(signal), 0)

    async def test_emit_exception_handling(self):
        """Exceptions in callbacks should propagate."""
        signal = Signal[str]()

        async def bad_callback(data: str):
            raise ValueError(f"Error processing: {data}")

        async def good_callback(data: str):
            return data.upper()

        await signal.connect(bad_callback)
        await signal.connect(good_callback)

        # Exception should propagate
        with self.assertRaises(ValueError, msg="Error processing: test"):
            await signal.emit("test")

    async def test_boolean_representation(self):
        """__bool__ should correctly indicate if callbacks are connected."""
        signal = Signal[str]()

        self.assertFalse(signal)  # Empty signal is falsy

        async def callback(data: str):
            pass

        await signal.connect(callback)
        self.assertTrue(signal)  # Non-empty signal is truthy

        await signal.disconnect(callback)
        self.assertFalse(signal)  # Back to falsy

    async def test_contains_operator(self):
        """in operator should check if callback is connected."""
        signal = Signal[int]()

        async def callback1(value: int):
            pass

        async def callback2(value: int):
            pass

        # Initially not connected
        self.assertTrue(callback1 not in signal)
        self.assertTrue(callback2 not in signal)

        # Connect callback1
        await signal.connect(callback1)
        self.assertTrue(callback1 in signal)
        self.assertTrue(callback2 not in signal)

        # Connect callback2
        await signal.connect(callback2)
        self.assertTrue(callback1 in signal)
        self.assertTrue(callback2 in signal)

        # Disconnect callback1
        await signal.disconnect(callback1)
        self.assertTrue(callback1 not in signal)
        self.assertTrue(callback2 in signal)

    async def test_len_operator(self):
        """len() should return correct number of callbacks."""
        signal = Signal[str]()
        callbacks = {}

        self.assertEqual(len(signal), 0)

        async def make_callback(idx: int):
            async def callback(data: str):
                pass
            value = callbacks.get(idx, callback)
            callbacks[idx] = value
            return value

        # Add 5 callbacks
        for i in range(5):
            callback = await make_callback(i)
            await signal.connect(callback)
            self.assertEqual(len(signal), i + 1)

        self.assertEqual(len(signal), 5)

        # Remove 2 callbacks
        for i in range(2):
            callback = await make_callback(i)
            await signal.disconnect(callback)
            self.assertEqual(len(signal), 5 - (i + 1))

        self.assertEqual(len(signal), 3)

    async def test_comprehensive_workflow(self):
        """Test a complete workflow with all operations."""
        signal = Signal[str, int]()
        events: List[str] = []

        async def logger(msg: str, count: int):
            events.append(f"log: {msg}-{count}")

        async def processor(msg: str, count: int):
            events.append(f"process: {msg.upper()}-{count}")

        async def counter(msg: str, count: int):
            events.append(f"count: {len(msg)}-{count}")

        # Phase 1: Connect all
        await signal.connect(logger)
        await signal.connect(processor)
        await signal.connect(counter)

        self.assertEqual(len(signal), 3)
        self.assertTrue(signal)
        self.assertTrue(logger in signal)
        self.assertTrue(processor in signal)
        self.assertTrue(counter in signal)

        # Phase 2: Emit
        await signal.emit("hello", 3)
        self.assertEqual(len(events), 3)
        self.assertIn("log: hello-3", events)
        self.assertIn("process: HELLO-3", events)
        self.assertIn("count: 5-3", events)

        # Phase 3: Disconnect one
        events.clear()
        await signal.disconnect(processor)
        self.assertEqual(len(signal), 2)
        self.assertTrue(processor not in signal)

        await signal.emit("world", 5)
        self.assertEqual(len(events), 2)
        self.assertIn("log: world-5", events)
        self.assertIn("count: 5-5", events)
        self.assertNotIn("process: WORLD-5", events) # Should not be called

        # Phase 4: Disconnect all
        events.clear()
        await signal.disconnect_all()
        self.assertEqual(len(signal), 0)
        self.assertFalse(signal)

        await signal.emit("test", 1)
        self.assertEqual(len(events), 0)  # No callbacks should be called
