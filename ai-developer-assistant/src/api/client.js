const API_BASE =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE) ||
  'http://127.0.0.1:8000';

async function _request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE}${path}`, opts);
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) throw Object.assign(new Error(data.detail || res.statusText), { status: res.status, data });
  return data;
}

export const api = {
  health: () => _request('GET', '/health'),

  createSession: (repo_path, bug_report, consent_confirmed, pre_scan) =>
    _request('POST', '/sessions', { repo_path, bug_report, consent_confirmed, pre_scan }),

  investigate: (session_id) =>
    _request('POST', `/sessions/${session_id}/investigate`),

  decision: (session_id, decision, patch_hash, approver, comment) =>
    _request('POST', `/sessions/${session_id}/decision`, {
      decision,
      patch_hash,
      approver,
      comment,
    }),

  getSession: (session_id) =>
    _request('GET', `/sessions/${session_id}`),

  listSessions: () =>
    _request('GET', '/sessions'),

  listProjects: () =>
    _request('GET', '/projects'),

  scanProject: (repo_path) =>
    _request('POST', '/projects/scan', { repo_path }),

  getSecurity: () =>
    _request('GET', '/security'),
};
