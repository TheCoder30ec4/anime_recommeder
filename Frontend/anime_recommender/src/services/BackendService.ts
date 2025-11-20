import { apiClient } from "../api/http";


interface Payload {
   query: string;
   session_id?: string;
}

export interface AnimeRecommendationResponse {
   session_id: string;
   query: string;
   assistant_message: {
      conversation: string;
      anime: Array<{
         anime_name: string;
         about_anime: string;
      }>;
      suggestion_for_next_question: string;
   };
}

// Get API URL from environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const backendService = {

    getAnimeRecommendations: async (payload: Payload) => {
        return await apiClient.post(`${API_BASE_URL}/chat/recommender`, payload);
    }
}
