export default function FilterPanel({ tags, filters, onChange }) {
  const toggle = (tagId) => {
    const next = filters.tags.includes(tagId)
      ? filters.tags.filter((t) => t !== tagId)
      : [...filters.tags, tagId]
    onChange({ ...filters, tags: next })
  }

  const sports = tags.filter((t) => t.category === 'sports')
  const social = tags.filter((t) => t.category === 'social')

  return (
    <div className="filter-panel">
      <div className="filter-section">
        <div className="filter-title">Availability</div>
        <div className="status-filters">
          {[
            { value: 'all',  label: 'All' },
            { value: 'open', label: '🟢 Open to Meet' },
            { value: 'busy', label: '⚫ Busy' },
          ].map(({ value, label }) => (
            <label key={value} className="status-filter-option">
              <input
                type="radio"
                name="statusFilter"
                value={value}
                checked={filters.status === value}
                onChange={() => onChange({ ...filters, status: value })}
              />
              {label}
            </label>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <div className="filter-title">Sports</div>
        <div className="tag-chips">
          {sports.map((tag) => (
            <button
              key={tag.id}
              className={`tag-chip ${filters.tags.includes(tag.id) ? 'selected' : ''}`}
              onClick={() => toggle(tag.id)}
            >
              {tag.emoji} #{tag.name}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <div className="filter-title">Social</div>
        <div className="tag-chips">
          {social.map((tag) => (
            <button
              key={tag.id}
              className={`tag-chip ${filters.tags.includes(tag.id) ? 'selected' : ''}`}
              onClick={() => toggle(tag.id)}
            >
              {tag.emoji} #{tag.name}
            </button>
          ))}
        </div>
      </div>

      {filters.tags.length > 0 && (
        <button
          className="clear-btn"
          onClick={() => onChange({ ...filters, tags: [] })}
        >
          Clear tag filters
        </button>
      )}
    </div>
  )
}
