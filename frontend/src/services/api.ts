import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8005';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Types
export interface Track {
  id: number;
  name: string;
  location: string;
  surface: string;
  circumference?: number;
  active: boolean;
}

export interface Horse {
  id: number;
  name: string;
  registration_number?: string;
  foaling_date?: string;
  sex?: string;
  color?: string;
  owner?: string;
  active: boolean;
}

export interface Driver {
  id: number;
  name: string;
  license_number?: string;
  hometown?: string;
  active: boolean;
}

export interface Trainer {
  id: number;
  name: string;
  license_number?: string;
  hometown?: string;
  active: boolean;
}

export interface Race {
  id: number;
  race_number: number;
  race_date: string;
  post_time?: string;
  distance?: number;
  purse?: number;
  race_type?: string;
  track_condition?: string;
  status: string;
  track: Track;
}

export interface RaceEntry {
  id: number;
  post_position: number;
  program_number?: string;
  morning_line_odds?: string;
  final_odds?: string;
  finish_position?: number;
  finish_time?: string;
  margin?: string;
  earnings?: number;
  scratched: boolean;
  disqualified: boolean;
  horse: Horse;
  driver: Driver;
  trainer: Trainer;
}

export interface RaceDetail extends Race {
  conditions?: string;
  weather?: string;
  temperature?: number;
  entries: RaceEntry[];
  created_at: string;
  updated_at?: string;
}

export interface HorseStats {
  horse_id: number;
  total_starts: number;
  wins: number;
  places: number;
  shows: number;
  win_percentage: number;
  place_percentage: number;
  show_percentage: number;
  total_earnings: number;
  average_earnings: number;
  best_time?: string;
  recent_form: string[];
}

export interface DriverStats {
  driver_id: number;
  total_starts: number;
  wins: number;
  places: number;
  shows: number;
  win_percentage: number;
  place_percentage: number;
  show_percentage: number;
  total_earnings: number;
  average_earnings: number;
}

export interface TrainerStats {
  trainer_id: number;
  total_starts: number;
  wins: number;
  places: number;
  shows: number;
  win_percentage: number;
  place_percentage: number;
  show_percentage: number;
  total_earnings: number;
  average_earnings: number;
}

export interface DashboardData {
  total_races_today: number;
  total_horses: number;
  total_drivers: number;
  total_trainers: number;
  recent_races: Race[];
  top_horses: any[];
  top_drivers: any[];
  top_trainers: any[];
}

// API functions
export const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  // Dashboard
  async getDashboardData(): Promise<DashboardData> {
    const response = await api.get('/api/analytics/dashboard');
    return response.data;
  },

  // Races
  async getRaces(params?: { date?: string; track_id?: number; limit?: number }): Promise<Race[]> {
    const response = await api.get('/api/races', { params });
    return response.data;
  },

  async getRace(id: number): Promise<RaceDetail> {
    const response = await api.get(`/api/races/${id}`);
    return response.data;
  },

  async getTodayRaces(): Promise<Race[]> {
    const response = await api.get('/api/races/today');
    return response.data;
  },

  async getRaceResults(raceId: number) {
    const response = await api.get(`/api/races/${raceId}/results`);
    return response.data;
  },

  // Horses
  async getHorses(params?: { name?: string; limit?: number }): Promise<Horse[]> {
    const response = await api.get('/api/horses', { params });
    return response.data;
  },

  async getHorse(id: number): Promise<Horse> {
    const response = await api.get(`/api/horses/${id}`);
    return response.data;
  },

  async getHorseStats(id: number): Promise<HorseStats> {
    const response = await api.get(`/api/horses/${id}/stats`);
    return response.data;
  },

  async getHorseRaces(id: number, limit?: number) {
    const response = await api.get(`/api/horses/${id}/races`, { params: { limit } });
    return response.data;
  },

  // Drivers
  async getDrivers(params?: { name?: string; limit?: number }): Promise<Driver[]> {
    const response = await api.get('/api/drivers', { params });
    return response.data;
  },

  async getDriver(id: number): Promise<Driver> {
    const response = await api.get(`/api/drivers/${id}`);
    return response.data;
  },

  async getDriverStats(id: number): Promise<DriverStats> {
    const response = await api.get(`/api/drivers/${id}/stats`);
    return response.data;
  },

  // Trainers
  async getTrainers(params?: { name?: string; limit?: number }): Promise<Trainer[]> {
    const response = await api.get('/api/trainers', { params });
    return response.data;
  },

  async getTrainer(id: number): Promise<Trainer> {
    const response = await api.get(`/api/trainers/${id}`);
    return response.data;
  },

  async getTrainerStats(id: number): Promise<TrainerStats> {
    const response = await api.get(`/api/trainers/${id}/stats`);
    return response.data;
  },

  // Tracks
  async getTracks(): Promise<Track[]> {
    const response = await api.get('/api/tracks');
    return response.data;
  },

  async getTrack(id: number): Promise<Track> {
    const response = await api.get(`/api/tracks/${id}`);
    return response.data;
  },

  // Analytics
  async getTopPerformers(category: string, metric: string, limit?: number) {
    const response = await api.get('/api/analytics/top-performers', {
      params: { category, metric, limit }
    });
    return response.data;
  },

  async getTrends(period: string) {
    const response = await api.get('/api/analytics/trends', {
      params: { period }
    });
    return response.data;
  },

  // Data management
  async fetchLatestData() {
    const response = await api.post('/api/data/fetch');
    return response.data;
  },

  async getDataStatus() {
    const response = await api.get('/api/data/status');
    return response.data;
  },
};

export default apiService;