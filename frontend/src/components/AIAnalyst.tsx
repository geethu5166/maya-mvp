import { Sparkles, Lightbulb } from "lucide-react"

interface AIAnalystProps {
  insight: string
  recommendations: string[]
  confidence: number
}

export default function AIAnalyst({ insight, recommendations, confidence }: AIAnalystProps) {
  return (
    <div className="card-lg bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border-l-4 border-blue-500">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
          <Sparkles size={20} className="text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-900 dark:text-white">AI Analyst</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">Confidence: {(confidence * 100).toFixed(0)}%</p>
        </div>
      </div>

      <p className="text-slate-900 dark:text-slate-100 mb-4">{insight}</p>

      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <Lightbulb size={16} />
          Recommendations
        </h4>
        <ul className="space-y-2">
          {recommendations.map((rec, idx) => (
            <li key={idx} className="text-sm text-slate-700 dark:text-slate-300 flex gap-2">
              <span className="text-blue-500 font-bold">{idx + 1}.</span>
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}