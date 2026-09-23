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
import sqlite3, hashlib, os
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
        # AUDIT FIX: the writer identity was a mutable public attribute, so any
        # caller could reassign it and assume another bank's ownership. It is
        # now write-once (set here, then only readable).
        self._writer = writer
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
            self.db.execute("INSERT INTO banks(bank,owner) VALUES(?,?)", (bank, self._writer))
            self.db.commit()
        elif row[0] != self._writer:
            raise PermissionError(
                f"BANK_OWNED_BY_OTHER: bank {bank!r} is owned by {row[0]!r}, not {self._writer!r}")

    def append(self, bank: str, key: str, value: str, ts: int, source: str) -> Row:
        self.claim(bank)
        # AUDIT FIX: `source` was omitted from the digest, so a row differing
        # only in its provenance shared a digest and source tampering was
        # undetectable. The digest now covers every durable field, and it is the
        # FULL 64 hex chars (a 16-char truncation is weak collision resistance).
        digest = hashlib.sha256(
            f"{bank}\x00{key}\x00{value}\x00{ts}\x00{source}".encode()).hexdigest()
        cur = self.db.execute(
            "INSERT INTO rows(bank,key,value,ts,source,digest) VALUES(?,?,?,?,?,?)",
            (bank, key, value, ts, source, digest))
        self.db.commit()
        return Row(cur.lastrowid, bank, key, value, ts, source, digest)

    def rows(self, bank: str | None = None, verify: bool = True) -> list[Row]:
        """Read rows. `verify=True` RECOMPUTES each digest and raises on a
        mismatch.

        AUDIT FIX: the digest was write-only — rows() returned the stored value
        verbatim, so corruption or a manual DB edit passed silently and the
        integrity claim was unenforced. An explicit `bank=""` is now honoured
        (`if bank:` treated "" as "no filter" and returned every bank).
        """
        q = "SELECT id,bank,key,value,ts,source,digest FROM rows"
        args = ()
        if bank is not None:
            q += " WHERE bank=?"; args = (bank,)
        q += " ORDER BY id"
        out = [Row(*r) for r in self.db.execute(q, args)]
        if verify:
            for r in out:
                want = hashlib.sha256(
                    f"{r.bank}\x00{r.key}\x00{r.value}\x00{r.ts}\x00{r.source}"
                    .encode()).hexdigest()
                if want != r.digest:
                    raise ValueError(
                        f"MEMORY_ROW_TAMPERED: row {r.id} digest {r.digest[:16]}… "
                        f"but the content hashes to {want[:16]}…")
        return out

    def count(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM rows").fetchone()[0]

    def close(self) -> None:
        self.db.close()

    @property
    def writer(self) -> str:
        """Read-only: the owner identity is fixed at construction."""
        return self._writer

    def __enter__(self): return self
    def __exit__(self, *a): self.close()
