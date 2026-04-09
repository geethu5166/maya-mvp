export function classnames(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    'INFO': 'text-blue-500 bg-blue-50 dark:bg-blue-900/20',
    'LOW': 'text-green-500 bg-green-50 dark:bg-green-900/20',
    'MEDIUM': 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20',
    'HIGH': 'text-orange-500 bg-orange-50 dark:bg-orange-900/20',
    'CRITICAL': 'text-red-500 bg-red-50 dark:bg-red-900/20',
  };
  return colors[severity] || 'text-gray-500 bg-gray-50 dark:bg-gray-900/20';
}

export function getSeverityBadgeColor(severity: string): string {
  const colors: Record<string, string> = {
    'INFO': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    'LOW': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    'MEDIUM': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    'HIGH': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    'CRITICAL': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };
  return colors[severity] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
}

export function getThreatLevel(score: number): { label: string; color: string } {
  if (score >= 85) return { label: 'Critical', color: 'text-red-600' };
  if (score >= 70) return { label: 'High', color: 'text-orange-600' };
  if (score >= 50) return { label: 'Medium', color: 'text-yellow-600' };
  if (score >= 30) return { label: 'Low', color: 'text-blue-600' };
  return { label: 'Info', color: 'text-gray-600' };
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function formatDateFull(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(date);
}

export function getTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
