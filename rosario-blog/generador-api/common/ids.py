"""UUID versión 7: los primeros 48 bits son la hora en milisegundos, así que los IDs se ordenan
por fecha de creación (por eso sirven de cursor de paginación). Monótono dentro del mismo milisegundo."""
import os
import threading
import time
import uuid

_lock = threading.Lock()
_last_ms = 0
_seq = 0


def uuid7() -> str:
    global _last_ms, _seq
    with _lock:
        ms = time.time_ns() // 1_000_000
        if ms <= _last_ms:                 # mismo milisegundo (o reloj atrasado): se incrementa el contador
            ms = _last_ms
            _seq += 1
            if _seq > 0xFFF:
                ms += 1
                _seq = 0
        else:
            _seq = int.from_bytes(os.urandom(2), "big") & 0x7FF  # arranca bajo para dejar margen
        _last_ms = ms
        rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
        value = ((ms & 0xFFFFFFFFFFFF) << 80) | (0x7 << 76) | (_seq << 64) | (0b10 << 62) | rand_b
        return str(uuid.UUID(int=value))
