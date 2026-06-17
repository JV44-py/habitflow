// ─────────────────────────────────────────────
//  HabitFlow  ·  supabase.js
//  Supabase auth client + Django API wrapper
// ─────────────────────────────────────────────

const SUPABASE_URL = 'https://YOUR_PROJECT_ID.supabase.co';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';
const API_BASE = '/api';

// ── Supabase client (CDN build) ──────────────
const { createClient } = supabase;
const sb = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ── Auth helpers ─────────────────────────────
const Auth = {
  async signUp(email, password, firstName, lastName) {
    return sb.auth.signUp({
      email, password,
      options: { data: { first_name: firstName, last_name: lastName } }
    });
  },

  async signIn(email, password) {
    return sb.auth.signInWithPassword({ email, password });
  },

  async signOut() {
    await sb.auth.signOut();
    window.location.href = '/login/';
  },

  async resetPassword(email) {
    return sb.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/profile/`
    });
  },

  async getSession() {
    const { data } = await sb.auth.getSession();
    return data.session;
  },

  async getToken() {
    const session = await this.getSession();
    return session?.access_token || null;
  },

  onAuthStateChange(cb) {
    return sb.auth.onAuthStateChange(cb);
  }
};

// ── Django REST API wrapper ───────────────────
const API = {
  async _request(method, path, body = null) {
    const token = await Auth.getToken();
    if (!token) {
      window.location.href = '/login/';
      return null;
    }

    const opts = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-CSRFToken': getCookie('csrftoken'),
      },
    };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(`${API_BASE}${path}`, opts);

    if (res.status === 401) {
      await Auth.signOut();
      return null;
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.message || `HTTP ${res.status}`);
    }

    return res.status === 204 ? null : res.json();
  },

  get:    (path)       => API._request('GET',    path),
  post:   (path, body) => API._request('POST',   path, body),
  patch:  (path, body) => API._request('PATCH',  path, body),
  put:    (path, body) => API._request('PUT',    path, body),
  delete: (path)       => API._request('DELETE', path),

  // ── Convenience endpoints ──
  dashboard:    ()           => API.get('/dashboard/'),
  profile:      ()           => API.get('/profile/'),
  updateProfile:(data)       => API.patch('/profile/', data),
  analytics:    (period)     => API.get(`/analytics/?period=${period}`),
  achievements: ()           => API.get('/achievements/'),
  calendar:     (y, m)       => API.get(`/calendar/?year=${y}&month=${m}`),

  habits: {
    list:       (params = '') => API.get(`/habits/${params}`),
    create:     (data)        => API.post('/habits/', data),
    update:     (id, data)    => API.patch(`/habits/${id}/`, data),
    delete:     (id)          => API.delete(`/habits/${id}/`),
    toggle:     (id, data)    => API.post(`/habits/${id}/toggle_complete/`, data),
    history:    (id, days)    => API.get(`/habits/${id}/history/?days=${days}`),
    byRoutine:  ()            => API.get('/habits/by_routine/'),
  },

  categories: {
    list:   ()     => API.get('/categories/'),
    create: (data) => API.post('/categories/', data),
    delete: (id)   => API.delete(`/categories/${id}/`),
  },

  goals: {
    list:   ()     => API.get('/goals/'),
    create: (data) => API.post('/goals/', data),
    update: (id, d)=> API.patch(`/goals/${id}/`, d),
    delete: (id)   => API.delete(`/goals/${id}/`),
  },
};

// ── Utility ───────────────────────────────────
function getCookie(name) {
  const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
  return v ? v[2] : '';
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function timeAgo(dateStr) {
  const diff = (Date.now() - new Date(dateStr)) / 1000;
  if (diff < 60)    return 'just now';
  if (diff < 3600)  return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

function showToast(message, type = 'success') {
  const colors = {
    success: 'bg-emerald-500',
    error:   'bg-red-500',
    info:    'bg-blue-500',
    warning: 'bg-amber-500',
  };
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };

  const toast = document.createElement('div');
  toast.className = `fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3
    rounded-2xl text-white shadow-2xl text-sm font-medium
    transform translate-y-8 opacity-0 transition-all duration-300
    ${colors[type]}`;
  toast.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;
  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-8', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('translate-y-8', 'opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function debounce(fn, delay = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

// ── Auth guard (call on protected pages) ─────
async function requireAuth() {
  const session = await Auth.getSession();
  if (!session) {
    window.location.href = '/login/';
    return false;
  }
  return true;
}

// ── Theme persistence ─────────────────────────
function applyTheme() {
  const theme = localStorage.getItem('hf_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', theme);
  document.documentElement.classList.toggle('dark', theme === 'dark');
}
applyTheme();

function toggleTheme() {
  const current = localStorage.getItem('hf_theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem('hf_theme', next);
  applyTheme();
}
