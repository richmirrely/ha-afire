"""Asynchronous local Gizwits GAgent client for AFIRE fireplaces."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable

from .const import (
    COLOR_KEYS,
    DEFAULT_PORT,
    EFFECT_TO_FLAG,
    FLAG_COLORS,
    FLAG_EFFECTS,
    FLAG_FLAME,
    FLAG_ORANGE_LIGHT,
    FLAG_POWER,
    FLAG_RGB_POWER,
    FLAG_SPEED,
)
from .protocol import (
    MAGIC,
    AfireState,
    ProtocolError,
    build_control_body,
    build_frame,
    decode_state,
)

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5
RESPONSE_TIMEOUT = 4
KEEPALIVE_INTERVAL = 5


class AfireError(Exception):
    """Base error for AFIRE communication."""


class AfireConnectionError(AfireError):
    """Raised when the fireplace cannot be reached."""


class AfireAuthenticationError(AfireError):
    """Raised when the local passcode is rejected."""


StateListener = Callable[[AfireState], None]


class AfireClient:
    """Maintain a local TCP connection to an AFIRE fireplace."""

    def __init__(self, host: str, passcode: str, port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        self.passcode = passcode

        self.state: AfireState | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._keepalive_task: asyncio.Task[None] | None = None
        self._connect_lock = asyncio.Lock()
        self._send_lock = asyncio.Lock()
        self._control_lock = asyncio.Lock()
        self._sequence = 0
        self._ack_waiters: dict[int, asyncio.Future[None]] = {}
        self._state_waiters: set[asyncio.Future[AfireState]] = set()
        self._listeners: set[StateListener] = set()

    @property
    def connected(self) -> bool:
        """Return whether the TCP reader is running."""
        return bool(
            self._writer
            and not self._writer.is_closing()
            and self._reader_task
            and not self._reader_task.done()
        )

    def add_state_listener(self, listener: StateListener) -> Callable[[], None]:
        """Register a state callback and return its unsubscribe function."""
        self._listeners.add(listener)

        def remove() -> None:
            self._listeners.discard(listener)

        return remove

    async def async_connect(self) -> None:
        """Connect and authenticate using the local GAgent passcode."""
        async with self._connect_lock:
            if self.connected:
                return
            # A previous reader may have stopped while its keepalive task is
            # still sleeping. Cancel both before installing a new transport.
            await self.async_disconnect()

            try:
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=CONNECT_TIMEOUT,
                )
                passcode = self.passcode.encode("ascii")
                login_body = len(passcode).to_bytes(2, "big") + passcode
                self._writer.write(build_frame(0x08, login_body))
                await self._writer.drain()
                command, body = await asyncio.wait_for(
                    self._async_read_frame(), timeout=RESPONSE_TIMEOUT
                )
            except (
                OSError,
                TimeoutError,
                UnicodeEncodeError,
                asyncio.IncompleteReadError,
            ) as err:
                await self.async_disconnect()
                raise AfireConnectionError(
                    f"Unable to connect to {self.host}:{self.port}"
                ) from err

            if command != 0x09 or not body or body[-1] != 0:
                await self.async_disconnect()
                raise AfireAuthenticationError("The fireplace rejected the passcode")

            self._reader_task = asyncio.create_task(
                self._async_reader_loop(), name=f"afire-reader-{self.host}"
            )
            self._keepalive_task = asyncio.create_task(
                self._async_keepalive_loop(), name=f"afire-keepalive-{self.host}"
            )

    async def async_disconnect(self) -> None:
        """Disconnect and stop background tasks."""
        tasks = (self._keepalive_task, self._reader_task)
        self._keepalive_task = None
        self._reader_task = None
        for task in tasks:
            if task and task is not asyncio.current_task():
                task.cancel()
        for task in tasks:
            if task and task is not asyncio.current_task():
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        await self._async_close_transport()

    async def async_request_state(self) -> AfireState:
        """Request and return the latest fireplace state."""
        await self.async_connect()
        loop = asyncio.get_running_loop()
        waiter: asyncio.Future[AfireState] = loop.create_future()
        self._state_waiters.add(waiter)
        try:
            await self._async_send(build_frame(0x90, b"\x02"))
            return await asyncio.wait_for(waiter, timeout=RESPONSE_TIMEOUT)
        except TimeoutError as err:
            raise AfireConnectionError("Timed out waiting for fireplace state") from err
        finally:
            self._state_waiters.discard(waiter)

    async def async_set_power(self, enabled: bool) -> None:
        """Set fireplace power."""
        await self._async_change_bits(FLAG_POWER, FLAG_POWER if enabled else 0)

    async def async_set_orange_light(self, enabled: bool) -> None:
        """Set the orange decorative light."""
        await self._async_change_bits(
            FLAG_ORANGE_LIGHT, FLAG_ORANGE_LIGHT if enabled else 0
        )

    async def async_set_rgb_power(self, enabled: bool) -> None:
        """Enable RGB light, or disable it and all animated effects."""
        if enabled:
            await self._async_change_bits(FLAG_RGB_POWER, FLAG_RGB_POWER)
        else:
            await self._async_change_bits(FLAG_RGB_POWER | FLAG_EFFECTS, 0)

    async def async_set_color(self, color_key: str) -> None:
        """Select one of the 15 mutually exclusive static colours."""
        try:
            selected_flag = 1 << (3 + COLOR_KEYS.index(color_key))
        except ValueError as err:
            raise ValueError(f"Unknown AFIRE colour: {color_key}") from err
        await self._async_change_bits(FLAG_COLORS, selected_flag)

    async def async_set_effect(self, effect: str | None) -> None:
        """Select Smooth/Fade effect, or clear every effect."""
        selected_flag = 0 if effect is None else EFFECT_TO_FLAG[effect]
        await self._async_change_bits(FLAG_EFFECTS, selected_flag)

    async def async_set_flame(self, value: int) -> None:
        """Set flame level from 1 to 8."""
        await self._async_control(flags=FLAG_FLAME, flame=value)

    async def async_set_speed(self, value: int) -> None:
        """Set flame speed from 1 to 8."""
        await self._async_control(flags=FLAG_SPEED, speed=value)

    async def _async_change_bits(self, mask: int, selected: int) -> None:
        state = await self._async_get_state()
        bits = (state.bits & ~mask) | selected
        await self._async_control(flags=mask, bits=bits)

    async def _async_get_state(self) -> AfireState:
        if self.state is None:
            return await self.async_request_state()
        return self.state

    async def _async_control(
        self,
        *,
        flags: int,
        bits: int | None = None,
        flame: int | None = None,
        speed: int | None = None,
    ) -> None:
        # The fireplace firmware reliably applies one numeric datapoint per
        # control frame, so flame and speed are intentionally separate calls.
        async with self._control_lock:
            await self.async_connect()
            state = await self._async_get_state()
            values_bits = state.bits if bits is None else bits
            values_flame = state.flame if flame is None else flame
            values_speed = state.speed if speed is None else speed

            self._sequence = (self._sequence + 1) & 0xFFFFFFFF
            if self._sequence == 0:
                self._sequence = 1
            sequence = self._sequence
            body = build_control_body(
                sequence, flags, values_bits, values_flame, values_speed
            )

            loop = asyncio.get_running_loop()
            waiter: asyncio.Future[None] = loop.create_future()
            self._ack_waiters[sequence] = waiter
            try:
                await self._async_send(build_frame(0x93, body))
                await asyncio.wait_for(waiter, timeout=RESPONSE_TIMEOUT)
            except TimeoutError as err:
                raise AfireConnectionError("Timed out waiting for control ACK") from err
            finally:
                self._ack_waiters.pop(sequence, None)

    async def _async_send(self, frame: bytes) -> None:
        async with self._send_lock:
            if not self._writer or self._writer.is_closing():
                raise AfireConnectionError("Fireplace is not connected")
            try:
                self._writer.write(frame)
                await self._writer.drain()
            except OSError as err:
                raise AfireConnectionError("Failed to send data to fireplace") from err

    async def _async_reader_loop(self) -> None:
        try:
            while True:
                command, body = await self._async_read_frame()
                if command == 0x91 and len(body) >= 6 and body[0] in (0x03, 0x04):
                    state = decode_state(body[1:6])
                    self.state = state
                    for waiter in tuple(self._state_waiters):
                        if not waiter.done():
                            waiter.set_result(state)
                    for listener in tuple(self._listeners):
                        try:
                            listener(state)
                        except Exception:  # pragma: no cover - defensive callback guard
                            _LOGGER.exception("AFIRE state listener failed")
                elif command == 0x94 and len(body) >= 4:
                    sequence = int.from_bytes(body[:4], "big")
                    waiter = self._ack_waiters.get(sequence)
                    if waiter and not waiter.done():
                        waiter.set_result(None)
        except asyncio.CancelledError:
            raise
        except (OSError, asyncio.IncompleteReadError, ProtocolError) as err:
            _LOGGER.debug("AFIRE connection closed: %s", err)
        finally:
            error = AfireConnectionError("Fireplace connection was closed")
            for waiter in tuple(self._ack_waiters.values()):
                if not waiter.done():
                    waiter.set_exception(error)
            for waiter in tuple(self._state_waiters):
                if not waiter.done():
                    waiter.set_exception(error)
            await self._async_close_transport()

    async def _async_keepalive_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(KEEPALIVE_INTERVAL)
                await self._async_send(build_frame(0x15))
        except asyncio.CancelledError:
            raise
        except AfireError:
            return

    async def _async_read_frame(self) -> tuple[int, bytes]:
        if self._reader is None:
            raise AfireConnectionError("Fireplace is not connected")
        magic = await self._reader.readexactly(4)
        if magic != MAGIC:
            raise ProtocolError(f"invalid GAgent magic: {magic.hex()}")

        length = 0
        shift = 0
        for _ in range(4):
            byte = (await self._reader.readexactly(1))[0]
            length |= (byte & 0x7F) << shift
            if not byte & 0x80:
                break
            shift += 7
        else:
            raise ProtocolError("invalid GAgent frame length")

        payload = await self._reader.readexactly(length)
        if len(payload) < 3:
            raise ProtocolError("GAgent payload is too short")
        command = int.from_bytes(payload[1:3], "big")
        return command, payload[3:]

    async def _async_close_transport(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None
        if writer:
            writer.close()
            with contextlib.suppress(OSError, TimeoutError):
                await asyncio.wait_for(writer.wait_closed(), timeout=1)
