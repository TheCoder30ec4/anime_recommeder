"use client";

import * as React from "react";
import { Textarea } from "./textarea";
import { cn } from "../../lib/utils";
import {
    ArrowUpIcon,
    MoreHorizontal,
    ThumbsUp,
    ThumbsDown,
    Copy,
    RefreshCcw,
    Paperclip,
    Mic,
    Image,
} from "lucide-react";
import { ScrollArea } from "./scroll-area";
import { chatController } from "../../controllers/chat";
import { AnimeRecommendationResponse } from "../../services/BackendService";
import { cardDataController, FormattedAnimeCard } from "../../controllers/CardData";
import { AnimeCardList } from "../AnimeCardList";

interface UseAutoResizeTextareaProps {
    minHeight: number;
    maxHeight?: number;
}

function useAutoResizeTextarea({
    minHeight,
    maxHeight,
}: UseAutoResizeTextareaProps) {
    const textareaRef = React.useRef<HTMLTextAreaElement>(null);

    const adjustHeight = React.useCallback(
        (reset?: boolean) => {
            const textarea = textareaRef.current;
            if (!textarea) return;

            if (reset) {
                textarea.style.height = `${minHeight}px`;
                return;
            }

            // Temporarily shrink to get the right scrollHeight
            textarea.style.height = `${minHeight}px`;

            // Calculate new height
            const newHeight = Math.max(
                minHeight,
                Math.min(
                    textarea.scrollHeight,
                    maxHeight ?? Number.POSITIVE_INFINITY
                )
            );

            textarea.style.height = `${newHeight}px`;
        },
        [minHeight, maxHeight]
    );

    React.useEffect(() => {
        // Set initial height
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = `${minHeight}px`;
        }
    }, [minHeight]);

    // Adjust height on window resize
    React.useEffect(() => {
        const handleResize = () => adjustHeight();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [adjustHeight]);

    return { textareaRef, adjustHeight };
}

type ChatMessage = {
    role: "user" | "assistant";
    content: string;
};

const seededMessages: ChatMessage[] = [
    {
        role: "assistant",
        content: "Hi! 👋\nI'm your AI Anime Recommender. Tell me what kind of anime you're looking for, and I'll help you find the perfect match!",
    },
];

export function VercelV0Chat() {
    const [value, setValue] = React.useState("");
    const [messages, setMessages] = React.useState(seededMessages);
    const [isLoading, setIsLoading] = React.useState(false);
    const [animeCards, setAnimeCards] = React.useState<FormattedAnimeCard[]>([]);
    const { textareaRef, adjustHeight } = useAutoResizeTextarea({
        minHeight: 60,
        maxHeight: 200,
    });
    const scrollAreaRef = React.useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when messages change
    React.useEffect(() => {
        if (scrollAreaRef.current) {
            scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSendMessage = async () => {
        if (!value.trim() || isLoading) return;

        const userMessage = value.trim();
        setValue("");
        adjustHeight(true);

        // Add user message to chat
        setMessages(prev => [...prev, { role: "user", content: userMessage }]);
        setIsLoading(true);

        try {
            // Send message to backend via chatController
            const response: AnimeRecommendationResponse = await chatController.sendMessage(userMessage);

            console.log('Backend Response:', response);
            
            // If we have anime recommendations, fetch MAL data for each
            if (response.assistant_message.anime && response.assistant_message.anime.length > 0) {
                const cards = await cardDataController.fetchAnimeCards(response.assistant_message.anime);
                setAnimeCards(cards);
                
                // Don't add assistant message to chat when showing cards
                // Just show the cards below
            } else {
                // Only add assistant response to chat if no anime recommendations
                setMessages(prev => [
                    ...prev,
                    { 
                        role: "assistant", 
                        content: response.assistant_message.conversation
                    }
                ]);
            }
        } catch (error) {
            console.error("Error sending message:", error);
            // Add error message
            setMessages(prev => [
                ...prev,
                {
                    role: "assistant",
                    content: "Sorry, I encountered an error. Please try again later."
                }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (
        e: React.KeyboardEvent<HTMLTextAreaElement>
    ) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <section className="flex min-h-screen flex-col">
            <main className="flex flex-1 justify-center px-3 sm:px-6">
                <div className="flex w-full max-w-3xl flex-1 flex-col">
                    <ScrollArea className="flex-1 overflow-hidden" ref={scrollAreaRef}>
                        <div className="flex flex-col gap-10 px-1 py-12">
                            {messages.map((message, index) => {
                                const isUser = message.role === "user";

                                return (
                                    <div
                                        key={`${message.role}-${index}`}
                                        className={cn(
                                            "flex w-full gap-4",
                                            isUser
                                                ? "flex-row-reverse"
                                                : "flex-row"
                                        )}
                                    >
                                        <div
                                            className={cn(
                                                "mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold uppercase tracking-wide",
                                                isUser
                                                    ? "bg-neutral-800 text-neutral-200"
                                                    : "bg-emerald-400/10 text-emerald-300"
                                            )}
                                        >
                                            {isUser ? "You" : "AI"}
                                        </div>

                                        <div
                                            className={cn(
                                                "flex max-w-[640px] flex-col gap-3",
                                                isUser
                                                    ? "items-end text-right"
                                                    : "items-start text-left"
                                            )}
                                        >
                                            <div
                                                className={cn(
                                                    "w-full rounded-3xl border px-6 py-5 text-sm leading-7 shadow-[0_32px_80px_-48px_rgba(0,0,0,0.85)] backdrop-blur",
                                                    isUser
                                                        ? "border-neutral-800 bg-neutral-900/80 text-neutral-100"
                                                        : "border-neutral-800/70 bg-neutral-900/70 text-neutral-100"
                                                )}
                                            >
                                                <p className="whitespace-pre-wrap text-base leading-7 text-neutral-100">
                                                    {message.content}
                                                </p>
                                            </div>

                                            {!isUser && (
                                                <div className="flex flex-wrap items-center gap-1 text-neutral-500">
                                                    {[ThumbsUp, ThumbsDown, Copy, RefreshCcw, MoreHorizontal].map(
                                                        (Icon, iconIndex) => (
                                                            <button
                                                                key={`${message.role}-${index}-action-${iconIndex}`}
                                                                className="inline-flex h-8 w-8 items-center justify-center rounded-full transition hover:bg-neutral-800/70 hover:text-neutral-300"
                                                                aria-label="Message action"
                                                            >
                                                                <Icon className="h-4 w-4" />
                                                            </button>
                                                        )
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}

                            {/* Display anime cards if available */}
                            {animeCards.length > 0 && (
                                <div className="mt-8">
                                    <AnimeCardList animeList={animeCards} />
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </div>
            </main>

            <footer className="border-t border-neutral-900/80 bg-neutral-950/95">
                <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
                    <div className="rounded-3xl border border-neutral-800/70 bg-neutral-900/80 p-4 shadow-[0_32px_80px_-55px_rgba(0,0,0,0.9)]">
                        <div className="flex items-center justify-between px-1 text-neutral-500">
                            <button className="inline-flex h-8 w-8 items-center justify-center rounded-full transition hover:bg-neutral-800/80 hover:text-neutral-300">
                                <Paperclip className="h-4 w-4" />
                            </button>
                            <div className="flex items-center gap-1">
                                <button className="inline-flex h-8 w-8 items-center justify-center rounded-full transition hover:bg-neutral-800/80 hover:text-neutral-300">
                                    <Image className="h-4 w-4" />
                                </button>
                                <button className="inline-flex h-8 w-8 items-center justify-center rounded-full transition hover:bg-neutral-800/80 hover:text-neutral-300">
                                    <Mic className="h-4 w-4" />
                                </button>
                            </div>
                        </div>

                        <div className="relative mt-3">
                            <Textarea
                                ref={textareaRef}
                                value={value}
                                onChange={(e) => {
                                    setValue(e.target.value);
                                    adjustHeight();
                                }}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask anything"
                                className={cn(
                                    "w-full resize-none rounded-2xl border border-neutral-800/70 bg-neutral-900/90 pr-16 text-sm leading-6",
                                    "text-neutral-100 placeholder:text-neutral-500",
                                    "px-4 py-3",
                                    "focus:outline-none focus-visible:ring-0 focus-visible:ring-offset-0",
                                    "min-h-[52px]"
                                )}
                                style={{
                                    overflow: "hidden",
                                }}
                            />

                            <button
                                type="button"
                                onClick={handleSendMessage}
                                disabled={!value.trim() || isLoading}
                                className={cn(
                                    "absolute bottom-3.5 right-3.5 inline-flex h-9 w-9 items-center justify-center rounded-full border border-neutral-700 transition-colors",
                                    value.trim() && !isLoading
                                        ? "bg-neutral-100 text-neutral-900 hover:bg-white"
                                        : "bg-neutral-900/60 text-neutral-600 cursor-not-allowed"
                                )}
                            >
                                {isLoading ? (
                                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-neutral-500 border-t-neutral-900" />
                                ) : (
                                    <ArrowUpIcon
                                        className={cn(
                                            "h-4 w-4",
                                            value.trim()
                                                ? "text-neutral-900"
                                                : "text-neutral-500"
                                        )}
                                    />
                                )}
                                <span className="sr-only">Send</span>
                            </button>
                        </div>
                    </div>

                    <p className="mt-4 text-center text-xs text-neutral-600">
                        AI can make mistakes. Recommendations are personalized suggestions.
                    </p>
                </div>
            </footer>
        </section>
    );
}
