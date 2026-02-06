import type { NewsItem } from "@/api/client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ExternalLink } from "lucide-react";

function scoreBadgeVariant(score: number | null) {
  if (score === null) return "outline" as const;
  if (score >= 7) return "success" as const;
  if (score >= 4) return "warning" as const;
  return "destructive" as const;
}

function sourceIcon(source: string) {
  switch (source) {
    case "telegram":
      return "📡";
    case "reddit":
      return "🔴";
    case "rss":
      return "📰";
    default:
      return "🌐";
  }
}

export function NewsCard({ item }: { item: NewsItem }) {
  return (
    <Card className="transition-colors hover:border-gray-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{sourceIcon(item.source_type)}</span>
            <CardTitle>{item.title ?? "Untitled"}</CardTitle>
          </div>
          <Badge variant={scoreBadgeVariant(item.sentiment_score)}>
            {item.sentiment_score !== null
              ? `${item.sentiment_score}/10`
              : "N/A"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p>{item.summary ?? item.title ?? "No summary available"}</p>
        <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
          <span>
            {item.created_at
              ? new Date(item.created_at).toLocaleDateString()
              : ""}
          </span>
          {item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-blue-400 hover:text-blue-300"
            >
              Open <ExternalLink size={12} />
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
