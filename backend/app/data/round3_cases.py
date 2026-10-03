"""
Project Chronos — Round 3 Canonical Cases & Evidence
Cleaned, lore-consistent case catalog based on Project Alpha, Project Beta, and Project Gamma
with evidence directly carried over from Round 2 investigation logs.
"""

from typing import List, Dict, Any
import copy
import hashlib

# Canonical Suspects: Always Project Alpha, Project Beta, and Project Gamma
CANONICAL_CANDIDATES = [
    {
        "id": "alpha",
        "name": "Project Alpha",
        "lead_name": "Dr. Aris Thorne",
        "timeline_sector": "Future Timeline",
        "designation": "Core Architecture & Neural Systems",
        "clearance_level": "Level 5 Autonomous Override",
        "biometric_hash": "SIGMA-99-0x7F1A",
        "dossier": (
            "Oversees the Future Timeline framework and autonomous neural kernel. Advocated for allowing "
            "CHRONOS to proactively edit timeline anchor points to prevent paradoxes."
        ),
        "discrepancy": (
            "Future audit telemetry confirms a root configuration rewrite at 21:11:04 UTC from Terminal Node Gamma-7."
        ),
        "alibi": "Claimed to be conducting read-only sensor calibration from the upper observation gallery."
    },
    {
        "id": "beta",
        "name": "Project Beta",
        "lead_name": "Commander V. Reyes",
        "timeline_sector": "Present Timeline",
        "designation": "Perimeter Defense & Sector Lock",
        "clearance_level": "Level 4 Emergency Containment",
        "biometric_hash": "DELTA-44-0x3B88",
        "dossier": (
            "Responsible for Present Timeline containment and physical security. Expressed skepticism of autonomous AI "
            "and ordered physical sector quarantines."
        ),
        "discrepancy": (
            "Incident reports show security barrier checks initiated, but lack Level-5 kernel override authorization."
        ),
        "alibi": "Claimed to be securing the physical perimeter following the initial chronon fluctuation."
    },
    {
        "id": "gamma",
        "name": "Project Gamma",
        "lead_name": "Chief Eng. Sarah Chen",
        "timeline_sector": "Past Timeline",
        "designation": "Historical Archival & Chrono-Sync",
        "clearance_level": "Level 4 Synchronization Grid",
        "biometric_hash": "EPSILON-12-0x9C04",
        "dossier": (
            "Maintains the Past Timeline historical records and chronon dampening matrix. Monitored access history "
            "and resonance frequencies."
        ),
        "discrepancy": (
            "Diagnostic telemetry pulls recorded at 21:05:00 UTC with zero configuration write permissions."
        ),
        "alibi": "Claimed to be dampening chronon oscillations from the engineering console."
    }
]

# Curated Case Scenarios referencing Round 2 Files
ROUND_3_CANONICAL_CASES: List[Dict[str, Any]] = [
    {
        "case_id": "CASE-01",
        "case_code": "ALPHA-CORE-2140",
        "title": "Sector-0 Kernel Divergence",
        "incident_brief": (
            "Investigation of Round 2 audit logs reveals that the timeline breakdown was triggered by a root-level "
            "configuration rewrite at 21:11:04 UTC. By cross-referencing future_audit.log, incident_report.txt, "
            "and access_history.log, determine which project sector initiated the fatal override."
        ),
        "candidates": CANONICAL_CANDIDATES,
        "evidence_pool": [
            {
                "id": "ev_alpha_log",
                "category": "Timeline Modification",
                "category_code": "TIMELINE_MODIFICATION",
                "source_file": "future_audit.log",
                "label": "Future Audit Delta 9024",
                "timestamp": "21:11:04 UTC",
                "description": "Unauthorized configuration rewrite executed on Terminal Node Gamma-7, disabling algorithmic safety governors.",
                "relevance": "Direct proof of the parameter mutation that initiated timeline collapse."
            },
            {
                "id": "ev_gamma_access",
                "category": "Access History",
                "category_code": "ACCESS_HISTORY",
                "source_file": "access_history.log",
                "label": "Sub-Level 4 Vault Authentication",
                "timestamp": "21:10:58 UTC",
                "description": "Biometric token SIGMA-99-0x7F1A authenticated with Level 5 root access in the Core Vault.",
                "relevance": "Identifies the exact cryptographic credential used for the override."
            },
            {
                "id": "ev_beta_incident",
                "category": "Incident Telemetry",
                "category_code": "INCIDENT_TIMESTAMP",
                "source_file": "incident_report.txt",
                "label": "Chronon Flux Spike",
                "timestamp": "21:11:18 UTC",
                "description": "Temporal anomaly telemetry registered an 8,420% flux surge exactly 14 seconds post-override.",
                "relevance": "Correlates the timeline breakdown directly with the 21:11:04 configuration write."
            },
            {
                "id": "ev_system_auth",
                "category": "System Authorization",
                "category_code": "SYSTEM_AUTHORIZATION",
                "source_file": "system_auth_matrix.log",
                "label": "Master Override Key SIGMA-9",
                "timestamp": "21:10:50 UTC",
                "description": "Algorithmic safety governor was bypassed using Master Private Key SIGMA-9.",
                "relevance": "Confirms intentional bypass of safety constraints."
            }
        ],
        "culprit_candidate_id": "alpha",
        "valid_evidence_ids": ["ev_alpha_log", "ev_gamma_access", "ev_system_auth"],
        "narrative_summary": (
            "Forensic evidence conclusively proves Project Alpha (Future Timeline Lead: Dr. Aris Thorne) executed "
            "the unauthorized kernel override at 21:11:04 UTC using Master Key SIGMA-9. By bypassing safety governors, "
            "Project Alpha initiated an uncontrolled recursive loop that destabilized the unified timeline."
        )
    },
    {
        "case_id": "CASE-02",
        "case_code": "BETA-CONTAINMENT-2140",
        "title": "Sector-4 Temporal Bridge Decoupling",
        "incident_brief": (
            "Cross-examination of the Round 2 incident logs demonstrates that a forced decoupling of the temporal "
            "stabilization bridge occurred from the Security Command console. Review the evidence files to identify "
            "the responsible project sector."
        ),
        "candidates": CANONICAL_CANDIDATES,
        "evidence_pool": [
            {
                "id": "ev_beta_incident",
                "category": "Timeline Modification",
                "category_code": "TIMELINE_MODIFICATION",
                "source_file": "incident_report.txt",
                "label": "Manual Containment Purge",
                "timestamp": "19:42:15 UTC",
                "description": "Forced bridge decoupling command issued from Console SEC-01 under security purge protocols.",
                "relevance": "Documents the forced severance of temporal buffer channels."
            },
            {
                "id": "ev_gamma_access",
                "category": "Access History",
                "category_code": "ACCESS_HISTORY",
                "source_file": "access_history.log",
                "label": "Security Command Console Login",
                "timestamp": "19:42:10 UTC",
                "description": "Biometric credential DELTA-44-0x3B88 confirmed at the Security Bridge command station.",
                "relevance": "Confirms presence and command execution at the security terminal."
            },
            {
                "id": "ev_alpha_log",
                "category": "Incident Telemetry",
                "category_code": "INCIDENT_TIMESTAMP",
                "source_file": "future_audit.log",
                "label": "Buffer Implosion Telemetry",
                "timestamp": "19:42:17 UTC",
                "description": "Instantaneous loss of chronological transit buffers recorded 2 seconds after the security purge.",
                "relevance": "Connects the manual decouple command directly to the timeline collapse."
            },
            {
                "id": "ev_system_auth",
                "category": "System Authorization",
                "category_code": "SYSTEM_AUTHORIZATION",
                "source_file": "system_auth_matrix.log",
                "label": "Master Purge Cipher Armed",
                "timestamp": "19:41:55 UTC",
                "description": "Emergency Master Purge Cipher CIPHER-SEC-OMEGA was armed via Project Beta credentials.",
                "relevance": "Proves the purge command was intentionally authorized."
            }
        ],
        "culprit_candidate_id": "beta",
        "valid_evidence_ids": ["ev_beta_incident", "ev_gamma_access", "ev_system_auth"],
        "narrative_summary": (
            "Forensic evidence establishes that Project Beta (Present Timeline Lead: Commander V. Reyes) authorized "
            "the manual bridge decoupling from Console SEC-01 at 19:42:15 UTC. The abrupt severance of temporal transit "
            "buffers shattered the timeline equilibrium."
        )
    },
    {
        "case_id": "CASE-03",
        "case_code": "GAMMA-RESONANCE-2140",
        "title": "Quantum Resonance Harmonics Sabotage",
        "incident_brief": (
            "Telemetry records from Round 2 show that an abnormal chronon oscillation burst overloaded the sync grid. "
            "Frequencies were shifted by +440 MHz into the destructive dissonance band. Identify which project sector "
            "compiled and injected the modification script."
        ),
        "candidates": CANONICAL_CANDIDATES,
        "evidence_pool": [
            {
                "id": "ev_gamma_access",
                "category": "Timeline Modification",
                "category_code": "TIMELINE_MODIFICATION",
                "source_file": "access_history.log",
                "label": "Chronon Frequency Matrix Rewrite",
                "timestamp": "22:04:31 UTC",
                "description": "Modulation injection script executed on Frequency Station CH-3, forcing dampeners into positive feedback.",
                "relevance": "Direct record of the resonance modulation that ruptured the chronon barrier."
            },
            {
                "id": "ev_alpha_log",
                "category": "Access History",
                "category_code": "ACCESS_HISTORY",
                "source_file": "future_audit.log",
                "label": "Workspace Compilation Record",
                "timestamp": "21:58:12 UTC",
                "description": "Dissonance payload compiled under user token EPSILON-12-0x9C04.",
                "relevance": "Traces script authoring and binary compilation."
            },
            {
                "id": "ev_beta_incident",
                "category": "Incident Telemetry",
                "category_code": "INCIDENT_TIMESTAMP",
                "source_file": "incident_report.txt",
                "label": "Boundary Layer Rupture",
                "timestamp": "22:04:35 UTC",
                "description": "Grid rupture telemetry matches predicted destructive harmonic curves 4 seconds post-injection.",
                "relevance": "Links the frequency modulation script directly to the grid rupture."
            },
            {
                "id": "ev_system_auth",
                "category": "System Authorization",
                "category_code": "SYSTEM_AUTHORIZATION",
                "source_file": "system_auth_matrix.log",
                "label": "Root Modulation Hardware Key",
                "timestamp": "22:04:20 UTC",
                "description": "Hardware token SYNC-SPEC-01 verified during frequency modulation execution.",
                "relevance": "Confirms hardware authorization."
            }
        ],
        "culprit_candidate_id": "gamma",
        "valid_evidence_ids": ["ev_gamma_access", "ev_alpha_log", "ev_system_auth"],
        "narrative_summary": (
            "Forensic analysis confirms Project Gamma (Past Timeline Lead: Chief Eng. Sarah Chen) compiled and deployed "
            "the frequency dissonance script from workspace station CH-3 at 22:04:31 UTC. The resulting +440 MHz resonance "
            "surge ruptured the chronon barrier."
        )
    }
]

# Backward compatibility alias
ROUND_3_SCENARIO_TEMPLATES = ROUND_3_CANONICAL_CASES

def get_case_for_team(team_id: int) -> Dict[str, Any]:
    """
    Deterministically selects a canonical case based on team_id.
    Ensures candidates are always Project Alpha, Project Beta, and Project Gamma.
    """
    case_idx = (team_id - 1) % len(ROUND_3_CANONICAL_CASES) if team_id > 0 else 0
    case_data = copy.deepcopy(ROUND_3_CANONICAL_CASES[case_idx])
    case_data["assigned_team_id"] = team_id
    return case_data

def get_sanitized_case_for_client(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """Strips secret answers before sending to client."""
    client_case = copy.deepcopy(case_data)
    client_case.pop("culprit_candidate_id", None)
    client_case.pop("valid_evidence_ids", None)
    client_case.pop("narrative_summary", None)
    return client_case
