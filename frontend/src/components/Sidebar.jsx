import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Dashboard', icon: '▣' },
  { to: '/compliance', label: 'Compliance Passport', icon: '✓' },
  { to: '/analytics', label: 'Analytics', icon: '◔' },
]

function Sidebar() {
  return (
    <aside className="w-full md:w-48 bg-white border-r border-gray-200 p-3 flex md:flex-col justify-between gap-4">
      <nav className="flex md:flex-col gap-2 overflow-auto">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-md text-sm whitespace-nowrap ${
                isActive ? 'bg-blue-50 text-ubBlue font-medium' : 'text-gray-600 hover:bg-gray-50'
              }`
            }
          >
            <span>{link.icon}</span>
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="text-xs text-gray-400">v1.0 · Hackathon Demo</div>
    </aside>
  )
}

export default Sidebar
