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

export const backendService = {

    getAnimeRecommendations: async (payload: Payload) => {
        return await apiClient.post("http://localhost:8000/chat/recommender", payload);
    }
}
