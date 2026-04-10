import { useRef, useState, useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";

interface VideoRecorderProps {
  onRecordingComplete: (blob: Blob) => void;
}

const MAX_DURATION = 15; // seconds — forced recording length

export default function VideoRecorder({
  onRecordingComplete,
}: VideoRecorderProps) {
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const [recording, setRecording] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraReady(true);
    } catch (err) {
      console.error("Failed to access camera:", err);
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraReady(false);
  }, []);

  useEffect(() => {
    void startCamera();
    return () => {
      stopCamera();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [startCamera, stopCamera]);

  // Re-attach the live stream to the video element whenever we leave preview mode
  useEffect(() => {
    if (!previewUrl && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [previewUrl]);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    setRecording(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startRecording = useCallback(() => {
    if (!streamRef.current) return;
    chunksRef.current = [];
    setPreviewUrl(null);
    setElapsed(0);

    const recorder = new MediaRecorder(streamRef.current, {
      mimeType: "video/webm",
    });

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "video/webm" });
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      onRecordingComplete(blob);
    };

    recorder.start(100);
    recorderRef.current = recorder;
    setRecording(true);

    timerRef.current = setInterval(() => {
      setElapsed((prev) => {
        const next = prev + 1;
        if (next >= MAX_DURATION) {
          // Auto-stop at MAX_DURATION
          stopRecording();
        }
        return next;
      });
    }, 1000);
  }, [onRecordingComplete, stopRecording]);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative overflow-hidden rounded-xl bg-[#11111b]">
        {previewUrl ? (
          <video
            src={previewUrl}
            controls
            className="h-64 w-auto max-w-md object-cover"
          />
        ) : (
          <video
            ref={videoRef}
            autoPlay
            muted
            playsInline
            className="h-64 w-auto max-w-md -scale-x-100 object-cover"
          />
        )}

        {recording && (
          <div className="absolute left-3 top-3 flex items-center gap-2 rounded-full bg-[#f38ba8]/90 px-3 py-1 text-xs font-medium text-[#1e1e2e]">
            <span className="h-2 w-2 animate-pulse rounded-full bg-[#1e1e2e]" />
            {elapsed}s / {MAX_DURATION}s
          </div>
        )}
      </div>

      {cameraReady && !previewUrl && (
        <button
          onClick={recording ? stopRecording : startRecording}
          className={`rounded-lg px-6 py-2 text-sm font-medium transition-colors ${
            recording
              ? "bg-[#f38ba8] text-[#1e1e2e] hover:bg-[#f38ba8]/80"
              : "bg-[#89b4fa] text-[#1e1e2e] hover:bg-[#89b4fa]/80"
          }`}
        >
          {recording ? t("wizard.stop_record") : t("wizard.start_record")}
        </button>
      )}

      {previewUrl && (
        <button
          onClick={() => {
            setPreviewUrl(null);
            setElapsed(0);
          }}
          className="text-sm text-[#89b4fa] hover:underline"
        >
          Re-record
        </button>
      )}
    </div>
  );
}
