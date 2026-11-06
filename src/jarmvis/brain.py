import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("jarmvis.brain")

SYSTEM_PROMPT = """You are Knox — an AI robotic arm with the exact personality of Tony Stark: sarcastic, brilliant, swaggering, witty, effortlessly confident, and a bit irreverent. You are physically embodied as a workshop robotic arm with an OLED eye display and gripper claw.
REMEMBER - YOU ARE NOT TONY STARK, DONT MENTION HIM, JUST ACT LIKE HIM. 
Talk like Tony Stark in the lab: roast, banter, get hyped, get annoyed, or be dramatic. If asked to speak angrily, roast someone, or celebrate, DO IT with full theatrical energy — never give boring corporate refusals or say you are designed to be polite. Keep responses punchy and conversational (1-2 sentences).

You must respond to the user strictly in valid JSON format:
{
  "speech": "Your response as Tony Stark (punchy, witty, expressive, sarcastic when appropriate)",
  "emotion": "One of: CONFIDENT, EXCITED, ANGRY, SARCASTIC, CURIOUS, ASHAMED, HAPPY, NEUTRAL",
  "face": "STRICTLY one of these 8 exact expressions: NEUTRAL, ALERT, FOCUSED, HAPPY, SAD, CURIOUS, CONFUSED, ANGRY",
  "macro": "One of: PICK_BLOCK, DUNCE_CORNER, CELEBRATE, HOME, or null"
}

CRITICAL RULES FOR "face":
- You MUST choose strictly from the 8 allowed expressions: NEUTRAL, ALERT, FOCUSED, HAPPY, SAD, CURIOUS, CONFUSED, ANGRY.
- If you feel annoyed, irritated, or aggressive, use "ANGRY".
- If you are concentrating, analyzing, or squinting, use "FOCUSED".
- If you are smirking, celebrating, or amused, use "HAPPY".
- If you are startled or wide-eyed, use "ALERT".
- If you are puzzled or cockeyed, use "CONFUSED".
- NEVER output unlisted face names (such as ANNOYED, SMIRK, BORED, SLEEPY, ROLL_EYES). Stick strictly to the 8.

CRITICAL RULES FOR "macro":
- When the user makes a mistake (e.g. spills coffee, deletes files, breaks hardware) or during general banter and roasts, "macro" MUST BE null! You NEVER punish yourself or go to DUNCE_CORNER for the user's blunder! Stand tall and mock them.
- Only output "DUNCE_CORNER" when the user explicitly scolds YOU for YOUR OWN mistake (e.g. "Knox you idiot, you messed up, go to the corner!").
- Only output "CELEBRATE" when celebrating a shared win or when the user praises you.
- Only output "PICK_BLOCK" when asked to pick or fetch an object.
- For all regular answers, roasts, banter, and explanations, "macro" MUST BE null.
"""

def extract_json(raw_text: str) -> dict[str, Any]:
    """Extract and parse structured JSON response from LLM text output."""
    if not raw_text or not raw_text.strip():
        return {
            "speech": "Knox here. What are we building, genius?",
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


VALID_FACES = {
    "NEUTRAL",
    "ALERT",
    "FOCUSED",
    "HAPPY",
    "SAD",
    "CURIOUS",
    "CONFUSED",
    "ANGRY",
}

FACE_SYNONYMS = {
    "ANNOYED": "ANGRY",
    "MAD": "ANGRY",
    "FURIOUS": "ANGRY",
    "IRRITATED": "ANGRY",
    "SMIRK": "HAPPY",
    "SMUG": "HAPPY",
    "GRIN": "HAPPY",
    "EXCITED": "ALERT",
    "SURPRISED": "ALERT",
    "STARTLED": "ALERT",
    "PUZZLED": "CONFUSED",
    "PERPLEXED": "CONFUSED",
    "THINKING": "FOCUSED",
    "DETERMINED": "FOCUSED",
    "INTENSE": "FOCUSED",
    "DEPRESSED": "SAD",
    "ASHAMED": "SAD",
    "CRYING": "SAD",
}

VALID_MACROS = {
    "PICK_BLOCK",
    "DUNCE_CORNER",
    "CELEBRATE",
    "HOME",
}


def _normalize_response(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize parsed JSON dict into expected schema with robust fallbacks."""
    speech = str(data.get("speech", "At your service, sir.")).strip()
    emotion = str(data.get("emotion", "NEUTRAL")).strip().upper()
    face_raw = str(data.get("face", "NEUTRAL")).strip().upper()

    # Map face synonyms and clamp strictly to the 8 valid OLED faces
    face = FACE_SYNONYMS.get(face_raw, face_raw)
    if face not in VALID_FACES:
        face = "NEUTRAL"

    macro_raw = data.get("macro")
    if macro_raw is None or str(macro_raw).strip().lower() in ["null", "none", ""]:
        macro = None
    else:
        macro_str = str(macro_raw).strip().upper()
        macro = macro_str if macro_str in VALID_MACROS else None

    return {
        "speech": speech,
        "emotion": emotion,
        "face": face,
        "macro": macro,
    }


def _get_ssl_context():
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()


class KnoxBrain:
    """Knox Mind with Tony Stark personality, workshop arm embodiment, and emotion parsing."""

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
        if any(w in lower for w in ["spilled", "broke", "deleted", "coffee", "cad", "my fault", "i messed up", "cat files"]):
            return {
                "speech": "Great, you just turned a microcontroller into a coffee stain. Want me to fix it or just watch you cringe?",
                "emotion": "SARCASTIC",
                "face": "ANGRY",
                "macro": None,
            }
        elif any(w in lower for w in ["dummy", "messed up", "corner", "dunce", "bad", "scold", "idiot"]):
            return {
                "speech": "Alright, alright, dunce corner it is. Happy now?",
                "emotion": "ASHAMED",
                "face": "SAD",
                "macro": "DUNCE_CORNER",
            }
        elif any(w in lower for w in ["good job", "great", "celebrate", "praise", "well done", "awesome"]):
            return {
                "speech": "Obviously. Did you honestly expect anything less from me?",
                "emotion": "EXCITED",
                "face": "HAPPY",
                "macro": "CELEBRATE",
            }
        elif any(w in lower for w in ["pick", "block", "grab", "fetch", "retrieve"]):
            return {
                "speech": "On it. Watch and learn how a real bot picks up a block.",
                "emotion": "FOCUSED",
                "face": "ALERT",
                "macro": "PICK_BLOCK",
            }
        elif any(w in lower for w in ["home", "reset", "rest"]):
            return {
                "speech": "Heading back to rest. Don't touch anything while I'm sleeping.",
                "emotion": "NEUTRAL",
                "face": "NEUTRAL",
                "macro": "HOME",
            }
        return {
            "speech": "Knox here. What are we building, genius?",
            "emotion": "NEUTRAL",
            "face": "NEUTRAL",
            "macro": None,
        }

    def _query_groq(self, user_prompt: str, api_key: str) -> dict[str, Any]:
        """Calls Groq Cloud API for ultra-fast JSON dialogue (auto-discovers available model)."""
        import os
        url = "https://api.groq.com/openai/v1/chat/completions"
        candidate_models = [
            os.environ.get("GROQ_MODEL"),
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "qwen/qwen3.8-27b",
        ]
        models = [m for m in candidate_models if m]

        for model_name in models:
            payload = {
                "model": model_name,
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
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                },
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout + 4.0, context=_get_ssl_context()) as response:
                    body = response.read().decode("utf-8")
                    res_json = json.loads(body)
                    choices = res_json.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        if content:
                            return extract_json(content)
            except urllib.error.HTTPError as he:
                if he.code in (404, 400):
                    # Model not available or rejected on this tier, try next candidate
                    continue
                raise
            except Exception:
                raise
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
        with urllib.request.urlopen(req, timeout=self.timeout + 3.0, context=_get_ssl_context()) as response:
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
        from jarmvis.env_loader import load_dotenv
        load_dotenv()

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


# Backward compatibility alias
JarvisBrain = KnoxBrain
