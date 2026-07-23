export function LoadingScreen({ label = 'Đang tải...' }: { label?: string }) {
  return (
    <div className="loading-screen">
      <div>
        <div className="pulse" aria-hidden="true" />
        <p style={{ marginTop: '1rem', color: 'var(--muted)' }}>{label}</p>
      </div>
    </div>
  );
}
