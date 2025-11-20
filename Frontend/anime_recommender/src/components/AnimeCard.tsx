import * as React from "react";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "./ui/card";

interface AnimeCardProps {
    animeName: string;
    imageUrl: string;
    aboutAnime: string;
}

export function AnimeCard({ animeName, imageUrl, aboutAnime }: AnimeCardProps) {
    return (
        <Card className="w-full max-w-sm overflow-hidden transition-all hover:shadow-lg">
            {/* Large Image */}
            <div className="relative h-80 w-full overflow-hidden">
                <img
                    src={imageUrl}
                    alt={animeName}
                    className="h-full w-full object-cover transition-transform duration-300 hover:scale-105"
                    onError={(e) => {
                        // Fallback image if loading fails
                        (e.target as HTMLImageElement).src = 
                            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='600'%3E%3Crect fill='%23262626' width='400' height='600'/%3E%3Ctext fill='%23737373' font-family='sans-serif' font-size='24' dy='10.5' font-weight='bold' x='50%25' y='50%25' text-anchor='middle'%3ENo Image%3C/text%3E%3C/svg%3E";
                    }}
                />
            </div>

            {/* Anime Name & Description */}
            <CardHeader>
                <CardTitle className="text-xl">{animeName}</CardTitle>
            </CardHeader>

            <CardContent>
                <CardDescription className="text-sm leading-relaxed">
                    {aboutAnime}
                </CardDescription>
            </CardContent>
        </Card>
    );
}

