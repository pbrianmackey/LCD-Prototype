"""
Data schema for the persistent knowledge store and the benchmark.

KnowledgeCard is the unit of the "persistent knowledge" store (spec section 6).
Two text fields matter and are used very differently downstream:

  - `text` / `title`: a natural, encyclopedia-style description of the technique,
    written the way a human domain reference would write it (jargon included).
    This is what an ordinary RAG baseline embeds and searches.

  - `capability_tags` + `mechanism_template`: a domain-neutral description of the
    *mechanism* -- what the technique actually does, stripped of field-specific
    nouns. This is what the capability-based (LCD) retriever embeds and searches.

The same card is retrievable by both paths; what differs is the representation
used to compute similarity, not the underlying data. That is the whole
experimental manipulation.

`domain_terms` lists the field-specific vocabulary the Abstractor should strip
out when it turns a retrieved card into a "general mechanism" (spec section 4).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class KnowledgeCard:
    id: str
    domain: str                     # e.g. "control_theory", "epidemiology", "software_engineering"
    title: str
    text: str                       # natural domain-native description (RAG baseline embeds this)
    capability_tags: List[str]      # short domain-neutral capability phrases (LCD embeds this)
    mechanism_template: str         # domain-neutral abstracted mechanism description
    domain_terms: List[str] = field(default_factory=list)   # jargon stripped during abstraction
    code_skeleton: Optional[str] = None   # dotted path to a callable/class in lcd.mechanisms
    is_distractor: bool = False     # same-domain card that looks relevant but under-performs
    notes: str = ""

    def rag_text(self) -> str:
        return f"{self.title}. {self.text}"

    def capability_text(self) -> str:
        return f"{'; '.join(self.capability_tags)}. {self.mechanism_template}"


@dataclass
class BenchmarkProblem:
    id: str
    title: str
    statement: str                  # problem text given to the system (must not leak donor jargon)
    donor_card_id: str               # ground truth: the KB card with the correct mechanism (eval-only)
    baseline_a_card_id: str           # id of the same-domain "default" card used for Baseline A (no retrieval)
    harness_module: str               # dotted path to benchmark.problems.<module> implementing evaluate()
    control_type: Optional[str] = None   # "naive_sufficient" | "no_kb_solution" | None
    historical_note: str = ""


def load_cards(path: str | Path) -> List[KnowledgeCard]:
    cards = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cards.append(KnowledgeCard(**d))
    return cards


def save_cards(cards: List[KnowledgeCard], path: str | Path) -> None:
    with open(path, "w") as f:
        for c in cards:
            f.write(json.dumps(asdict(c)) + "\n")


def load_problems(path: str | Path) -> List[BenchmarkProblem]:
    problems = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            problems.append(BenchmarkProblem(**d))
    return problems


def save_problems(problems: List[BenchmarkProblem], path: str | Path) -> None:
    with open(path, "w") as f:
        for p in problems:
            f.write(json.dumps(asdict(p)) + "\n")
