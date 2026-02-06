import { create } from "zustand";
import { persist } from "zustand/middleware";

export type TabType = "news" | "jobs" | "profile";

interface AppState {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;

  sourceFilter: string | null;
  setSourceFilter: (source: string | null) => void;

  telegramUser: { id: number; firstName: string } | null;
  setTelegramUser: (user: { id: number; firstName: string } | null) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      activeTab: "news",
      setActiveTab: (tab) => set({ activeTab: tab }),

      sourceFilter: null,
      setSourceFilter: (source) => set({ sourceFilter: source }),

      telegramUser: null,
      setTelegramUser: (user) => set({ telegramUser: user }),
    }),
    {
      name: "infra-app-store",
      partialize: (state) => ({
        activeTab: state.activeTab,
        sourceFilter: state.sourceFilter,
        telegramUser: state.telegramUser,
      }),
    },
  ),
);
