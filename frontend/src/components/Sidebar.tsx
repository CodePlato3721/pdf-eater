interface SidebarProps {
  files: string[]
}

export default function Sidebar({ files }: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="Uploaded documents">
      <h2 className="sidebar-title">Documents</h2>
      {files.length === 0 ? (
        <p className="sidebar-empty">No documents uploaded yet.</p>
      ) : (
        <ul className="sidebar-list">
          {files.map((file) => (
            <li key={file} className="sidebar-item">
              {file}
            </li>
          ))}
        </ul>
      )}
    </aside>
  )
}
