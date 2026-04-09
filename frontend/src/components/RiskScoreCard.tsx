import { AlertTriangle, TrendingUp } from 'lucide-react'
import { getThreatLevel } from '../utils/classnames'

interface RiskScoreCardProps {
  score: number
  trend?: number
  title: string
  subtitle?: string
}

export default function RiskScoreCard({ score, trend = 0, title, subtitle }: RiskScoreCardProps) {
  const threatLevel = getThreatLevel(score)
  const circumference = 2 * Math.PI * 45
  const strokeDashoffset = circumference - (score / 100) * circumference

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{title}</h3>
          {subtitle && <p className="text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
        </div>
        <AlertTriangle size={20} className={`${threatLevel.color}`} />
      </div>

      <div className="flex items-center justify-center gap-8">
        {/* Circular Progress */}
        <div className="relative w-28 h-28">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              className="text-slate-200 dark:text-slate-700"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className={`${threatLevel.color} transition-all duration-500`}
              strokeLinecap="round"
            />
          </svg>
          {/* Score text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">{score}</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Risk</span>
          </div>
        </div>

        {/* Details */}
        <div className="flex-1">
          <div className="mb-4">
            <p className={`text-2xl font-bold ${threatLevel.color}`}>{threatLevel.label}</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">Threat Level</p>
          </div>

          {trend !== 0 && (
            <div className={`flex items-center gap-1 ${trend > 0 ? 'text-red-600' : 'text-green-600'}`}>
              <TrendingUp size={16} className={trend < 0 ? 'rotate-180' : ''} />
              <span className="text-sm font-medium">{Math.abs(trend)}% {trend > 0 ? 'increase' : 'decrease'}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
