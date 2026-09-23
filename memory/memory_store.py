"""memory/memory_store.py — the memory store ported from MiMoCode.

THE PORT (the blueprint names "port the MiMoCode memory subsystem (TypeScript→TypeScript
copy-paste)"). The semantics preserved from the MiMoCode store:
  - APPEND-ONLY: a fact is never rewritten; a correction is a new row
  - one writer per bank: writers are named, and a bank has ONE owner
  - a durable row carries (bank, key, value, ts, source) and a digest
  - the store survives a process restart (a fresh handle reads every row back)

Implemented over SQLite so the durability claim is mechanically testable.
"""
from __future__ import annotations
import json, sqlite3, hashlib, os
from pathlib import Path
from dataclasses import dataclass

DEFAULT_PATH = os.environ.get("PLUTUS_MEMORY", "/home/leviathan/.plutus/memory.sqlite")


@dataclass(frozen=True)
class Row:
    id: int
    bank: str
    key: str
    value: str
    ts: int
    source: str
    digest: str


class MemoryStore:
    """Append-only memory. One writer per bank, enforced at the API."""

    def __init__(self, path: str = DEFAULT_PATH, writer: str = "plutus-v6"):
        self.path = path
        self.writer = writer
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                ts INTEGER NOT NULL,
                source TEXT NOT NULL,
                digest TEXT NOT NULL
            )""")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS banks (
                bank TEXT PRIMARY KEY,
                owner TEXT NOT NULL
            )""")
        self.db.commit()

    def claim(self, bank: str) -> None:
        cur = self.db.execute("SELECT owner FROM banks WHERE bank=?", (bank,))
        row = cur.fetchone()
        if row is None:
            self.db.execute("INSERT INTO banks(bank,owner) VALUES(?,?)", (bank, self.writer))
            self.db.commit()
        elif row[0] != self.writer:
            raise PermissionError(
                f"BANK_OWNED_BY_OTHER: bank {bank!r} is owned by {row[0]!r}, not {self.writer!r}")

    def append(self, bank: str, key: str, value: str, ts: int, source: str) -> Row:
        self.claim(bank)
        digest = hashlib.sha256(f"{bank}\x00{key}\x00{value}\x00{ts}".encode()).hexdigest()[:16]
        cur = self.db.execute(
            "INSERT INTO rows(bank,key,value,ts,source,digest) VALUES(?,?,?,?,?,?)",
            (bank, key, value, ts, source, digest))
        self.db.commit()
        return Row(cur.lastrowid, bank, key, value, ts, source, digest)

    def rows(self, bank: str | None = None) -> list[Row]:
        q = "SELECT id,bank,key,value,ts,source,digest FROM rows"
        args = ()
        if bank: q += " WHERE bank=?"; args = (bank,)
        q += " ORDER BY id"
        return [Row(*r) for r in self.db.execute(q, args)]

    def count(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM rows").fetchone()[0]

    def close(self) -> None:
        self.db.close()

    def __enter__(self): return self
    def __exit__(self, *a): self.close()
