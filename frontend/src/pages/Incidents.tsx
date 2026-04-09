import { useState } from 'react'
import { usePaginatedIncidents } from '../hooks/useQuery'
import { AlertCircle, Plus, Filter, Clock, User, Tag } from 'lucide-react'
import { getSeverityBadgeColor, formatDateFull } from '../utils/classnames'

export default function Incidents() {
  const { incidents, loading, page, setPage, total } = usePaginatedIncidents()
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null)

  const statuses = ['DETECTED', 'INVESTIGATING', 'CONTAINED', 'RESOLVED']

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Incidents</h1>
          <p className="text-slate-600 dark:text-slate-400">Manage and track security incidents</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus size={20} />
          New Incident
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search incidents..."
            className="input-field"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="input-field"
        >
          <option value="">All Status</option>
          {statuses.map(status => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
        <button className="btn-secondary flex items-center gap-2 px-4">
          <Filter size={18} />
          More Filters
        </button>
      </div>

      {/* Incidents List */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-12 text-slate-500">
            Loading incidents...
          </div>
        ) : incidents.length === 0 ? (
          <div className="text-center py-12">
            <AlertCircle size={48} className="mx-auto text-slate-300 dark:text-slate-700 mb-3" />
            <p className="text-slate-500 dark:text-slate-400">No incidents found</p>
          </div>
        ) : (
          incidents.map((incident) => (
            <div
              key={incident.incident_id}
              onClick={() => setSelectedIncident(selectedIncident === incident.incident_id ? null : incident.incident_id)}
              className="card p-6 cursor-pointer hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{incident.title}</h3>
                    <span className={`badge-threat ${getSeverityBadgeColor(incident.severity)}`}>
                      {incident.severity}
                    </span>
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                      incident.status === 'RESOLVED'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : incident.status === 'CONTAINED'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                        : 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
                    }`}>
                      {incident.status}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400">{incident.description}</p>
                </div>
              </div>

              {/* Expanded Details */}
              {selectedIncident === incident.incident_id && (
                <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-800 space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Created</p>
                      <p className="text-sm text-slate-900 dark:text-white">{formatDateFull(incident.created_at)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Last Updated</p>
                      <p className="text-sm text-slate-900 dark:text-white">{formatDateFull(incident.updated_at)}</p>
                    </div>
                    {incident.assignee && (
                      <div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1">
                          <User size={14} />
                          Assignee
                        </p>
                        <p className="text-sm text-slate-900 dark:text-white">{incident.assignee}</p>
                      </div>
                    )}
                    <div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Events</p>
                      <p className="text-sm text-slate-900 dark:text-white">{incident.events.length} events</p>
                    </div>
                  </div>

                  {/* Tags */}
                  {incident.tags && incident.tags.length > 0 && (
                    <div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Tags</p>
                      <div className="flex flex-wrap gap-2">
                        {incident.tags.map((tag, idx) => (
                          <span key={idx} className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                            <Tag size={14} />
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Timeline */}
                  <div>
                    <h4 className="font-semibold text-slate-900 dark:text-white mb-3">Related Events</h4>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {incident.events.slice(0, 3).map((event, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg text-sm">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-xs bg-slate-200 dark:bg-slate-700 px-2 py-1 rounded">
                              {event.event_type}
                            </span>
                            <span className={`badge-threat ${getSeverityBadgeColor(event.severity)}`}>
                              {event.severity}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 dark:text-slate-400">{formatDateFull(event.timestamp)}</p>
                        </div>
                      ))}
                      {incident.events.length > 3 && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 text-center py-2">
                          +{incident.events.length - 3} more events
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                    <button className="btn-primary text-sm">
                      Investigate
                    </button>
                    <button className="btn-secondary text-sm">
                      Assign
                    </button>
                    <button className="btn-secondary text-sm">
                      Change Status
                    </button>
                  </div>
                </div>
              )}

              {/* Footer */}
              <div className="flex items-center justify-between mt-4 text-xs text-slate-500 dark:text-slate-400">
                <div className="flex items-center gap-4">
                  {incident.assignee && (
                    <div className="flex items-center gap-1">
                      <User size={14} />
                      {incident.assignee}
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <Clock size={14} />
                    {incident.events.length} events
                  </div>
                </div>
                <span>{formatDateFull(incident.created_at)}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {!loading && incidents.length > 0 && (
        <div className="flex items-center justify-between pt-6 border-t border-slate-200 dark:border-slate-800">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total} incidents
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="btn-secondary disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page * 20 >= total}
              className="btn-secondary disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
