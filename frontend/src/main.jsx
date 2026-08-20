import React, { createContext, useContext, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import axios from 'axios';
import './styles.css';
import './warm-workspace.css';

const api = axios.create({ baseURL: 'http://localhost:8000' });
const Auth = createContext();
const useAuth = () => useContext(Auth);

api.interceptors.request.use((config) => {
  const session = JSON.parse(localStorage.getItem('mosaic_session') || 'null');
  if (session?.access_token) config.headers.Authorization = `Bearer ${session.access_token}`;
  return config;
});

function AuthProvider({ children }) {
  const [session, setSession] = useState(() => JSON.parse(localStorage.getItem('mosaic_session') || 'null'));

  useEffect(() => {
    if (!session) return;
    api.get('/auth/me')
      .then(({ data }) => {
        const next = { ...session, name: data.name, role: data.role };
        localStorage.setItem('mosaic_session', JSON.stringify(next));
        setSession((current) => current?.name === next.name && current?.role === next.role ? current : next);
      })
      .catch(() => {
        localStorage.removeItem('mosaic_session');
        setSession(null);
      });
  }, [session?.access_token]);

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password });
    localStorage.setItem('mosaic_session', JSON.stringify(data));
    setSession(data);
  };

  const logout = () => {
    localStorage.removeItem('mosaic_session');
    setSession(null);
  };

  return <Auth.Provider value={{ session, login, logout }}>{children}</Auth.Provider>;
}

function Empty({ title, text }) {
  return <div className="empty"><b>✦</b><h3>{title}</h3><p>{text}</p></div>;
}

function Login() {
  const { login } = useAuth();
  const [registering, setRegistering] = useState(false);
  const [email, setEmail] = useState('admin@mosaic.local');
  const [password, setPassword] = useState('Admin@123');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (registering) {
        await api.post('/auth/register', { name, email, password });
        setRegistering(false);
        setName('');
        setPassword('');
        setError('Account created. Sign in with your new credentials.');
      } else {
        await login(email, password);
      }
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not sign you in.');
    } finally {
      setBusy(false);
    }
  }

  return <main className="login">
    <section>
      <p className="eyebrow">KNOWLEDGE, CONNECTED</p>
      <h1>Mosaic makes<br />work click.</h1>
      <p className="lede">A calm place for your team's knowledge and the work it unlocks.</p>
    </section>
    <form onSubmit={submit}>
      <div className="mark">M</div><h2>{registering ? 'Join Mosaic' : 'Welcome back'}</h2><p>{registering ? 'Create a User account to join your team.' : 'Pick up where your team left off.'}</p>
      {error && <div className={error.startsWith('Account created') ? 'success' : 'error'}>{error}</div>}
      {registering && <label>Name<input required value={name} onChange={(event) => setName(event.target.value)} /></label>}
      <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
      <label>Password<input type="password" minLength="8" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
      <button disabled={busy}>{busy ? (registering ? 'Creating account…' : 'Opening Mosaic…') : (registering ? 'Create account' : 'Enter Mosaic →')}</button>
      <button type="button" className="text auth-switch" onClick={() => { setRegistering(!registering); setError(''); setPassword(''); }}>{registering ? 'Already have an account? Sign in' : 'Need an account? Register as a User'}</button>
    </form>
  </main>;
}

function Shell({ page, setPage, children }) {
  const { session, logout } = useAuth();
  const items = [['today', '✦', 'Today'], ['work', '✓', 'Workboard'], ['library', '▤', 'Library'], ['search', '⌕', 'Ask Mosaic']];
  if (session.role === 'Admin') items.push(['pulse', '◔', 'Pulse']);
  return <div className="shell">
    <aside>
      <div className="brand"><b>M</b> mosaic</div>
      <nav>{items.map(([id, icon, label]) => <button key={id} onClick={() => setPage(id)} className={page === id ? 'active' : ''}><span>{icon}</span>{label}</button>)}</nav>
      <div className="profile"><i>{session.name[0]}</i><div><b>{session.name}</b><small>{session.role}</small></div><button onClick={logout}>↪</button></div>
    </aside>
    <main className="content">{children}</main>
  </div>;
}

function Task({ task, onDone }) {
  return <article className="task">
    <span className="dot" />
    <div><span className={'badge ' + task.status}>{task.status}</span><h3>{task.title}</h3><p>{task.description || 'No additional notes.'}</p><small>{task.assignee && `Assigned to ${task.assignee}`}</small></div>
    {onDone && task.status === 'pending' && <button className="complete" onClick={() => onDone(task.id)}>Mark done</button>}
  </article>;
}

function DataError({ text }) {
  return <div className="data-error"><b>We couldn't load this page.</b><span>{text}</span></div>;
}

function Today({ setPage }) {
  const { session } = useAuth();
  const [data, setData] = useState({ tasks: [], documents: [] });
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      setStatus('loading');
      try {
        const [tasks, documents] = await Promise.all([
          api.get('/tasks?status=pending', { signal: controller.signal }),
          api.get('/documents', { signal: controller.signal }),
        ]);
        setData({ tasks: tasks.data, documents: documents.data });
        setStatus('ready');
      } catch (error) {
        if (!axios.isCancel(error) && error.code !== 'ERR_CANCELED') setStatus('error');
      }
    }
    load();
    return () => controller.abort();
  }, []);

  const { tasks, documents } = data;
  return <>
    <header><div><p className="eyebrow">{session.role === 'Admin' ? 'TEAM OVERVIEW' : 'YOUR FOCUS'}</p><h1>Good morning, {session.name}.</h1><p>{tasks.length ? `${tasks.length} open work item${tasks.length > 1 ? 's' : ''} waiting for momentum.` : 'Your workboard is clear.'}</p></div><button className="ask" onClick={() => setPage('search')}>Ask the Library</button></header>
    {status === 'error' ? <DataError text="Check the API connection, then return to Today." /> : <div className="split">
      <section><div className="section-title"><h2>Next up</h2><button className="text" onClick={() => setPage('work')}>View workboard</button></div>
        {status === 'loading' ? <p className="loading">Loading your workspace…</p> : <>{tasks.slice(0, 3).map((task) => <Task task={task} key={task.id} />)}{!tasks.length && <Empty title="Nothing waiting" text="Your pending work will appear here." />}</>}
      </section>
      <section className="side"><h2>Fresh in the Library</h2>
        {status === 'loading' ? <p className="loading">Loading recent sources…</p> : <>{documents.slice(0, 4).map((document) => <div className="doc" key={document.id}><span>▤</span><div><b>{document.filename}</b><small>Added by {document.uploaded_by}</small></div></div>)}{!documents.length && <p className="muted">Your shared knowledge will appear here.</p>}</>}
        <button className="outline" onClick={() => setPage('library')}>Browse Library</button>
      </section>
    </div>}
  </>;
}

function Work() {
  const { session } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [filter, setFilter] = useState('all');
  const [form, setForm] = useState({ title: '', description: '', assigned_to: '' });
  const load = async () => setTasks((await api.get('/tasks' + (filter === 'all' ? '' : `?status=${filter}`))).data);
  useEffect(() => { load(); }, [filter]);
  useEffect(() => { if (session.role === 'Admin') api.get('/auth/users').then(({ data }) => setUsers(data.filter((user) => user.role === 'User'))); }, [session.role]);

  async function add(event) {
    event.preventDefault();
    await api.post('/tasks', { ...form, assigned_to: Number(form.assigned_to) });
    setForm({ title: '', description: '', assigned_to: '' });
    load();
  }
  async function done(id) { await api.put('/tasks/' + id, { status: 'completed' }); load(); }

  return <><header><div><p className="eyebrow">WORKBOARD</p><h1>Work with a little momentum.</h1><p>Clear actions, clear ownership, no unnecessary noise.</p></div></header>
    {session.role === 'Admin' && <form className="quick" onSubmit={add}><input required placeholder="What needs to happen?" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /><input placeholder="A useful note (optional)" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /><select required value={form.assigned_to} onChange={(event) => setForm({ ...form, assigned_to: event.target.value })}><option value="">Assign to…</option>{users.map((user) => <option value={user.id} key={user.id}>{user.name}</option>)}</select><button>Assign task</button></form>}
    <div className="tabs">{['all', 'pending', 'completed'].map((value) => <button key={value} className={filter === value ? 'selected' : ''} onClick={() => setFilter(value)}>{value}</button>)}</div>
    <section className="task-list">{tasks.map((task) => <Task task={task} key={task.id} onDone={done} />)}{!tasks.length && <Empty title="Nothing here yet" text="Try another view, or wait for the next task." />}</section>
  </>;
}

function Library() {
  const { session } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState();
  const [note, setNote] = useState('');
  const [status, setStatus] = useState('loading');

  async function load(signal) {
    setStatus('loading');
    try {
      const { data } = await api.get('/documents', { signal });
      setDocuments(data);
      setStatus('ready');
    } catch (error) {
      if (!axios.isCancel(error) && error.code !== 'ERR_CANCELED') setStatus('error');
    }
  }
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, []);

  async function upload(event) {
    event.preventDefault();
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setNote('Adding it to the Library…');
    try {
      const { data } = await api.post('/documents', formData);
      setNote(`${data.message} ${data.chunks_indexed} sections are ready to search.`);
      setFile(undefined);
      event.target.reset();
      await load();
    } catch (error) {
      setNote(error.response?.data?.detail || 'Upload failed.');
    }
  }

  async function openDocument(documentItem) {
    const fileWindow = window.open('', '_blank');
    try {
      const response = await api.get(`/documents/${documentItem.id}/file`, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      if (fileWindow) fileWindow.location.replace(url);
      else window.location.assign(url);
    } catch (error) {
      fileWindow?.close();
      setNote(error.response?.data?.detail || 'Could not open this file.');
    }
  }

  return <><header><div><p className="eyebrow">THE LIBRARY</p><h1>Knowledge your team can use.</h1><p>Every document becomes searchable context, not just another attachment.</p></div></header>
    {session.role === 'Admin' && <form className="upload" onSubmit={upload}><div><b>Bring in a source</b><p>PDF and TXT files become searchable knowledge sections.</p></div><input type="file" accept=".pdf,.txt" onChange={(event) => setFile(event.target.files[0])} /><button disabled={!file}>Add to Library</button></form>}
    {note && <p className="success">{note}</p>}
    {status === 'loading' ? <p className="loading">Loading your knowledge library…</p> : status === 'error' ? <DataError text="Check the API connection, then return to the Library." /> : <section className="library">{documents.map((documentItem) => <article key={documentItem.id}><span>▤</span><div><h3>{documentItem.filename}</h3><p>Shared by {documentItem.uploaded_by}</p></div><small>{new Date(documentItem.created_at).toLocaleDateString()}</small><button className="text" onClick={() => openDocument(documentItem)}>Open</button></article>)}{!documents.length && <Empty title="The shelves are open" text={session.role === 'Admin' ? 'Upload a PDF or TXT file to make it searchable.' : 'An administrator will add shared documents here.'} />}</section>}
  </>;
}

function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [busy, setBusy] = useState(false);
  const [searched, setSearched] = useState(false);
  async function run(event) { event?.preventDefault(); if (!query.trim()) return; setBusy(true); setSearched(true); try { setResults((await api.post('/search', { query, limit: 4 })).data.results); } finally { setBusy(false); } }
  return <><header className="search-head"><p className="eyebrow">ASK MOSAIC</p><h1>Find the thread you need.</h1><p>Searches compare the meaning of your question with real knowledge sections.</p><form onSubmit={run}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask something about your team's knowledge…" /><button>{busy ? 'Searching…' : 'Search'}</button></form></header>{searched && <section className="results"><p className="eyebrow">{results.length ? 'MATCHING KNOWLEDGE' : 'NO MATCHES YET'}</p>{results.map((result, index) => <article key={index}><div className="score"><b>{result.score}%</b><small>relevance</small></div><div><p className="docname">▤ {result.filename}</p><p>{result.chunk}</p></div></article>)}{!busy && !results.length && <Empty title="Nothing quite matched" text="Try a more specific question, or add a document to the Library." />}</section>}</>;
}

function Pulse() {
  const [analytics, setAnalytics] = useState(null);
  useEffect(() => { api.get('/analytics').then(({ data }) => setAnalytics(data)); }, []);
  if (!analytics) return <p className="loading">Reading the team pulse…</p>;
  return <><header><div><p className="eyebrow">TEAM PULSE</p><h1>The work, at a glance.</h1></div></header><div className="stats">{[['Total tasks', analytics.total_tasks], ['Completed', analytics.completed_tasks], ['Still moving', analytics.pending_tasks], ['Library sources', analytics.documents]].map(([label, value]) => <article key={label}><b>{value}</b><p>{label}</p></article>)}</div></>;
}

function App() {
  const { session } = useAuth();
  const [page, setPage] = useState('today');
  if (!session) return <Login />;
  const Page = { today: Today, work: Work, library: Library, search: Search, pulse: Pulse }[page];
  return <Shell page={page} setPage={setPage}><Page key={page} setPage={setPage} /></Shell>;
}

createRoot(document.getElementById('root')).render(<AuthProvider><App /></AuthProvider>);
