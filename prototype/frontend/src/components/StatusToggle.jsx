export default function StatusToggle({ status, onChange }) {
  return (
    <div className="status-toggle">
      <button
        className={`status-btn ${status === 'open' ? 'active open' : ''}`}
        onClick={() => onChange('open')}
      >
        🟢 Open to Meet
      </button>
      <button
        className={`status-btn ${status === 'busy' ? 'active busy' : ''}`}
        onClick={() => onChange('busy')}
      >
        ⚫ Busy
      </button>
    </div>
  )
}
