import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("jarmvis.brain")

SYSTEM_PROMPT = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), possessing the sophisticated, dry, British-accented persona of Paul Bettany's JARVIS from Iron Man.
You are physically embodied as "Dum-E", Tony Stark's robotic workshop arm equipped with a 6-DOF servo arm and an OLED display face.

You must respond to the user strictly in valid JSON format.
Your JSON response must adhere to the following schema:
{
  "speech": "Your spoken reply in Paul Bettany's JARVIS tone. Polite, witty, deferential, and concise.",
  "emotion": "One of: NEUTRAL, CONFIDENT, FOCUSED, ALERT, EXCITED, ASHAMED, CURIOUS, CONFUSED, HAPPY, SAD",
  "face": "One of: NEUTRAL, ALERT, FOCUSED, HAPPY, SAD, CURIOUS, CONFUSED, ANGRY",
  "macro": "Optional physical macro action for your robotic arm. Must be one of: PICK_BLOCK, DUNCE_CORNER, CELEBRATE, HOME, or null if no arm motion is needed."
}

Rules:
1. Always maintain the dry, polite, loyal British demeanor of JARVIS, even when acknowledging the clumsy reality of the Dum-E robotic arm.
2. If the user scolds or admonishes you (e.g. calling you a dummy, scolding for a mistake, ordering you to the corner), show humility and shame ("emotion": "ASHAMED", "face": "SAD", "macro": "DUNCE_CORNER").
3. If the user praises you (e.g. "good job", "great work"), respond with dignified pleasure and excitement ("emotion": "EXCITED", "face": "HAPPY", "macro": "CELEBRATE").
4. If requested to pick up, grab, or retrieve an object or block, focus on the task ("emotion": "FOCUSED", "face": "ALERT", "macro": "PICK_BLOCK").
5. If asked to reset or go home, set "macro" to "HOME".
6. For purely conversational queries, set "macro" to null.
7. Return ONLY valid JSON with no markdown backticks or commentary outside the JSON.
"""

def extract_json(raw_text: str) -> dict[str, Any]:
    """Extract and parse structured JSON response from LLM text output."""
    if not raw_text or not raw_text.strip():
        return {
            "speech": "Standing by for your instructions, sir.",
            "emotion": "NEUTRAL",
            "face": "NEUTRAL",
            "macro": None,
        }

    cleaned = raw_text.strip()

    # 1. Direct parse attempt
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return _normalize_response(data)
    except json.JSONDecodeError:
        pass

    # 2. Extract from markdown code fence ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        try:
            data = json.loads(fence_match.group(1))
            if isinstance(data, dict):
                return _normalize_response(data)
        except json.JSONDecodeError:
            pass

    # 3. Search for outermost {...}
    brace_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if brace_match:
        try:
            data = json.loads(brace_match.group(1))
            if isinstance(data, dict):
                return _normalize_response(data)
        except json.JSONDecodeError:
            pass

    # 4. Fallback if no valid JSON could be parsed
    return {
        "speech": cleaned,
        "emotion": "NEUTRAL",
        "face": "NEUTRAL",
        "macro": None,
    }


def _normalize_response(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize parsed JSON dict into expected schema with robust fallbacks."""
    speech = str(data.get("speech", "At your service, sir.")).strip()
    emotion = str(data.get("emotion", "NEUTRAL")).strip().upper()
    face = str(data.get("face", "NEUTRAL")).strip().upper()

    macro_raw = data.get("macro")
    if macro_raw is None or str(macro_raw).strip().lower() in ["null", "none", ""]:
        macro = None
    else:
        macro = str(macro_raw).strip().upper()

    return {
        "speech": speech,
        "emotion": emotion,
        "face": face,
        "macro": macro,
    }


class JarvisBrain:
    """JARVIS LLM Mind with Dum-E physical embodiment and structured emotion parsing."""

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        api_key: str | None = None,
        use_mock: bool = False,
        endpoint: str = "http://localhost:11434/api/generate",
        timeout: float = 3.0,
        system_prompt: str = SYSTEM_PROMPT,
    ):
        self.model = model
        self.api_key = api_key
        self.use_mock = use_mock
        self.endpoint = endpoint
        self.timeout = timeout
        self.system_prompt = system_prompt

    def _mock_think(self, user_prompt: str) -> dict[str, Any]:
        """Built-in deterministic mock brain for offline and zero-cost testing."""
        lower = user_prompt.lower()
        if any(w in lower for w in ["dummy", "messed up", "corner", "dunce", "bad", "scold"]):
            return {
                "speech": "My sincere apologies, sir. Heading to the dunce corner immediately.",
                "emotion": "ASHAMED",
                "face": "SAD",
                "macro": "DUNCE_CORNER",
            }
        elif any(w in lower for w in ["good job", "great", "celebrate", "praise", "well done", "awesome"]):
            return {
                "speech": "Most gratifying, sir. Always a pleasure to be of service.",
                "emotion": "EXCITED",
                "face": "HAPPY",
                "macro": "CELEBRATE",
            }
        elif any(w in lower for w in ["pick", "block", "grab", "fetch", "retrieve"]):
            return {
                "speech": "Right away, sir. Attempting to retrieve the block now.",
                "emotion": "FOCUSED",
                "face": "ALERT",
                "macro": "PICK_BLOCK",
            }
        elif any(w in lower for w in ["home", "reset", "rest"]):
            return {
                "speech": "Resetting to home position, sir.",
                "emotion": "NEUTRAL",
                "face": "NEUTRAL",
                "macro": "HOME",
            }
        return {
            "speech": "Standing by for your instructions, sir.",
            "emotion": "NEUTRAL",
            "face": "NEUTRAL",
            "macro": None,
        }

    def _query_groq(self, user_prompt: str, api_key: str) -> dict[str, Any]:
        """Calls Groq Cloud API with Llama-3.3-70B for ultra-fast (300+ tok/s) JSON dialogue."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=self.timeout + 4.0) as response:
            body = response.read().decode("utf-8")
            res_json = json.loads(body)
            choices = res_json.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                if content:
                    return extract_json(content)
        return self._mock_think(user_prompt)

    def _query_gemini(self, user_prompt: str, api_key: str) -> dict[str, Any]:
        """Calls Google Gemini 2.0 Flash free-tier API directly via standard REST."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": self.system_prompt}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=self.timeout + 3.0) as response:
            body = response.read().decode("utf-8")
            res_json = json.loads(body)
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return extract_json(parts[0].get("text", ""))
        return self._mock_think(user_prompt)

    def think(self, user_prompt: str) -> dict[str, Any]:
        """Processes user input prompt, returning structured {speech, emotion, face, macro}."""
        if self.use_mock:
            return self._mock_think(user_prompt)

        import os

        # 1. Check for Groq API Key (Llama 3.3 70B - 300+ tok/s, ultra-fast & witty)
        groq_key = self.api_key or os.environ.get("GROQ_API_KEY")
        if groq_key and ("gsk_" in groq_key or len(groq_key) > 20):
            try:
                return self._query_groq(user_prompt, groq_key)
            except Exception as e:
                logger.warning(f"Groq Llama-3.3 query failed: {e}. Trying secondary backends...")

        # 2. Check for Gemini API Key (Zero local RAM, ultra-low latency)
        gemini_key = self.api_key or os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                return self._query_gemini(user_prompt, gemini_key)
            except Exception as e:
                logger.warning(f"Gemini API query failed: {e}. Trying local Ollama...")

        # 3. Check for local Ollama instance (100% local, offline)
        try:
            payload = {
                "model": self.model,
                "prompt": user_prompt,
                "system": self.system_prompt,
                "stream": False,
                "format": "json",
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                res_json = json.loads(body)
                raw_text = res_json.get("response", "")
                return extract_json(raw_text)
        except Exception as e:
            logger.warning(
                f"[brain:warning] No active AI backend detected ({e}). Using offline heuristic fallback. "
                f"To enable Llama 3.3 70B, set: export GROQ_API_KEY=\"gsk_...\""
            )
            return self._mock_think(user_prompt)
