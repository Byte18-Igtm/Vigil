from __future__ import annotations

import hashlib
import re
from typing import Callable, Dict, List, Optional, Set, Tuple

from models import (
    AgentStatusEntry,
    AggregationOutcome,
    ConflictRecord,
    EvidenceItem,
    SubAgentResult,
)


# ---------------------------------------------------------------------------
# Public hash function — single source of truth
# Import this in patching.py and supervisor.py; never reimplement it.
# ---------------------------------------------------------------------------

def patch_hash(patch: str) -> str:
    return hashlib.sha256(patch.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Diff introspection helpers
# ---------------------------------------------------------------------------

def _touched_files(patch: str) -> Set[str]:
    """Return the set of old-side filenames mentioned in a unified diff.

    Known limitation: new-file patches (--- /dev/null) are not counted,
    so they won't show as overlapping with other patches.
    """
    files: Set[str] = set()
    for line in patch.splitlines():
        if line.startswith("--- "):
            path = line[4:].strip()
            if path != "/dev/null":
                if path.startswith("a/"):
                    path = path[2:]
                files.add(path)
    return files


def _changed_old_lines(patch: str) -> Dict[str, Set[int]]:
    """
    For each file in the patch, return the set of OLD-file line numbers that
    are removed (lines starting with '-', not '---').

    For a pure insertion, record the old-file line number that the new lines
    are inserted BEFORE (i.e. the current value of old_lineno when the first
    '+' line is seen in a hunk that has no '-' lines).

    Lines starting with '\\' (e.g. '\\ No newline at end of file') are skipped
    and do NOT advance the old-line counter.
    Context lines advance the counter but are NOT added to the set.
    '+' lines do NOT advance the old counter.

    Known limitation: a removed content line that itself starts with '-- '
    would be misread as a file header.
    """
    result: Dict[str, Set[int]] = {}
    current_file: Optional[str] = None
    old_lineno: int = 0
    hunk_removed: List[int] = []
    hunk_has_removal = False
    hunk_insertion_point: Optional[int] = None
    in_hunk = False

    def _flush_hunk() -> None:
        nonlocal hunk_has_removal, hunk_insertion_point
        if current_file is None:
            return
        if hunk_has_removal:
            result.setdefault(current_file, set()).update(hunk_removed)
        elif hunk_insertion_point is not None:
            result.setdefault(current_file, set()).add(hunk_insertion_point)
        hunk_removed.clear()
        hunk_has_removal = False
        hunk_insertion_point = None

    hunk_re = re.compile(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")

    for line in patch.splitlines():
        # Skip "\ No newline at end of file" and similar markers
        if line.startswith("\\"):
            continue

        if line.startswith("--- "):
            _flush_hunk()
            in_hunk = False
            path = line[4:].strip()
            if path == "/dev/null":
                current_file = None
            else:
                current_file = path[2:] if path.startswith("a/") else path
            old_lineno = 0
            continue

        if line.startswith("+++ "):
            continue

        m = hunk_re.match(line)
        if m:
            _flush_hunk()
            in_hunk = True
            old_lineno = int(m.group(1))
            continue

        if not in_hunk:
            continue

        if line.startswith("-") and not line.startswith("---"):
            hunk_removed.append(old_lineno)
            hunk_has_removal = True
            old_lineno += 1
        elif line.startswith("+") and not line.startswith("+++"):
            if hunk_insertion_point is None:
                hunk_insertion_point = old_lineno
            # '+' lines do NOT advance old_lineno
        else:
            # context line — advances counter but not added to set
            old_lineno += 1

    _flush_hunk()
    return result


def _changed_line_count(patch: str) -> int:
    return sum(
        1 for line in patch.splitlines()
        if (line.startswith("+") or line.startswith("-"))
        and not line.startswith("+++") and not line.startswith("---")
    )


def _max_confidence(result: SubAgentResult) -> float:
    if not result.findings:
        return 0.0
    return max(f.confidence for f in result.findings)


_AGENT_ORDER = ["debug", "test", "maintenance"]


def _agent_rank(agent_name: str) -> int:
    try:
        return _AGENT_ORDER.index(agent_name)
    except ValueError:
        return len(_AGENT_ORDER)


# ---------------------------------------------------------------------------
# Evidence merging
# ---------------------------------------------------------------------------

def _prefix_evidence(evidence: List[EvidenceItem], agent: str) -> List[EvidenceItem]:
    return [
        EvidenceItem(
            id=f"{agent}:{item.id}",
            type=item.type,
            source=agent,
            content=item.content,
        )
        for item in evidence
    ]


def _merge_evidence(results: List[SubAgentResult]) -> List[EvidenceItem]:
    seen: Set[str] = set()
    merged: List[EvidenceItem] = []
    for r in results:
        for item in _prefix_evidence(r.evidence, r.agent):
            if item.id not in seen:
                seen.add(item.id)
                merged.append(item)
    return merged


# ---------------------------------------------------------------------------
# Corroboration — single source of truth
# ---------------------------------------------------------------------------

def _corroborators(
    candidate_agents: List[str],
    candidate_hash: str,
    patch: str,
    results: List[SubAgentResult],
) -> List[Tuple[str, str]]:
    """
    Return a list of (agent_name, detail_string) for agents that corroborate
    this candidate, sorted by agent rank.

    Corroboration rules (all require status == "ok"):
    (i)  The candidate group has more than one agent: every agent after the
         first (sorted by rank) counts as a corroborator with detail
         "identical patch".
    (ii) An agent NOT in candidate_agents, with no competing patch
         (proposed_patch is None OR its hash == candidate_hash), has a
         finding where:
         - finding.file is in the candidate's touched files, AND
         - finding.line is None OR finding.line is in that file's changed
           old lines.
         An agent proposing a DIFFERENT patch never corroborates.

    Returns list sorted by _agent_rank.
    """
    candidate_files = _touched_files(patch)
    changed_lines = _changed_old_lines(patch)

    corroborating: List[Tuple[str, str]] = []

    # Rule (i): multi-agent group — agents[1:] (already rank-sorted) corroborate
    if len(candidate_agents) > 1:
        for agent in candidate_agents[1:]:
            corroborating.append((agent, "identical patch"))

    # Rule (ii): external agents with no competing patch
    for r in results:
        if r.agent in candidate_agents:
            continue
        if r.status != "ok":
            continue

        other_hash = patch_hash(r.proposed_patch) if r.proposed_patch else None
        if other_hash is not None and other_hash != candidate_hash:
            continue  # competing patch — never corroborates

        for finding in r.findings:
            if finding.file not in candidate_files:
                continue
            file_lines = changed_lines.get(finding.file, set())
            if finding.line is None or finding.line in file_lines:
                loc = (
                    f"{finding.file}:{finding.line}"
                    if finding.line is not None
                    else finding.file
                )
                corroborating.append((r.agent, f"finding on {loc}"))
                break

    return sorted(corroborating, key=lambda t: _agent_rank(t[0]))


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def _patches_overlap(patch_a: str, patch_b: str) -> bool:
    return bool(_touched_files(patch_a) & _touched_files(patch_b))


# ---------------------------------------------------------------------------
# Main aggregation pipeline
# ---------------------------------------------------------------------------

def aggregate(
    results: List[SubAgentResult],
    apply_check_fn: Callable[[str], bool],
) -> AggregationOutcome:
    """
    Pure aggregation pipeline. apply_check_fn(patch) returns True if the patch
    passes a dry-run check; injected so this function is unit-testable without git.
    State transitions are NOT performed here.
    """
    agent_statuses: List[AgentStatusEntry] = [
        AgentStatusEntry(agent=r.agent, status=r.status, error=r.error)
        for r in results
    ]

    limitations: List[str] = []
    conflicts: List[ConflictRecord] = []

    # Step 1: collect patches from ok agents
    ok_with_patch = [r for r in results if r.status == "ok" and r.proposed_patch]

    # Step 2: deduplicate by patch hash; sort each group by agent rank for stability
    groups: Dict[str, List[str]] = {}
    hash_to_patch: Dict[str, str] = {}
    for r in sorted(ok_with_patch, key=lambda r: _agent_rank(r.agent)):
        assert r.proposed_patch is not None
        h = patch_hash(r.proposed_patch)
        groups.setdefault(h, []).append(r.agent)
        hash_to_patch[h] = r.proposed_patch

    # Step 3: drop patches failing apply-check (exceptions count as failure)
    valid_hashes: List[str] = []
    for h, agents in groups.items():
        try:
            ok = apply_check_fn(hash_to_patch[h])
        except Exception as exc:
            limitations.append(
                f"dry-run check errored for patch from "
                f"{', '.join(agents)}: {type(exc).__name__}"
            )
            continue
        if ok:
            valid_hashes.append(h)
        else:
            limitations.append(
                f"patch from {', '.join(agents)} failed dry-run check — skipped"
            )

    # Step 4: nothing left → terminal outcome
    all_failed = all(r.status in ("failed", "timeout", "skipped") for r in results)

    if not valid_hashes:
        if all_failed or not results:
            return AggregationOutcome(
                chosen_patch=None,
                patch_hash=None,
                patch_source_agents=[],
                selection_reason=None,
                root_cause="",
                confidence=0.0,
                evidence=[],
                conflicts=conflicts,
                limitations=limitations,
                agent_statuses=agent_statuses,
                terminal_reason="failed",
                failure_reason="All agents failed, timed out, or were skipped.",
            )
        return AggregationOutcome(
            chosen_patch=None,
            patch_hash=None,
            patch_source_agents=[],
            selection_reason=None,
            root_cause="",
            confidence=0.0,
            evidence=_merge_evidence(results),
            conflicts=conflicts,
            limitations=limitations,
            agent_statuses=agent_statuses,
            terminal_reason="no_patch",
            failure_reason="Agents ran but no usable patch survived validation.",
        )

    # Step 5: rank candidates
    result_by_agent: Dict[str, SubAgentResult] = {r.agent: r for r in results}

    def _score(h: str) -> Tuple:
        agents = groups[h]
        p = hash_to_patch[h]
        corrs = _corroborators(agents, h, p, results)
        best_confidence = max(
            (_max_confidence(result_by_agent[a]) for a in agents if a in result_by_agent),
            default=0.0,
        )
        line_count = _changed_line_count(p)
        best_rank = min((_agent_rank(a) for a in agents), default=999)
        return (
            0 if corrs else 1,
            -best_confidence,
            line_count,
            best_rank,
            h,
        )

    valid_hashes_sorted = sorted(valid_hashes, key=_score)
    chosen_hash = valid_hashes_sorted[0]
    chosen_patch = hash_to_patch[chosen_hash]
    chosen_agents = groups[chosen_hash]  # sorted by agent rank

    # Step 6: unchosen candidates → conflicts or limitations
    for h in valid_hashes_sorted[1:]:
        other_patch = hash_to_patch[h]
        other_agents = groups[h]
        if _patches_overlap(chosen_patch, other_patch):
            conflicts.append(ConflictRecord(
                description=(
                    f"Overlapping patch from {', '.join(other_agents)} touches "
                    f"the same file(s) as the chosen patch from "
                    f"{', '.join(chosen_agents)}."
                ),
                agents_involved=sorted(
                    chosen_agents + other_agents, key=_agent_rank
                ),
                resolution=f"picked_{chosen_agents[0]}",
            ))
        else:
            limitations.append(
                f"Alternative non-overlapping patch from "
                f"{', '.join(other_agents)} not applied."
            )

    # Step 7: conflicting claims (different primary file across ok agents)
    primary_files: Dict[str, Optional[str]] = {}
    for r in results:
        if r.status == "ok" and r.findings:
            best = max(r.findings, key=lambda f: f.confidence)
            primary_files[r.agent] = best.file

    unique_primary_files = set(v for v in primary_files.values() if v)
    if len(unique_primary_files) > 1:
        conflicts.append(ConflictRecord(
            description=(
                f"Agents disagree on the primary file: "
                f"{', '.join(f'{a}={f}' for a, f in sorted(primary_files.items()) if f)}"
            ),
            agents_involved=sorted(primary_files.keys(), key=_agent_rank),
            resolution="open",
        ))

    # Step 8: root cause and confidence from chosen agent
    chosen_results = [
        result_by_agent[a] for a in chosen_agents if a in result_by_agent
    ]
    best_result = max(
        chosen_results,
        key=lambda r: _max_confidence(r),
        default=None,
    )
    if best_result and best_result.findings:
        best_finding = max(best_result.findings, key=lambda f: f.confidence)
        root_cause = best_finding.claim
        confidence = best_finding.confidence
    else:
        root_cause = "Unknown"
        confidence = 0.0

    # Step 9: selection reason — built entirely from _corroborators output
    corrs = _corroborators(chosen_agents, chosen_hash, chosen_patch, results)
    if corrs:
        detail_parts = [f"{agent} ({detail})" for agent, detail in corrs]
        reason = (
            f"{chosen_agents[0]} patch chosen: corroborated by "
            + ", ".join(detail_parts)
        )
    else:
        reason = (
            f"{chosen_agents[0]} patch chosen: "
            f"highest confidence ({confidence:.2f}), "
            f"{_changed_line_count(chosen_patch)} changed line(s)"
        )

    return AggregationOutcome(
        chosen_patch=chosen_patch,
        patch_hash=chosen_hash,
        patch_source_agents=chosen_agents,
        selection_reason=reason,
        root_cause=root_cause,
        confidence=confidence,
        evidence=_merge_evidence(results),
        conflicts=conflicts,
        limitations=limitations,
        agent_statuses=agent_statuses,
        terminal_reason=None,
        failure_reason=None,
    )
