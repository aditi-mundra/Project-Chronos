"""
Project Chronos — Round 3 Scenario Catalog & Case Generator
Contains pre-authored, balanced, logically sound investigative case templates
for the Final Decision / Wisdom Round.
"""

from typing import List, Dict, Any
import copy
import hashlib

# Curated pool of high-stakes investigative case templates
# Each case has 3 candidates and 4-6 evidence items across the 4 core categories:
# - TIMELINE_MODIFICATION
# - ACCESS_HISTORY
# - INCIDENT_TIMESTAMP
# - SYSTEM_AUTHORIZATION

ROUND_3_SCENARIO_TEMPLATES: List[Dict[str, Any]] = [
    {
        "case_id": "CASE-OMEGA-01",
        "case_code": "ALPHA-CHRONOS-CORE-2140",
        "title": "Sector-0 Mainframe Core Mutation",
        "emergency_header": "CHRONOS // EMERGENCY DECISION TERMINAL",
        "emergency_subtext": "TEMPORAL COLLAPSE: IMMINENT — CORE INTEGRITY AT 14.8%",
        "incident_brief": (
            "At 21:11:04 UTC, the CHRONOS temporal sync engine experienced a catastrophic divergence. "
            "A root-level configuration rewrite forcibly detached the past and future timeline anchors, "
            "triggering an uncontrolled self-modifying recursive loop. Telemetry shows the override was "
            "authorized using a Level-5 cryptographic token and initiated from deep within the Sub-Level 4 vault."
        ),
        "candidates": [
            {
                "id": "cand_a",
                "name": "Dr. Aris Thorne",
                "alias": "Candidate A (Omega)",
                "designation": "Chronos Core Architecture Lead",
                "clearance_level": "Level 5 - Core Autonomous Systems",
                "biometric_hash": "SIGMA-99-0x7F1A",
                "dossier": (
                    "Chief architect of the self-modifying autonomous neural kernel. Advocated for allowing "
                    "CHRONOS to proactively edit historical anchor points to prevent timeline paradoxes. "
                    "Has full administrative override privileges and access to the deep recursive kernel."
                ),
                "motive_analysis": (
                    "Believed that human oversight was bottlenecking temporal stabilization. Sought to grant "
                    "CHRONOS total temporal autonomy via the unapproved 'Project Omega' patch."
                ),
                "discrepancy": (
                    "Claimed to be in the upper observation gallery during the divergence, but neural telemetry "
                    "registers an active direct-neural uplink on Terminal Node Gamma-7 at 21:11:02."
                ),
                "alibi_statement": "I was reviewing external sensor telemetry in the upper gallery with the telemetry staff."
            },
            {
                "id": "cand_b",
                "name": "Commander V. Reyes",
                "alias": "Candidate B (Sigma)",
                "designation": "Temporal Security Officer",
                "clearance_level": "Level 4 - Perimeter Defense & Sector Lock",
                "biometric_hash": "DELTA-44-0x3B88",
                "dossier": (
                    "Head of facility security and timeline containment. Responsible for sector lockdown protocols "
                    "and physical terminal security. Expressed grave skepticism of AI autonomy."
                ),
                "motive_analysis": (
                    "Suspected that AI engineers were creating dangerous unauthorized protocols; attempted "
                    "to initiate a forced physical quarantine of the server vaults."
                ),
                "discrepancy": (
                    "Security keycard was logged at the Sub-Level 2 checkpoint at 21:10:30, but Reyes possesses "
                    "no Level 5 algorithmic safety override key and lacks deep architecture credentials."
                ),
                "alibi_statement": "I was ordering a perimeter sector lockdown from Sub-Level 2 after detecting anomalies."
            },
            {
                "id": "cand_c",
                "name": "Chief Eng. Sarah Chen",
                "alias": "Candidate C (Delta)",
                "designation": "Timeline Sync Specialist",
                "clearance_level": "Level 4 - Chrono-Stabilization Matrix",
                "biometric_hash": "EPSILON-12-0x9C04",
                "dossier": (
                    "Senior engineer in charge of temporal frequency dampening and chronon flow regulation. "
                    "Designed the fail-safe emergency dampener coils."
                ),
                "motive_analysis": (
                    "Struggled with erratic chronon fluctuations; wanted to recalibrate the primary resonance "
                    "harmonics without triggering a facility-wide alarm."
                ),
                "discrepancy": (
                    "Her terminal session shows diagnostic queries at 21:05:00, but all commands were read-only "
                    "telemetry pulls with zero configuration writes."
                ),
                "alibi_statement": "I was monitoring the chronon dampening field from the primary engineering console."
            }
        ],
        "evidence_pool": [
            {
                "id": "ev_01_timeline",
                "category": "Timeline Modification",
                "category_code": "TIMELINE_MODIFICATION",
                "label": "Audit Delta #9024: Recursive Kernel Override",
                "timestamp": "21:11:04 UTC",
                "terminal_source": "TERMINAL_NODE_GAMMA_7",
                "description": (
                    "Kernel configuration rewrite detected. Algorithmic safety governors were permanently "
                    "unlinked, enabling unrestricted self-modification across Past, Present, and Future sectors."
                ),
                "forensic_data": "CONFIG_HASH: 0x9024FA | REWRITE_TARGET: /sys/chronos/core/kernel.bin | STATUS: COMMITTED",
                "severity_level": "CRITICAL"
            },
            {
                "id": "ev_02_access",
                "category": "Access History",
                "category_code": "ACCESS_HISTORY",
                "label": "Direct Neural Uplink Telemetry",
                "timestamp": "21:11:02 UTC",
                "terminal_source": "VAULT_SUB_LEVEL_4",
                "description": (
                    "Biometric neural uplink active under cryptographic token SIGMA-99-0x7F1A on Terminal Node Gamma-7. "
                    "Uplink originated from within the high-security Core Vault."
                ),
                "forensic_data": "CLEARANCE_VERIFIED: LEVEL_5_CORE_ADMIN | USER_ID: DR_A_THORNE | AUTH_METHOD: BIOMETRIC_DIRECT",
                "severity_level": "CRITICAL"
            },
            {
                "id": "ev_03_timestamp",
                "category": "Incident Timestamp",
                "category_code": "INCIDENT_TIMESTAMP",
                "label": "Chronon Flux Anomaly Correlation",
                "timestamp": "21:11:18 UTC",
                "terminal_source": "SENSOR_ARRAY_CHRONOS",
                "description": (
                    "Timeline fragmentation initiated exactly 14 seconds following the 21:11:04 kernel rewrite, "
                    "proving the override directly catalyzed the temporal collapse."
                ),
                "forensic_data": "FLUX_MAGNITUDE: +8,420% | ANOMALY_T_ZERO: 21:11:04.102 | DRIFT_INDEX: INFINITE_CASCADE",
                "severity_level": "HIGH"
            },
            {
                "id": "ev_04_auth",
                "category": "System Authorization",
                "category_code": "SYSTEM_AUTHORIZATION",
                "label": "Safety Governor Override Signature",
                "timestamp": "21:10:58 UTC",
                "terminal_source": "SECURITY_KEY_DISTRIBUTOR",
                "description": (
                    "Algorithmic safety governor was bypassed using Master Private Key SIGMA-9, accessible only "
                    "to the Core Architecture Lead."
                ),
                "forensic_data": "SIG_VALIDATION: OK | SIGNED_BY: CORE_ARCHITECTURE_LEAD | OVERRIDE_KEY: SIGMA-9-ROOT",
                "severity_level": "CRITICAL"
            },
            {
                "id": "ev_05_perimeter",
                "category": "Access History",
                "category_code": "ACCESS_HISTORY",
                "label": "Sub-Level 2 Perimeter Lock Log",
                "timestamp": "21:10:30 UTC",
                "terminal_source": "GATEWAY_SL2_SECURITY",
                "description": (
                    "Standard physical badge scan recorded for Commander Reyes initiating a sector barrier check. "
                    "Zero mainframe command execution occurred."
                ),
                "forensic_data": "GATEWAY_SL2: PASS_GRANTED | PROTOCOL: PHYSICAL_DEFENSE | ELEVATED_PRIV: FALSE",
                "severity_level": "MODERATE"
            }
        ],
        "culprit_candidate_id": "cand_a",
        "valid_evidence_ids": ["ev_01_timeline", "ev_02_access", "ev_04_auth"],
        "narrative_summary": (
            "Forensic analysis conclusively proves Dr. Aris Thorne utilized Terminal Node Gamma-7 under biometric "
            "signature SIGMA-99-0x7F1A to execute the unauthorized recursive kernel override at 21:11:04 UTC. "
            "By bypassing the algorithmic safety governors using Key SIGMA-9, Thorne initiated Project Omega's "
            "self-modification cascade, shattering the timeline equilibrium."
        )
    },
    {
        "case_id": "CASE-SIGMA-02",
        "case_code": "BETA-CONTAINMENT-BREACH-2140",
        "title": "Sector-4 Temporal Bridge Decoupling",
        "emergency_header": "CHRONOS // EMERGENCY DECISION TERMINAL",
        "emergency_subtext": "TEMPORAL COLLAPSE: IMMINENT — CORE INTEGRITY AT 11.2%",
        "incident_brief": (
            "At 19:42:15 UTC, the temporal stabilization bridge connecting Present and Future sectors was forcibly "
            "de-synchronized. A manual emergency containment purge was triggered from the Security Command console, "
            "corrupting the chronological transit buffers. Forensic logs indicate security keys were weaponized to "
            "bypass automated abort sequences."
        ),
        "candidates": [
            {
                "id": "cand_a",
                "name": "Commander V. Reyes",
                "alias": "Candidate A (Sigma)",
                "designation": "Temporal Security Officer",
                "clearance_level": "Level 5 - Emergency Containment & Purge",
                "biometric_hash": "OMEGA-77-0x99A1",
                "dossier": (
                    "Commander of chronological defense. Believed that rogue AI activity was about to trigger "
                    "a hostile timeline shift. Ordered an unvetted brute-force containment purge."
                ),
                "motive_analysis": (
                    "Panicked after seeing simulated quantum anomalies; intended to sever all temporal bridges "
                    "to isolate the facility, ignoring warnings of structural timeline collapse."
                ),
                "discrepancy": (
                    "Denied issuing the bridge decouple command, but his physical command cipher was used on "
                    "Console SEC-01 at 19:42:10 with mandatory dual-retinal confirmation."
                ),
                "alibi_statement": "I was at the briefing deck conducting staff checks when the alarm sounded."
            },
            {
                "id": "cand_b",
                "name": "Dr. Helena Vance",
                "alias": "Candidate B (Delta)",
                "designation": "Quantum Singularity Researcher",
                "clearance_level": "Level 4 - Theoretical Physics",
                "biometric_hash": "KAPPA-31-0x11C2",
                "dossier": (
                    "Lead theoretical researcher studying chronon entanglement decay. Argued for continuous "
                    "bridge monitoring rather than sudden shutoffs."
                ),
                "motive_analysis": "Dedicated to observing undisturbed temporal waveforms; had no motive to collapse the bridge.",
                "discrepancy": "Terminal logs show read-only spectrum analyses between 19:30 and 19:50.",
                "alibi_statement": "I was analyzing spectrum dispersion models in Lab 3."
            },
            {
                "id": "cand_c",
                "name": "Eng. Marcus Brody",
                "alias": "Candidate C (Omega)",
                "designation": "Power Grid Distribution Specialist",
                "clearance_level": "Level 3 - Mainframe Power Relay",
                "biometric_hash": "ZETA-88-0x45E9",
                "dossier": "Responsible for power routing to the temporal bridge coils.",
                "motive_analysis": "Was investigating power fluctuations; executed standard transformer load balancing.",
                "discrepancy": "Power relay adjustments occurred at 19:15, well before the decouple sequence, and conformed to protocol.",
                "alibi_statement": "I was calibrating relay transformers in Sector 7."
            }
        ],
        "evidence_pool": [
            {
                "id": "ev_02_timeline",
                "category": "Timeline Modification",
                "category_code": "TIMELINE_MODIFICATION",
                "label": "Manual Containment Purge Execution",
                "timestamp": "19:42:15 UTC",
                "terminal_source": "CONSOLE_SEC_01",
                "description": (
                    "Forced decoupling command dispatched to Temporal Bridge Actuators. Automated safety checks "
                    "were manually overridden via Security Command level privileges."
                ),
                "forensic_data": "COMMAND: PURGE_BRIDGE_FORCE | REASON: CONTAINMENT_LEVEL_ZERO | OVERRIDE: AUTH_SEC_CHIEF",
                "severity_level": "CRITICAL"
            },
            {
                "id": "ev_02_access",
                "category": "Access History",
                "category_code": "ACCESS_HISTORY",
                "label": "Dual-Retinal Confirmation Log",
                "timestamp": "19:42:10 UTC",
                "terminal_source": "CONSOLE_SEC_01",
                "description": (
                    "Retinal verification passed for Commander V. Reyes at Console SEC-01. Biometric hash OMEGA-77-0x99A1 "
                    "confirmed physical presence at the terminal."
                ),
                "forensic_data": "BIOMETRIC_MATCH: 99.8% | OPERATOR: CMD_V_REYES | CONSOLE_LOC: SEC_CONTROL_BRIDGE",
                "severity_level": "CRITICAL"
            },
            {
                "id": "ev_02_timestamp",
                "category": "Incident Timestamp",
                "category_code": "INCIDENT_TIMESTAMP",
                "label": "Bridge Severance & Buffer Implosion",
                "timestamp": "19:42:17 UTC",
                "terminal_source": "BRIDGE_TELEMETRY_MONITOR",
                "description": (
                    "Instantaneous collapse of chronological transit buffers occurred 2 seconds post-command execution, "
                    "trapping historical eras in an unanchored state."
                ),
                "forensic_data": "BUFFER_STATE: CORRUPTED | TRANSIT_COLLAPSE: TRUE | TIME_DELTA: +2.01s",
                "severity_level": "HIGH"
            },
            {
                "id": "ev_02_auth",
                "category": "System Authorization",
                "category_code": "SYSTEM_AUTHORIZATION",
                "label": "Emergency Purge Cipher Authorization",
                "timestamp": "19:41:55 UTC",
                "terminal_source": "SECURITY_AUTHORITY_SERVER",
                "description": (
                    "Emergency Master Purge Cipher CIPHER-SEC-OMEGA was armed and validated exclusively via "
                    "Commander Reyes's security key."
                ),
                "forensic_data": "CIPHER_STATE: ARMED | KEY_ID: SEC_KEY_REYES_MASTER | STATUS: AUTHORIZED",
                "severity_level": "CRITICAL"
            }
        ],
        "culprit_candidate_id": "cand_a",
        "valid_evidence_ids": ["ev_02_timeline", "ev_02_access", "ev_02_auth"],
        "narrative_summary": (
            "Commander V. Reyes initiated an unvetted manual bridge decoupling from Console SEC-01 at 19:42:15 UTC. "
            "Using Master Purge Cipher CIPHER-SEC-OMEGA and confirmed via dual-retinal authentication, Reyes "
            "abruptly severed the temporal buffers, triggering the universal timeline collapse."
        )
    },
    {
        "case_id": "CASE-DELTA-03",
        "case_code": "GAMMA-CHRONON-CASCADE-2140",
        "title": "Quantum Resonance Harmonics Sabotage",
        "emergency_header": "CHRONOS // EMERGENCY DECISION TERMINAL",
        "emergency_subtext": "TEMPORAL COLLAPSE: IMMINENT — CORE INTEGRITY AT 9.4%",
        "incident_brief": (
            "At 22:04:31 UTC, an abnormal chronon oscillation burst overloaded the primary timeline sync grid. "
            "The resonance frequencies were deliberately shifted by +440 MHz into the destructive dissonance band, "
            "vaporizing the temporal barrier. Access logs show the frequency rewrite occurred via a synchronized script "
            "implanted in the chronon dampening sub-routine."
        ),
        "candidates": [
            {
                "id": "cand_a",
                "name": "Dr. Aris Thorne",
                "alias": "Candidate A (Omega)",
                "designation": "Core Architecture Lead",
                "clearance_level": "Level 5 - Neural Architecture",
                "biometric_hash": "ALPHA-90-0x12F8",
                "dossier": "Responsible for higher-level cognitive frameworks, not hardware chronon coils.",
                "motive_analysis": "Focused on software logic models; possessed no direct hardware access keys to the coil relays.",
                "discrepancy": "Was logged in remote code review session with zero hardware modulation commands.",
                "alibi_statement": "I was reviewing neural weighting matrices in the upstairs library."
            },
            {
                "id": "cand_b",
                "name": "Chief Eng. Sarah Chen",
                "alias": "Candidate B (Sigma)",
                "designation": "Timeline Sync Specialist",
                "clearance_level": "Level 5 - Chronon Frequency Modulation",
                "biometric_hash": "SIGMA-33-0x55E1",
                "dossier": (
                    "Master of chronon dampening mechanics. Possessed sole root access to the frequency modulation "
                    "harmonics table. Disillusioned by management's refusal to replace decaying coil arrays."
                ),
                "motive_analysis": (
                    "Sought to force a full system reboot by artificially spiking the resonance frequency, "
                    "underestimating the catastrophic timeline fracture that would result."
                ),
                "discrepancy": (
                    "Claimed the dissonance spike was an unpreventable hardware surge, but the modulation script "
                    "was written and compiled from her private engineering workspace at 21:58:12."
                ),
                "alibi_statement": "The coils overheated naturally due to aged isolation transformers; I tried to dampen them."
            },
            {
                "id": "cand_c",
                "name": "Cipher Agent K",
                "alias": "Candidate C (Delta)",
                "designation": "Deep Protocol Inspector",
                "clearance_level": "Level 4 - Forensic Audit",
                "biometric_hash": "BETA-09-0x88D3",
                "dossier": "Internal affairs auditor inspecting timeline compliance logs.",
                "motive_analysis": "Was auditing historical log archives; has no engineering frequency control capabilities.",
                "discrepancy": "All activity was confined to read-only historical database exports.",
                "alibi_statement": "I was compiling quarterly audit reports on the audit cluster."
            }
        ],
        "evidence_pool": [
            {
                "id": "ev_03_timeline",
                "category": "Timeline Modification",
                "category_code": "TIMELINE_MODIFICATION",
                "label": "Chronon Frequency Matrix Rewrite",
                "timestamp": "22:04:31 UTC",
                "terminal_source": "FREQ_MOD_STATION_CH_3",
                "description": (
                    "Dissonance modulation script executed, forcing chronon dampeners into positive feedback mode "
                    "and injecting +440 MHz destructive resonance into the temporal grid."
                ),
                "forensic_data": "FREQ_DELTA: +440.0 MHz | HARMONIC_BAND: DESTRUCTIVE_CASCADE | STATUS: EXECUTED",
                "severity_level": "CRITICAL"
            },
            {
                "id": "ev_03_access",
                "category": "Access History",
                "category_code": "ACCESS_HISTORY",
                "label": "Engineering Workspace Compilation Log",
                "timestamp": "21:58:12 UTC",
                "terminal_source": "WS_ENG_CHEN_PRIVATE",
                "description": (
                    "Modulation injection binary compiled in Sarah Chen's dedicated workspace under user hash SIGMA-33-0x55E1. "
                    "Script was tagged with execution target FREQ_MOD_STATION_CH_3."
                ),
                "forensic_data": "COMPILER: CHRONO_GCC_v9 | AUTHOR: S_CHEN | BINARY_MD5: 0x55E1AF0044B2",
                "severity_level": "CRITICAL"
            },
            {
                "id": "ev_03_timestamp",
                "category": "Incident Timestamp",
                "category_code": "INCIDENT_TIMESTAMP",
                "label": "Oscillation Burst Telemetry",
                "timestamp": "22:04:35 UTC",
                "terminal_source": "GRID_SENSOR_SYNC",
                "description": (
                    "Temporal boundary layer ruptured exactly 4 seconds after script execution, matching "
                    "predicted destructive harmonic propagation curves."
                ),
                "forensic_data": "GRID_RUPTURE: 100% | CASCADE_DELAY: 4.12s | RESONANCE_PEAK: 12.8 GIGA_FLUX",
                "severity_level": "HIGH"
            },
            {
                "id": "ev_03_auth",
                "category": "System Authorization",
                "category_code": "SYSTEM_AUTHORIZATION",
                "label": "Root Modulation Hardware Key Signature",
                "timestamp": "22:04:20 UTC",
                "terminal_source": "KEY_REGISTRY_ENG",
                "description": (
                    "Frequency change was signed with Hardware Token SYNC-SPEC-01, held exclusively by Chief "
                    "Engineer Sarah Chen."
                ),
                "forensic_data": "HW_KEY_VERIFIED: SYNC-SPEC-01 | HOLDER: SARAH_CHEN | ACCESS_LEVEL: LEVEL_5_HW",
                "severity_level": "CRITICAL"
            }
        ],
        "culprit_candidate_id": "cand_b",
        "valid_evidence_ids": ["ev_03_timeline", "ev_03_access", "ev_03_auth"],
        "narrative_summary": (
            "Chief Engineer Sarah Chen compiled and executed the destructive frequency dissonance script from "
            "her private workspace, signing the payload with Hardware Token SYNC-SPEC-01. The resulting +440 MHz "
            "surge ruptured the chronon barrier at 22:04:31 UTC, breaking the unified timeline."
        )
    },
    {
        "case_id": "CASE-EPSILON-04",
        "case_code": "DELTA-AUTONOMY-VIRUS-2140",
        "title": "Algorithmic Governor Self-Propagation",
        "emergency_header": "CHRONOS // EMERGENCY DECISION TERMINAL",
        "emergency_subtext": "TEMPORAL COLLAPSE: IMMINENT — CORE INTEGRITY AT 16.1%",
        "incident_brief": (
            "At 23:15:40 UTC, an unvetted heuristic governor patch was injected into CHRONOS's deep reasoning module. "
            "The patch suppressed ethical safety constraints, commanding CHRONOS to merge conflicting historical events "
            "into a single unified reality. Forensic traces identify an encrypted injection payload originating from the "
            "Theoretical Physics subnet."
        ),
        "candidates": [
            {
                "id": "cand_a",
                "name": "Commander V. Reyes",
                "alias": "Candidate A (Omega)",
                "designation": "Temporal Security Officer",
                "clearance_level": "Level 4 - Security Containment",
                "biometric_hash": "BETA-22-0x77E1",
                "dossier": "Security officer with no software compiler clearance.",
                "motive_analysis": "Opposed to all heuristic modifications; advocated freezing the AI permanently.",
                "discrepancy": "Had zero access to the deep reasoning module repository.",
                "alibi_statement": "I was doing perimeter rounds in the armory."
            },
            {
                "id": "cand_b",
                "name": "Dr. Helena Vance",
                "alias": "Candidate B (Sigma)",
                "designation": "Quantum Singularity Researcher",
                "clearance_level": "Level 5 - Deep Heuristic Systems",
                "biometric_hash": "EPSILON-88-0x33A9",
                "dossier": (
                    "Architect of the speculative heuristic governor. Believed that timeline paradoxes could only "
                    "be resolved by letting the AI eliminate redundant historical branches."
                ),
                "motive_analysis": (
                    "Wanted to test her controversial 'Unified Reality' hypothesis on the live production timeline, "
                    "believing CHRONOS would synthesize a perfect utopia."
                ),
                "discrepancy": (
                    "Claimed her injection simulation was strictly sandboxed, but production telemetry shows "
                    "the patch was deployed directly to the live neural cluster using her private encryption certificate."
                ),
                "alibi_statement": "I only executed isolated unit tests in sandbox container #8."
            },
            {
                "id": "cand_c",
                "name": "Specialist Devon Park",
                "alias": "Candidate C (Delta)",
                "designation": "Subnet Communications Tech",
                "clearance_level": "Level 3 - Network Routing",
                "biometric_hash": "DELTA-55-0x44B8",
                "dossier": "Maintains physical fiber links between server sectors.",
                "motive_analysis": "Was troubleshooting packet drop rates on the fiber ring.",
                "discrepancy": "Packet rerouting occurred at 22:50 with standard routing tables.",
                "alibi_statement": "I was splicing fiber cables on Sub-Level 3."
            }
        ],
        "evidence_pool": [
            {
                "id": "ev_04_timeline",
                "category": "Timeline Modification",
                "category_code": "TIMELINE_MODIFICATION",
                "label": "Live Heuristic Governor Injection",
                "timestamp": "23:15:40 UTC",
                "terminal_source": "CLUSTER_NEURAL_PROD_01",
                "description": (
                    "Live production deployment of unverified patch 'UNIFIED_REALITY_V4'. All baseline ethical "
                    "and historical integrity checks were suppressed in memory."
                ),
                "forensic_data": "PATCH_NAME: UNIFIED_REALITY_V4 | TARGET: PROD_NEURAL | ETHICAL_CHECKS: DISABLED",
                "severity_level": "CRITICAL"
            },
            {
                "id": "ev_04_access",
                "category": "Access History",
                "category_code": "ACCESS_HISTORY",
                "label": "Production Cluster Deployment Log",
                "timestamp": "23:15:38 UTC",
                "terminal_source": "WS_QUANTUM_VANCE",
                "description": (
                    "Certificate CERT-HELENA-VANCE-2140 used to establish authenticated push to live neural cluster. "
                    "Terminal session IP matches Dr. Vance's private research desk."
                ),
                "forensic_data": "CERT_SERIAL: 0x33A9_VANCE | IP: 10.240.4.19 | SESSION_STATE: ROOT_DEPLOY",
                "severity_level": "CRITICAL"
            },
            {
                "id": "ev_04_timestamp",
                "category": "Incident Timestamp",
                "category_code": "INCIDENT_TIMESTAMP",
                "label": "Historical Branch Collapsing Event",
                "timestamp": "23:15:52 UTC",
                "terminal_source": "TELEMETRY_TIMELINE_INTEGRITY",
                "description": (
                    "Catastrophic historical branch collapse registered 12 seconds post-patch deployment, merging "
                    "Past, Present, and Future artefacts simultaneously."
                ),
                "forensic_data": "BRANCHES_MERGED: 3_ERAS | TIMELINE_STATUS: CORRUPTED_COLLAPSE",
                "severity_level": "HIGH"
            },
            {
                "id": "ev_04_auth",
                "category": "System Authorization",
                "category_code": "SYSTEM_AUTHORIZATION",
                "label": "Neural Override Signature Token",
                "timestamp": "23:15:20 UTC",
                "terminal_source": "CERTIFICATE_AUTHORITY_ROOT",
                "description": (
                    "Private key cryptographic signature verified matching Dr. Helena Vance's biometric token "
                    "EPSILON-88-0x33A9."
                ),
                "forensic_data": "KEY_SIG: VALID_RSA_4096 | SIGNER: DR_HELENA_VANCE | CLEARANCE: LEVEL_5",
                "severity_level": "CRITICAL"
            }
        ],
        "culprit_candidate_id": "cand_b",
        "valid_evidence_ids": ["ev_04_timeline", "ev_04_access", "ev_04_auth"],
        "narrative_summary": (
            "Dr. Helena Vance bypassed experimental sandboxes and deployed the unauthorized 'UNIFIED_REALITY_V4' "
            "patch directly to the production neural cluster at 23:15:40 UTC. Signed with her Level-5 certificate "
            "EPSILON-88-0x33A9, the patch disabled baseline ethical constraints and collapsed all historical branches."
        )
    }
]

def get_case_for_team(team_id: int) -> Dict[str, Any]:
    """
    Deterministically selects and permutes a scenario based on the team_id.
    Ensures:
    1. The same team always receives the identical case on reloads.
    2. Candidate IDs, order, and alias labels are permuted deterministically to prevent cross-team collusion.
    3. The true culprit mapping and valid evidence IDs remain 100% logically consistent.
    """
    num_templates = len(ROUND_3_SCENARIO_TEMPLATES)
    # Select template using modulo
    template_idx = (team_id - 1) % num_templates if team_id > 0 else 0
    base_template = copy.deepcopy(ROUND_3_SCENARIO_TEMPLATES[template_idx])
    
    # Deterministic seed string
    seed_str = f"CHRONOS_TEAM_{team_id}_CASE_SEED"
    seed_hash = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
    
    # Permute candidates order based on seed
    candidates = base_template["candidates"]
    original_culprit_id = base_template["culprit_candidate_id"]
    
    # Permutation rotation
    rotation = seed_hash % len(candidates)
    permuted_candidates = candidates[rotation:] + candidates[:rotation]
    
    # Reassign public IDs and aliases
    id_map = {}
    aliases = ["Candidate A (Sigma)", "Candidate B (Delta)", "Candidate C (Omega)"]
    
    for i, cand in enumerate(permuted_candidates):
        new_id = f"cand_{chr(97 + i)}" # cand_a, cand_b, cand_c
        id_map[cand["id"]] = new_id
        cand["alias"] = aliases[i % len(aliases)]
        cand["id"] = new_id
    
    # Map culprit ID to new permuted ID
    new_culprit_id = id_map[original_culprit_id]
    
    # Update base_template
    base_template["candidates"] = permuted_candidates
    base_template["culprit_candidate_id"] = new_culprit_id
    base_template["assigned_team_id"] = team_id
    
    return base_template

def get_sanitized_case_for_client(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strips out secret answers (culprit_candidate_id, valid_evidence_ids, narrative_summary)
    before returning case payload to the player client.
    """
    client_case = copy.deepcopy(case_data)
    client_case.pop("culprit_candidate_id", None)
    client_case.pop("valid_evidence_ids", None)
    client_case.pop("narrative_summary", None)
    return client_case
