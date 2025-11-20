interface Query {
    query: string;
    session_id?: string;
}

export const apiClient = {
    post: async <T>(url: string, query: Query): Promise<T> => {
        const res = await fetch(url, {
            method: 'POST',
            body: JSON.stringify(query),
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!res.ok) {
            const errorText = await res.text();
            console.error('API Error:', res.status, errorText);
            throw new Error(`Failed to fetch data: ${res.status} - ${errorText}`);
        }

        return res.json();
    },

    get: async <T>(url: string, params?: Record<string, string | number>): Promise<T> => {
        // Convert params object → query string
        const queryString = params
            ? '?' + new URLSearchParams(
                Object.entries(params).reduce((acc, [key, value]) => {
                    acc[key] = String(value);
                    return acc;
                }, {} as Record<string, string>)
            ).toString()
            : '';

        const res = await fetch(url + queryString, {
            method: 'GET',
        });

        if (!res.ok) {
            const errorText = await res.text();
            console.error('API Error:', res.status, errorText);
            throw new Error(`Failed to fetch data: ${res.status} - ${errorText}`);
        }

        return res.json();
    }
};
