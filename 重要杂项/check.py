from __future__ import annotations

import argparse
import importlib.abc
import importlib.util
import json
import os
import re
import runpy
import subprocess
import sys
import traceback
import types
from pathlib import Path
from typing import Iterable


# ============================================================
# Configuration
# ============================================================

CHILD_EXIT_MISSING = 73
ENV_CHILD = "RMC_CHILD"
ENV_STUBS = "RMC_STUBS"


# ============================================================
# Universal stub objects
# ============================================================

class StubMeta(type):
    """Metaclass used by generated fake classes."""

    def __getattr__(cls, name: str):
        return StubValue(f"{cls.__name__}.{name}")

    def __call__(cls, *args, **kwargs):
        return StubValue(f"{cls.__name__}()")

    def __getitem__(cls, item):
        return StubValue(f"{cls.__name__}[{item!r}]")

    def __bool__(cls):
        return False

    def __iter__(cls):
        return iter(())

    def __len__(cls):
        return 0

    def __add__(cls, other):
        return StubValue()

    def __radd__(cls, other):
        return StubValue()

    def __sub__(cls, other):
        return StubValue()

    def __rsub__(cls, other):
        return StubValue()

    def __mul__(cls, other):
        return StubValue()

    def __rmul__(cls, other):
        return StubValue()

    def __truediv__(cls, other):
        return StubValue()

    def __rtruediv__(cls, other):
        return StubValue()

    def __eq__(cls, other):
        return False

    def __ne__(cls, other):
        return True


class StubBase(metaclass=StubMeta):
    """Base class used when a missing module attribute is subclassed."""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name: str):
        return StubValue(f"{type(self).__name__}.{name}")

    def __call__(self, *args, **kwargs):
        return StubValue()

    def __getitem__(self, item):
        return StubValue()

    def __setitem__(self, key, value):
        pass

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def __bool__(self):
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return False

    def __await__(self):
        async def _empty():
            return StubValue()

        return _empty().__await__()

    def __mro_entries__(self, bases):
        return (StubBase,)

    def __add__(self, other):
        return StubValue()

    def __radd__(self, other):
        return StubValue()

    def __sub__(self, other):
        return StubValue()

    def __rsub__(self, other):
        return StubValue()

    def __mul__(self, other):
        return StubValue()

    def __rmul__(self, other):
        return StubValue()

    def __truediv__(self, other):
        return StubValue()

    def __rtruediv__(self, other):
        return StubValue()

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True


class StubValue:
    """
    A permissive fake value.

    This object exists only to allow the target program to continue
    far enough to expose additional missing imports.
    """

    def __init__(self, name: str = "stub"):
        self._stub_name = name

    def __repr__(self):
        return f"<StubValue {self._stub_name}>"

    def __str__(self):
        return ""

    def __getattr__(self, name: str):
        return StubValue(f"{self._stub_name}.{name}")

    def __call__(self, *args, **kwargs):
        return StubValue(f"{self._stub_name}()")

    def __getitem__(self, item):
        return StubValue(f"{self._stub_name}[{item!r}]")

    def __setitem__(self, key, value):
        pass

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def __bool__(self):
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return False

    def __await__(self):
        async def _empty():
            return self

        return _empty().__await__()

    def __mro_entries__(self, bases):
        return (StubBase,)

    def __add__(self, other):
        return StubValue()

    def __radd__(self, other):
        return StubValue()

    def __sub__(self, other):
        return StubValue()

    def __rsub__(self, other):
        return StubValue()

    def __mul__(self, other):
        return StubValue()

    def __rmul__(self, other):
        return StubValue()

    def __truediv__(self, other):
        return StubValue()

    def __rtruediv__(self, other):
        return StubValue()

    def __mod__(self, other):
        return StubValue()

    def __rmod__(self, other):
        return StubValue()

    def __lt__(self, other):
        return False

    def __le__(self, other):
        return False

    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return False

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True

    def __hash__(self):
        return id(self)


def make_stub_class(name: str):
    """
    Produce a fake class for names that look like classes.
    """
    safe_name = re.sub(r"\W+", "_", name.split(".")[-1])
    if not safe_name or safe_name[0].isdigit():
        safe_name = "StubType"

    return StubMeta(
        safe_name,
        (StubBase,),
        {
            "__module__": "__main__",
        },
    )


# ============================================================
# Fake module
# ============================================================

class StubModule(types.ModuleType):
    """
    Fake module used only for dependency probing.
    """

    def __init__(self, name: str):
        super().__init__(name)

        self.__package__ = name
        self.__path__ = []
        self.__all__ = []

    def __repr__(self):
        return f"<StubModule {self.__name__}>"

    def __getattr__(self, name: str):
        # Heuristic:
        # Uppercase names often represent classes/constants.
        # Class-like names become fake classes so:
        #
        #     class X(missing.PluginBase):
        #
        # can continue.
        if name and name[0].isupper():
            return make_stub_class(f"{self.__name__}.{name}")

        return StubValue(f"{self.__name__}.{name}")

    def __call__(self, *args, **kwargs):
        return StubValue(f"{self.__name__}()")

    def __getitem__(self, item):
        return StubValue(f"{self.__name__}[{item!r}]")

    def __setitem__(self, key, value):
        pass

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def __bool__(self):
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return False

    def __mro_entries__(self, bases):
        return (StubBase,)

    def __await__(self):
        async def _empty():
            return self

        return _empty().__await__()

    def __add__(self, other):
        return StubValue()

    def __radd__(self, other):
        return StubValue()

    def __sub__(self, other):
        return StubValue()

    def __rsub__(self, other):
        return StubValue()

    def __mul__(self, other):
        return StubValue()

    def __rmul__(self, other):
        return StubValue()

    def __truediv__(self, other):
        return StubValue()

    def __rtruediv__(self, other):
        return StubValue()

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True


# ============================================================
# Import hook
# ============================================================

class StubLoader(importlib.abc.Loader):

    def __init__(self, fullname: str):
        self.fullname = fullname

    def create_module(self, spec):
        return StubModule(spec.name)

    def exec_module(self, module):
        pass


class StubFinder(importlib.abc.MetaPathFinder):
    """
    Only intercepts modules that the parent process has already
    identified as missing.

    Important:
        A missing "requests.foo" never causes "requests"
        to be replaced.
    """

    def __init__(self, missing: Iterable[str]):
        self.missing = set(missing)

    def is_stubbed(self, fullname: str) -> bool:
        for name in self.missing:
            if fullname == name:
                return True

            # If the missing module itself is a package-like stub,
            # permit its descendants to exist as stubs too.
            if fullname.startswith(name + "."):
                return True

        return False

    def find_spec(self, fullname, path=None, target=None):

        if not self.is_stubbed(fullname):
            return None

        return importlib.util.spec_from_loader(
            fullname,
            StubLoader(fullname),
            is_package=True,
        )


# ============================================================
# Child process
# ============================================================

def extract_missing_module(exc: ModuleNotFoundError) -> str | None:
    """
    Prefer ModuleNotFoundError.name because it identifies the
    actual module that importlib failed to locate.
    """

    name = getattr(exc, "name", None)

    if isinstance(name, str) and name:
        return name

    match = re.search(
        r"No module named ['\"]([^'\"]+)['\"]",
        str(exc),
    )

    if match:
        return match.group(1)

    return None


def child_main(target: Path, target_args: list[str]) -> int:

    raw_stubs = os.environ.get(ENV_STUBS, "[]")

    try:
        missing = set(json.loads(raw_stubs))
    except (json.JSONDecodeError, TypeError):
        print(
            "[RMC] Invalid stub list.",
            file=sys.stderr,
        )
        return 2

    # Install the finder only inside the isolated child.
    sys.meta_path.insert(0, StubFinder(missing))

    # Make target argv look like normal execution.
    sys.argv = [str(target), *target_args]

    try:
        runpy.run_path(
            str(target),
            run_name="__main__",
        )

    except ModuleNotFoundError as exc:

        module = extract_missing_module(exc)

        if module is None:
            traceback.print_exc()
            return 1

        print(
            f"RMC_MISSING:{module}",
            file=sys.stderr,
            flush=True,
        )

        traceback.print_exc()
        return CHILD_EXIT_MISSING

    except BaseException:
        # Do not turn unrelated application errors into fake
        # dependency errors.
        traceback.print_exc()
        return 1

    return 0


# ============================================================
# Parent process
# ============================================================

def parse_target_args(values: list[str]) -> tuple[str, list[str]]:
    if "--" in values:
        index = values.index("--")
        return values[0], values[index + 1:]

    return values[0], values[1:]


def run_child(
    checker: Path,
    target: Path,
    stubs: set[str],
    target_args: list[str],
    timeout: float | None,
) -> subprocess.CompletedProcess:

    env = os.environ.copy()

    env[ENV_CHILD] = "1"
    env[ENV_STUBS] = json.dumps(
        sorted(stubs),
        ensure_ascii=False,
    )

    command = [
        sys.executable,
        str(checker),
        "--child",
        str(target),
        "--",
        *target_args,
    ]

    return subprocess.run(
        command,
        cwd=target.parent,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )


def extract_sentinel(stderr: str) -> str | None:

    for line in stderr.splitlines():
        if line.startswith("RMC_MISSING:"):
            return line[len("RMC_MISSING:"):].strip()

    return None


COMMON_PACKAGE_MAP = {
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "yaml": "PyYAML",
    "PIL": "Pillow",
    "Crypto": "pycryptodome",
    "jwt": "PyJWT",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "serial": "pyserial",
}


def print_result(missing: set[str]):

    print()
    print("=" * 72)
    print("DISCOVERY RESULT")
    print("=" * 72)

    if not missing:
        print()
        print("No unhandled ModuleNotFoundError was discovered.")
        return

    print()

    for name in sorted(missing):
        package = COMMON_PACKAGE_MAP.get(
            name.split(".")[0],
            name.split(".")[0],
        )

        print(f"  import: {name}")
        print(f"  pip:    python -m pip install {package}")
        print()


def parent_main(
    target: Path,
    target_args: list[str],
    max_rounds: int,
    timeout: float | None,
    verbose: bool,
):

    checker = Path(__file__).resolve()

    missing: set[str] = set()

    print("=" * 72)
    print("Runtime Missing Module Checker")
    print("=" * 72)
    print(f"Target: {target}")
    print()

    for round_number in range(1, max_rounds + 1):

        print("-" * 72)
        print(f"RUN #{round_number}")
        print("-" * 72)

        try:
            result = run_child(
                checker=checker,
                target=target,
                stubs=missing,
                target_args=target_args,
                timeout=timeout,
            )

        except subprocess.TimeoutExpired:
            print()
            print("[STOP] Target process timed out.")
            print("Use --timeout to control this limit.")
            print_result(missing)
            return 2

        new_missing = extract_sentinel(
            result.stderr
        )

        if verbose and result.stdout:
            print(result.stdout, end="")

        if result.returncode == 0:

            print()
            print("[OK] Target finished normally.")
            print_result(missing)
            return 0

        if new_missing is not None:

            if new_missing in missing:
                print()
                print(
                    f"[STOP] The same missing module appeared again:"
                    f" {new_missing}"
                )

                if verbose:
                    print(result.stderr)

                print_result(missing)
                return 2

            missing.add(new_missing)

            print()
            print(f"[MISSING] {new_missing}")
            print("[ACTION] Recorded; restarting in a clean child process.")

            continue

        print()
        print("[STOP] Program failed with a non-module exception.")

        if result.stderr:
            print()
            print(result.stderr, end="")

        print_result(missing)
        return 1

    print()
    print(
        f"[STOP] Reached maximum round count: {max_rounds}"
    )

    print_result(missing)
    return 2


# ============================================================
# CLI
# ============================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description=(
            "Repeatedly runs a Python program and records "
            "unhandled ModuleNotFoundError dependencies."
        )
    )

    parser.add_argument(
        "--child",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "target",
        help="Python script to inspect.",
    )

    parser.add_argument(
        "--max-rounds",
        type=int,
        default=100,
        help="Maximum number of discovery rounds.",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Per-run timeout in seconds.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show child-process output.",
    )

    return parser


def main():

    parser = build_parser()
    args, unknown = parser.parse_known_args()

    target = Path(args.target).resolve()

    if not target.exists():
        print(f"[ERROR] Target does not exist: {target}")
        raise SystemExit(2)

    if args.child:
        # In child mode, unknown arguments after "--" belong to target.
        target_args = []

        if "--" in unknown:
            index = unknown.index("--")
            target_args = unknown[index + 1:]

        return child_main(
            target=target,
            target_args=target_args,
        )

    # Normal mode.
    target_args = []

    if "--" in unknown:
        index = unknown.index("--")
        target_args = unknown[index + 1:]

    return parent_main(
        target=target,
        target_args=target_args,
        max_rounds=args.max_rounds,
        timeout=args.timeout,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    raise SystemExit(main())

