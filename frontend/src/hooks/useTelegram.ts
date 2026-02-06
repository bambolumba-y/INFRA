import { useEffect } from "react";
import { useAppStore } from "@/store/appStore";

/**
 * Initialise the Telegram Web App SDK and expose basic helpers.
 *
 * The SDK is loaded via `@telegram-apps/sdk` which expects to run inside
 * the Telegram WebView.  Outside Telegram the hook is a no-op.
 */
export function useTelegram() {
  const setTelegramUser = useAppStore((s) => s.setTelegramUser);
  const telegramUser = useAppStore((s) => s.telegramUser);

  useEffect(() => {
    async function init() {
      try {
        const sdk = await import("@telegram-apps/sdk");

        if (!sdk.isTMA()) return;

        sdk.init();

        // initDataUser is a Computed<User | undefined> signal
        const user = sdk.initDataUser();
        if (user) {
          setTelegramUser({
            id: user.id,
            firstName: user.first_name,
          });
        }
      } catch {
        // Not inside Telegram – fine for local dev
      }
    }
    void init();
  }, [setTelegramUser]);

  function haptic(type: "light" | "medium" | "heavy" = "light") {
    try {
      const w = window as unknown as Record<string, unknown>;
      const tg = w.Telegram as
        | { WebApp?: { HapticFeedback?: { impactOccurred: (s: string) => void } } }
        | undefined;
      tg?.WebApp?.HapticFeedback?.impactOccurred(type);
    } catch {
      // ignored
    }
  }

  return { telegramUser, haptic };
}
