import { apiClient } from "../api/http";

interface Payload {
    q: string;
    limit?: number;
}

export const malService = {
    getAnime: async (payload: Payload) => {

        return await apiClient.get('https://api.jikan.moe/v4/anime', {...payload})
    }
}