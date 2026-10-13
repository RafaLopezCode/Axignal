"""What one observed organization would cost a subscriber's own agent each month.

A transparent model, not a measurement: every task an agent would have to perform to
reproduce what AXIGNAL delivers for one organization (the ten families, crossings and
their evolution), with the raw tokens it would read and write, the tool calls and the
seconds per call. Three scenarios bound the uncertainty. Prices are the GPT-6 Luna
rates configured in production (AXIGNAL_AXENT_INPUT/OUTPUT_PER_MILLION).

    python -m tools.evaluation.agent_cost
"""

from __future__ import annotations

import json
from dataclasses import dataclass

LUNA_INPUT_USD_PER_M = 0.125
LUNA_OUTPUT_USD_PER_M = 0.50
#: Reference exchange rate (state it, revise it); not a live quote.
EUR_PER_USD = 0.92
SECOND_ORGANIZATION_EUR = 4.95


@dataclass(frozen=True)
class Task:
    family: str
    what: str
    calls: int  # tool calls (searches, fetches, API reads, model questions)
    raw_input_k: float  # thousand tokens the results put into the agent's context
    weekly: bool  # repeated weekly to see evolution (volatile), else monthly
    reproducible: str  # "yes", "partial", "no": can an agent obtain it on its own?


TASKS: tuple[Task, ...] = (
    Task("presence", "Read the website (8 pages) and audit structured data, sharing tags, languages", 10, 96, False, "yes"),
    Task("presence", "Real-user speed (CrUX API, needs its own Google key)", 2, 3, True, "partial"),
    Task("presence", "Ask AI assistants 5 category questions and check who is named", 5, 10, False, "partial"),
    Task("reputation", "Search press in its languages and read results", 6, 60, True, "partial"),
    Task("reputation", "Identify its Wikipedia articles and read monthly pageviews", 4, 12, False, "yes"),
    Task("reputation", "Find review profiles it links and read them", 3, 30, False, "partial"),
    Task("value", "Establish its activity, offer and certifications from site and registers", 4, 40, False, "yes"),
    Task("markets", "Premises, languages, group countries (GLEIF), hiring countries", 4, 30, False, "yes"),
    Task("relationships", "Technology suppliers, logo walls, group parents and subsidiaries", 3, 25, False, "yes"),
    Task("relationships", "Public contract awards of 12 months: its clients, partners, competitors", 8, 120, False, "no"),
    Task("demand", "Search open public calls in its countries (several portals) and screen them", 12, 144, True, "partial"),
    Task("demand", "Who buys from its sector (input-output tables) and recurring buyers", 3, 40, False, "partial"),
    Task("activity", "Read its job board and own publications", 2, 25, True, "yes"),
    Task("economics", "Official registers and Wikidata: revenue, employees, accounts", 5, 30, False, "yes"),
    Task("organization", "Identifiers, legal names, LEI, register numbers", 3, 15, False, "yes"),
    Task("context", "Sector headlines in its country, screened for relevance", 4, 40, True, "partial"),
    Task("context", "New regulation for its activity in its countries (official journals)", 6, 90, True, "partial"),
    Task("crossings", "Cross the families (INXIGHTs) and write the reading with sources", 2, 60, False, "yes"),
    Task("evolution", "Load last month's notes and diff every family (evolution/regression)", 2, 50, True, "partial"),
)  # fmt: skip

SCENARIOS = {
    # context amplification: an agent loop re-reads its growing context on each turn;
    # output share: reasoning and notes written, as a share of raw input read;
    # seconds per call: tool round trip plus model turn; human: supervision minutes.
    "efficient": {"amplification": 1.5, "output_share": 0.05, "seconds_per_call": 8, "human_initial_min": 10, "human_weekly_min": 5},
    "central": {"amplification": 4.0, "output_share": 0.10, "seconds_per_call": 15, "human_initial_min": 25, "human_weekly_min": 10},
    "heavy": {"amplification": 10.0, "output_share": 0.15, "seconds_per_call": 25, "human_initial_min": 45, "human_weekly_min": 20},
}  # fmt: skip
WEEKS_PER_MONTH = 4.33


def month(scenario: dict[str, float]) -> dict[str, float]:
    """One organization, one steady month: a full study, then weekly volatile refreshes."""
    calls = sum(t.calls for t in TASKS) + WEEKS_PER_MONTH * sum(t.calls for t in TASKS if t.weekly)
    raw = sum(t.raw_input_k for t in TASKS) + WEEKS_PER_MONTH * sum(
        t.raw_input_k for t in TASKS if t.weekly
    )
    input_tokens = raw * 1000 * scenario["amplification"]
    output_tokens = raw * 1000 * scenario["output_share"]
    usd = input_tokens / 1e6 * LUNA_INPUT_USD_PER_M + output_tokens / 1e6 * LUNA_OUTPUT_USD_PER_M
    agent_minutes = calls * scenario["seconds_per_call"] / 60
    human_minutes = scenario["human_initial_min"] + WEEKS_PER_MONTH * scenario["human_weekly_min"]
    return {
        "tool_calls": round(calls),
        "input_tokens_m": round(input_tokens / 1e6, 2),
        "output_tokens_m": round(output_tokens / 1e6, 3),
        "token_cost_eur": round(usd * EUR_PER_USD, 2),
        "agent_minutes": round(agent_minutes),
        "human_minutes": round(human_minutes),
    }


def main() -> int:
    report = {
        "prices": {"luna_input_usd_per_m": LUNA_INPUT_USD_PER_M,
                   "luna_output_usd_per_m": LUNA_OUTPUT_USD_PER_M,
                   "eur_per_usd": EUR_PER_USD, "axignal_second_organization_eur": SECOND_ORGANIZATION_EUR},
        "scenarios": {name: month(s) for name, s in SCENARIOS.items()},
        "not_reproducible_by_an_agent": [t.what for t in TASKS if t.reproducible == "no"],
        "partially_reproducible": [t.what for t in TASKS if t.reproducible == "partial"],
    }  # fmt: skip
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
