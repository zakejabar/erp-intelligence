"use client";

import { useState } from "react";
import { runAgent } from "@/lib/api";

export default function Home() {
    const [query, setQuery] = useState("");
    const [file, setFile] = useState<File | null>(null);
    const [response, setResponse] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !query) return alert("Please provide both file and query");

        setLoading(true);
        try {
            // Hardcoded user_id for now
            const result = await runAgent(query, "user_123", file);
            setResponse(result.answer);
        } catch (error) {
            console.error(error);
            setResponse("Error running agent");
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-24 bg-gray-900 text-white">
            <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
                <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
                    ERP Intelligence Agent
                </p>
            </div>

            <div className="relative flex place-items-center before:absolute before:h-[300px] before:w-[480px] before:-translate-x-1/2 before:rounded-full before:bg-gradient-to-br before:from-transparent before:to-blue-700 before:opacity-10 before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-[180px] after:w-[240px] after:translate-x-1/3 after:bg-gradient-to-t after:from-sky-900 after:via-[#0141ff] after:opacity-40 after:blur-2xl after:content-['']">
                <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-lg z-10">

                    <label className="block">
                        <span className="text-gray-300">Upload Invoice (JSON/CSV)</span>
                        <input
                            type="file"
                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                            className="mt-1 block w-full text-sm text-gray-400
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-md file:border-0
                    file:text-sm file:font-semibold
                    file:bg-blue-600 file:text-white
                    hover:file:bg-blue-700"
                        />
                    </label>

                    <textarea
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Ask about the invoice..."
                        className="w-full p-3 rounded bg-gray-800 border border-gray-700 focus:outline-none focus:border-blue-500 h-32"
                    />

                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
                    >
                        {loading ? "Thinking..." : "Analyze"}
                    </button>
                </form>
            </div>

            <div className="mb-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:grid-cols-1 lg:text-left">
                {response && (
                    <div className="p-6 bg-gray-800 rounded-lg border border-gray-700 mt-8">
                        <h3 className="text-xl font-bold mb-4 text-blue-400">Agent Response:</h3>
                        <div className="whitespace-pre-wrap">{response}</div>
                    </div>
                )}
            </div>
        </main>
    );
}