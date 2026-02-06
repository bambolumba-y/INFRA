import { useAppStore, type TabType } from "@/store/appStore";
import { Button } from "@/components/ui/Button";
import { Newspaper, Briefcase, User } from "lucide-react";

const TABS: { key: TabType; label: string; icon: typeof Newspaper }[] = [
  { key: "news", label: "News", icon: Newspaper },
  { key: "jobs", label: "Jobs", icon: Briefcase },
  { key: "profile", label: "Profile", icon: User },
];

const SOURCES = [
  { key: null, label: "All" },
  { key: "telegram", label: "📡 Telegram" },
  { key: "reddit", label: "🔴 Reddit" },
  { key: "rss", label: "📰 RSS" },
] as const;

export function FilterBar() {
  const activeTab = useAppStore((s) => s.activeTab);
  const setActiveTab = useAppStore((s) => s.setActiveTab);
  const sourceFilter = useAppStore((s) => s.sourceFilter);
  const setSourceFilter = useAppStore((s) => s.setSourceFilter);

  return (
    <div className="space-y-3">
      {/* Tab bar */}
      <div className="flex gap-1 rounded-lg bg-gray-900 p-1">
        {TABS.map(({ key, label, icon: Icon }) => (
          <Button
            key={key}
            variant={activeTab === key ? "default" : "ghost"}
            size="sm"
            className="flex-1 gap-1.5"
            onClick={() => setActiveTab(key)}
          >
            <Icon size={14} />
            {label}
          </Button>
        ))}
      </div>

      {/* Source filter (only on news tab) */}
      {activeTab === "news" && (
        <div className="flex gap-1.5 overflow-x-auto">
          {SOURCES.map(({ key, label }) => (
            <Button
              key={label}
              variant={sourceFilter === key ? "default" : "outline"}
              size="sm"
              onClick={() => setSourceFilter(key)}
            >
              {label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
