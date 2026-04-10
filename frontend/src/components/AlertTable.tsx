import { SecurityEvent } from "../types"
import { ChevronRight, Search } from "lucide-react"
import { getSeverityBadgeColor, getTimeAgo } from "../utils/classnames"
import { useState } from "react"

interface AlertTableProps {
  events: SecurityEvent[]
  onSelectEvent?: (event: SecurityEvent) => void
}

export default function AlertTable({ events, onSelectEvent }: AlertTableProps) {
  const [filter, setFilter] = useState("")
  const [sortBy] = useState<"time" | "severity">("time")

  const filteredEvents = events.filter(e =>
    e.event_type.toLowerCase().includes(filter.toLowerCase()) ||
    e.user?.toLowerCase().includes(filter.toLowerCase()) ||
    e.asset?.toLowerCase().includes(filter.toLowerCase())
  )

  const sortedEvents = [...filteredEvents].sort((a, b) => {
    if (sortBy === "time") {
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    } else {
      const severityOrder = { CRITICAL: 5, HIGH: 4, MEDIUM: 3, LOW: 2, INFO: 1 }
      return (severityOrder[b.severity as keyof typeof severityOrder] || 0) -
             (severityOrder[a.severity as keyof typeof severityOrder] || 0)
    }
  })

  return (
    <div className="card">
      <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Security Events</h2>
        <span className="text-sm bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full">
          {events.length} events
        </span>
      </div>

      <div className="p-6 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search events..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900 dark:text-white">Event Type</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900 dark:text-white">Severity</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900 dark:text-white">Time</th>
              <th className="px-6 py-3 text-right text-sm font-semibold text-slate-900 dark:text-white">Action</th>
            </tr>
          </thead>
          <tbody>
            {sortedEvents.map((event) => (
              <tr key={event.event_id} className="border-b border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer" onClick={() => onSelectEvent?.(event)}>
                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white">{event.event_type}</td>
                <td className="px-6 py-4 text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityBadgeColor(event.severity)}`}>
                    {event.severity}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{getTimeAgo(event.timestamp)}</td>
                <td className="px-6 py-4 text-right"><ChevronRight size={18} className="text-blue-500" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}