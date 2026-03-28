/**
 * API Client for Lighthouse Backend
 */

import axios, { AxiosError } from 'axios';

const API_BASE_URL = '/api/v1';

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API Types
export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string;
  bio?: string;
  avatar_url?: string;
  has_agreed_to_protocol: boolean;
  created_at: string;
}

export interface CitationPreview {
  target_output_id: string;
  citation_type: 'agree' | 'criticize' | 'develop' | 'reference';
  excerpt?: string;
}

export interface Output {
  id: string;
  user_id: string;
  title?: string;
  content: string;
  category: string;
  tags: string[];
  visibility: 'public' | 'private';
  ai_review_status: 'pending' | 'approved' | 'rejected';
  ai_review_flagged_categories?: string[];
  ai_review_feedback?: string;
  novelty_score?: number;
  originality_score?: number; // 0-100, Lighthouse Protocol originality score
  ai_generated_probability?: number; // 0-100%, probability content is AI-generated
  originality_warnings?: string[]; // Warning messages from originality checks
  originality_reasoning?: string; // LLM reasoning explaining the originality score
  referenced_entity_type?: string;
  referenced_entity_id?: string;
  referenced_entity_data?: {
    name?: string;
    address?: string;
    lat?: number;
    lng?: number;
    photos?: string[];
    rating?: number;
    [key: string]: any; // Allow additional fields for different entity types
  };
  hash: string;
  content_hash: string;
  previous_hash?: string;
  version: number;
  created_at: string;
  updated_at?: string;
  // Citation information (outputs this output cites)
  citing_outputs?: CitationPreview[];
}

export interface Citation {
  id: string;
  source_output_id: string;
  target_output_id: string;
  citation_type: 'agree' | 'criticize' | 'develop' | 'reference';
  excerpt?: string;
  created_at: string;
}

export interface CitationAuthorPreview {
  id: string;
  username: string;
  display_name: string;
  avatar_url?: string;
}

export interface CitationOutputPreview {
  id: string;
  content: string;
  category: string;
  created_at: string;
  author: CitationAuthorPreview;
}

export interface CitationWithOutput extends Citation {
  source_output: CitationOutputPreview;
}

export interface CitationStats {
  output_id: string;
  incoming_citations: number;
  outgoing_citations: number;
  incoming_by_type: {
    agree: number;
    criticize: number;
    develop: number;
    reference: number;
  };
}

export interface Agreement {
  user_id: string;
  output_id: string;
  agreed_at: string;
}

export interface FollowStats {
  follower_count: number;
  following_count: number;
  is_following: boolean;
}

export interface OutputFollowStats {
  follower_count: number;
  is_following: boolean;
}

export interface Follow {
  id: string;
  follower_id: string;
  followed_id: string;
  created_at: string;
}

export interface OutputFollow {
  id: string;
  user_id: string;
  output_id: string;
  created_at: string;
}

export interface HashVerificationResponse {
  output_id: string;
  content_hash_valid: boolean;
  full_hash_valid: boolean;
  hash_chain_valid: boolean;
  message: string;
}

// Auth API
export const authAPI = {
  register: (data: {
    email: string;
    username: string;
    password: string;
    display_name: string;
    age_verified: boolean;
  }) => api.post<User>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    api.post<{ access_token: string; refresh_token: string; user: User }>('/auth/login', data),

  me: () => api.get<User>('/auth/me'),

  refresh: (refresh_token: string) =>
    api.post<{ access_token: string }>('/auth/refresh', { refresh_token }),
};

// Users API
export const usersAPI = {
  updateProfile: (data: Partial<User>) => api.patch<User>('/users/me', data),

  search: (query: string, limit = 20) =>
    api.get<User[]>('/users/search', { params: { query, limit } }),

  getByUsername: (username: string) => api.get<User>(`/users/${username}`),

  follow: (username: string) => api.post(`/users/${username}/follow`),

  unfollow: (username: string) => api.delete(`/users/${username}/follow`),

  getFollowers: (username: string, limit = 20, offset = 0) =>
    api.get<User[]>(`/users/${username}/followers`, { params: { limit, offset } }),

  getFollowing: (username: string, limit = 20, offset = 0) =>
    api.get<User[]>(`/users/${username}/following`, { params: { limit, offset } }),

  getProtocolAgreementStatus: () =>
    api.get<{ has_agreed_to_protocol: boolean; user_id: string }>('/users/me/protocol-agreement'),

  agreeToProtocol: () => api.post<{ message: string }>('/users/me/protocol-agreement'),
};

// Outputs API
export const outputsAPI = {
  create: (data: {
    title?: string;
    content: string;
    category: string;
    tags?: string[];
    referenced_entity_type?: string;
    referenced_entity_id?: string;
    referenced_entity_data?: any;
  }) => api.post<Output>('/outputs/', data),

  update: (id: string, data: {
    title?: string;
    content?: string;
    category?: string;
    tags?: string[];
    referenced_entity_type?: string;
    referenced_entity_id?: string;
    referenced_entity_data?: any;
  }) => api.patch<Output>(`/outputs/${id}`, data),

  get: (id: string) => api.get<Output>(`/outputs/${id}`),

  getHistory: (id: string) => api.get<Output[]>(`/outputs/${id}/history`),

  getTimeline: (limit = 20, offset = 0, visibility?: string, category?: string) =>
    api.get<Output[]>('/outputs/', { params: { limit, offset, visibility, category } }),

  getUserOutputs: (username: string, limit = 20, offset = 0) =>
    api.get<Output[]>(`/outputs/user/${username}`, { params: { limit, offset } }),

  getMyRejected: () => api.get<Output[]>('/outputs/me/rejected'),

  verifyHash: (id: string) => api.get<HashVerificationResponse>(`/outputs/${id}/verify`),
};

// Citations API
export const citationsAPI = {
  create: (data: {
    source_output_id: string;
    target_output_id: string;
    citation_type: 'agree' | 'criticize' | 'develop' | 'reference';
    excerpt?: string;
  }) => api.post<Citation>('/citations/', data),

  getCiting: (outputId: string, citationType?: string, limit = 50, offset = 0) =>
    api.get<CitationWithOutput[]>(`/citations/output/${outputId}/citing`, {
      params: { citation_type: citationType, limit, offset },
    }),

  getCited: (outputId: string, citationType?: string, limit = 50, offset = 0) =>
    api.get<CitationWithOutput[]>(`/citations/output/${outputId}/cited`, {
      params: { citation_type: citationType, limit, offset },
    }),

  getStats: (outputId: string) =>
    api.get<CitationStats>(`/citations/output/${outputId}/stats`),

  getGraph: (outputId: string, depth = 2) =>
    api.get(`/citations/output/${outputId}/graph`, { params: { depth } }),

  delete: (citationId: string) => api.delete(`/citations/${citationId}`),
};

// Agreements API
export const agreementsAPI = {
  agree: (outputId: string) => api.post(`/agreements/?output_id=${outputId}`),

  removeAgreement: (outputId: string) => api.delete(`/agreements/${outputId}`),

  getUsersWhoAgreed: (outputId: string, limit = 50, offset = 0) =>
    api.get<Agreement[]>(`/agreements/output/${outputId}`, { params: { limit, offset } }),

  getUserAgreedOutputs: (username: string, limit = 50, offset = 0) =>
    api.get<Output[]>(`/agreements/user/${username}`, { params: { limit, offset } }),

  getCount: (outputId: string) =>
    api.get<{ output_id: string; agreement_count: number }>(`/agreements/output/${outputId}/count`),

  checkStatus: (outputId: string) =>
    api.get<{ has_agreed: boolean; output_id: string; agreed_at?: string }>(
      `/agreements/check/${outputId}`
    ),
};

// Follow API (User Follow)
export const followAPI = {
  followUser: (userId: string) =>
    api.post<Follow>('/follow/users', { followed_id: userId }),

  unfollowUser: (userId: string) =>
    api.delete(`/follow/users/${userId}`),

  getUserStats: (userId: string) =>
    api.get<FollowStats>(`/follow/users/${userId}/stats`),

  getFollowers: (userId: string, limit = 20, offset = 0) =>
    api.get<Follow[]>(`/follow/users/${userId}/followers`, { params: { limit, offset } }),

  getFollowing: (userId: string, limit = 20, offset = 0) =>
    api.get<Follow[]>(`/follow/users/${userId}/following`, { params: { limit, offset } }),
};

// Output Follow API
export const outputFollowAPI = {
  followOutput: (outputId: string) =>
    api.post<OutputFollow>('/follow/outputs', { output_id: outputId }),

  unfollowOutput: (outputId: string) =>
    api.delete(`/follow/outputs/${outputId}`),

  getOutputStats: (outputId: string) =>
    api.get<OutputFollowStats>(`/follow/outputs/${outputId}/stats`),

  getFollowers: (outputId: string, limit = 20, offset = 0) =>
    api.get<OutputFollow[]>(`/follow/outputs/${outputId}/followers`, { params: { limit, offset } }),
};

// Search API
export const searchAPI = {
  searchOutputs: (
    query: string,
    options?: {
      category?: string;
      tags?: string;
      visibility?: string;
      limit?: number;
      offset?: number;
    }
  ) =>
    api.get<Output[]>('/search/outputs', {
      params: { q: query, ...options },
    }),

  searchTags: (query: string, limit = 20) =>
    api.get<Array<{ tag: string; count: number }>>('/search/tags', {
      params: { q: query, limit },
    }),

  searchUsers: (query: string, limit = 20, offset = 0) =>
    api.get<User[]>('/search/users', {
      params: { q: query, limit, offset },
    }),
};

// Notifications API
export interface Notification {
  id: string;
  user_id: string;
  actor_id: string;
  type: 'follow' | 'unfollow' | 'citation' | 'agreement' | 'output_follow';
  output_id?: string;
  citation_id?: string;
  is_read: boolean;
  message?: string;
  created_at: string;
  actor_username: string;
  actor_display_name: string;
  actor_avatar_url?: string;
  output_content_preview?: string;
}

export interface NotificationStats {
  total_count: number;
  unread_count: number;
}

export const notificationsAPI = {
  getNotifications: (limit = 20, offset = 0, unread_only = false) =>
    api.get<Notification[]>('/notifications/', {
      params: { limit, offset, unread_only },
    }),

  getStats: () =>
    api.get<NotificationStats>('/notifications/stats'),

  markAsRead: (notificationIds: string[]) =>
    api.post('/notifications/mark-read', { notification_ids: notificationIds }),

  markAllAsRead: () =>
    api.post('/notifications/mark-all-read'),
};
