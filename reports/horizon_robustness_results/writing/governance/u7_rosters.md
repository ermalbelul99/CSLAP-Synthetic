# Panel and seat rosters under user decision U7

These rosters replace the defaults in plan §4.4 (panel table and default-seat table) for every dispatch from seq 17 onward.

**Vote weights:** opus 2, fable 2, sonnet 1. Haiku is never seated.

**Fable seats.** A seat marked `fable→opus` or `fable→sonnet` goes to fable when the time is past `state.json` `families.fable.retry_after`. Otherwise it goes to the family after the arrow, keeping the same agent type. If a fable dispatch fails on usage limits, `retry_after` becomes the failure time plus 12 h and the seat is re-dispatched to its fallback family.

**Identity rules.** The plan §4.4 rules still apply. A builder never votes on, reviews or confirms its own artifact. Panels mix at least two families. Independent confirmers and fix confirmers of ORCH-built artifacts are non-opus (DR-001 A-003); while fable is unavailable, that means sonnet.

## Decision panels

The weights below apply while fable is unavailable. Once fable is available, each `fable→` seat carries weight 2.

| Panel | Seats: agent type / family (weight) | Total weight, fable unavailable | Strict majority needs more than |
|---|---|---|---|
| **SCI-5** | results-integrity-reviewer/opus (2); scientific-reviewer/fable→opus (2); formulation-reviewer/sonnet (1); positioning-reviewer/opus (2); general-purpose practitioner reader/sonnet (1) | 8 | 4 |
| **NOV-5** | positioning-reviewer/opus (2); scientific-reviewer/sonnet (1); formulation-reviewer/fable→opus (2); results-integrity-reviewer/opus (2); general-purpose handling editor/sonnet (1) | 8 | 4 |
| **MATH-3** | formulation-reviewer/opus (2); code-reviewer/fable→sonnet (1); general-purpose independent deriver/sonnet (1) | 4 | 2 |
| **PRES-3** | narrative-reviewer/opus (2); academic-prose-auditor/fable→opus (2); results-integrity-reviewer/sonnet (1) | 5 | 2.5 |
| **PRES-5** | PRES-3 plus scientific-reviewer/sonnet (1) and positioning-reviewer/sonnet (1) | 7 | 3.5 |
| **ADP-3** (unnamed) | three seats from opus, fable→opus and sonnet, with at least one sonnet and at least one opus or fable, none a builder of the artifact | depends on seats | half the total |
| **REF-3** | general-purpose referee (optimization) /opus; general-purpose referee (warehouse application) /fable→opus; general-purpose referee (empirical methodology) /sonnet | not voted | — |

**Red and blue seats** rotate by card among the seated identities, as in plan §4.3.

**Builder substitution.** If a listed seat's identity built the artifact under decision, it is replaced by the same agent type from another permitted family. If that is impossible, another agent type with the needed tools takes the seat. The substitution is recorded in the DR.

## Default seats

| Seat | U7 default |
|---|---|
| CRT reader 1 | general-purpose/sonnet, fresh |
| CRT reader 2 | general-purpose/opus, fresh |
| RTP author | scientific-reviewer/fable→opus. If opus built the package's main artifacts, use scientific-reviewer/sonnet. |
| Independent confirmer of an ORCH-built artifact | the plan's agent type for the artifact kind, family sonnet (fable when available) |
| Independent confirmer of a non-ORCH artifact | the plan's agent type, from a family different from the builder's |
| Blue-team critic | general-purpose from a permitted family that built none of the artifacts under review |
| Second chair | general-purpose from a family different from the voters under check |
| Check-script author / code reviewer | general-purpose/sonnet author; code-reviewer/opus reviewer (or the reverse, so the families always differ) |
| Blind-pair builders (DBR) | one opus identity and one sonnet identity (fable replaces either when available). Where general-purpose/sonnet is also the check author, use optimization-coder/sonnet. |
| Extra literature search | academic-researcher/fable→sonnet |
