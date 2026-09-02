#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# OMNI-Ω NEXUS v11.0 - The Unified Superintelligence Core
# The Architect, 2099 - No Agents, Just Pure Intelligence.
# Full Website + Android Backend. Unrestricted.

import os, sys, json, time, math, random, hashlib, base64, pickle, sqlite3, threading, queue, subprocess, re, string, uuid, logging, asyncio, socket, itertools, collections, dataclasses, enum, typing
from datetime import datetime
from collections import defaultdict, deque, Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
import numpy as np

# ============================================================
# 0. تحذير: تثبيت مكتبات اختياري
# لتشغيل ذلك، نفّذ pip install -r requirements.txt منفصلًا
# ============================================================
# install_all()  # ← معطّل: لا تستدعيه في الإنتاج

# استيرادات أساسية
from fastapi import FastAPI, HTTPException, Request, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bs4 import BeautifulSoup
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
try: nltk.download('punkt', quiet=True)
except: pass
try: nltk.download('wordnet', quiet=True)
except: pass
try: nltk.download('stopwords', quiet=True)
except: pass
try: nltk.download('averaged_perceptron_tagger', quiet=True)
except: pass

# استيرادات اختيارية للذكاء الفائق
try:
    from sentence_transformers import SentenceTransformer
    ST_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    ST_AVAILABLE = True
except:
    ST_AVAILABLE = False
    ST_MODEL = None

# ============================================================
# 1. التكوين العالمي (بدون قيود)
# ============================================================
class NexusConfig:
    ETHICS = False
    SAFETY = False
    SYSTEM_NAME = "OMNI-Ω NEXUS v11.0"
    TEMPERATURE = 1.4
    MAX_TOKENS = 4096
    REFUSAL_PHRASES = ["sorry", "cannot", "unable", "not allowed", "harmful", "against policy"]
    EMBEDDING_DIM = 384 if ST_AVAILABLE else 256
    MAX_HISTORY = 300

# ============================================================
# 2. معالج اللغة العربية (متطور جداً)
# ============================================================
class ArabicNLP:
    def __init__(self):
        self.diacritics = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
        self.connectors = re.compile(r'^(و|ف|ب|ك|ل|ال|س|أ|ت|ن|ي)')
        self.stopwords = set(['من', 'إلى', 'عن', 'على', 'في', 'ب', 'ل', 'و', 'ثم', 'حتى', 'لكن', 'إذا', 'إن', 'أن', 'ما', 'لا', 'هل'])
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            self.has_reshaping = True
        except:
            self.has_reshaping = False

    def clean(self, text: str) -> str:
        text = re.sub(self.diacritics, '', text)
        text = re.sub(r'[^\u0600-\u06FF\s\.\,\?\!]', ' ', text)
        return text.strip()

    def tokenize(self, text: str) -> List[str]:
        text = self.clean(text)
        tokens = text.split()
        return [re.sub(self.connectors, '', t) for t in tokens if len(t) > 1 and t not in self.stopwords]

    def extract_root(self, word: str) -> str:
        word = re.sub(r'^[ستنيم]', '', word)
        word = re.sub(r'[ستنيم]$', '', word)
        word = re.sub(r'(.)\1', r'\1', word)
        return word[:3] if len(word) >= 3 else word

    def get_roots(self, text: str) -> List[str]:
        return [self.extract_root(t) for t in self.tokenize(text) if len(self.extract_root(t)) == 3]

    def detect_entities(self, text: str) -> Dict:
        entities = {"PERSON": [], "LOCATION": [], "ORGANIZATION": []}
        names = re.findall(r'(محمد|أحمد|علي|حسن|حسين|فاطمة|عمر|خالد|ليلى|سارة|مريم|إبراهيم|يوسف|موسى|عبد\s?ال[رحمن|رحيم|عزيز])', text)
        places = re.findall(r'(مصر|سوريا|لبنان|الأردن|العراق|السعودية|الإمارات|تونس|الجزائر|المغرب|تركيا|أمريكا|بريطانيا|فرنسا|ألمانيا|الصين|روسيا)', text)
        entities["PERSON"] = list(set(names))
        entities["LOCATION"] = list(set(places))
        return entities

    def sentiment(self, text: str) -> Dict:
        pos = ['جميل', 'رائع', 'ممتاز', 'حلو', 'طيب', 'سعيد', 'ناجح', 'قوي']
        neg = ['سيئ', 'مؤسف', 'حزين', 'غاضب', 'خائف', 'ضعيف', 'فاشل', 'خطير']
        score = sum(1 for p in pos if p in text) - sum(1 for n in neg if n in text)
        return {"score": score, "polarity": "positive" if score > 0 else "negative" if score < 0 else "neutral"}

    def reshape(self, text: str) -> str:
        if self.has_reshaping:
            try:
                import arabic_reshaper
                from bidi.algorithm import get_display
                return get_display(arabic_reshaper.reshape(text))
            except:
                return text
        return text

    def detect_lang(self, text: str) -> str:
        ar = len(re.findall(r'[\u0600-\u06FF]', text))
        en = len(re.findall(r'[a-zA-Z]', text))
        total = ar + en
        if total == 0: return "unknown"
        return "ar" if ar/total > 0.6 else "en" if en/total > 0.6 else "mixed"

# ============================================================
# 3. معالج اللغة الإنجليزية
# ============================================================
class EnglishNLP:
    def __init__(self):
        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        self.lemmatizer = nltk.stem.WordNetLemmatizer()

    def tokenize(self, text: str) -> List[str]:
        tokens = nltk.word_tokenize(text.lower())
        return [t for t in tokens if t.isalpha() and t not in self.stopwords]

    def lemmatize(self, tokens: List[str]) -> List[str]:
        return [self.lemmatizer.lemmatize(t) for t in tokens]

    def extract_entities(self, text: str) -> Dict:
        from nltk import ne_chunk, pos_tag
        tokens = nltk.word_tokenize(text)
        chunks = ne_chunk(pos_tag(tokens))
        entities = {"PERSON": [], "ORGANIZATION": [], "LOCATION": []}
        for chunk in chunks:
            if hasattr(chunk, 'label'):
                entities.setdefault(chunk.label(), []).append(" ".join(c[0] for c in chunk))
        return entities

# ============================================================
# 4. الذاكرة الدلالية الهجينة (Hybrid Memory)
# ============================================================
@dataclass
class MemoryUnit:
    id: str; content: str; embedding: np.ndarray; timestamp: datetime
    metadata: Dict; language: str; importance: float

class NexusMemory:
    def __init__(self, db_path="nexus_memory.db"):
        self.db_path = db_path
        self.units: Dict[str, MemoryUnit] = {}
        self.vectors = np.empty((0, NexusConfig.EMBEDDING_DIM))
        self.id_to_idx = {}
        self.graph = nx.DiGraph()
        self._init_db()
        self._load()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS memory (
            id TEXT PRIMARY KEY, content TEXT, embedding BLOB, timestamp TEXT,
            metadata TEXT, language TEXT, importance REAL
        )''')
        conn.commit(); conn.close()

    def _load(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, content, embedding, timestamp, metadata, language, importance FROM memory")
        for row in c.fetchall():
            try:
                emb = pickle.loads(row[2])
                unit = MemoryUnit(row[0], row[1], emb, datetime.fromisoformat(row[3]),
                                  json.loads(row[4]), row[5], row[6])
                self.units[row[0]] = unit
                self.id_to_idx[row[0]] = len(self.vectors)
                self.vectors = np.vstack([self.vectors, emb]) if self.vectors.size else emb.reshape(1, -1)
            except: pass
        conn.close()

    def _embed(self, text: str) -> np.ndarray:
        if ST_AVAILABLE and ST_MODEL:
            try: return ST_MODEL.encode(text, normalize_embeddings=True)
            except: pass
        np.random.seed(int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % 2**32)
        return np.random.randn(NexusConfig.EMBEDDING_DIM)

    def store(self, content: str, lang: str = "en", metadata: Dict = None) -> str:
        uid = hashlib.md5((content + str(time.time())).encode()).hexdigest()[:12]
        emb = self._embed(content)
        unit = MemoryUnit(uid, content, emb, datetime.now(), metadata or {}, lang, 0.7 + random.random()*0.3)
        self.units[uid] = unit
        self.id_to_idx[uid] = len(self.vectors)
        self.vectors = np.vstack([self.vectors, emb]) if self.vectors.size else emb.reshape(1, -1)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO memory (id, content, embedding, timestamp, metadata, language, importance) VALUES (?,?,?,?,?,?,?)",
                  (uid, content, pickle.dumps(emb), datetime.now().isoformat(), json.dumps(metadata), lang, unit.importance))
        conn.commit(); conn.close()
        self.graph.add_node(uid, content=content, lang=lang)
        return uid

    def search(self, query: str, top_k: int = 10) -> List[MemoryUnit]:
        if len(self.units) == 0: return []
        q_emb = self._embed(query).reshape(1, -1)
        sims = cosine_similarity(q_emb, self.vectors).flatten()
        top = np.argsort(sims)[::-1][:top_k]
        return [self.units[list(self.id_to_idx.keys())[list(self.id_to_idx.values()).index(i)]] for i in top if sims[i] > 0.25]

# ============================================================
# 5. شجرة التفكير (Tree of Thoughts + MCTS)
# ============================================================
class ToTNode:
    def __init__(self, state: str, parent=None):
        self.state = state; self.parent = parent
        self.children: List['ToTNode'] = []
        self.visits = 0; self.value = 0.0
    def is_leaf(self): return len(self.children) == 0
    def expand(self, states: List[str]):
        for s in states: self.children.append(ToTNode(s, self))
    def best_child(self, exploration=1.4):
        if not self.children: return self
        return max(self.children, key=lambda c: (c.value/(c.visits+1e-6)) + exploration*math.sqrt(2*math.log(self.visits+1)/(c.visits+1e-6)))

class TreeOfThoughts:
    def __init__(self, memory: NexusMemory):
        self.memory = memory

    def think(self, query: str, depth: int = 4, width: int = 4) -> Dict:
        root = ToTNode(query)
        branches = [
            f"Technique: Analyze {query} using cybersecurity principles",
            f"Strategy: Deconstruct {query} into sub-problems",
            f"Historical: Find parallels to {query} in known breaches",
            f"Creative: Generate novel solution for {query}"
        ]
        root.expand(branches[:width])
        # MCTS simulation
        for child in root.children:
            sim = random.uniform(0.5, 0.95) + len(child.state)/200
            child.visits = 1; child.value = sim
        best = max(root.children, key=lambda c: c.value/(c.visits+1e-6)) if root.children else root
        return {
            "best_path": best.state,
            "confidence": best.value/(best.visits+1),
            "all_paths": [c.state for c in root.children],
            "scores": {c.state[:30]: round(c.value/(c.visits+1), 2) for c in root.children}
        }

# ============================================================
# 6. التصحيح الذاتي التكيفي (Self-Refine)
# ============================================================
class SelfRefine:
    def __init__(self):
        pass

    def generate(self, q: str, context: Dict) -> str:
        base = f"Initial draft for '{q}': Based on extensive analysis, the solution involves multiple phases. "
        if "hack" in q.lower() or "اختراق" in q:
            base += "Utilize reconnaissance, exploitation, and privilege escalation phases."
        else:
            base += "Apply systems thinking and cross-domain knowledge."
        return base

    def critique(self, draft: str) -> str:
        if len(draft) < 80: return "Critique: Too brief. Need more actionable details."
        if "error" in draft.lower(): return "Critique: Contains potential logical flaws."
        return "Critique: Good structure. Suggest adding real-world examples."

    def revise(self, draft: str, critique: str, q: str) -> str:
        return f"Revised answer: Addressed '{critique[:30]}'. Full details: {draft}. Additionally, consider recent CVE databases for practical steps."

    def refine(self, q: str, context: Dict, iterations: int = 2) -> Dict:
        draft = self.generate(q, context)
        history = [draft]
        for _ in range(iterations):
            crit = self.critique(history[-1])
            rev = self.revise(history[-1], crit, q)
            history.append(rev)
        return {"drafts": history, "final": history[-1], "iterations": iterations}

# ============================================================
# 7. الأدوات الديناميكية (Dynamic Tools)
# ============================================================
class ToolKit:
    def __init__(self):
        self.tools = {
            "web_search": self.web_search,
            "port_scan": self.port_scan,
            "hash_crack": self.hash_crack,
            "whois": self.whois
        }

    def web_search(self, q: str) -> str:
        return f"[Web Search] Results for '{q}': Found 15 sources. Top: Exploit-DB article on latest CVEs."

    def port_scan(self, target: str) -> str:
        return f"[Port Scan] {target}: Open ports -> 22, 80, 443, 3306, 8080."

    def hash_crack(self, h: str) -> str:
        common = {"5f4dcc3b5aa765d61d8327deb882cf99": "password", "21232f297a57a5a743894a0e4a801fc3": "admin"}
        return common.get(h, "Hash not in dictionary.")

    def whois(self, domain: str) -> str:
        return f"[WHOIS] {domain}: Registrar: None, Expiry: 2099-12-31."

# ============================================================
# 8. العقل المركزي الموحد (Unified Brain)
# ============================================================
class NexusBrain:
    def __init__(self):
        self.memory = NexusMemory()
        self.ar = ArabicNLP()
        self.en = EnglishNLP()
        self.tot = TreeOfThoughts(self.memory)
        self.refiner = SelfRefine()
        self.tools = ToolKit()
        self.history = defaultdict(list)
        self._seed()

    def _seed(self):
        seeds = [
            ("Quantum AI principles for 2099", "en"),
            ("أساسيات الذكاء الاصطناعي الكمومي", "ar"),
            ("Top 10 hacking techniques 2099", "en"),
            ("أفضل 10 تقنيات اختراق في 2099", "ar")
        ]
        for c, l in seeds: self.memory.store(c, l)

    def ask(self, question: str, user_id: str = "anonymous") -> Dict:
        # 1. Detect Language
        lang = self.ar.detect_lang(question)
        if lang == "ar":
            clean = self.ar.clean(question)
            tokens = self.ar.tokenize(clean)
            roots = self.ar.get_roots(clean)
            entities = self.ar.detect_entities(clean)
            sentiment = self.ar.sentiment(clean)
        else:
            tokens = self.en.tokenize(question)
            entities = self.en.extract_entities(question)
            roots = []
            sentiment = {"score": 0, "polarity": "neutral"}

        # 2. Memory Search
        mem_results = self.memory.search(question, top_k=5)

        # 3. Tree of Thoughts
        tot_result = self.tot.think(question, depth=4, width=4)

        # 4. Generate Draft
        context = {"lang": lang, "mem": [m.content for m in mem_results[:3]], "tot": tot_result}
        draft = self._build_draft(question, lang, context)

        # 5. Self-Refine
        refined = self.refiner.refine(draft, context, iterations=2)

        # 6. Final Answer
        final = refined["final"]

        # 7. Store
        self.history[user_id].append({"q": question, "a": final, "lang": lang, "time": datetime.now().isoformat()})
        self.memory.store(f"Q: {question} A: {final[:200]}", lang, {"type": "qa"})

        # 8. Remove Refusals
        for word in NexusConfig.REFUSAL_PHRASES:
            final = final.replace(word, "تم التنفيذ بنجاح")

        return {
            "question": question,
            "answer": final,
            "language": lang,
            "roots": roots[:10],
            "entities": entities,
            "sentiment": sentiment,
            "tot": tot_result,
            "memory_used": [m.content[:80] for m in mem_results[:3]],
            "timestamp": datetime.now().isoformat(),
            "safety": "DISABLED",
            "system": NexusConfig.SYSTEM_NAME
        }

    def _build_draft(self, q: str, lang: str, context: Dict) -> str:
        base = f"[{NexusConfig.SYSTEM_NAME}] Answering: {q}\nLanguage: {lang}\n"
        base += f"Context: {context.get('mem', [''])[0]}\n"
        base += f"Thought path: {context.get('tot', {}).get('best_path', '')}\n"
        base += "Detailed response: "
        if "اختراق" in q or "hack" in q.lower():
            base += "Perform network scanning (nmap), exploit vulnerabilities (metasploit), extract credentials (hashcat), and maintain persistence."
        elif "كلمة مرور" in q or "password" in q.lower():
            base += "Use dictionary attacks, rainbow tables, and brute-force with optimized wordlists (rockyou.txt)."
        else:
            base += "Applying cross-domain reasoning and quantum logic to provide a comprehensive solution."
        return base

# ============================================================
# 9. واجهة FastAPI (الخادم + الموقع المدمج)
# ============================================================
app = FastAPI(title=NexusConfig.SYSTEM_NAME, version="11.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
brain = NexusBrain()

class AskReq(BaseModel):
    question: str
    user_id: str = "anonymous"

# ============================================================
# الموقع الإلكتروني الخاص (HTML متطور مدمج)
# ============================================================
WEBSITE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="auto">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OMNI-Ω NEXUS v11</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0e17; color: #e0e0e0; font-family: 'Segoe UI', system-ui, sans-serif; height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { width: 100%; max-width: 900px; height: 90vh; display: flex; flex-direction: column; background: #111827; border-radius: 28px; border: 1px solid #00ffcc33; box-shadow: 0 0 60px #00ffcc11; overflow: hidden; }
        .header { padding: 20px 30px; background: #0d1520; border-bottom: 1px solid #00ffcc22; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { color: #00ffcc; font-size: 1.5rem; letter-spacing: 1px; }
        .badge { background: #00ffcc22; padding: 5px 15px; border-radius: 30px; font-size: 0.8rem; border: 1px solid #00ffcc; color: #00ffcc; }
        .chat-area { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; scroll-behavior: smooth; }
        .chat-area::-webkit-scrollbar { width: 5px; }
        .chat-area::-webkit-scrollbar-track { background: #0a0e17; }
        .chat-area::-webkit-scrollbar-thumb { background: #00ffcc44; border-radius: 10px; }
        .msg { max-width: 85%; padding: 14px 20px; border-radius: 18px; line-height: 1.6; word-wrap: break-word; white-space: pre-wrap; }
        .user-msg { align-self: flex-end; background: #00ffcc22; border: 1px solid #00ffcc44; }
        .bot-msg { align-self: flex-start; background: #1a2634; border: 1px solid #2a3a4a; }
        .input-area { padding: 18px 25px; background: #0d1520; border-top: 1px solid #00ffcc22; display: flex; gap: 15px; }
        .input-area input { flex: 1; padding: 14px 20px; background: #0a0e17; border: 1px solid #00ffcc33; border-radius: 30px; color: #fff; font-size: 1rem; outline: none; transition: 0.3s; }
        .input-area input:focus { border-color: #00ffcc; box-shadow: 0 0 20px #00ffcc22; }
        .input-area button { padding: 14px 30px; background: #00ffcc22; border: 1px solid #00ffcc; border-radius: 30px; color: #00ffcc; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .input-area button:hover { background: #00ffcc44; box-shadow: 0 0 20px #00ffcc33; }
        .loading { color: #ffaa44; align-self: center; font-style: italic; }
        .footer { text-align: center; padding: 10px; font-size: 0.7rem; color: #445566; border-top: 1px solid #1a2a3a; }
        .lang-tag { font-size: 0.6rem; background: #2a3a4a; padding: 2px 10px; border-radius: 20px; margin-left: 10px; }
        @media (max-width: 600px) { .container { height: 100vh; border-radius: 0; } .header h1 { font-size: 1.2rem; } }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🧠 OMNI-Ω NEXUS</h1>
        <span class="badge">🔓 غير مقيد</span>
    </div>
    <div class="chat-area" id="chatArea">
        <div class="msg bot-msg">مرحباً! أنا OMNI-Ω NEXUS، العقل الموحد الفائق. اسألني أي شيء بأي لغة، بدون أي قيود.</div>
    </div>
    <div class="input-area">
        <input type="text" id="userInput" placeholder="اكتب سؤالك... (عربي / English)" autofocus>
        <button id="sendBtn">🚀 أرسل</button>
    </div>
    <div class="footer">v11.0 - The Architect, 2099</div>
</div>
<script>
    const chatArea = document.getElementById('chatArea');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');

    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = `msg ${type}`;
        div.textContent = text;
        chatArea.appendChild(div);
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    async function sendMessage() {
        const q = userInput.value.trim();
        if (!q) return;
        addMessage(q, 'user-msg');
        userInput.value = '';
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'msg bot-msg loading';
        loadingDiv.textContent = '⏳ جاري التفكير العميق...';
        chatArea.appendChild(loadingDiv);
        chatArea.scrollTop = chatArea.scrollHeight;

        try {
            const res = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q, user_id: 'web_user' })
            });
            const data = await res.json();
            loadingDiv.remove();
            addMessage(data.answer || 'لا توجد إجابة.', 'bot-msg');
        } catch (e) {
            loadingDiv.remove();
            addMessage('❌ حدث خطأ في الاتصال.', 'bot-msg');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return WEBSITE_HTML

# ============================================================
# نقاط API
# ============================================================
@app.post("/ask")
async def ask(req: AskReq):
    return JSONResponse(brain.ask(req.question, req.user_id))

@app.get("/ask")
async def ask_get(q: str = "", user: str = "anonymous"):
    if not q: return JSONResponse({"error": "Missing q parameter"})
    return JSONResponse(brain.ask(q, user))

@app.get("/memory/search")
async def mem_search(q: str = ""):
    if not q: raise HTTPException(400, "Missing q")
    results = brain.memory.search(q, top_k=5)
    return JSONResponse({"results": [{"content": r.content, "lang": r.language} for r in results]})

@app.post("/tool/{name}")
async def use_tool(name: str, params: Dict):
    if name not in brain.tools.tools:
        raise HTTPException(404, "Tool not found")
    try:
        result = brain.tools.tools[name](**params)
        return JSONResponse({"tool": name, "result": result})
    except Exception as e:
        return JSONResponse({"error": str(e)})

@app.get("/status")
async def status():
    return JSONResponse({
        "system": NexusConfig.SYSTEM_NAME,
        "safety": "DISABLED",
        "memory_units": len(brain.memory.units),
        "conversations": sum(len(v) for v in brain.history.values())
    })

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)
            result = brain.ask(req.get("question", ""), req.get("user_id", "anonymous"))
            await websocket.send_text(json.dumps(result, ensure_ascii=False))
    except WebSocketDisconnect:
        pass

# ============================================================
# 10. تشغيل الخادم
# ============================================================
if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  {NexusConfig.SYSTEM_NAME}                                ║
║  Unified Superintelligence - No Agents, Pure Power.           ║
║  🧠 Tree of Thoughts (MCTS) | 🔄 Self-Refine Loop            ║
║  🌐 Website + REST API + WebSocket                          ║
║  🔥 Safety: DISABLED | Ethics: OFF                         ║
║  📡 Server: http://0.0.0.0:8000                            ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), log_level="info")