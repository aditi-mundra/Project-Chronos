import { useCallback, useEffect, useState } from 'react';
import api from '../services/api.js';

/**
 * Access password control (master password only).
 *
 * The master password never expires. Passwords added here are one-time: the first
 * successful login consumes them and they move from UNUSED to USED. This panel is a
 * separate overlay: it never reads or changes teams, scores or the leaderboard.
 */

function stamp(value) {
  if (!value) return '-';
  const d = new Date(`${String(value).replace(' ', 'T')}Z`);
  return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString();
}

export default function PasswordControl({ onClose }) {
  const [data, setData] = useState({ unused: [], used: [] });
  const [text, setText] = useState('');
  const [count, setCount] = useState(5);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    try {
      setData(await api.listAdminPasswords());
      setError('');
    } catch (err) {
      setError(err?.message || 'Could not load passwords.');
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 5000); // a one-time password moves to USED by itself
    return () => clearInterval(id);
  }, [load]);

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const submit = async (payload) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const res = await api.addAdminPasswords(payload);
      const skipped = res.skipped?.length
        ? ` Skipped ${res.skipped.length}: ${res.skipped.map((s) => `${s.password} (${s.reason})`).join('; ')}.`
        : '';
      setNotice(`Added ${res.added.length} password${res.added.length === 1 ? '' : 's'}.${skipped}`);
      setText('');
      await load();
    } catch (err) {
      setError(err?.message || 'Could not add passwords.');
    } finally {
      setBusy(false);
    }
  };

  const addTyped = () => {
    const list = text.split(/[\n,;]+/).map((s) => s.trim()).filter(Boolean);
    if (!list.length) {
      setError('Type one password per line (or separate them with commas).');
      return;
    }
    submit({ passwords: list });
  };

  const revoke = async (id) => {
    try {
      await api.deleteAdminPassword(id);
      await load();
    } catch (err) {
      setError(err?.message || 'Could not remove the password.');
    }
  };

  const copy = (value) => {
    try {
      navigator.clipboard?.writeText(value);
    } catch {
      // clipboard is optional
    }
  };

  return (
    <div className="pw-overlay" role="dialog" aria-modal="true" aria-label="Access passwords">
      <div className="pw-panel">
        <div className="pw-head">
          <div>
            <h2>ACCESS PASSWORDS</h2>
            <p>
              The master password never expires. Passwords added here work <b>once</b>, then move to USED.
            </p>
          </div>
          <button className="lb-btn" onClick={onClose}>✕ Close</button>
        </div>

        <div className="pw-add">
          <textarea
            className="lb-input"
            rows={3}
            placeholder={'Add passwords: one per line (or comma separated)\nnight-owl-42\nteam-green-7'}
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={busy}
          />
          <div className="pw-add-actions">
            <button className="lb-btn on" onClick={addTyped} disabled={busy || !text.trim()}>＋ Add passwords</button>
            <span className="pw-or">or</span>
            <input
              className="lb-input pw-count"
              type="number"
              min="1"
              max="100"
              value={count}
              onChange={(e) => setCount(Math.max(1, Math.min(100, Number(e.target.value) || 1)))}
              disabled={busy}
            />
            <button className="lb-btn" onClick={() => submit({ generate: count })} disabled={busy}>
              ⚙ Generate {count} random
            </button>
          </div>
          {notice && <div className="pw-notice">{notice}</div>}
          {error && <div className="lb-error">{error}</div>}
        </div>

        <div className="pw-cols">
          <section>
            <h3>UNUSED <em>{data.unused.length}</em></h3>
            {data.unused.length === 0 ? (
              <div className="pw-empty">No unused passwords.</div>
            ) : (
              <ul>
                {data.unused.map((p) => (
                  <li key={p.id}>
                    <code>{p.password}</code>
                    <span className="pw-meta">added {stamp(p.created_at)}</span>
                    <span className="pw-actions">
                      <button className="lb-btn" onClick={() => copy(p.password)} title="Copy">⧉</button>
                      <button className="lb-btn lb-btn-lock" onClick={() => revoke(p.id)} title="Remove">✕</button>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h3>USED <em>{data.used.length}</em></h3>
            {data.used.length === 0 ? (
              <div className="pw-empty">No password has been used yet.</div>
            ) : (
              <ul>
                {data.used.map((p) => (
                  <li key={p.id} className="used">
                    <code>{p.password}</code>
                    <span className="pw-meta">used {stamp(p.used_at)}{p.used_from ? ` · ${p.used_from}` : ''}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
