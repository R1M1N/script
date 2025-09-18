const API_BASE = ''; // same origin
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const topKEl = document.getElementById('topK');
const statusBadge = document.getElementById('statusBadge');

let isDark = false;
let sending = false;

function bubble(text, who = 'bot', sources = []) {
  const wrap = document.createElement('div');
  wrap.className = `flex ${who === 'user' ? 'justify-end' : 'justify-start'}`;

  const card = document.createElement('div');
  card.className = `max-w-[80%] rounded-2xl px-4 py-3 border shadow-sm ${
    who === 'user'
      ? 'bg-brand text-white border-brand/10'
      : 'bg-white text-slate-900 border-slate-200'
  }`;

  // message
  const p = document.createElement('p');
  p.className = 'whitespace-pre-wrap text-sm leading-6';
  p.textContent = text;
  card.appendChild(p);

  // sources
  if (sources && sources.length) {
    const sWrap = document.createElement('div');
    sWrap.className = `mt-3 text-xs ${who === 'user' ? 'text-white/90' : 'text-slate-600'}`;
    const title = document.createElement('div');
    title.textContent = 'Sources:';
    sWrap.appendChild(title);
    const list = document.createElement('ul');
    list.className = 'list-disc ml-5 mt-1 space-y-1';
    sources.slice(0, 5).forEach(s => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = s.url || '#';
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.className = 'underline decoration-dotted hover:decoration-solid';
      a.textContent = s.title || s.url || 'source';
      li.appendChild(a);
      list.appendChild(li);
    });
    sWrap.appendChild(list);
    card.appendChild(sWrap);
  }

  wrap.appendChild(card);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function typing(on = true) {
  if (on) {
    const t = document.createElement('div');
    t.id = 'typing';
    t.className = 'flex justify-start';
    t.innerHTML = `
      <div class="max-w-[80%] rounded-2xl px-4 py-3 border shadow-sm bg-white text-slate-900 border-slate-200">
        <span class="inline-flex items-center gap-2 text-sm">
          <span class="relative flex h-2 w-2"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand opacity-75"></span><span class="relative inline-flex rounded-full h-2 w-2 bg-brand"></span></span>
          Typing…
        </span>
      </div>`;
    messagesEl.appendChild(t);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  } else {
    const t = document.getElementById('typing');
    if (t) t.remove();
  }
}

async function send() {
  const q = inputEl.value.trim();
  if (!q || sending) return;
  sending = true;

  bubble(q, 'user');
  inputEl.value = '';
  typing(true);

  try {
    const res = await fetch(`${API_BASE}/rag`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ message: q, context_k: parseInt(topKEl.value, 10) })
    }); // POST JSON with Fetch API
    const data = await res.json();
    typing(false);
    bubble(data.response || 'No response.', 'bot', data.context_used || []);
  } catch (e) {
    typing(false);
    bubble('Request failed. Please try again.', 'bot');
  } finally {
    sending = false;
  }
}

sendBtn.addEventListener('click', send);
inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

document.getElementById('themeBtn').addEventListener('click', () => {
  isDark = !isDark;
  document.documentElement.classList.toggle('dark', isDark);
  document.body.className = isDark ? 'bg-slate-900 text-slate-100' : 'bg-slate-50 text-slate-900';
});
