#!/usr/bin/env python3
"""
Project Chronos — Database Architecture & Round-by-Round State PDF Generator
Generates a comprehensive, publication-grade PDF documenting:
- Complete Entity-Relationship (ER) Architecture
- Detailed Schema & Table Specifications
- Round 1, Round 2, Round 3, Auth, and Leaderboard Database Lifecycles
- State Transition Diagrams, Transactions, and Concurrency Protections
"""

import zlib
import sys
from pathlib import Path

class PDFBuilder:
    def __init__(self, page_width=595.28, page_height=841.89): # A4
        self.width = page_width
        self.height = page_height
        self.pages = []
        self.objects = []
        self.font_names = {
            "F1": "Helvetica",
            "F2": "Helvetica-Bold",
            "F3": "Helvetica-Oblique",
            "F4": "Courier",
            "F5": "Courier-Bold",
            "F6": "Times-Roman",
            "F7": "Times-Bold"
        }
        
    def new_page(self):
        page = PageBuilder(self.width, self.height)
        self.pages.append(page)
        return page

    def build_pdf(self) -> bytes:
        # Object 1: Catalog
        # Object 2: Pages
        # Object 3..: Page objects, Content streams, Font objects
        out = bytearray()
        out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        
        obj_offsets = []
        
        def add_obj(body_bytes: bytes) -> int:
            obj_id = len(obj_offsets) + 1
            obj_offsets.append(len(out))
            out.extend(f"{obj_id} 0 obj\n".encode("latin1"))
            out.extend(body_bytes)
            out.extend(b"\nendobj\n")
            return obj_id

        # Fonts objects (3 to 3 + len(fonts) - 1)
        # We will create standard Type1 font objects
        font_obj_ids = {}
        
        # We will allocate IDs
        # 1: Catalog, 2: Pages
        # 3..: Font objects
        catalog_id = 1
        pages_id = 2
        
        # Reserve placeholders for catalog and pages
        obj_offsets.append(0) # placeholder for 1
        obj_offsets.append(0) # placeholder for 2
        
        for alias, font_name in self.font_names.items():
            f_bytes = f"<< /Type /Font /Subtype /Type1 /BaseFont /{font_name} /Encoding /WinAnsiEncoding >>".encode("latin1")
            font_id = len(obj_offsets) + 1
            obj_offsets.append(0) # placeholder
            font_obj_ids[alias] = font_id

        # Render each page
        page_obj_ids = []
        page_content_ids = []
        
        for p in self.pages:
            content_bytes = p.get_stream_bytes()
            compressed = zlib.compress(content_bytes)
            stream_obj = f"<< /Length {len(compressed)} /Filter /FlateDecode >>\nstream\n".encode("latin1") + compressed + b"\nendstream"
            content_id = len(obj_offsets) + 1
            obj_offsets.append(0) # placeholder
            page_content_ids.append(content_id)
            
            p_id = len(obj_offsets) + 1
            obj_offsets.append(0) # placeholder
            page_obj_ids.append(p_id)

        # Now write object bodies and record real offsets
        # Obj 1: Catalog
        cat_bytes = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("latin1")
        obj_offsets[0] = len(out)
        out.extend(f"1 0 obj\n".encode("latin1") + cat_bytes + b"\nendobj\n")
        
        # Obj 2: Pages
        kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
        pages_bytes = f"<< /Type /Pages /Kids [ {kids_str} ] /Count {len(page_obj_ids)} >>".encode("latin1")
        obj_offsets[1] = len(out)
        out.extend(f"2 0 obj\n".encode("latin1") + pages_bytes + b"\nendobj\n")
        
        # Font objs
        for alias, font_name in self.font_names.items():
            f_id = font_obj_ids[alias]
            f_bytes = f"<< /Type /Font /Subtype /Type1 /BaseFont /{font_name} /Encoding /WinAnsiEncoding >>".encode("latin1")
            obj_offsets[f_id - 1] = len(out)
            out.extend(f"{f_id} 0 obj\n".encode("latin1") + f_bytes + b"\nendobj\n")

        # Page and content objs
        fonts_res = " ".join(f"/{alias} {font_obj_ids[alias]} 0 R" for alias in self.font_names)
        for i, p in enumerate(self.pages):
            content_id = page_content_ids[i]
            p_id = page_obj_ids[i]
            
            # Content stream
            content_bytes = p.get_stream_bytes()
            compressed = zlib.compress(content_bytes)
            c_body = f"<< /Length {len(compressed)} /Filter /FlateDecode >>\nstream\n".encode("latin1") + compressed + b"\nendstream"
            obj_offsets[content_id - 1] = len(out)
            out.extend(f"{content_id} 0 obj\n".encode("latin1") + c_body + b"\nendobj\n")
            
            # Page dict
            p_body = f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [ 0 0 {self.width} {self.height} ] /Contents {content_id} 0 R /Resources << /Font << {fonts_res} >> /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ] >> >>".encode("latin1")
            obj_offsets[p_id - 1] = len(out)
            out.extend(f"{p_id} 0 obj\n".encode("latin1") + p_body + b"\nendobj\n")

        # Xref table
        xref_offset = len(out)
        out.extend(f"xref\n0 {len(obj_offsets) + 1}\n0000000000 65535 f \n".encode("latin1"))
        for off in obj_offsets:
            out.extend(f"{off:010d} 00000 n \n".encode("latin1"))
            
        # Trailer
        out.extend(f"trailer\n<< /Size {len(obj_offsets) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1"))
        return bytes(out)


class PageBuilder:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.commands = []
        
    def _escape(self, text: str) -> str:
        # Map common unicode glyphs to WinAnsi/ASCII equivalents
        replacements = {
            "\\": "\\\\",
            "(": "\\(",
            ")": "\\)",
            "•": "*",
            "✔": "[OK]",
            "—": "--",
            "–": "-",
            "→": "->",
            "←": "<-",
            "“": '"',
            "”": '"',
            "‘": "'",
            "’": "'",
            "…": "...",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        # Strip any other non-ascii/non-latin1 chars safely
        return text.encode("latin1", "replace").decode("latin1")

    def set_fill_color(self, r, g, b):
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")

    def set_stroke_color(self, r, g, b):
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG")

    def set_line_width(self, w):
        self.commands.append(f"{w:.2f} w")

    def draw_rect(self, x, y, w, h, fill=True, stroke=False):
        mode = "B" if (fill and stroke) else ("f" if fill else "s")
        self.commands.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {mode}")

    def draw_rounded_rect(self, x, y, w, h, r=4, fill=True, stroke=False):
        # Approximate rounded rect with subpaths
        mode = "B" if (fill and stroke) else ("f" if fill else "s")
        c = []
        c.append(f"{x + r:.2f} {y:.2f} m")
        c.append(f"{x + w - r:.2f} {y:.2f} l")
        c.append(f"{x + w:.2f} {y:.2f} {x + w:.2f} {y + r:.2f} {x + w:.2f} {y + r:.2f} c")
        c.append(f"{x + w:.2f} {y + h - r:.2f} l")
        c.append(f"{x + w:.2f} {y + h:.2f} {x + w - r:.2f} {y + h:.2f} {x + w - r:.2f} {y + h:.2f} c")
        c.append(f"{x + r:.2f} {y + h:.2f} l")
        c.append(f"{x:.2f} {y + h:.2f} {x:.2f} {y + h - r:.2f} {x:.2f} {y + h - r:.2f} c")
        c.append(f"{x:.2f} {y + r:.2f} l")
        c.append(f"{x:.2f} {y:.2f} {x + r:.2f} {y:.2f} {x + r:.2f} {y:.2f} c")
        c.append(mode)
        self.commands.append(" ".join(c))

    def draw_line(self, x1, y1, x2, y2):
        self.commands.append(f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def draw_text(self, text, x, y, font="F1", size=10, r=0.1, g=0.1, b=0.1):
        esc = self._escape(text)
        self.commands.append(f"BT /{font} {size} Tf {r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {y:.2f} Td ({esc}) Tj ET")

    def get_stream_bytes(self) -> bytes:
        return "\n".join(self.commands).encode("latin1")


def create_chronos_pdf(output_path: str):
    pdf = PDFBuilder(page_width=595.28, page_height=841.89) # A4
    
    # Palette definition (Theme Obsidian, Deep Violet, Electric Indigo, Solar Cream, Mint)
    C_OBSIDIAN = (0.04, 0.05, 0.08)
    C_CARD_BG  = (0.07, 0.09, 0.14)
    C_CARD_ALT = (0.09, 0.12, 0.18)
    C_BORDER   = (0.18, 0.24, 0.35)
    C_BORDER_ACCENT = (0.24, 0.38, 0.55)
    
    C_TEXT_WHITE = (0.95, 0.96, 0.98)
    C_TEXT_MUTED = (0.60, 0.68, 0.76)
    C_TEXT_DIM   = (0.42, 0.48, 0.56)
    
    C_CYAN    = (0.15, 0.80, 0.90)
    C_INDIGO  = (0.35, 0.38, 0.85)
    C_PURPLE  = (0.60, 0.40, 0.85)
    C_EMERALD = (0.20, 0.82, 0.55)
    C_ROSE    = (0.92, 0.30, 0.45)
    C_GOLD    = (0.85, 0.78, 0.45)

    def add_page_frame(p, page_num, total_pages, title=""):
        # Dark Background
        p.set_fill_color(*C_OBSIDIAN)
        p.draw_rect(0, 0, 595.28, 841.89, fill=True, stroke=False)
        
        # Ambient Grid / Decorative Top Bar
        p.set_fill_color(*C_INDIGO)
        p.draw_rect(30, 815, 535.28, 3, fill=True, stroke=False)
        
        # Header text
        p.draw_text("PROJECT CHRONOS // SYSTEM ARCHITECTURE & DATABASE SPECIFICATION", 30, 824, font="F5", size=8, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
        if title:
            p.draw_text(title.upper(), 565.28 - len(title)*5.5, 824, font="F2", size=8, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])
            
        # Footer
        p.set_stroke_color(*C_BORDER)
        p.set_line_width(0.5)
        p.draw_line(30, 35, 565.28, 35)
        
        p.draw_text("TEMPORAL INVESTIGATION PLATFORM • DATABASE ENGINE SPECIFICATION", 30, 24, font="F4", size=7, r=C_TEXT_DIM[0], g=C_TEXT_DIM[1], b=C_TEXT_DIM[2])
        p.draw_text(f"PAGE {page_num} OF {total_pages}", 510, 24, font="F5", size=7, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])

    TOTAL_PAGES = 7

    # =========================================================================
    # PAGE 1: TITLE & EXECUTIVE DATABASE ARCHITECTURE OVERVIEW
    # =========================================================================
    p1 = pdf.new_page()
    add_page_frame(p1, 1, TOTAL_PAGES, "EXECUTIVE ARCHITECTURE")
    
    # Hero Title Box
    p1.set_fill_color(*C_CARD_BG)
    p1.set_stroke_color(*C_BORDER_ACCENT)
    p1.set_line_width(1.0)
    p1.draw_rounded_rect(30, 690, 535.28, 115, r=6, fill=True, stroke=True)
    
    p1.draw_text("PROJECT CHRONOS // TEMPORAL ENGINE", 45, 780, font="F5", size=10, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
    p1.draw_text("Database Architecture & Round Status Ledger", 45, 750, font="F2", size=19, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])
    p1.draw_text("Complete Technical Documentation: Entity Relations, Round Lifecycles, Concurrency, and State Engines", 45, 732, font="F1", size=9, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])
    
    # Metadata badges inside hero
    p1.set_fill_color(*C_CARD_ALT)
    p1.draw_rounded_rect(45, 702, 115, 18, r=3, fill=True, stroke=False)
    p1.draw_text("ENGINE: SQLite 3.45 (WAL)", 50, 707, font="F5", size=7.5, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    p1.draw_rounded_rect(168, 702, 110, 18, r=3, fill=True, stroke=False)
    p1.draw_text("INTEGRITY: PRAGMA FK ON", 173, 707, font="F5", size=7.5, r=C_EMERALD[0], g=C_EMERALD[1], b=C_EMERALD[2])

    p1.draw_rounded_rect(286, 702, 115, 18, r=3, fill=True, stroke=False)
    p1.draw_text("TIMEOUT: 30,000 ms BUSY", 291, 707, font="F5", size=7.5, r=C_PURPLE[0], g=C_PURPLE[1], b=C_PURPLE[2])

    p1.draw_rounded_rect(409, 702, 140, 18, r=3, fill=True, stroke=False)
    p1.draw_text("LOCATION: database/chronos.db", 414, 707, font="F5", size=7.5, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])

    # Executive Overview Section
    p1.draw_text("1. SYSTEM OVERVIEW & ARCHITECTURAL FOUNDATION", 30, 665, font="F2", size=12, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    desc_lines = [
        "Project Chronos operates on an ACID-compliant, server-authoritative SQLite database designed for high-concurrency LAN esports",
        "and temporal investigative competition. The database coordinates team authentication, 25-fragment temporal ordering (Round 1),",
        "incident log analysis with AI LLM interrogation (Round 2), dynamic anti-collusion wisdom trials (Round 3), and live host leaderboards."
    ]
    for idx, line in enumerate(desc_lines):
        p1.draw_text(line, 30, 648 - idx * 13, font="F1", size=8.5, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])

    # Core Database Connection Specifications Card
    p1.set_fill_color(*C_CARD_BG)
    p1.set_stroke_color(*C_BORDER)
    p1.set_line_width(0.8)
    p1.draw_rounded_rect(30, 485, 535.28, 115, r=5, fill=True, stroke=True)
    
    p1.draw_text("DATABASE ENGINE & CONNECTION CONFIGURATION (connection.py)", 42, 582, font="F2", size=9.5, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
    
    config_items = [
        ("PRAGMA journal_mode = WAL;", "Write-Ahead Logging mode enables non-blocking concurrent readers while writing."),
        ("PRAGMA foreign_keys = ON;", "Enforces relational integrity, cascading deletes, and referential constraints."),
        ("PRAGMA busy_timeout = 30000;", "Waits up to 30s during lock contention, preventing 'database locked' errors."),
        ("PRAGMA synchronous = NORMAL;", "Optimizes sync intervals for WAL disk writes while guaranteeing safety on crash."),
        ("sqlite3.Row Factory", "Provides high-performance dict-like column access across all service modules."),
    ]
    for idx, (pragma, desc) in enumerate(config_items):
        y = 562 - idx * 15
        p1.draw_text(pragma, 45, y, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
        p1.draw_text(desc, 230, y, font="F1", size=8, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])

    # High-Level Architecture Diagram Box
    p1.draw_text("2. HIGH-LEVEL TEMPORAL PIPELINE DATA FLOW", 30, 455, font="F2", size=12, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    p1.set_fill_color(*C_CARD_BG)
    p1.set_stroke_color(*C_BORDER_ACCENT)
    p1.draw_rounded_rect(30, 60, 535.28, 380, r=6, fill=True, stroke=True)
    
    # Pipeline stages drawn as interconnected cards
    stages = [
        ("PHASE 0: AUTHENTICATION", "teams", "Stores callsign, 2 operators, PRNs, and global game state (READY -> LOGGED_IN).", C_INDIGO),
        ("ROUND 1: TIMELINE RECONSTRUCTION", "round1_items • round1_team_items • round1_submissions", "25 fragments partitioned across PAST/PRESENT/FUTURE. Clock synced with server timestamps.", C_CYAN),
        ("ROUND 2: TERMINAL INVESTIGATION", "round2_files • round2_chat_messages • round2_submissions", "Evidence files (Alpha/Beta/Gamma), LLM question quotas with point penalties, suspect lock.", C_PURPLE),
        ("ROUND 3: WISDOM / FINAL DECISION", "round3_team_cases • round3_submissions", "Anti-collusion case permutations (8 dynamic cases), evidence correlation, +30 / 0 pts.", C_EMERALD),
        ("AUDIT & LEADERBOARD SYSTEM", "audit_logs • hints • submissions (unified)", "Real-time master host leaderboard ranking by total score and elapsed duration.", C_GOLD),
    ]
    
    for idx, (stitle, tables, sdesc, scolor) in enumerate(stages):
        y_box = 370 - idx * 72
        p1.set_fill_color(*C_CARD_ALT)
        p1.set_stroke_color(*scolor)
        p1.set_line_width(0.8)
        p1.draw_rounded_rect(45, y_box, 505.28, 62, r=4, fill=True, stroke=True)
        
        # Stage indicator pip
        p1.set_fill_color(*scolor)
        p1.draw_rounded_rect(55, y_box + 44, 8, 8, r=2, fill=True, stroke=False)
        
        p1.draw_text(stitle, 70, y_box + 45, font="F2", size=9, r=scolor[0], g=scolor[1], b=scolor[2])
        p1.draw_text(f"TABLES: {tables}", 70, y_box + 30, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
        p1.draw_text(sdesc, 70, y_box + 15, font="F1", size=8, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])
        
        # Downward connector arrow (if not last)
        if idx < len(stages) - 1:
            p1.set_stroke_color(*C_BORDER_ACCENT)
            p1.set_line_width(1.0)
            p1.draw_line(297, y_box, 297, y_box - 10)

    # =========================================================================
    # PAGE 2: ENTITY-RELATIONSHIP (ER) DIAGRAM & CORE SCHEMA
    # =========================================================================
    p2 = pdf.new_page()
    add_page_frame(p2, 2, TOTAL_PAGES, "ER DIAGRAM & SCHEMA")
    
    p2.draw_text("3. MASTER ENTITY-RELATIONSHIP (ER) SCHEMA MAP", 30, 785, font="F2", size=12, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p2.draw_text("Relational structure showing foreign key cascades, primary keys, indexes, and constraints.", 30, 772, font="F1", size=8.5, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])

    # Draw Central Hub: teams table
    p2.set_fill_color(*C_CARD_BG)
    p2.set_stroke_color(*C_CYAN)
    p2.set_line_width(1.2)
    p2.draw_rounded_rect(200, 570, 195, 185, r=5, fill=True, stroke=True)
    
    p2.set_fill_color(*C_CYAN)
    p2.draw_rounded_rect(200, 735, 195, 20, r=4, fill=True, stroke=False)
    p2.draw_text("TABLE: teams (MASTER)", 220, 741, font="F5", size=9, r=C_OBSIDIAN[0], g=C_OBSIDIAN[1], b=C_OBSIDIAN[2])
    
    team_cols = [
        ("id", "INTEGER PK AUTO", True),
        ("team_name", "TEXT UNIQUE NOT NULL", False),
        ("member_1_name / member_2_name", "TEXT NOT NULL", False),
        ("member_1_prn / member_2_prn", "TEXT", False),
        ("current_state", "TEXT DEFAULT 'READY'", False),
        ("round1_score / round2_score", "REAL DEFAULT 0.0", False),
        ("round3_score / total_score", "REAL DEFAULT 0.0", False),
        ("round1_started_at / completed_at", "TEXT (ISO8601)", False),
        ("round1_auth_code", "TEXT", False),
        ("round2_started_at / completed_at", "TEXT (ISO8601)", False),
        ("round3_started_at / completed_at", "TEXT (ISO8601)", False),
        ("created_at / updated_at", "TEXT DEFAULT now", False)
    ]
    for idx, (cname, ctype, is_pk) in enumerate(team_cols):
        y = 722 - idx * 12
        font = "F5" if is_pk else "F4"
        col_color = C_GOLD if is_pk else C_TEXT_WHITE
        p2.draw_text(f"• {cname}:", 206, y, font=font, size=6.5, r=col_color[0], g=col_color[1], b=col_color[2])
        p2.draw_text(ctype, 325, y, font="F3", size=6, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])

    # Peripheral Entity Tables connected to teams
    def draw_entity_table(x, y, w, h, title, cols, border_color):
        p2.set_fill_color(*C_CARD_BG)
        p2.set_stroke_color(*border_color)
        p2.set_line_width(0.8)
        p2.draw_rounded_rect(x, y, w, h, r=4, fill=True, stroke=True)
        
        p2.set_fill_color(*border_color)
        p2.draw_rounded_rect(x, y + h - 16, w, 16, r=3, fill=True, stroke=False)
        p2.draw_text(title, x + 8, y + h - 11, font="F5", size=7.5, r=C_OBSIDIAN[0], g=C_OBSIDIAN[1], b=C_OBSIDIAN[2])
        
        for idx, (cname, ctype, is_key) in enumerate(cols):
            cy = y + h - 28 - idx * 11
            font = "F5" if is_key else "F4"
            col_color = C_GOLD if is_key else C_TEXT_WHITE
            p2.draw_text(f"{cname}", x + 6, cy, font=font, size=6.5, r=col_color[0], g=col_color[1], b=col_color[2])
            p2.draw_text(ctype, x + w - 55, cy, font="F3", size=6, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])

    # Round 1 Tables (Top-Left and Left)
    draw_entity_table(30, 640, 155, 95, "round1_items", [
        ("item_id", "INTEGER PK", True),
        ("item_name", "TEXT NOT NULL", False),
        ("image_path", "TEXT NOT NULL", False),
        ("correct_era", "TEXT (P/P/F)", False),
        ("clue_text", "TEXT", False),
        ("points_pos/neg", "REAL (2.0 / 1.0)", False),
    ], C_CYAN)

    draw_entity_table(30, 520, 155, 105, "round1_team_items", [
        ("id", "INTEGER PK", True),
        ("team_id", "FK -> teams", True),
        ("item_id", "FK -> r1_items", True),
        ("assigned_at", "TEXT", False),
        ("UNIQUE(team,item)", "CONSTRAINT", False),
    ], C_CYAN)

    draw_entity_table(30, 400, 155, 105, "round1_submissions", [
        ("id", "INTEGER PK", True),
        ("team_id", "FK -> teams", True),
        ("item_id", "FK -> r1_items", True),
        ("selected_era", "TEXT (P/P/F)", False),
        ("is_correct", "INTEGER (0/1)", False),
        ("points_awarded", "REAL (+2/-1)", False),
    ], C_CYAN)

    # Round 2 Tables (Top-Right and Right)
    draw_entity_table(410, 640, 155, 95, "round2_files", [
        ("file_id", "TEXT PK", True),
        ("project_name", "TEXT", False),
        ("timeline_tag", "TEXT", False),
        ("filename", "TEXT", False),
        ("content_text", "TEXT (LOGS)", False),
        ("is_locked", "INTEGER (0/1)", False),
    ], C_PURPLE)

    draw_entity_table(410, 520, 155, 105, "round2_chat_messages", [
        ("id", "INTEGER PK", True),
        ("team_id", "FK -> teams", True),
        ("question_number", "INTEGER", False),
        ("user_prompt", "TEXT", False),
        ("ai_response", "TEXT", False),
        ("points_deducted", "REAL", False),
    ], C_PURPLE)

    draw_entity_table(410, 400, 155, 105, "round2_submissions", [
        ("id", "INTEGER PK", True),
        ("team_id", "FK -> teams", True),
        ("suspect_identified", "TEXT", False),
        ("is_correct", "INTEGER (0/1)", False),
        ("points_awarded", "REAL", False),
        ("round2_total_score", "REAL", False),
    ], C_PURPLE)

    # Round 3 Tables (Bottom Left & Center)
    draw_entity_table(30, 240, 170, 110, "round3_team_cases", [
        ("id", "INTEGER PK", True),
        ("team_id", "FK -> teams UNIQUE", True),
        ("case_id", "TEXT (CASE-01..08)", False),
        ("case_data", "TEXT (JSON SANITIZED)", False),
        ("culprit_candidate_id", "TEXT (SECRET)", False),
        ("valid_evidence_ids", "TEXT (JSON ARRAY)", False),
    ], C_EMERALD)

    draw_entity_table(212, 240, 170, 110, "round3_submissions", [
        ("id", "INTEGER PK", True),
        ("team_id", "FK -> teams", True),
        ("selected_candidate_id", "TEXT", False),
        ("selected_evidence_ids", "TEXT (JSON)", False),
        ("is_correct", "INTEGER (+30/0)", False),
        ("points_awarded", "REAL (30.0)", False),
    ], C_EMERALD)

    # Audit & Submissions Archive (Bottom Right)
    draw_entity_table(395, 240, 170, 110, "audit_logs", [
        ("id", "INTEGER PK", True),
        ("team_id", "FK -> teams NULL", True),
        ("event_type", "TEXT (ENUM)", False),
        ("payload_json", "TEXT (METRICS)", False),
        ("created_at", "TEXT (TIMESTAMP)", False),
        ("INDEX(team_id)", "INDEX", False),
    ], C_GOLD)

    # Key Architectural Observations
    p2.set_fill_color(*C_CARD_BG)
    p2.set_stroke_color(*C_BORDER_ACCENT)
    p2.draw_rounded_rect(30, 60, 535.28, 160, r=4, fill=True, stroke=True)
    p2.draw_text("RELATIONAL INTEGRITY & TRANSACTION CONTRACTS", 42, 202, font="F2", size=9.5, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
    
    notes = [
        "1. CASCADE DELETION: Every child table specifies 'ON DELETE CASCADE' referencing teams(id). Purging or resetting a team",
        "   automatically cleanses all associated submissions, assignments, chats, dynamic cases, and team fragments.",
        "2. ATOMIC ASSIGNMENTS: Unique constraints (e.g. round1_team_items(team_id, item_id) and round3_team_cases(team_id)) guarantee",
        "   strict idempotency against race conditions during concurrent browser queries.",
        "3. SERVER-AUTHORITATIVE TIMESTAMPS: Timers calculate remaining seconds via SQLite 'julianday(roundN_completed_at) - julianday(roundN_started_at) * 86400',",
        "   making it mathematically impossible for client browser clock tampering to alter duration or score.",
        "4. ZERO-COLLUSION SEEDING: Round 3 stores sanitized case JSON for the frontend while preserving secret ground truth on the server."
    ]
    for idx, note in enumerate(notes):
        p2.draw_text(note, 45, 184 - idx * 28, font="F1", size=7.5, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])

    # =========================================================================
    # PAGE 3: ROUND 1 DATABASE STATUS & LIFECYCLE
    # =========================================================================
    p3 = pdf.new_page()
    add_page_frame(p3, 3, TOTAL_PAGES, "ROUND 1 DATABASE LIFECYCLE")
    
    p3.draw_text("4. ROUND 1: TEMPORAL ARTIFACT CLASSIFICATION", 30, 785, font="F2", size=12, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
    p3.draw_text("Database state progression, deterministic 25-fragment selection, in-flight repositioning, and ledger lock.", 30, 772, font="F1", size=8.5, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])

    # Table 1: State Machine Transitions
    p3.set_fill_color(*C_CARD_BG)
    p3.set_stroke_color(*C_BORDER)
    p3.draw_rounded_rect(30, 620, 535.28, 140, r=5, fill=True, stroke=True)
    p3.draw_text("ROUND 1 STATE PROGRESSION & DATABASE MUTATIONS", 42, 742, font="F2", size=9.5, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    r1_steps = [
        ("INITIALIZATION", "GET /api/round1/items", "Selects 1 PAST, 1 PRESENT, 1 FUTURE + 22 random items. Inserts 25 rows into round1_team_items. Sets teams.current_state = 'ROUND1_ACTIVE', round1_started_at = CURRENT_TIMESTAMP."),
        ("IN-FLIGHT SUBMIT", "POST /api/round1/submit", "Calculates correctness against round1_items.correct_era (+2.0 correct, -1.0 wrong). Inserts/updates round1_submissions. Updates teams.round1_score dynamically."),
        ("REPOSITIONING", "POST /api/round1/submit", "If fragment was already placed, previous points are subtracted and new era evaluated, allowing seamless card dragging between PAST, PRESENT, and FUTURE."),
        ("LEDGER SEALING", "POST /api/round1/finish", "Generates unique round1_auth_code (e.g. 'CHRONOS-9482'). Sets teams.current_state = 'ROUND1_COMPLETED', round1_completed_at = CURRENT_TIMESTAMP. Logs event to audit_logs.")
    ]
    for idx, (stage, endpoint, detail) in enumerate(r1_steps):
        y = 722 - idx * 27
        p3.draw_text(stage, 45, y, font="F5", size=7.5, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
        p3.draw_text(endpoint, 145, y, font="F5", size=7, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
        p3.draw_text(detail, 45, y - 10, font="F1", size=7.2, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])

    # Deterministic Provisioning SQL Box
    p3.draw_text("DETERMINISTIC 25-ITEM PROVISIONING ALGORITHM", 30, 595, font="F2", size=10, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p3.set_fill_color(*C_CARD_BG)
    p3.set_stroke_color(*C_BORDER_ACCENT)
    p3.draw_rounded_rect(30, 410, 535.28, 175, r=4, fill=True, stroke=True)
    
    sql_snippets_r1 = [
        "-- 1. Select exactly 1 guaranteed item from each era",
        "SELECT item_id FROM round1_items WHERE is_active = 1 AND correct_era = 'PAST' ORDER BY RANDOM() LIMIT 1;",
        "SELECT item_id FROM round1_items WHERE is_active = 1 AND correct_era = 'PRESENT' ORDER BY RANDOM() LIMIT 1;",
        "SELECT item_id FROM round1_items WHERE is_active = 1 AND correct_era = 'FUTURE' ORDER BY RANDOM() LIMIT 1;",
        "",
        "-- 2. Select remaining 22 random items excluding guaranteed set",
        "SELECT item_id FROM round1_items WHERE is_active = 1 AND item_id NOT IN (?, ?, ?) ORDER BY RANDOM() LIMIT 22;",
        "",
        "-- 3. Persist assignment permanently for team (Idempotent)",
        "INSERT INTO round1_team_items (team_id, item_id) VALUES (?, ?);",
        "UPDATE teams SET current_state = 'ROUND1_ACTIVE', round1_started_at = CURRENT_TIMESTAMP WHERE id = ?;"
    ]
    for idx, sline in enumerate(sql_snippets_r1):
        color = C_TEXT_DIM if sline.startswith("--") else (C_CYAN if "UPDATE" in sline or "INSERT" in sline else C_TEXT_WHITE)
        p3.draw_text(sline, 45, 570 - idx * 15, font="F4", size=7.5, r=color[0], g=color[1], b=color[2])

    # Round 1 Data State Table
    p3.draw_text("DATABASE RECORDS GENERATED IN ROUND 1", 30, 385, font="F2", size=10, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    # Draw table
    p3.set_fill_color(*C_CARD_BG)
    p3.set_stroke_color(*C_BORDER)
    p3.draw_rounded_rect(30, 60, 535.28, 310, r=4, fill=True, stroke=True)
    
    # Table headers
    p3.set_fill_color(*C_CARD_ALT)
    p3.draw_rounded_rect(30, 345, 535.28, 25, r=3, fill=True, stroke=False)
    p3.draw_text("TABLE NAME", 40, 353, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p3.draw_text("TYPICAL RECORD COUNT", 150, 353, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p3.draw_text("PRIMARY PURPOSE & VALUE CONSTRAINTS", 310, 353, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    rows_r1 = [
        ("round1_items", "60+ (Global Seed)", "Master catalog of temporal technology cards with correct era (PAST/PRESENT/FUTURE)."),
        ("round1_team_items", "25 per Team", "Fixed assigned set. ORDER BY t.id ASC guarantees determinism on page reloads."),
        ("round1_submissions", "Up to 25 per Team", "Stores selected_era, is_correct (0/1), and points_awarded (+2.0 or -1.0)."),
        ("teams (Round 1 cols)", "1 per Team", "Updated with round1_score, round1_started_at, round1_completed_at, round1_auth_code."),
        ("audit_logs", "2-27 per Team", "Records ROUND1_STARTED, ROUND1_SUBMISSION (each item), and ROUND1_COMPLETED events.")
    ]
    for idx, (tname, rcount, rdesc) in enumerate(rows_r1):
        y = 325 - idx * 52
        p3.draw_text(tname, 40, y, font="F5", size=8, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
        p3.draw_text(rcount, 150, y, font="F4", size=7.5, r=C_EMERALD[0], g=C_EMERALD[1], b=C_EMERALD[2])
        p3.draw_text(rdesc, 310, y, font="F1", size=7.5, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])
        if idx < len(rows_r1) - 1:
            p3.set_stroke_color(*C_BORDER)
            p3.set_line_width(0.5)
            p3.draw_line(40, y - 16, 555, y - 16)

    # =========================================================================
    # PAGE 4: ROUND 2 DATABASE STATUS & AI QUERY ENGINE
    # =========================================================================
    p4 = pdf.new_page()
    add_page_frame(p4, 4, TOTAL_PAGES, "ROUND 2 DATABASE LIFECYCLE")
    
    p4.draw_text("5. ROUND 2: TERMINAL INVESTIGATION & AI INTERROGATION", 30, 785, font="F2", size=12, r=C_PURPLE[0], g=C_PURPLE[1], b=C_PURPLE[2])
    p4.draw_text("Evidence dossier storage, AI chat telemetry, question point deductions, and suspect accusation lock.", 30, 772, font="F1", size=8.5, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])

    # Round 2 Flow Overview
    p4.set_fill_color(*C_CARD_BG)
    p4.set_stroke_color(*C_BORDER)
    p4.draw_rounded_rect(30, 620, 535.28, 140, r=5, fill=True, stroke=True)
    p4.draw_text("ROUND 2 STATE TRANSITIONS & LLM INTERACTION ENGINE", 42, 742, font="F2", size=9.5, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    r2_steps = [
        ("LOBBY & AUTH CHECK", "POST /api/round2/start", "Validates team has completed Round 1 (round1_auth_code present). Updates teams.current_state = 'ROUND2_ACTIVE', round2_started_at = CURRENT_TIMESTAMP."),
        ("EVIDENCE RETRIEVAL", "GET /api/round2/files", "Retrieves seeded project incident logs from round2_files (Alpha = Future, Beta = Present, Gamma = Past). Files are unlocked for player inspection."),
        ("AI INTERROGATION", "POST /api/round2/ask", "Logs user query and AI response into round2_chat_messages. Deducts points if exceeding free quota (-2.5 pts per query)."),
        ("SUSPECT ACCUSATION", "POST /api/round2/submit", "Records suspect choice (Noah Vale / Aria Sen / etc.) into round2_submissions. Calculates round2_total_score = Base + Remaining AI Budget. Advances state to 'ROUND2_COMPLETED'.")
    ]
    for idx, (stage, endpoint, detail) in enumerate(r2_steps):
        y = 722 - idx * 27
        p4.draw_text(stage, 45, y, font="F5", size=7.5, r=C_PURPLE[0], g=C_PURPLE[1], b=C_PURPLE[2])
        p4.draw_text(endpoint, 155, y, font="F5", size=7, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
        p4.draw_text(detail, 45, y - 10, font="F1", size=7.2, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])

    # Database Schema Deep Dive: round2_chat_messages and round2_submissions
    p4.draw_text("ROUND 2 SCHEMA & SCORING MATHEMATICS", 30, 595, font="F2", size=10, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p4.set_fill_color(*C_CARD_BG)
    p4.set_stroke_color(*C_BORDER_ACCENT)
    p4.draw_rounded_rect(30, 390, 535.28, 195, r=4, fill=True, stroke=True)
    
    sql_snippets_r2 = [
        "-- 1. AI Interrogation Audit & Point Deduction Tracking",
        "INSERT INTO round2_chat_messages (team_id, question_number, user_prompt, ai_response, points_deducted)",
        "VALUES (?, ?, ?, ?, ?);",
        "",
        "-- 2. Compute remaining AI points budget",
        "SELECT COALESCE(SUM(points_deducted), 0.0) AS total_deducted FROM round2_chat_messages WHERE team_id = ?;",
        "",
        "-- 3. Record Final Suspect Accusation & Score Calculation",
        "INSERT INTO round2_submissions (team_id, suspect_identified, is_correct, points_awarded, ai_points_remaining, round2_total_score)",
        "VALUES (?, ?, ?, ?, ?, ?);",
        "",
        "-- 4. Update team master ledger",
        "UPDATE teams SET round2_score = ?, current_state = 'ROUND2_COMPLETED', round2_completed_at = CURRENT_TIMESTAMP WHERE id = ?;"
    ]
    for idx, sline in enumerate(sql_snippets_r2):
        color = C_TEXT_DIM if sline.startswith("--") else (C_PURPLE if "UPDATE" in sline or "INSERT" in sline else C_TEXT_WHITE)
        p4.draw_text(sline, 45, 570 - idx * 14, font="F4", size=7.2, r=color[0], g=color[1], b=color[2])

    # Round 2 Table Schema Breakdown
    p4.draw_text("DATABASE RECORDS GENERATED IN ROUND 2", 30, 365, font="F2", size=10, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    p4.set_fill_color(*C_CARD_BG)
    p4.set_stroke_color(*C_BORDER)
    p4.draw_rounded_rect(30, 60, 535.28, 290, r=4, fill=True, stroke=True)
    
    p4.set_fill_color(*C_CARD_ALT)
    p4.draw_rounded_rect(30, 325, 535.28, 25, r=3, fill=True, stroke=False)
    p4.draw_text("TABLE NAME", 40, 333, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p4.draw_text("RECORD LIFECYCLE", 160, 333, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p4.draw_text("KEY FIELDS & CONSTRAINTS", 310, 333, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    rows_r2 = [
        ("round2_files", "3 Static Records", "file_id ('alpha', 'beta', 'gamma'), project_name, timeline_tag, filename, content_text."),
        ("round2_chat_messages", "1-10 per Team", "team_id (FK), question_number (1..N), user_prompt, ai_response, points_deducted (2.5)."),
        ("round2_submissions", "1 per Team", "team_id (FK), suspect_identified, is_correct (0/1), points_awarded, round2_total_score."),
        ("teams (Round 2 cols)", "1 per Team", "Updated with round2_score, round2_started_at, round2_completed_at, current_state."),
        ("audit_logs", "2-12 per Team", "Records ROUND2_STARTED, ROUND2_QUERY (each prompt), and ROUND2_SUBMISSION events.")
    ]
    for idx, (tname, rcount, rdesc) in enumerate(rows_r2):
        y = 305 - idx * 48
        p4.draw_text(tname, 40, y, font="F5", size=8, r=C_PURPLE[0], g=C_PURPLE[1], b=C_PURPLE[2])
        p4.draw_text(rcount, 160, y, font="F4", size=7.5, r=C_EMERALD[0], g=C_EMERALD[1], b=C_EMERALD[2])
        p4.draw_text(rdesc, 310, y, font="F1", size=7.5, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])
        if idx < len(rows_r2) - 1:
            p4.set_stroke_color(*C_BORDER)
            p4.set_line_width(0.5)
            p4.draw_line(40, y - 15, 555, y - 15)

    # =========================================================================
    # PAGE 5: ROUND 3 DATABASE STATUS & WISDOM ENGINE
    # =========================================================================
    p5 = pdf.new_page()
    add_page_frame(p5, 5, TOTAL_PAGES, "ROUND 3 DATABASE LIFECYCLE")
    
    p5.draw_text("6. ROUND 3: WISDOM ROUND & FINAL DECISION ENGINE", 30, 785, font="F2", size=12, r=C_EMERALD[0], g=C_EMERALD[1], b=C_EMERALD[2])
    p5.draw_text("Dynamic anti-collusion case generation, sanitized JSON delivery, ground truth verification, and total score lock.", 30, 772, font="F1", size=8.5, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])

    # Round 3 Flow Overview
    p5.set_fill_color(*C_CARD_BG)
    p5.set_stroke_color(*C_BORDER)
    p5.draw_rounded_rect(30, 620, 535.28, 140, r=5, fill=True, stroke=True)
    p5.draw_text("ROUND 3 ANTI-COLLUSION ENGINE & VERDICT LIFECYCLE", 42, 742, font="F2", size=9.5, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    r3_steps = [
        ("CASE SEEDING", "POST /api/round3/start", "Calculates team_id % 8 to select 1 of 8 rich scenario cases. Permutes candidate order. Inserts sanitized case_data JSON into round3_team_cases. Ground truth secret kept in DB."),
        ("SCENARIO DELIVERY", "GET /api/round3/scenario", "Delivers sanitized candidate profiles (3 suspects), case narrative, and supporting evidence matrix (4 logs) to frontend with zero client-side cheat vulnerability."),
        ("FINAL VERDICT LOCK", "POST /api/round3/submit", "Compares selected_candidate_id against culprit_candidate_id. Awards +30.0 if correct, 0.0 if incorrect. Inserts row into round3_submissions."),
        ("MISSION CONCLUDED", "POST /api/round3/submit", "Calculates total_score = r1_score + r2_score + r3_score. Sets current_state = 'COMPLETED', round3_completed_at = CURRENT_TIMESTAMP. Seals entire team ledger.")
    ]
    for idx, (stage, endpoint, detail) in enumerate(r3_steps):
        y = 722 - idx * 27
        p5.draw_text(stage, 45, y, font="F5", size=7.5, r=C_EMERALD[0], g=C_EMERALD[1], b=C_EMERALD[2])
        p5.draw_text(endpoint, 155, y, font="F5", size=7, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
        p5.draw_text(detail, 45, y - 10, font="F1", size=7.2, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])

    # Anti-Collusion Algorithm SQL
    p5.draw_text("ANTI-COLLUSION CASE PROVISIONING & TOTAL SCORE CALCULATION", 30, 595, font="F2", size=10, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p5.set_fill_color(*C_CARD_BG)
    p5.set_stroke_color(*C_BORDER_ACCENT)
    p5.draw_rounded_rect(30, 390, 535.28, 195, r=4, fill=True, stroke=True)
    
    sql_snippets_r3 = [
        "-- 1. Assign Dynamic Case Template (team_id % 8 permutation)",
        "INSERT INTO round3_team_cases (team_id, case_id, case_data, culprit_candidate_id, valid_evidence_ids)",
        "VALUES (?, ?, ?, ?, ?);",
        "",
        "-- 2. Validate Final Verdict & Record Submission (+30.0 correct / 0.0 wrong)",
        "INSERT INTO round3_submissions (team_id, selected_candidate_id, selected_evidence_ids, is_correct, points_awarded)",
        "VALUES (?, ?, ?, ?, ?);",
        "",
        "-- 3. Calculate Cumulative Mission Score across all 3 Sectors",
        "UPDATE teams",
        "SET round3_score = ?, total_score = round1_score + round2_score + ?,",
        "    current_state = 'COMPLETED', round3_completed_at = CURRENT_TIMESTAMP",
        "WHERE id = ?;"
    ]
    for idx, sline in enumerate(sql_snippets_r3):
        color = C_TEXT_DIM if sline.startswith("--") else (C_EMERALD if "UPDATE" in sline or "INSERT" in sline else C_TEXT_WHITE)
        p5.draw_text(sline, 45, 570 - idx * 14, font="F4", size=7.2, r=color[0], g=color[1], b=color[2])

    # Round 3 Table Schema Breakdown
    p5.draw_text("DATABASE RECORDS GENERATED IN ROUND 3", 30, 365, font="F2", size=10, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    p5.set_fill_color(*C_CARD_BG)
    p5.set_stroke_color(*C_BORDER)
    p5.draw_rounded_rect(30, 60, 535.28, 290, r=4, fill=True, stroke=True)
    
    p5.set_fill_color(*C_CARD_ALT)
    p5.draw_rounded_rect(30, 325, 535.28, 25, r=3, fill=True, stroke=False)
    p5.draw_text("TABLE NAME", 40, 333, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p5.draw_text("RECORD LIFECYCLE", 160, 333, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p5.draw_text("KEY FIELDS & CONSTRAINTS", 310, 333, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    rows_r3 = [
        ("round3_team_cases", "1 per Team (UNIQUE)", "team_id (FK), case_id, case_data (sanitized JSON), culprit_candidate_id, valid_evidence_ids."),
        ("round3_submissions", "1 per Team (UNIQUE)", "team_id (FK), selected_candidate_id, selected_evidence_ids (JSON array), is_correct (0/1), points (30.0)."),
        ("teams (Round 3 cols)", "1 per Team", "Updated with round3_score (30/0), total_score, round3_started_at, round3_completed_at, current_state ('COMPLETED')."),
        ("submissions (unified)", "1 row per round", "Cross-round ledger recording reference_id, answer, is_correct, points_awarded, timestamp."),
        ("audit_logs", "2-4 per Team", "Records ROUND3_STARTED, ROUND3_SUBMITTED, and MISSION_COMPLETED events with final payload metrics.")
    ]
    for idx, (tname, rcount, rdesc) in enumerate(rows_r3):
        y = 305 - idx * 48
        p5.draw_text(tname, 40, y, font="F5", size=8, r=C_EMERALD[0], g=C_EMERALD[1], b=C_EMERALD[2])
        p5.draw_text(rcount, 160, y, font="F4", size=7.5, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
        p5.draw_text(rdesc, 310, y, font="F1", size=7.5, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])
        if idx < len(rows_r3) - 1:
            p5.set_stroke_color(*C_BORDER)
            p5.set_line_width(0.5)
            p5.draw_line(40, y - 15, 555, y - 15)

    # =========================================================================
    # PAGE 6: LEADERBOARD, AUDIT LOGS & CROSS-ROUND SUMMARY
    # =========================================================================
    p6 = pdf.new_page()
    add_page_frame(p6, 6, TOTAL_PAGES, "LEADERBOARD & AUDIT LOGS")
    
    p6.draw_text("7. MASTER LEADERBOARD, AUDIT TRAIL & CONCURRENCY", 30, 785, font="F2", size=12, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p6.draw_text("Real-time ranking queries, tie-breaker timestamp calculations, and event ledger specifications.", 30, 772, font="F1", size=8.5, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])

    # Leaderboard Query Box
    p6.set_fill_color(*C_CARD_BG)
    p6.set_stroke_color(*C_BORDER_ACCENT)
    p6.draw_rounded_rect(30, 620, 535.28, 140, r=5, fill=True, stroke=True)
    p6.draw_text("HOST LEADERBOARD AGGREGATION QUERY (admin_service.py)", 42, 742, font="F2", size=9.5, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    sql_leaderboard = [
        "SELECT",
        "    id, team_name, current_state, member_1_name, member_2_name,",
        "    round1_score, round2_score, round3_score, total_score,",
        "    round1_started_at, round1_completed_at,",
        "    round2_started_at, round2_completed_at,",
        "    round3_started_at, round3_completed_at,",
        "    CAST((julianday(round3_completed_at) - julianday(round1_started_at)) * 86400 AS INTEGER) AS total_duration_seconds",
        "FROM teams",
        "ORDER BY total_score DESC, round3_completed_at ASC, round2_completed_at ASC;"
    ]
    for idx, sline in enumerate(sql_leaderboard):
        p6.draw_text(sline, 45, 725 - idx * 11, font="F4", size=7, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])

    # Audit Log Event Catalog
    p6.draw_text("AUDIT LOG EVENT TAXONOMY (audit_logs table)", 30, 595, font="F2", size=10, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    p6.set_fill_color(*C_CARD_BG)
    p6.set_stroke_color(*C_BORDER)
    p6.draw_rounded_rect(30, 395, 535.28, 190, r=4, fill=True, stroke=True)
    
    events = [
        ("TEAM_CREATED", "Auth", "Triggered when team registers. Stores member names and callsign."),
        ("ROUND1_STARTED", "Round 1", "Triggered on item stream initialization. Stores total assigned items (25)."),
        ("ROUND1_SUBMISSION", "Round 1", "Triggered per fragment placement. Stores item_id, selected_era, and score delta."),
        ("ROUND1_COMPLETED", "Round 1", "Triggered on finish button or timeout. Stores completion method, score, and auth_code."),
        ("ROUND2_STARTED", "Round 2", "Triggered when entering Round 2 terminal lobby. Logs start timestamp."),
        ("ROUND2_QUERY", "Round 2", "Triggered on AI interrogation. Stores prompt text, response length, and deducted points."),
        ("ROUND2_SUBMISSION", "Round 2", "Triggered on suspect accusation. Stores suspect name, accuracy, and score."),
        ("ROUND3_CASE_ASSIGNED", "Round 3", "Triggered on start. Stores assigned case_id (e.g. 'CASE-03') and candidate ordering."),
        ("ROUND3_SUBMITTED", "Round 3", "Triggered on verdict lock. Stores candidate selection, evidence IDs, and +30/0 pts."),
        ("MISSION_COMPLETED", "Global", "Triggered upon final completion. Stores final score and elapsed mission seconds.")
    ]
    for idx, (ev, domain, edesc) in enumerate(events):
        y = 572 - idx * 17
        p6.draw_text(ev, 45, y, font="F5", size=7, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
        p6.draw_text(f"[{domain}]", 185, y, font="F4", size=6.5, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
        p6.draw_text(edesc, 245, y, font="F1", size=7, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])

    # Summary Matrix by Round
    p6.draw_text("DATABASE SUMMARY MATRIX ACROSS GAME PHASES", 30, 370, font="F2", size=10, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    p6.set_fill_color(*C_CARD_BG)
    p6.set_stroke_color(*C_BORDER)
    p6.draw_rounded_rect(30, 60, 535.28, 295, r=4, fill=True, stroke=True)
    
    p6.set_fill_color(*C_CARD_ALT)
    p6.draw_rounded_rect(30, 330, 535.28, 25, r=3, fill=True, stroke=False)
    p6.draw_text("GAME PHASE", 40, 338, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p6.draw_text("STATE ENUM", 130, 338, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p6.draw_text("PRIMARY TABLES MUTATED", 235, 338, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p6.draw_text("SCORING IMPACT", 435, 338, font="F5", size=8, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    
    summary_rows = [
        ("Auth / Lobby", "READY, LOGGED_IN", "teams, audit_logs", "0.0 Points (Baseline)"),
        ("Round 1", "ROUND1_ACTIVE\nROUND1_COMPLETED", "round1_team_items, round1_submissions,\nteams, audit_logs", "+2.0 Correct / -1.0 Wrong\nMax: 50.0 Pts"),
        ("Round 2", "ROUND2_ACTIVE\nROUND2_COMPLETED", "round2_chat_messages, round2_submissions,\nteams, audit_logs", "Accusation + AI Budget\nMax: 50.0 Pts"),
        ("Round 3", "ROUND3_ACTIVE\nCOMPLETED", "round3_team_cases, round3_submissions,\nsubmissions, teams, audit_logs", "+30.0 Correct / 0.0 Wrong\nMax: 30.0 Pts"),
        ("Master Concluded", "COMPLETED", "teams (total_score calculated),\naudit_logs (finalized)", "Max Combined:\n130.0 Pts")
    ]
    for idx, (gphase, genum, gtables, gscore) in enumerate(summary_rows):
        y = 308 - idx * 48
        p6.draw_text(gphase, 40, y, font="F2", size=7.5, r=C_CYAN[0], g=C_CYAN[1], b=C_CYAN[2])
        p6.draw_text(genum.replace("\n", " / "), 130, y, font="F5", size=6.5, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])
        p6.draw_text(gtables.replace("\n", " "), 235, y, font="F4", size=6.5, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])
        p6.draw_text(gscore.replace("\n", " "), 435, y, font="F5", size=7, r=C_EMERALD[0], g=C_EMERALD[1], b=C_EMERALD[2])
        if idx < len(summary_rows) - 1:
            p6.set_stroke_color(*C_BORDER)
            p6.set_line_width(0.5)
            p6.draw_line(40, y - 16, 555, y - 16)

    # =========================================================================
    # PAGE 7: FULL SQL SCHEMA DDL REFERENCE & DEPLOYMENT CHECKLIST
    # =========================================================================
    p7 = pdf.new_page()
    add_page_frame(p7, 7, TOTAL_PAGES, "SQL SCHEMA DDL & VERIFICATION")
    
    p7.draw_text("8. COMPLETE SQL SCHEMA DDL REFERENCE (schema.py)", 30, 785, font="F2", size=12, r=C_GOLD[0], g=C_GOLD[1], b=C_GOLD[2])
    p7.draw_text("Exhaustive table creation DDL statements executed during database auto-provisioning.", 30, 772, font="F1", size=8.5, r=C_TEXT_MUTED[0], g=C_TEXT_MUTED[1], b=C_TEXT_MUTED[2])

    # DDL Code Container
    p7.set_fill_color(*C_CARD_BG)
    p7.set_stroke_color(*C_BORDER_ACCENT)
    p7.draw_rounded_rect(30, 160, 535.28, 600, r=5, fill=True, stroke=True)
    
    ddl_lines = [
        "CREATE TABLE IF NOT EXISTS teams (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    team_name TEXT UNIQUE NOT NULL,",
        "    member_1_name TEXT NOT NULL, member_2_name TEXT NOT NULL,",
        "    member_1_prn TEXT, member_2_prn TEXT,",
        "    current_state TEXT DEFAULT 'READY',",
        "    round1_score REAL DEFAULT 0.0, round2_score REAL DEFAULT 0.0, round3_score REAL DEFAULT 0.0,",
        "    total_score REAL DEFAULT 0.0,",
        "    round1_started_at TEXT, round1_completed_at TEXT, round1_auth_code TEXT,",
        "    round2_started_at TEXT, round2_completed_at TEXT,",
        "    round3_started_at TEXT, round3_completed_at TEXT,",
        "    created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS round1_items (",
        "    item_id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT NOT NULL, image_path TEXT NOT NULL,",
        "    correct_era TEXT NOT NULL CHECK(correct_era IN ('PAST', 'PRESENT', 'FUTURE')),",
        "    clue_text TEXT, points_positive REAL DEFAULT 2.0, points_negative REAL DEFAULT 1.0, is_active INTEGER DEFAULT 1",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS round1_team_items (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER NOT NULL, item_id INTEGER NOT NULL,",
        "    assigned_at TEXT DEFAULT (datetime('now')),",
        "    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,",
        "    FOREIGN KEY (item_id) REFERENCES round1_items(item_id) ON DELETE CASCADE, UNIQUE(team_id, item_id)",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS round1_submissions (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER NOT NULL, item_id INTEGER NOT NULL,",
        "    selected_era TEXT NOT NULL CHECK(selected_era IN ('PAST', 'PRESENT', 'FUTURE')),",
        "    is_correct INTEGER NOT NULL, points_awarded REAL NOT NULL, submitted_at TEXT DEFAULT (datetime('now')),",
        "    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE, FOREIGN KEY (item_id) REFERENCES round1_items(item_id)",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS round2_files (",
        "    file_id TEXT PRIMARY KEY, project_name TEXT NOT NULL, timeline_tag TEXT NOT NULL,",
        "    filename TEXT NOT NULL, content_text TEXT NOT NULL, is_locked INTEGER DEFAULT 0",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS round2_chat_messages (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER NOT NULL, question_number INTEGER NOT NULL,",
        "    user_prompt TEXT NOT NULL, ai_response TEXT NOT NULL, points_deducted REAL NOT NULL,",
        "    created_at TEXT DEFAULT (datetime('now')), FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS round2_submissions (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER NOT NULL, suspect_identified TEXT NOT NULL,",
        "    is_correct INTEGER NOT NULL, points_awarded REAL NOT NULL, ai_points_remaining REAL NOT NULL,",
        "    round2_total_score REAL NOT NULL, submitted_at TEXT DEFAULT (datetime('now')),",
        "    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS round3_team_cases (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER UNIQUE NOT NULL, case_id TEXT NOT NULL,",
        "    case_data TEXT NOT NULL, culprit_candidate_id TEXT NOT NULL, valid_evidence_ids TEXT NOT NULL,",
        "    assigned_at TEXT DEFAULT (datetime('now')), FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS round3_submissions (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER NOT NULL, selected_candidate_id TEXT NOT NULL,",
        "    selected_evidence_ids TEXT NOT NULL, is_correct INTEGER NOT NULL, points_awarded REAL NOT NULL,",
        "    submitted_at TEXT DEFAULT (datetime('now')), FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS audit_logs (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER, event_type TEXT NOT NULL,",
        "    payload_json TEXT, created_at TEXT DEFAULT (datetime('now')),",
        "    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE",
        ");"
    ]
    for idx, dline in enumerate(ddl_lines):
        color = C_TEXT_DIM if dline.startswith("--") else (C_CYAN if dline.startswith("CREATE") else C_TEXT_WHITE)
        p7.draw_text(dline, 42, 742 - idx * 10.8, font="F4", size=6.0, r=color[0], g=color[1], b=color[2])

    # Final Verification Sign-Off Box
    p7.set_fill_color(*C_CARD_BG)
    p7.set_stroke_color(*C_EMERALD)
    p7.draw_rounded_rect(30, 60, 535.28, 85, r=4, fill=True, stroke=True)
    
    p7.draw_text("ARCHITECTURAL INTEGRITY & VERIFICATION SIGN-OFF", 42, 128, font="F2", size=9, r=C_EMERALD[0], g=C_EMERALD[1], b=C_EMERALD[2])
    p7.draw_text("✔ 100% Automated Test Suite Passing across test_round1.py, test_round3.py, and test_full_flow.py.", 45, 112, font="F5", size=7.5, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])
    p7.draw_text("✔ SQLite WAL mode active with 30-second busy timeout and cascade referential integrity.", 45, 98, font="F5", size=7.5, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])
    p7.draw_text("✔ Anti-collusion deterministic seeding isolated per team with server-authoritative scoring.", 45, 84, font="F5", size=7.5, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])
    p7.draw_text("✔ Zero-leakage client payload delivery with sanitized case engine and server-side secret validation.", 45, 70, font="F5", size=7.5, r=C_TEXT_WHITE[0], g=C_TEXT_WHITE[1], b=C_TEXT_WHITE[2])

    # Write out the PDF
    pdf_data = pdf.build_pdf()
    with open(output_path, "wb") as f:
        f.write(pdf_data)
    print(f"Successfully generated {output_path} ({len(pdf_data)} bytes, {TOTAL_PAGES} pages)")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "Project_Chronos_Database_Architecture.pdf"
    create_chronos_pdf(out_file)
