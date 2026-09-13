"""Frozen research policy, source allowlist and deterministic experiment design."""

from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import json
import re


REVISION = "horizon-cslap-1.0"
# Model arms. Exploratory revision 3 (13 Sep 2026) added HIST+ACT-T: the HIST+ACT
# model optimised inside the tightened band delta*(1-lambda), exactly as TIGHT
# tightens the nominal model. Membership sets are shared by every module so an
# arm property can never be defined twice.
ARMS = ("NOM", "TIGHT", "HIST", "HIST+ACT", "HIST+ACT-T")
SCENARIO_ARMS = ("HIST", "HIST+ACT", "HIST+ACT-T")     # historical block scenarios
ACTIVATION_ARMS = ("HIST+ACT", "HIST+ACT-T")           # inactive-product activation, nu
TIGHTENED_ARMS = ("TIGHT", "HIST+ACT-T")               # optimise inside delta*(1-lambda)
SYNTHETIC_ROOT = "exp02a_instances"
INDUSTRIAL_SOURCE = "Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv"
CPLEX_PYTHON = r"C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe"
HEXALY_PYTHON = r"C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe"
REPO_ROOT = Path(__file__).resolve().parents[2]


class ContractError(ValueError):
    """A named data/model contract failed; never silently repair it."""

    def __init__(self, code, message):
        self.code = str(code)
        super().__init__(f"{self.code}: {message}")


def decimal_share(value, name="share"):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ContractError("DATA_CONTRACT_ERROR", f"invalid {name}") from exc
    if not result.is_finite() or not Decimal(0) <= result <= Decimal(1):
        raise ContractError("DATA_CONTRACT_ERROR", f"{name} must be finite in [0,1]")
    return result


def share_text(value):
    return format(decimal_share(value).normalize(), "f")


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def allowed_source(path, root=REPO_ROOT):
    """Resolve exact approved files, rejecting traversal and symlink escapes."""
    root = Path(root).resolve()
    raw = Path(path)
    target = (raw if raw.is_absolute() else root / raw).resolve()
    try:
        rel = target.relative_to(root).as_posix()
    except ValueError as exc:
        raise ContractError("SOURCE_NOT_ALLOWED", "source escapes repository") from exc
    if rel == INDUSTRIAL_SOURCE:
        return rel
    match = re.fullmatch(
        r"exp02a_instances/syn_(50|500|1000|2000)sku_seed(\d+)/"
        r"syn_(50|500|1000|2000)sku_(products|stations|orders)\.csv", rel)
    if match and match.group(1) == match.group(3):
        size, seed = int(match.group(1)), int(match.group(2))
        last_seed = {50: 1012, 500: 1010, 1000: 1004, 2000: 1003}[size]
        if 1001 <= seed <= last_seed:
            return rel
    raise ContractError("SOURCE_NOT_ALLOWED", "file is not in the approved empirical allowlist")


def horizon_grid(product_count):
    if type(product_count) is not int or product_count <= 0:
        raise ContractError("DATA_CONTRACT_ERROR", "positive integer catalogue size required")
    return tuple(sorted({(product_count + 1) // 2, product_count, 2 * product_count}))


def origins(order_count, product_count, maximum=2):
    if type(order_count) is not int or order_count < 0 or maximum not in (1, 2, 3, 4):
        raise ContractError("DATA_CONTRACT_ERROR", "invalid origin design")
    n_max = horizon_grid(product_count)[-1]
    first = 7 * order_count // 10
    count = min(maximum, (order_count - first) // n_max)
    return tuple(first + j * n_max for j in range(count))


def eligible(origin, n, order_count):
    if type(n) is not int or n <= 0 or type(origin) is not int or origin < 0:
        raise ContractError("DATA_CONTRACT_ERROR", "invalid complete-order horizon/origin")
    if origin // n < 3:
        return "INSUFFICIENT_HISTORY"
    if origin + n > order_count:
        return "INSUFFICIENT_FUTURE"
    return None


def holdout_origin(order_count, product_count):
    """Deployment origin of a held-out validation (exploratory revision 3).

    The end of the furthest future the first origin can score, first + 2P: no
    solve, survey or re-scoring of the study reads an order at or beyond it.
    The 2P spacing rule of ``origins`` cannot generate it, so it is explicit.
    Raises when even the half horizon would not fit after it.
    """
    if type(order_count) is not int or order_count < 0:
        raise ContractError("DATA_CONTRACT_ERROR", "invalid origin design")
    grid = horizon_grid(product_count)
    origin = 7 * order_count // 10 + grid[-1]      # first origin + n_max, as origins() spaces them
    if eligible(origin, grid[0], order_count):
        raise ContractError("DATA_CONTRACT_ERROR", "stream too short for a held-out deployment origin")
    return origin


def time_cap(product_count, kind="synthetic"):
    if kind == "industrial":
        return 1800
    try:
        return {50: 120, 500: 300, 1000: 600, 2000: 1200}[product_count]
    except KeyError as exc:
        raise ContractError("DATA_CONTRACT_ERROR", "no empirical time cap for this catalogue") from exc


@dataclass(frozen=True)
class Protocol:
    revision: str = REVISION
    delta: str = "0.01"
    nu: str = "0.01"
    # "0.03" was added on 11 Sep 2026 for exploratory revision 2 (two-sided rule);
    # every earlier campaign used values already on this grid.
    deltas: tuple = ("0", "0.0025", "0.005", "0.01", "0.02", "0.03", "0.05")
    nus: tuple = ("0", "0.0025", "0.005", "0.01", "0.02", "0.05")
    tightening: tuple = ("0", "0.25", "0.5", "0.75", "1")
    seeds: tuple = (11, 22, 33)
    max_origins: int = 2
    share_tolerance: float = 1e-8
    threads: int = 1
    # Exploratory revision 2: the two-sided rule's data-supported primary slack.
    rules: tuple = ("upper_only", "two_sided")
    two_sided_delta: str = "0.02"

    def __post_init__(self):
        if self.revision != REVISION:
            raise ContractError("PROTOCOL_REVISION", "unsupported protocol revision")
        for value in (self.delta, self.nu, self.two_sided_delta, *self.deltas, *self.nus, *self.tightening):
            decimal_share(value)
        if self.rules != ("upper_only", "two_sided") or self.two_sided_delta not in self.deltas:
            raise ContractError("PROTOCOL_REVISION", "unsupported workload rule configuration")
        for values in (self.deltas, self.nus, self.tightening, self.seeds):
            if not isinstance(values, tuple) or not values or len(set(values)) != len(values):
                raise ContractError("DATA_CONTRACT_ERROR", "immutable unique nonempty grid required")
        if any(type(s) is not int or s < 0 for s in self.seeds):
            raise ContractError("DATA_CONTRACT_ERROR", "invalid solver seeds")
        if self.max_origins not in (1, 2, 3, 4) or type(self.threads) is not int or self.threads < 1:
            raise ContractError("DATA_CONTRACT_ERROR", "invalid resources/origins")
        if self.share_tolerance != 1e-8:
            raise ContractError("PROTOCOL_REVISION", "numerical policy change requires revision")

    def to_dict(self):
        return asdict(self)

    @property
    def fingerprint(self):
        return digest(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        for key in ("deltas", "nus", "tightening", "seeds", "rules"):
            if key in data:
                data[key] = tuple(data[key])
        return cls(**data)
