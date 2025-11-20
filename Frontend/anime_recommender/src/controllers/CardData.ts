import { malService } from "../services/MalService";

interface AnimeFromBackend {
    anime_name: string;
    about_anime: string;
}

interface MALAnimeData {
    data?: Array<{
        mal_id?: number;
        title?: string;
        images?: {
            jpg?: {
                large_image_url?: string;
                image_url?: string;
            };
        };
    }>;
}

export interface FormattedAnimeCard {
    animeName: string;
    imageUrl: string;
    aboutAnime: string;
}

export const cardDataController = {
    // Fetch anime data from MAL API based on backend recommendations
    fetchAnimeCards: async (animeList: AnimeFromBackend[]): Promise<FormattedAnimeCard[]> => {
        try {
            const animeDataPromises = animeList.map(async (anime) => {
                try {
                    const malData = await malService.getAnime({
                        q: anime.anime_name,
                        limit: 1
                    }) as MALAnimeData;
                    
                    console.log(`MAL Data for "${anime.anime_name}":`, malData);

                    // Extract image URL from MAL data
                    const imageUrl = malData?.data?.[0]?.images?.jpg?.large_image_url 
                        || malData?.data?.[0]?.images?.jpg?.image_url
                        || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='600'%3E%3Crect fill='%23262626' width='400' height='600'/%3E%3Ctext fill='%23737373' font-family='sans-serif' font-size='24' dy='10.5' font-weight='bold' x='50%25' y='50%25' text-anchor='middle'%3ENo Image%3C/text%3E%3C/svg%3E";

                    return {
                        animeName: anime.anime_name,
                        imageUrl: imageUrl,
                        aboutAnime: anime.about_anime
                    };
                } catch (error) {
                    console.error(`Error fetching MAL data for "${anime.anime_name}":`, error);
                    return {
                        animeName: anime.anime_name,
                        imageUrl: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='600'%3E%3Crect fill='%23262626' width='400' height='600'/%3E%3Ctext fill='%23737373' font-family='sans-serif' font-size='24' dy='10.5' font-weight='bold' x='50%25' y='50%25' text-anchor='middle'%3ENo Image%3C/text%3E%3C/svg%3E",
                        aboutAnime: anime.about_anime
                    };
                }
            });

            const results = await Promise.all(animeDataPromises);
            console.log('Formatted anime card data:', results);
            return results;
        } catch (error) {
            console.error('Error fetching anime cards:', error);
            throw error;
        }
    }
};

