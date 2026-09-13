"""Solver-neutral immutable contracts; indices always cover the full catalogue.

All intervals are zero-based half-open complete-order indices. Sparse count pairs
are sorted unique (product_index, positive_integer_count). Audit metadata is a
tuple of (string_key, string_value), with JSON strings for structured values.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from fractions import Fraction
import math
import re

from .protocol import (ACTIVATION_ARMS, ARMS, SCENARIO_ARMS, TIGHTENED_ARMS,
                       ContractError, REVISION, allowed_source, decimal_share,
                       digest, share_text)


def _require(condition, message, code="DATA_CONTRACT_ERROR"):
    if not condition:
        raise ContractError(code, message)


def _integers(values, nonnegative=True):
    return isinstance(values, tuple) and all(type(v) is int and (v >= 0 or not nonnegative) for v in values)


def _pairs(values, positive=False):
    _require(isinstance(values, tuple), "pairs must be immutable tuples")
    keys = []
    for pair in values:
        _require(isinstance(pair, tuple) and len(pair) == 2 and _integers(pair), "invalid index/count pair")
        if positive:
            _require(pair[1] > 0, "count must be positive")
        keys.append(pair[0])
    _require(keys == sorted(set(keys)), "pair keys must be sorted and unique")


def _audit(values):
    _require(isinstance(values, tuple) and all(isinstance(x, tuple) and len(x) == 2
             and all(isinstance(v, str) for v in x) for x in values), "invalid immutable audit metadata")


@dataclass(frozen=True)
class SourceFile:
    path: str
    sha256: str
    size_bytes: int

    def __post_init__(self):
        allowed_source(self.path)
        _require(isinstance(self.sha256, str) and re.fullmatch(r"[0-9a-f]{64}", self.sha256), "invalid source hash")
        _require(type(self.size_bytes) is int and self.size_bytes >= 0, "invalid source length")


@dataclass(frozen=True)
class CatalogueManifest:
    dataset_id: str
    kind: str
    product_ids: tuple
    station_ids: tuple
    capacities: tuple
    source_files: tuple = ()
    exogenous_fixed: tuple = ()
    allowed_stations: tuple = ()
    known_reference: tuple = ()
    slot_ids: tuple = ()
    geometry_provenance: str = "verified_exogenous"
    roster_provenance: str = "verified_exogenous"
    audit: tuple = ()
    revision: str = REVISION

    def __post_init__(self):
        _require(self.revision == REVISION, "unsupported manifest revision")
        _require(self.kind in ("synthetic", "industrial", "fixture"), "unknown source kind")
        _require(isinstance(self.dataset_id, str) and bool(self.dataset_id), "dataset id required")
        for ids in (self.product_ids, self.station_ids):
            _require(isinstance(ids, tuple) and len(ids) > 0 and len(set(ids)) == len(ids)
                     and all(isinstance(v, str) and v.strip() == v and v for v in ids), "invalid full ID universe")
        _require(_integers(self.capacities) and len(self.capacities) == self.s
                 and all(c > 0 for c in self.capacities) and sum(self.capacities) == self.p,
                 "full catalogue must exactly fill all positive station capacities")
        _require(isinstance(self.source_files, tuple) and all(isinstance(v, SourceFile) for v in self.source_files),
                 "invalid source manifest")
        _require(self.kind == "fixture" or bool(self.source_files), "empirical source hashes required")
        source_paths = [v.path for v in self.source_files]
        _require(len(set(source_paths)) == len(source_paths), "duplicate source file")
        if self.kind == "industrial":
            _require(len(source_paths) == 1 and source_paths[0].endswith("BERNER_ORDER_LINES_09-12.csv"),
                     "industrial manifest must use exactly the approved industrial export")
        elif self.kind == "synthetic":
            _require(len(source_paths) == 3 and all(p.startswith("exp02a_instances/" + self.dataset_id + "/") for p in source_paths),
                     "synthetic manifest must use the three files from its one instance")
            _require({p.rsplit("_", 1)[-1] for p in source_paths} == {"products.csv", "stations.csv", "orders.csv"},
                     "synthetic source trio incomplete")
        _pairs(self.exogenous_fixed)
        _require(all(p < self.p and s < self.s for p, s in self.exogenous_fixed), "fixed index outside catalogue")
        _require(isinstance(self.allowed_stations, tuple), "allowed stations must be immutable")
        if self.allowed_stations:
            _require(len(self.allowed_stations) == self.p, "allowed-station table must cover full catalogue")
            for stations in self.allowed_stations:
                _require(_integers(stations) and stations and len(set(stations)) == len(stations)
                         and all(s < self.s for s in stations), "invalid allowed station list")
        _require(all(s in self.eligible_stations(p) for p, s in self.exogenous_fixed), "fixed product has forbidden station")
        fixed_occupancy = [0] * self.s
        for p, s in self.exogenous_fixed:
            fixed_occupancy[s] += 1
        _require(all(c <= capacity for c, capacity in zip(fixed_occupancy, self.capacities)), "fixed products exceed storage")
        _require(_integers(self.known_reference), "reference indices must be immutable")
        if self.known_reference:
            self.check_storage(self.known_reference, self.exogenous_fixed)
        _require(isinstance(self.slot_ids, tuple), "slot labels must be immutable")
        if self.slot_ids:
            _require(len(self.slot_ids) == self.s and all(isinstance(v, tuple) and len(v) == c
                     for v, c in zip(self.slot_ids, self.capacities)), "slot map has wrong dimensions")
            flat = [v for station in self.slot_ids for v in station]
            _require(len(set(flat)) == self.p and all(isinstance(v, str) and v for v in flat), "slot IDs must be globally unique")
        for name in (self.geometry_provenance, self.roster_provenance):
            _require(name in ("verified_exogenous", "assumed_exogenous"), "usable exogenous metadata required")
        _audit(self.audit)

    @property
    def p(self):
        return len(self.product_ids)

    @property
    def s(self):
        return len(self.station_ids)

    def eligible_stations(self, p):
        return self.allowed_stations[p] if self.allowed_stations else tuple(range(self.s))

    def check_storage(self, assignment, fixed=()):
        _require(_integers(assignment) and len(assignment) == self.p, "assignment omits catalogue products")
        _pairs(fixed)
        _require(all(p < self.p and s < self.s for p, s in fixed), "fixed assignment index outside universe")
        occupancy = [0] * self.s
        for p, s in enumerate(assignment):
            _require(s < self.s and s in self.eligible_stations(p), "invalid product station")
            occupancy[s] += 1
        _require(tuple(occupancy) == self.capacities, "station slot occupancy mismatch")
        _require(all(assignment[p] == s for p, s in fixed), "fixed location changed")

    @property
    def fingerprint(self):
        return digest(self.to_dict())

    def decision_dict(self):
        return {k: getattr(self, k) for k in ("product_ids", "station_ids", "capacities", "exogenous_fixed",
                "allowed_stations", "known_reference", "slot_ids")}

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        data["source_files"] = tuple(SourceFile(**v) for v in data.get("source_files", ()))
        for key in ("product_ids", "station_ids", "capacities", "known_reference"):
            data[key] = tuple(data.get(key, ()))
        for key in ("exogenous_fixed", "allowed_stations", "slot_ids", "audit"):
            data[key] = tuple(tuple(v) for v in data.get(key, ()))
        return cls(**data)


@dataclass(frozen=True)
class Order:
    order_id: str
    chronology_key: int
    lines: tuple
    observations: tuple = ()

    def __post_init__(self):
        _require(isinstance(self.order_id, str) and self.order_id.strip() == self.order_id and self.order_id, "order ID required")
        _require(type(self.chronology_key) is int and self.chronology_key >= 0, "invalid chronological key")
        _pairs(self.lines, positive=True)
        _require(bool(self.lines), "empty order is not an observation")
        _require(isinstance(self.observations, tuple) and all(isinstance(v, tuple) and _integers(v)
                 and len(v) == 2 for v in self.observations), "invalid historical station observations")

    @property
    def support(self):
        return tuple(p for p, count in self.lines)

    @property
    def total_lines(self):
        return sum(count for p, count in self.lines)

    @classmethod
    def from_dict(cls, data):
        return cls(data["order_id"], data["chronology_key"], tuple(tuple(v) for v in data["lines"]),
                   tuple(tuple(v) for v in data.get("observations", ())))


@dataclass(frozen=True)
class OrderedDemand:
    catalogue: CatalogueManifest
    orders: tuple
    audit: tuple = ()

    def __post_init__(self):
        _require(isinstance(self.orders, tuple) and all(isinstance(o, Order) for o in self.orders), "immutable orders required")
        keys = tuple(o.chronology_key for o in self.orders)
        _require(all(a < b for a, b in zip(keys, keys[1:])), "order keys must be strictly increasing and unique")
        _require(len({o.order_id for o in self.orders}) == len(self.orders), "duplicate complete order ID")
        for o in self.orders:
            _require(all(p < self.catalogue.p for p, count in o.lines), "ordered product outside known catalogue", "OUT_OF_CATALOGUE")
            _require(all(p < self.catalogue.p and s < self.catalogue.s for p, s in o.observations), "station observation outside universe")
        _audit(self.audit)


@dataclass(frozen=True)
class Scenario:
    counts: tuple
    total_lines: int
    start: int
    stop: int
    label: str = "block"

    def __post_init__(self):
        _pairs(self.counts, positive=True)
        _require(type(self.total_lines) is int and self.total_lines > 0
                 and sum(c for p, c in self.counts) == self.total_lines, "scenario total must equal positive line counts")
        _require(type(self.start) is int and type(self.stop) is int and 0 <= self.start < self.stop,
                 "invalid complete-order interval")

    @classmethod
    def from_dict(cls, data):
        return cls(tuple(tuple(v) for v in data["counts"]), data["total_lines"], data["start"], data["stop"], data.get("label", "block"))


@dataclass(frozen=True)
class ReferenceState:
    assignment: tuple
    fixed: tuple
    historical_counts: tuple
    station_line_counts: tuple
    origin: int
    history_hash: str
    provenance: str
    audit: tuple = ()

    def __post_init__(self):
        _require(_integers(self.assignment) and self.assignment, "complete immutable reference required")
        _pairs(self.fixed)
        _require(_integers(self.historical_counts) and len(self.historical_counts) == len(self.assignment)
                 and sum(self.historical_counts) > 0, "full positive historical workload required")
        _require(_integers(self.station_line_counts) and sum(self.station_line_counts) == sum(self.historical_counts), "reference workload is not conserved")
        _require(type(self.origin) is int and self.origin > 0, "positive historical prefix required")
        _require(isinstance(self.history_hash, str) and re.fullmatch(r"[0-9a-f]{64}", self.history_hash), "invalid history hash")
        _require(isinstance(self.provenance, str) and self.provenance, "reference provenance required")
        _audit(self.audit)

    @property
    def total_lines(self):
        return sum(self.historical_counts)

    @property
    def b(self):
        total = self.total_lines
        return tuple(c / total for c in self.station_line_counts)

    @property
    def inactive(self):
        return tuple(p for p, c in enumerate(self.historical_counts) if c == 0)

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        for key in ("assignment", "historical_counts", "station_line_counts"):
            data[key] = tuple(data[key])
        for key in ("fixed", "audit"):
            data[key] = tuple(tuple(v) for v in data.get(key, ()))
        return cls(**data)


@dataclass(frozen=True)
class TrainingProblem:
    catalogue: CatalogueManifest
    reference: ReferenceState
    n: int
    scenarios: tuple
    weighted_supports: tuple
    arm: str = "HIST+ACT"
    delta: str = "0.01"
    nu: str = "0.01"
    tightening: str = "0.5"
    revision: str = REVISION
    # Exploratory revision 2 (11 Sep 2026): "two_sided" additionally requires
    # every station to stay ABOVE b_s - delta. The default reproduces the
    # completed upper-only study byte-for-byte: see to_dict / model_hash.
    rule: str = "upper_only"

    def __post_init__(self):
        _require(self.revision == REVISION, "unsupported training revision")
        _require(self.arm in ARMS, "unknown model arm")
        _require(self.rule in ("upper_only", "two_sided"), "unknown workload rule")
        for name in ("delta", "nu", "tightening"):
            _require(isinstance(getattr(self, name), str), "policy values must be decimal strings")
            decimal_share(getattr(self, name), name)
        self.catalogue.check_storage(self.reference.assignment, self.reference.fixed)
        self.catalogue.check_storage(self.reference.assignment, self.catalogue.exogenous_fixed)
        _require(set(self.catalogue.exogenous_fixed).issubset(set(self.reference.fixed)), "exogenous fixed products lost from decision mask")
        _require(len(self.reference.historical_counts) == self.catalogue.p and len(self.reference.station_line_counts) == self.catalogue.s,
                 "reference dimensions do not cover full universe")
        observed = [0] * self.catalogue.s
        for p, s in enumerate(self.reference.assignment):
            observed[s] += self.reference.historical_counts[p]
        _require(tuple(observed) == self.reference.station_line_counts, "reference shares do not match allocation/workload")
        _require(type(self.n) is int and self.n > 0, "positive order horizon required")
        _require(isinstance(self.scenarios, tuple) and all(isinstance(v, Scenario) for v in self.scenarios), "immutable scenarios required")
        for scenario in self.scenarios:
            _require(scenario.stop <= self.reference.origin and all(p < self.catalogue.p for p, c in scenario.counts), "scenario accesses future or unknown products")
            _require(all(self.reference.historical_counts[p] > 0 for p, c in scenario.counts), "inactive product has historical scenario demand")
        if self.arm in SCENARIO_ARMS:
            _require(bool(self.scenarios), "robust model needs historical scenarios")
            _require(any(v.counts == self.nominal_scenario.counts and v.start == 0 and v.stop == self.reference.origin
                         for v in self.scenarios), "whole-history scenario missing")
        _require(isinstance(self.weighted_supports, tuple) and self.weighted_supports, "full weighted supports required")
        supports = []
        for entry in self.weighted_supports:
            _require(isinstance(entry, tuple) and len(entry) == 2, "weighted supports must be deeply immutable")
            support, weight = entry
            _require(_integers(support) and support and tuple(sorted(set(support))) == support
                     and all(p < self.catalogue.p for p in support) and type(weight) is int and weight > 0,
                     "invalid exact weighted support")
            supports.append(support)
        _require(len(set(supports)) == len(supports), "duplicate support must be weight-compressed exactly")
        _require(sum(w for support, w in self.weighted_supports) == self.reference.origin, "support truncation or order loss")

    @property
    def nominal_scenario(self):
        return Scenario(tuple((p, c) for p, c in enumerate(self.reference.historical_counts) if c),
                        self.reference.total_lines, 0, self.reference.origin, "history")

    @property
    def effective_scenarios(self):
        return (self.nominal_scenario,) if self.arm in ("NOM", "TIGHT") else self.scenarios

    @property
    def effective_nu(self):
        return float(decimal_share(self.nu)) if self.arm in ACTIVATION_ARMS and self.reference.inactive else 0.0

    @property
    def scoring_caps(self):
        return tuple(float(v) for v in self.rational_caps())

    def _effective_delta(self, optimization):
        delta = Fraction(self.delta)
        if optimization and self.arm in TIGHTENED_ARMS:
            delta *= 1 - Fraction(self.tightening)
        return delta

    def rational_caps(self, optimization=False):
        delta = self._effective_delta(optimization)
        total = self.reference.total_lines
        return tuple(min(Fraction(1), Fraction(c, total) + delta) for c in self.reference.station_line_counts)

    @property
    def two_sided(self):
        return self.rule == "two_sided"

    def rational_floors(self, optimization=False):
        """Lower ceilings max(0, b_s - delta); None under the upper-only rule.

        A floor is clipped at zero exactly as a cap is clipped at one, so a
        station whose target is below delta keeps a vacuous floor rather than
        a negative one.
        """
        if not self.two_sided:
            return None
        delta = self._effective_delta(optimization)
        total = self.reference.total_lines
        return tuple(max(Fraction(0), Fraction(c, total) - delta) for c in self.reference.station_line_counts)

    @property
    def optimization_caps(self):
        return tuple(float(v) for v in self.rational_caps(optimization=True))

    @property
    def input_hash(self):
        return digest(self.to_dict())

    @property
    def model_hash(self):
        """Identical mathematics deduplicates without forgetting audit provenance.

        In particular NOM ignores n; HIST+ACT with no inactive products equals
        HIST. The full input hash remains separate from this solve-cache key.
        The two-sided rule adds its floors and its name; the upper-only key is
        unchanged so every completed campaign keeps its identity.
        """
        payload = {"revision": self.revision, "catalogue": self.catalogue.decision_dict(),
                   "fixed": self.reference.fixed, "supports": self.weighted_supports,
                   "scenarios": [dict(counts=s.counts, total=s.total_lines) for s in self.effective_scenarios],
                   "caps": [str(v) for v in self.rational_caps(True)],
                   "nu": share_text(self.nu) if self.arm in ACTIVATION_ARMS and self.reference.inactive else "0",
                   "inactive": self.reference.inactive if self.arm in ACTIVATION_ARMS and Fraction(self.nu) > 0 else ()}
        if self.two_sided:
            payload["rule"] = self.rule
            payload["floors"] = [str(v) for v in self.rational_floors(True)]
        return digest(payload)

    def to_dict(self):
        # `rule` is serialised only when it departs from the default, so the
        # input hash of every upper-only problem (and therefore every existing
        # manifest, case record and frozen certificate) is byte-identical.
        data = asdict(self)
        if not self.two_sided:
            data.pop("rule")
        return data

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        data.setdefault("rule", "upper_only")
        data["catalogue"] = CatalogueManifest.from_dict(data["catalogue"])
        data["reference"] = ReferenceState.from_dict(data["reference"])
        data["scenarios"] = tuple(Scenario.from_dict(v) for v in data["scenarios"])
        data["weighted_supports"] = tuple((tuple(support), weight) for support, weight in data["weighted_supports"])
        return cls(**data)


class SolveStatus(str, Enum):
    OPTIMAL_WITHIN_TOLERANCE = "OPTIMAL_WITHIN_TOLERANCE"
    FEASIBLE = "FEASIBLE"
    PROVEN_INFEASIBLE = "PROVEN_INFEASIBLE"
    NO_INCUMBENT_LIMIT = "NO_INCUMBENT_LIMIT"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    NUMERICAL_ISSUE = "NUMERICAL_ISSUE"
    SOLVER_ERROR = "SOLVER_ERROR"
    DATA_CONTRACT_ERROR = "DATA_CONTRACT_ERROR"


@dataclass(frozen=True)
class SolveResult:
    backend: str
    backend_version: str
    status: SolveStatus
    native_status: str
    input_hash: str
    model_hash: str
    seed: int
    threads: int
    time_limit: float
    assignment: tuple | None = None
    objective: float | None = None
    bound: float | None = None
    gap: float | None = None
    build_seconds: float = 0.0
    solve_seconds: float = 0.0
    representation: str = ""
    solve_mode: str = "visits"
    bound_provenance: str = "unavailable"
    audit: tuple = ()

    def __post_init__(self):
        _require(isinstance(self.status, SolveStatus), "unknown normalized solve status")
        for name in ("objective", "bound", "gap", "build_seconds", "solve_seconds", "time_limit"):
            value = getattr(self, name)
            _require(value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)
                     and math.isfinite(value)), "solver results must use finite numbers or null")
        _require(self.assignment is None or _integers(self.assignment), "immutable solver assignment required")
        _require(self.solve_mode in ("visits", "min_slack"), "unknown optimization objective")
        _audit(self.audit)

    def to_dict(self):
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        data["status"] = SolveStatus(data["status"])
        if data.get("assignment") is not None:
            data["assignment"] = tuple(data["assignment"])
        data["audit"] = tuple(tuple(v) for v in data.get("audit", ()))
        return cls(**data)
