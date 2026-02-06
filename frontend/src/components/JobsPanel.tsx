import { useJobMatches } from "@/hooks/useApi";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Loader2 } from "lucide-react";

export function JobsPanel() {
  const { data: matches, isLoading, isError } = useJobMatches();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-gray-500" size={24} />
      </div>
    );
  }

  if (isError) {
    return <p className="py-8 text-center text-sm text-red-400">Failed to load job matches.</p>;
  }

  if (!matches || matches.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        No matches yet. Upload your resume to get started.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {matches.map((m) => (
        <Card key={m.job_id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                {m.title} — {m.company}
              </CardTitle>
              <Badge
                variant={
                  m.match_percentage >= 70
                    ? "success"
                    : m.match_percentage >= 40
                      ? "warning"
                      : "destructive"
                }
              >
                {m.match_percentage}% match
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <p>{m.recommendation}</p>
            {m.missing_skills.length > 0 && (
              <p className="mt-2 text-xs text-yellow-400">
                Missing: {m.missing_skills.join(", ")}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
