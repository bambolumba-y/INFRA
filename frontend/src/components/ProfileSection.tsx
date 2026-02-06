import { type ChangeEvent, useRef } from "react";
import { useUploadResume } from "@/hooks/useApi";
import { useTelegram } from "@/hooks/useTelegram";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Upload, Loader2 } from "lucide-react";

export function ProfileSection() {
  const fileRef = useRef<HTMLInputElement>(null);
  const upload = useUploadResume();
  const { telegramUser, haptic } = useTelegram();

  function handleFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    haptic("medium");
    upload.mutate(file);
  }

  return (
    <div className="space-y-4">
      {/* User info */}
      <Card>
        <CardHeader>
          <CardTitle>
            {telegramUser
              ? `Welcome, ${telegramUser.firstName}`
              : "Profile"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p>Upload your resume to get AI-powered job matching.</p>
        </CardContent>
      </Card>

      {/* Upload area */}
      <Card className="flex flex-col items-center gap-3 p-6">
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFile}
        />
        <Button
          variant="outline"
          className="gap-2"
          onClick={() => fileRef.current?.click()}
          disabled={upload.isPending}
        >
          {upload.isPending ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Upload size={16} />
          )}
          {upload.isPending ? "Processing…" : "Upload Resume (PDF)"}
        </Button>

        {upload.isSuccess && (
          <p className="text-sm text-green-400">
            Resume parsed successfully ✓
          </p>
        )}
        {upload.isError && (
          <p className="text-sm text-red-400">Upload failed. Please retry.</p>
        )}
      </Card>
    </div>
  );
}
