import { useNews } from "@/hooks/useApi";
import { NewsCard } from "@/components/NewsCard";
import { Loader2 } from "lucide-react";

export function NewsFeed() {
  const { data: news, isLoading, isError } = useNews();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-gray-500" size={24} />
      </div>
    );
  }

  if (isError) {
    return <p className="py-8 text-center text-sm text-red-400">Failed to load news feed.</p>;
  }

  if (!news || news.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        No news available. Scrapers are warming up…
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {news.map((item) => (
        <NewsCard key={item.id} item={item} />
      ))}
    </div>
  );
}
