const $ = id => document.getElementById(id);
let busy = false;
let configured = false;

function showView(view) {
  const chat = view === 'chat';
  $('chatView').hidden = !chat;
  $('filesView').hidden = chat;
  $('pageLabel').textContent = chat ? 'المحادثة' : 'ملفات المشروع';
  document.querySelectorAll('[data-view]').forEach(button => {
    const active = button.dataset.view === view;
    button.classList.toggle('active', active);
    if (active) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  });
}
document.querySelectorAll('[data-view]').forEach(button => {
  button.addEventListener('click', () => showView(button.dataset.view));
});

function setBusy(value) {
  busy = value;
  $('send').disabled = value || !configured;
  $('newChat').disabled = value;
  $('chatForm').setAttribute('aria-busy', String(value));
}

function message(text, type) {
  const box = document.createElement('div');
  box.className = 'message ' + type;
  box.dir = 'auto';
  const label = document.createElement('span');
  label.className = 'message-label';
  label.textContent = type === 'user' ? 'أنت' : type === 'error' ? 'تنبيه' : 'OMNI NEXUS · GPT-OSS';
  box.append(label, document.createTextNode(text));
  $('messages').append(box);
  box.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  return box;
}

async function send() {
  if (busy || !configured) return;
  const question = $('question').value.trim();
  if (!question) return;
  setBusy(true);
  $('welcome').hidden = true;
  const userMessage = message(question, 'user');
  $('question').value = '';
  const pending = message('جارٍ إعداد الرد…', 'bot');
  try {
    const response = await fetch('/ask', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }), signal: AbortSignal.timeout(55000)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'تعذّر إرسال الرسالة. جرّب بعد قليل.');
    pending.remove();
    const suffix = data.truncated ? '\n\nوصل الرد للحد الأقصى. اطلب مني المتابعة إذا احتجت.' : '';
    message((data.answer || 'لم يصل رد من الخادم.') + suffix, 'bot');
  } catch (error) {
    pending.remove();
    userMessage.remove();
    const text = error.name === 'TimeoutError' || error.name === 'TypeError'
      ? 'تعذّر الاتصال أو تأخر الرد. رسالتك محفوظة بالأسفل للمحاولة مجددًا.'
      : error.message;
    message(text, 'error');
    $('question').value = question;
  } finally {
    setBusy(false);
    $('question').focus();
  }
}
$('chatForm').addEventListener('submit', event => { event.preventDefault(); send(); });
$('question').addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault(); send();
  }
});
document.querySelectorAll('[data-prompt]').forEach(button => {
  button.addEventListener('click', () => {
    $('question').value = button.dataset.prompt;
    $('question').focus();
  });
});
$('newChat').addEventListener('click', async () => {
  if (busy) return;
  setBusy(true);
  try {
    const response = await fetch('/chat/reset', { method: 'POST', signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error();
    document.querySelectorAll('.message').forEach(element => element.remove());
    $('welcome').hidden = false;
    $('question').value = '';
    showView('chat');
    $('question').focus();
  } catch {
    message('تعذّر بدء محادثة جديدة. جرّب مرة ثانية.', 'error');
  } finally { setBusy(false); }
});

async function status() {
  try {
    const response = await fetch('/status', { signal: AbortSignal.timeout(15000) });
    if (!response.ok) throw new Error();
    const data = await response.json();
    configured = data.configured === true;
    $('connection').textContent = configured ? 'المحادثة جاهزة' : 'المحادثة قيد التجهيز';
    $('connection').classList.toggle('online', configured);
    $('modelLabel').textContent = configured ? 'GPT-OSS' : 'غير متصل';
    $('modelNote').textContent = configured
      ? 'GPT-OSS عبر Groq. يخضع الاستخدام لحصة الخدمة المتاحة.'
      : 'خدمة الذكاء الاصطناعي قيد التجهيز. ملفات المشروع متاحة للتنزيل.';
  } catch {
    configured = false;
    $('connection').textContent = 'الخادم غير متاح';
    $('connection').classList.remove('online');
    $('modelLabel').textContent = 'غير متصل';
    $('modelNote').textContent = 'تعذّر الاتصال بالخادم. أعد تحميل الصفحة للمحاولة.';
  } finally { $('send').disabled = busy || !configured; }
}

async function files() {
  try {
    const response = await fetch('/project/files');
    if (!response.ok) throw new Error();
    const data = await response.json();
    $('fileCount').textContent = data.files.length;
    $('fileList').replaceChildren();
    for (const file of data.files) {
      const row = document.createElement('div'); row.className = 'file-row';
      const name = document.createElement('span'); name.className = 'file-name'; name.textContent = file.name;
      const size = document.createElement('span'); size.className = 'file-size';
      size.textContent = file.size < 1024 ? file.size + ' B' : (file.size / 1024).toFixed(1) + ' KB';
      const link = document.createElement('a');
      link.href = '/project/file/' + file.name.split('/').map(encodeURIComponent).join('/');
      link.textContent = '↓'; link.setAttribute('aria-label', 'تنزيل ' + file.name);
      row.append(name, size, link); $('fileList').append(row);
    }
  } catch { $('fileList').textContent = 'تعذّر تحميل الملفات. أعد تحميل الصفحة للمحاولة مجددًا.'; }
}
status();
files();
