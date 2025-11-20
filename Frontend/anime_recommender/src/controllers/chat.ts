import { backendService, AnimeRecommendationResponse } from "../services/BackendService";

// Generate a unique session ID
const generateSessionId = (): string => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Get or create session ID from localStorage
const getSessionId = (): string => {
    let sessionId = localStorage.getItem('anime_chat_session_id');
    if (!sessionId) {
        sessionId = generateSessionId();
        localStorage.setItem('anime_chat_session_id', sessionId);
    }
    return sessionId;
};

export const chatController = {
    // Send a message and get anime recommendations
    sendMessage: async (query: string): Promise<AnimeRecommendationResponse> => {
        try {
            const sessionId = getSessionId();
            const response = await backendService.getAnimeRecommendations({
                query,
                session_id: sessionId
            });
            return response as AnimeRecommendationResponse;
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    },

    // Clear current session and start a new one
    clearSession: () => {
        localStorage.removeItem('anime_chat_session_id');
        return generateSessionId();
    },

    // Get current session ID
    getCurrentSessionId: () => {
        return getSessionId();
    }
};
