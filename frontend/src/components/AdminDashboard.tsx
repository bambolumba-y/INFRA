import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchSources,
  createSource,
  updateSource,
  deleteSource,
  fetchAdminHealth,
  type ScrapingSource,
} from "@/api/client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ArrowLeft, Plus, Trash2, Activity } from "lucide-react";

interface AddFormState {
  source_type: string;
  name: string;
  interval_minutes: number;
}

export function AdminDashboard({ onBack }: { onBack: () => void }) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<AddFormState>({
    source_type: "telegram",
    name: "",
    interval_minutes: 15,
  });

  const sourcesQuery = useQuery({
    queryKey: ["admin", "sources"],
    queryFn: fetchSources,
    staleTime: 10_000,
  });

  const healthQuery = useQuery({
    queryKey: ["admin", "health"],
    queryFn: fetchAdminHealth,
    staleTime: 10_000,
  });

  const createMut = useMutation({
    mutationFn: createSource,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "sources"] });
      setShowForm(false);
      setForm({ source_type: "telegram", name: "", interval_minutes: 15 });
    },
  });

  const updateMut = useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: { enabled?: boolean; interval_minutes?: number } }) =>
      updateSource(id, updates),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "sources"] });
    },
  });

  const deleteMut = useMutation({
    mutationFn: deleteSource,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "sources"] });
    },
  });

  const sources: ScrapingSource[] = sourcesQuery.data ?? [];

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="sticky top-0 z-10 border-b border-gray-800 bg-gray-950/90 backdrop-blur">
        <div className="mx-auto max-w-2xl px-4 py-3 flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-lg font-bold tracking-tight">Admin Panel</h1>
            <p className="text-xs text-gray-500">Manage sources & system</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-2xl space-y-4 px-4 py-4">
        {/* System Health */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            {healthQuery.isLoading ? (
              <p className="text-gray-500">Loading...</p>
            ) : healthQuery.error ? (
              <p className="text-red-400">Failed to load health data</p>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">Scheduler:</span>
                  <Badge variant={healthQuery.data?.scheduler_running ? "success" : "destructive"}>
                    {healthQuery.data?.scheduler_running ? "Running" : "Stopped"}
                  </Badge>
                </div>
                {healthQuery.data?.jobs.map((job) => (
                  <div key={job.id} className="text-xs text-gray-500">
                    {job.name} — next: {job.next_run ?? "N/A"}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sources */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Scraping Sources</CardTitle>
              <Button size="sm" onClick={() => setShowForm(!showForm)}>
                <Plus className="mr-1 h-3 w-3" />
                Add Source
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {showForm && (
              <form
                className="mb-4 space-y-3 rounded-lg border border-gray-800 p-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  createMut.mutate(form);
                }}
              >
                <div className="flex gap-2">
                  <select
                    className="rounded-md border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-200"
                    value={form.source_type}
                    onChange={(e) => setForm({ ...form, source_type: e.target.value })}
                  >
                    <option value="telegram">Telegram</option>
                    <option value="reddit">Reddit</option>
                    <option value="rss">RSS</option>
                  </select>
                  <input
                    className="flex-1 rounded-md border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-200 placeholder:text-gray-600"
                    placeholder="Channel / Subreddit / Feed URL"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    required
                  />
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-xs text-gray-400">Interval (min):</label>
                  <input
                    type="number"
                    min={1}
                    className="w-20 rounded-md border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-200"
                    value={form.interval_minutes}
                    onChange={(e) => setForm({ ...form, interval_minutes: Number(e.target.value) })}
                  />
                  <Button type="submit" size="sm" disabled={createMut.isPending}>
                    {createMut.isPending ? "Adding..." : "Add"}
                  </Button>
                </div>
              </form>
            )}

            {sourcesQuery.isLoading ? (
              <p className="text-gray-500">Loading sources...</p>
            ) : sources.length === 0 ? (
              <p className="text-gray-500">No sources configured yet.</p>
            ) : (
              <div className="space-y-2">
                {sources.map((src) => (
                  <div
                    key={src.id}
                    className="flex items-center justify-between rounded-lg border border-gray-800 p-3"
                  >
                    <div className="flex items-center gap-2">
                      <Badge variant={src.enabled ? "success" : "outline"}>
                        {src.source_type}
                      </Badge>
                      <span className="text-sm">{src.name}</span>
                      <span className="text-xs text-gray-500">every {src.interval_minutes}m</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          updateMut.mutate({
                            id: src.id,
                            updates: { enabled: !src.enabled },
                          })
                        }
                      >
                        {src.enabled ? "Disable" : "Enable"}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteMut.mutate(src.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-400" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
