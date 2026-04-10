import { useState, useCallback, useEffect } from 'react';
import axios, { AxiosInstance } from 'axios';
import { LoginRequest, LoginResponse, SecurityEvent, Incident, PaginatedResponse, User } from '../types';

let apiClient: AxiosInstance;

// Initialize API client
function initializeApiClient() {
  const token = localStorage.getItem('token');
  apiClient = axios.create({
    baseURL: '/api/v1',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return apiClient;
}

function getApiClient() {
  if (!apiClient) {
    initializeApiClient();
  }
  return apiClient;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (credentials: LoginRequest) => {
    setLoading(true);
    setError(null);
    try {
      const client = getApiClient();
      const response = await client.post<LoginResponse>('/auth/login', credentials);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setUser(userData);
      
      // Update default header
      client.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return userData;
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setUser(null);
    getApiClient().defaults.headers.common['Authorization'] = '';
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token && !user) {
      // Could fetch current user here
      initializeApiClient();
    }
  }, [user]);

  return { user, loading, error, login, logout };
}

export function useQuery<T>(url: string, dependencies: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      try {
        setLoading(true);
        const client = getApiClient();
        const response = await client.get<T>(url);
        if (mounted) {
          setData(response.data);
          setError(null);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'Failed to fetch data');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchData();
    return () => {
      mounted = false;
    };
  }, dependencies);

  return { data, loading, error };
}

export function usePaginatedEvents(filters?: any) {
  const [page, setPage] = useState(1);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    let mounted = true;

    const fetchEvents = async () => {
      try {
        setLoading(true);
        const client = getApiClient();
        const response = await client.get<PaginatedResponse<SecurityEvent>>(
          `/events?page=${page}&limit=20`,
          { params: filters }
        );
        if (mounted) {
          setEvents(response.data.items);
          setTotal(response.data.total);
          setError(null);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'Failed to fetch events');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchEvents();
    return () => {
      mounted = false;
    };
  }, [page, filters]);

  return { events, loading, error, total, page, setPage };
}

export function usePaginatedIncidents(filters?: any) {
  const [page, setPage] = useState(1);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    let mounted = true;

    const fetchIncidents = async () => {
      try {
        setLoading(true);
        const client = getApiClient();
        const response = await client.get<PaginatedResponse<Incident>>(
          `/incidents?page=${page}&limit=20`,
          { params: filters }
        );
        if (mounted) {
          setIncidents(response.data.items);
          setTotal(response.data.total);
          setError(null);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'Failed to fetch incidents');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchIncidents();
    return () => {
      mounted = false;
    };
  }, [page, filters]);

  return { incidents, loading, error, total, page, setPage };
}

export async function createIncident(data: {
  title: string;
  description: string;
  severity: string;
  event_ids?: string[];
}) {
  const client = getApiClient();
  return client.post<Incident>('/incidents', data);
}

export async function updateIncident(
  incidentId: string,
  data: Partial<Incident>
) {
  const client = getApiClient();
  return client.patch<Incident>(`/incidents/${incidentId}`, data);
}

export async function acknowledgeAlert(alertId: string) {
  const client = getApiClient();
  return client.post(`/alerts/${alertId}/acknowledge`);
}