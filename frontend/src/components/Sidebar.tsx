import { BarChart3, AlertCircle, Shield, Zap } from 'lucide-react'

interface SidebarProps {
  currentPage: 'dashboard' | 'incidents' | 'settings'
  setCurrentPage: (page: 'dashboard' | 'incidents' | 'settings') => void
}

export default function Sidebar({ currentPage, setCurrentPage }: SidebarProps) {
  const menuItems = [
    {
      id: 'dashboard',
      icon: BarChart3,
      label: 'Dashboard',
      badge: null,
    },
    {
      id: 'incidents',
      icon: AlertCircle,
      label: 'Incidents',
      badge: 3,
    },
    {
      id: 'settings',
      icon: Shield,
      label: 'Security',
      badge: null,
    },
  ]

  return (
    <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
            <Shield size={24} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-slate-900 dark:text-white text-lg">MAYA</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Enterprise SOC</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id
          
          return (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id as any)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Icon size={20} />
              <span className="flex-1 text-left font-medium">{item.label}</span>
              {item.badge && (
                <span className="bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                  {item.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-6 border-t border-slate-200 dark:border-slate-800">
        <button className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
          <Zap size={18} />
          <span>Run Playbook</span>
        </button>
      </div>
    </aside>
  )
}
