import * as React from "react";
import { AnimeCard } from "./AnimeCard";

interface AnimeData {
    animeName: string;
    imageUrl: string;
    aboutAnime: string;
}

interface AnimeCardListProps {
    animeList: AnimeData[];
}

export function AnimeCardList({ animeList }: AnimeCardListProps) {
    if (!animeList || animeList.length === 0) {
        return null;
    }

    return (
        <div className="w-full">
            <h2 className="mb-6 text-2xl font-bold text-neutral-100">
                Recommended Anime
            </h2>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                {animeList.map((anime, index) => (
                    <AnimeCard
                        key={`${anime.animeName}-${index}`}
                        animeName={anime.animeName}
                        imageUrl={anime.imageUrl}
                        aboutAnime={anime.aboutAnime}
                    />
                ))}
            </div>
        </div>
    );
}


