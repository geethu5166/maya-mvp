// API Response Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface User {
  user_id: string;
  username: string;
  email: string;
  roles: string[];
}

// Event Types
export type EventType = 
  | 'ssh_brute_force'
  | 'unusual_database_query'
  | 'unusual_file_transfer'
  | 'privilege_escalation'
  | 'failed_login_attempt'
  | 'successful_login'
  | 'port_scanning'
  | 'malware_detected'
  | 'data_exfiltration';

export type SeverityLevel = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface SecurityEvent {
  event_id: string;
  event_type: EventType;
  severity: SeverityLevel;
  timestamp: string;
  user?: string;
  asset?: string;
  source_ip?: string;
  description: string;
  details: Record<string, any>;
}

// Incident Types
export type IncidentStatus = 'DETECTED' | 'INVESTIGATING' | 'CONTAINED' | 'RESOLVED';

export interface Incident {
  incident_id: string;
  title: string;
  description: string;
  severity: SeverityLevel;
  status: IncidentStatus;
  created_at: string;
  updated_at: string;
  events: SecurityEvent[];
  assignee?: string;
  tags?: string[];
}

// Alert Types
export interface Alert {
  alert_id: string;
  incident_id: string;
  message: string;
  severity: SeverityLevel;
  created_at: string;
  read: boolean;
}

// Detection Result
export interface DetectionResult {
  detected: boolean;
  severity_score: number;
  confidence: number;
  reasoning: string;
  recommended_action: string;
}

// Analytics
export interface AnalyticsData {
  total_events: number;
  total_incidents: number;
  critical_alerts: number;
  detection_accuracy: number;
  trends: TrendData[];
}

export interface TrendData {
  timestamp: string;
  count: number;
  severity: SeverityLevel;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Filters
export interface EventFilter {
  event_type?: EventType;
  severity?: SeverityLevel;
  user?: string;
  asset?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

export interface IncidentFilter {
  status?: IncidentStatus;
  severity?: SeverityLevel;
  assignee?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}
