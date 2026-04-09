import { User } from '../types'
import { Bell, Sun, Moon, LogOut, Settings } from 'lucide-react'

interface HeaderProps {
  darkMode: boolean
  onToggleDarkMode: () => void
  onLogout: () => void
  user: User
}

export default function Header({ darkMode, onToggleDarkMode, onLogout, user }: HeaderProps) {
  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex items-center justify-between">
      <div className="flex-1">
        <h1 className="text-xl font-bold text-slate-900 dark:text-white">MAYA SOC</h1>
      </div>

      <div className="flex items-center gap-6">
        {/* Notifications */}
        <button className="relative p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
          <Bell size={20} className="text-slate-600 dark:text-slate-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={onToggleDarkMode}
          className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
        >
          {darkMode ? (
            <Sun size={20} className="text-yellow-500" />
          ) : (
            <Moon size={20} className="text-slate-600" />
          )}
        </button>

        {/* Settings */}
        <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
          <Settings size={20} className="text-slate-600 dark:text-slate-400" />
        </button>

        {/* User Menu */}
        <div className="flex items-center gap-3 pl-6 border-l border-slate-200 dark:border-slate-800">
          <div className="text-right">
            <p className="text-sm font-medium text-slate-900 dark:text-white">{user.username}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">{user.roles[0]}</p>
          </div>
          
          <button
            onClick={onLogout}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            title="Logout"
          >
            <LogOut size={18} className="text-slate-600 dark:text-slate-400" />
          </button>
        </div>
      </div>
    </header>
  )
}
