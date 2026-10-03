"""
Project Chronos — Gemini AI Investigation Assistant Service
Provides restricted analytical hints based on unlocked files.
"""

import os
from typing import Dict, Any, List

class GeminiService:
    @staticmethod
    def generate_investigation_response(user_prompt: str, available_files: List[Dict[str, Any]]) -> str:
        """
        Generates restricted responses assisting players in cross-referencing audit logs
        without revealing the culprit directly.
        """
        # Built-in heuristic offline assistant in case Gemini API key is not configured
        prompt_lower = user_prompt.lower()
        
        if "alpha" in prompt_lower or "future" in prompt_lower or "21:11" in prompt_lower:
            return (
                "CHRONOS ANALYST: Project Alpha telemetry shows a root configuration modification committed at 21:11:04 UTC. "
                "Notice that this change preceded the anomalous chronon flux readings."
            )
        elif "beta" in prompt_lower or "incident" in prompt_lower:
            return (
                "CHRONOS ANALYST: Project Beta records an instantaneous stability drop immediately following the 21:11:04 override. "
                "Check which system credential authorized the algorithmic governor bypass."
            )
        elif "gamma" in prompt_lower or "access" in prompt_lower or "who" in prompt_lower:
            return (
                "CHRONOS ANALYST: Project Gamma access history logs an authenticated session on Terminal Node Gamma-7 under a Level-5 cryptographic token."
            )
        else:
            return (
                "CHRONOS ANALYST: Focus your inquiry on correlating the timestamp of the configuration rewrite in Alpha with the biometric signatures logged in Gamma."
            )
