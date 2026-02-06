import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchNews,
  uploadResume,
  fetchJobMatches,
  saveApiKeys,
} from "@/api/client";
import { useAppStore } from "@/store/appStore";

export function useNews() {
  const sourceFilter = useAppStore((s) => s.sourceFilter);
  return useQuery({
    queryKey: ["news", sourceFilter],
    queryFn: () =>
      fetchNews(sourceFilter ? { source_type: sourceFilter } : undefined),
    staleTime: 30_000,
  });
}

export function useJobMatches() {
  return useQuery({
    queryKey: ["jobMatches"],
    queryFn: fetchJobMatches,
    staleTime: 60_000,
  });
}

export function useUploadResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadResume,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["jobMatches"] });
    },
  });
}

export function useSaveApiKeys() {
  return useMutation({ mutationFn: saveApiKeys });
}
