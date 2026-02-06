import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAppStore } from "@/store/appStore";
import { useTelegram } from "@/hooks/useTelegram";
import { FilterBar } from "@/components/FilterBar";
import { NewsFeed } from "@/components/NewsFeed";
import { JobsPanel } from "@/components/JobsPanel";
import { ProfileSection } from "@/components/ProfileSection";
import { AdminDashboard } from "@/components/AdminDashboard";

const queryClient = new QueryClient();

function Dashboard() {
  const activeTab = useAppStore((s) => s.activeTab);
  const [showAdmin, setShowAdmin] = useState(
    () => window.location.pathname === "/admin",
  );
  useTelegram();

  if (showAdmin) {
    return <AdminDashboard onBack={() => setShowAdmin(false)} />;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="sticky top-0 z-10 border-b border-gray-800 bg-gray-950/90 backdrop-blur">
        <div className="mx-auto max-w-2xl px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold tracking-tight">INFRA</h1>
            <p className="text-xs text-gray-500">Intelligence Terminal</p>
          </div>
          <button
            onClick={() => setShowAdmin(true)}
            className="text-xs text-gray-500 hover:text-gray-300"
          >
            Admin
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-2xl space-y-4 px-4 py-4">
        <FilterBar />

        {activeTab === "news" && <NewsFeed />}
        {activeTab === "jobs" && <JobsPanel />}
        {activeTab === "profile" && <ProfileSection />}
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}

export default App;
