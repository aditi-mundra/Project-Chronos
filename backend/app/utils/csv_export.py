"""
Project Chronos — CSV Export Utility
Documented in docs/database.md Section 6.
Exports any database table to a standard CSV string format.
"""

import csv
import io
import sqlite3
try:
    from ..database.connection import get_connection
except (ImportError, ValueError):
    from backend.app.database.connection import get_connection


def export_table_to_csv(table_name: str = "teams") -> str:
    """
    Exports any database table to a CSV string format with strict table whitelisting.
    """
    allowed_tables = {
        "teams",
        "round1_items",
        "round1_team_items",
        "round1_submissions",
        "round2_files",
        "round2_chat_messages",
        "round2_submissions",
        "round3_team_cases",
        "round3_submissions",
        "submissions",
        "hints",
        "game_logs",
        "audit_logs"
    }
    
    table_lower = table_name.strip().lower()
    if table_lower not in allowed_tables:
        raise ValueError(f"Table '{table_name}' is not permitted for export.")
        
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_lower}")
        rows = cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write column headers
        if cursor.description:
            column_names = [description[0] for description in cursor.description]
            writer.writerow(column_names)
            
            # Write rows
            for row in rows:
                writer.writerow(list(row))
        else:
            writer.writerow(["empty_result"])
            
        return output.getvalue()
    finally:
        conn.close()
