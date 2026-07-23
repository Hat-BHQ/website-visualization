import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '@/auth/useAuth';
import { ErrorState } from '@/components/ErrorState';

export function LoginPage() {
  const navigate = useNavigate();
  const auth = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    try {
      await auth.login(email, password);
      navigate('/modules', { replace: true });
    } catch {
      setSubmitError('Email hoặc mật khẩu không đúng.');
    }
  }

  return (
    <div className="hero-grid">
      <aside className="hero-aside">
        <div className="hero-brand">
          <span className="brand-mark">HQ</span>
          <span>HQ Portal</span>
        </div>

        <div className="hero-content">
          <h1>One portal for every HQ workflow.</h1>
          <p>
            Đăng nhập một lần, chọn đúng module, và đi thẳng vào các công cụ dành cho HQA hoặc HQS với quyền được kiểm tra từ backend.
          </p>

          <div className="hero-pills">
            <span className="pill">Secure JWT</span>
            <span className="pill">Module-based access</span>
            <span className="pill">React + Vite</span>
          </div>

          <div className="hero-card">
            <strong style={{ display: 'block', marginBottom: '0.5rem' }}>HQ Portal</strong>
            <span style={{ color: 'rgba(255,255,255,0.75)' }}>HQA marketplace, HQS operations, system access.</span>
          </div>
        </div>
      </aside>

      <section className="auth-panel">
        <div className="auth-card">
          <div style={{ marginBottom: '1.5rem' }}>
            <div className="hero-brand" style={{ color: 'var(--text)' }}>
              <span className="brand-mark" style={{ background: 'linear-gradient(135deg, var(--hqa), var(--hqs))', color: 'white' }}>HQ</span>
              <span>HQ Portal</span>
            </div>
            <h2 style={{ marginBottom: 0 }}>Đăng nhập</h2>
            <p style={{ color: 'var(--muted)', lineHeight: 1.7 }}>Sử dụng tài khoản được backend cấp module và quyền tương ứng.</p>
          </div>

          <form className="field-stack" onSubmit={handleSubmit}>
            <label className="field-label" htmlFor="email">Email</label>
            <input id="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="admin.hqa@company.com" />

            <label className="field-label" htmlFor="password">Mật khẩu</label>
            <input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="••••••••" />

            {(auth.error || submitError) ? (
              <ErrorState title="Đăng nhập thất bại" message={auth.error ?? submitError ?? 'Không thể đăng nhập.'} />
            ) : null}

            <button className="action-button" type="submit" disabled={auth.isLoading}>
              {auth.isLoading ? 'Đang đăng nhập...' : 'Đăng nhập'}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
