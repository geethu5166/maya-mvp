import { useState, useEffect } from "react"
import { usePaginatedEvents, useQuery } from "../hooks/useQuery"
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import AlertTable from "../components/AlertTable"
import RiskScoreCard from "../components/RiskScoreCard"
import AIAnalyst from "../components/AIAnalyst"
import ThreatMap from "../components/ThreatMap"
import { TrendingUp, Activity, AlertTriangle, Shield } from "lucide-react"

export default function Dashboard() {
  const { events, loading } = usePaginatedEvents()
  const [selectedEvent, setSelectedEvent] = useState(null)

  const trendData = [
    { time: "00:00", alerts: 12, incidents: 3 },
    { time: "04:00", alerts: 19, incidents: 5 },
    { time: "08:00", alerts: 25, incidents: 7 },
    { time: "12:00", alerts: 42, incidents: 12 },
    { time: "16:00", alerts: 31, incidents: 8 },
    { time: "20:00", alerts: 28, incidents: 6 },
  ]

  const severityData = [
    { name: "Critical", value: 12, color: "#dc2626" },
    { name: "High", value: 24, color: "#ea580c" },
    { name: "Medium", value: 45, color: "#f59e0b" },
    { name: "Low", value: 19, color: "#10b981" },
  ]

  const threatsByCountry = [
    { country: "China", count: 124, severity: "CRITICAL" },
    { country: "Russia", count: 89, severity: "HIGH" },
    { country: "Unknown", count: 56, severity: "MEDIUM" },
    { country: "Brazil", count: 34, severity: "LOW" },
  ]

  return (
    <div className="p-8 space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Total Events</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">2,847</p>
            </div>
            <Activity size={40} className="text-blue-500 opacity-20" />
          </div>
          <p className="text-xs text-green-600 mt-2">↑ 12% from yesterday</p>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Critical Alerts</p>
              <p className="text-3xl font-bold text-red-600">12</p>
            </div>
            <AlertTriangle size={40} className="text-red-500 opacity-20" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Active Incidents</p>
              <p className="text-3xl font-bold text-orange-600">5</p>
            </div>
            <Shield size={40} className="text-orange-500 opacity-20" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Detection Rate</p>
              <p className="text-3xl font-bold text-green-600">98.7%</p>
            </div>
            <TrendingUp size={40} className="text-green-500 opacity-20" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="p-6 border-b border-slate-200 dark:border-slate-800">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Alert Trends</h3>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="alerts" stroke="#3b82f6" />
                <Line type="monotone" dataKey="incidents" stroke="#ef4444" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="p-6 border-b border-slate-200 dark:border-slate-800">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Severity Distribution</h3>
          </div>
          <div className="p-6 flex justify-center">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={severityData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AlertTable events={events || []} onSelectEvent={setSelectedEvent} />
        </div>
        <div className="space-y-6">
          <RiskScoreCard riskScore={42} />
          <ThreatMap threats={threatsByCountry} />
        </div>
      </div>

      {selectedEvent && (
        <AIAnalyst 
          insight="Analysis of the selected security event indicates potential lateral movement"
          recommendations={["Isolate the compromised host", "Review account privileges", "Check command history"]}
          confidence={0.87}
        />
      )}
    </div>
  )
}