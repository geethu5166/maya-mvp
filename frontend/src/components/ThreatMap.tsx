import { Globe, Activity } from "lucide-react"

interface ThreatData {
  country: string
  count: number
  severity: string
}

interface ThreatMapProps {
  threats: ThreatData[]
}

export default function ThreatMap({ threats = [] }: ThreatMapProps) {
  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-6 p-6 border-b border-slate-200 dark:border-slate-800">
        <Globe size={24} className="text-red-500" />
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Threat Map</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">Global attack origins</p>
        </div>
      </div>

      <div className="p-6">
        <div className="space-y-3">
          {threats.map((threat) => (
            <div key={threat.country} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition">
              <div className="flex items-center gap-3">
                <Activity size={18} className={
                  threat.severity === "CRITICAL" ? "text-red-500" :
                  threat.severity === "HIGH" ? "text-orange-500" :
                  threat.severity === "MEDIUM" ? "text-yellow-500" :
                  "text-green-500"
                } />
                <div>
                  <p className="font-medium text-slate-900 dark:text-white">{threat.country}</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{threat.severity} severity</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-slate-900 dark:text-white">{threat.count}</p>
                <span className={`text-xs px-2 py-1 rounded font-medium ${
                  threat.severity === "CRITICAL" ? "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300" :
                  threat.severity === "HIGH" ? "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300" :
                  threat.severity === "MEDIUM" ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300" :
                  "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                }`}>
                  {threat.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}