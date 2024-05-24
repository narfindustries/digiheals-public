import os
import json
import stat
import tempfile
from argparse import Namespace
from pyjfuzz.lib import PJFConfiguration, PJFFactory
import dataclasses
from typing import Optional, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class JsonFuzzEvent():
    input_path: Path
    output_path: Optional[Path] = None
    fuzzed: bool = False

    @property
    def filename(self) -> str:
        return self.input_path.name

    def fuzz(self, data):
        fuzzer = PJFFactory(PJFConfiguration(
            Namespace(json=json.loads(data), level=6, nologo=True)))
        fuzzed = fuzzer.fuzzed
        with open(self.output_path, "w") as out:
            out.write(fuzzed)
        self.fuzzed = True

    @property
    def output_name(self) -> str:
        if self.output_path:
            return self.output_path.name

    def __post_init__(self):
        file_fuzz_dir = JsonFuzzSession.OUTPUT_DIR
        if not file_fuzz_dir.exists():
            file_fuzz_dir.mkdir(parents=True)
        out = tempfile.NamedTemporaryFile(dir=file_fuzz_dir,
                                          prefix=self.filename + ".fuzz.",
                                          suffix=".json",
                                          delete=False, mode="w")
        self.output_path = Path(out.name)
        # tempfile creates with rw------- perms, make it world readable
        out.close()
        self.output_path.chmod(0o644)


class JsonFuzzSession():
    SESSIONS = {}
    OUTPUT_DIR = Path("/synthea/output/fuzzed")
    THREAD_POOL = ThreadPoolExecutor(max_workers=5)

    def __init__(self, filepath: str, seed=None, *args, **kwargs):
        self.filepath = Path(filepath)
        self.events = []
        if seed is not None:
            random.seed(seed)

    def fuzz(self, count=1) -> JsonFuzzEvent:
        logger.info("Fuzing %s times", count)
        if not hasattr(self, "_data"):
            with open(self.filepath, "r") as f:
                self._data = f.read()
        objs = [JsonFuzzEvent(self.filepath) for _ in range(count)]
        [self.THREAD_POOL.submit(o.fuzz, self._data) for o in objs]
        self.events += objs
        return objs

    @property
    def pending_fuzzes(self):
        pending = [o for o in self.events if not o.fuzzed]
        if not pending:
            self.events = []
        return len(pending)

    @classmethod
    def rm_session(cls, id):
        if id in cls.SESSIONS:
            del cls.SESSIONS[id]

    @classmethod
    def get_session(cls, id, *args, **kwargs):
        return cls.SESSIONS.setdefault(id, cls(*args, **kwargs))

    @classmethod
    def all_sessions(cls):
        return cls.SESSIONS.values()
