"""Server-side Groq chat. Credentials never enter responses or downloadable files."""
import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from collections import OrderedDict, deque
from datetime import datetime, timezone


class AIError(Exception):
    def __init__(self, status, message, retry_after=None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.retry_after = retry_after


class NexusAI:
    MODEL = "openai/gpt-oss-120b"
    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
    SYSTEM = (
        "You are OmniNexus, a helpful assistant powered by GPT-OSS on Groq. "
        "Answer accurately in the user's language; use clear natural Arabic when asked in Arabic. "
        "Be concise unless the user asks for detail. Admit uncertainty. "
        "You have no live web browsing, terminal, file access, or tool execution in this chat. "
        "Never claim to have run tools, scanned systems, or read files you have not been given. "
        "The website has a separate project-files download section. "
        "Do not claim to be ChatGPT or the assistant that built this site. "
        "Give the final answer without private reasoning or internal analysis."
    )

    def __init__(self):
        self.sessions = OrderedDict()
        self.inflight = set()
        self.lock = threading.RLock()
        self.requests = deque()
        self.daily_count = 0
        self.day = ""

    @property
    def configured(self):
        return bool(os.environ.get("GROQ_API_KEY", "").strip())

    def _cleanup(self):
        now = time.monotonic()
        for owner, entry in list(self.sessions.items()):
            if now - entry["time"] > 3600 and owner not in self.inflight:
                del self.sessions[owner]
        while len(self.sessions) > 128:
            removable = next((k for k in self.sessions if k not in self.inflight), None)
            if removable is None:
                break
            del self.sessions[removable]

    def _reserve(self, owner):
        now = time.monotonic()
        self._cleanup()
        if owner in self.inflight:
            raise AIError(409, "في رسالة عم تنعالج. انتظر الرد قبل إرسال رسالة جديدة.")
        day = datetime.now(timezone.utc).date().isoformat()
        if self.day != day:
            self.day, self.daily_count = day, 0
        while self.requests and now - self.requests[0] >= 60:
            self.requests.popleft()
        if len(self.requests) >= 10:
            raise AIError(429, "المحادثة مشغولة حاليًا. جرّب بعد دقيقة.", 60)
        if self.daily_count >= 300:
            raise AIError(429, "وصل الموقع لحدّه اليومي. جرّب بكرا.", 3600)
        self.requests.append(now)
        self.daily_count += 1
        self.inflight.add(owner)
        entry = self.sessions.get(owner, {"turns": []})
        return list(entry["turns"])

    def _complete(self, messages):
        payload = {
            "model": self.MODEL,
            "messages": messages,
            "max_completion_tokens": 2048,
            "reasoning_effort": "low",
            "include_reasoning": False,
            "stream": False,
        }
        request = urllib.request.Request(
            self.ENDPOINT,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + os.environ["GROQ_API_KEY"].strip(),
                "Content-Type": "application/json",
                "User-Agent": "OmniNexus/12",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.loads(response.read(1_000_000))
        except urllib.error.HTTPError as error:
            if error.code == 429:
                raise AIError(429, "وصلنا لحد استخدام النموذج المجاني. جرّب لاحقًا.", 60) from None
            if error.code in (401, 403):
                raise AIError(503, "تعذّر تفعيل اتصال الذكاء الاصطناعي. يلزم مراجعة إعدادات الخدمة.") from None
            raise AIError(502, "خدمة الذكاء الاصطناعي غير متاحة مؤقتًا. جرّب بعد قليل.") from None
        except (TimeoutError, socket.timeout):
            raise AIError(504, "الرد أخذ وقتًا أطول من المتوقع. جرّب مرة ثانية.") from None
        except (urllib.error.URLError, OSError, ValueError):
            raise AIError(502, "تعذّر الاتصال بخدمة الذكاء الاصطناعي. جرّب لاحقًا.") from None
        try:
            choice = data["choices"][0]
            answer = choice["message"].get("content")
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError()
            return answer.strip(), choice.get("finish_reason") == "length"
        except (KeyError, IndexError, TypeError, ValueError):
            raise AIError(502, "ما وصل رد مكتمل. جرّب سؤالًا أقصر.") from None

    def ask(self, question, owner):
        if not isinstance(question, str) or not question.strip() or len(question) > 4000:
            raise AIError(422, "اكتب رسالة بين 1 و4000 حرف.")
        if not self.configured:
            raise AIError(503, "المحادثة قيد التجهيز. جرّب لاحقًا.")
        with self.lock:
            turns = self._reserve(owner)
        try:
            # Keep recent complete turns within the free tier's modest token allowance.
            context, remaining = [], 2200
            for turn in reversed(turns[-6:]):
                cost = len(turn[0]) + len(turn[1])
                if cost > remaining:
                    break
                context[0:0] = [{"role": "user", "content": turn[0]},
                                {"role": "assistant", "content": turn[1]}]
                remaining -= cost
            messages = [{"role": "system", "content": self.SYSTEM}] + context
            messages.append({"role": "user", "content": question.strip()})
            answer, truncated = self._complete(messages)
            with self.lock:
                turns.append((question.strip(), answer))
                self.sessions[owner] = {"turns": turns[-6:], "time": time.monotonic()}
                self.sessions.move_to_end(owner)
                self._cleanup()
            return {"answer": answer, "mode": "ai", "model": self.MODEL,
                    "provider": "Groq", "truncated": truncated,
                    "timestamp": datetime.now(timezone.utc).isoformat()}
        finally:
            with self.lock:
                self.inflight.discard(owner)

    def reset(self, owner):
        with self.lock:
            if owner in self.inflight:
                raise AIError(409, "انتظر اكتمال الرد قبل بدء محادثة جديدة.")
            self.sessions.pop(owner, None)

    def search(self, owner, query):
        with self.lock:
            self._cleanup()
            turns = self.sessions.get(owner, {}).get("turns", [])
            return [{"content": f"Q: {q}\nA: {a}"} for q, a in turns
                    if query.casefold() in (q + a).casefold()][:5]
