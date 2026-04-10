import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import StepIndicator from "@/components/StepIndicator";
import PhotoDropZone from "@/components/PhotoDropZone";
import VideoRecorder from "@/components/VideoRecorder";
import { useAvatars } from "@/hooks/useAvatars";
import { useTaskPolling } from "@/hooks/useTaskPolling";
import {
  uploadSourcePhoto,
  uploadDrivingVideo,
  startGeneration,
} from "@/api/avatars";

export default function CreateWizardPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { addAvatar } = useAvatars();

  const [step, setStep] = useState(0);
  const [name, setName] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [video, setVideo] = useState<File | Blob | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const avatarIdRef = useRef<string | null>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);

  const steps = [
    t("wizard.step1_title"),
    t("wizard.step2_title"),
    t("wizard.step3_title"),
  ];

  const { status } = useTaskPolling(taskId, {
    onComplete: () => {
      setGenerating(false);
      if (avatarIdRef.current) {
        navigate(`/avatars/${avatarIdRef.current}`);
      }
    },
    onError: (s) => {
      setGenerating(false);
      setError(s.error ?? "Generation failed");
    },
  });

  const handlePhotoSelected = useCallback((file: File) => {
    setPhoto(file);
    setPhotoPreview(URL.createObjectURL(file));
  }, []);

  const handleVideoFile = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        setVideo(file);
        setVideoPreview(URL.createObjectURL(file));
      }
    },
    [],
  );

  const handleRecordingComplete = useCallback((blob: Blob) => {
    setVideo(blob);
    setVideoPreview(URL.createObjectURL(blob));
  }, []);

  const canNext = (): boolean => {
    if (step === 0) return name.trim().length > 0 && photo !== null;
    if (step === 1) return video !== null;
    return true;
  };

  const handleGenerate = async () => {
    if (!photo || !video) return;
    setGenerating(true);
    setError(null);

    try {
      const avatar = await addAvatar(name);
      avatarIdRef.current = avatar.id;

      await uploadSourcePhoto(avatar.id, photo);
      await uploadDrivingVideo(
        avatar.id,
        video instanceof File ? video : video,
      );

      const { task_id } = await startGeneration(avatar.id);
      setTaskId(task_id);
    } catch (err) {
      setGenerating(false);
      setError(err instanceof Error ? err.message : "Failed to start generation");
    }
  };

  const progress = status?.progress ?? 0;

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <StepIndicator steps={steps} currentStep={step} />
      </div>

      {/* Step 1: Name & Photo */}
      {step === 0 && (
        <div className="space-y-6">
          <div>
            <label className="mb-2 block text-sm font-medium text-[#a6adc8]">
              {t("wizard.step1_title")}
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("wizard.name_placeholder")}
              className="w-full rounded-lg border border-[#45475a] bg-[#313244] px-4 py-2.5 text-sm text-[#cdd6f4] placeholder-[#6c7086] outline-none transition-colors focus:border-[#89b4fa]"
            />
          </div>
          <PhotoDropZone
            onFileSelected={handlePhotoSelected}
            previewUrl={photoPreview}
          />
        </div>
      )}

      {/* Step 2: Driving Video */}
      {step === 1 && (
        <div className="space-y-6">
          <div>
            <label className="mb-4 block text-sm font-medium text-[#a6adc8]">
              {t("wizard.upload_video")}
            </label>
            <div
              onClick={() => videoInputRef.current?.click()}
              className="cursor-pointer rounded-xl border-2 border-dashed border-[#45475a] p-8 text-center transition-colors hover:border-[#89b4fa]/50"
            >
              <input
                ref={videoInputRef}
                type="file"
                accept="video/*"
                onChange={handleVideoFile}
                className="hidden"
              />
              {videoPreview && video instanceof File ? (
                <video
                  src={videoPreview}
                  controls
                  className="mx-auto max-h-48 rounded-lg"
                />
              ) : (
                <div className="flex flex-col items-center gap-2 text-[#6c7086]">
                  <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
                  </svg>
                  <p className="text-sm">{t("wizard.drag_drop")}</p>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="h-px flex-1 bg-[#45475a]" />
            <span className="text-xs text-[#6c7086]">
              {t("wizard.or_record")}
            </span>
            <div className="h-px flex-1 bg-[#45475a]" />
          </div>

          <VideoRecorder onRecordingComplete={handleRecordingComplete} />
        </div>
      )}

      {/* Step 3: Confirm & Generate */}
      {step === 2 && (
        <div className="space-y-6">
          <h3 className="text-lg font-medium">{t("wizard.confirm_summary")}</h3>

          <div className="rounded-xl border border-[#313244] bg-[#181825] p-6">
            <div className="flex items-center gap-6">
              {photoPreview && (
                <img
                  src={photoPreview}
                  alt="Preview"
                  className="h-24 w-24 rounded-lg object-cover"
                />
              )}
              <div>
                <p className="text-lg font-medium text-[#cdd6f4]">{name}</p>
                <p className="mt-1 text-sm text-[#a6adc8]">
                  Photo: {photo?.name}
                </p>
                <p className="text-sm text-[#a6adc8]">
                  Video:{" "}
                  {video instanceof File ? video.name : "Webcam recording"}
                </p>
              </div>
            </div>
          </div>

          {generating && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-[#a6adc8]">
                  {status?.message ?? "Processing..."}
                </span>
                <span className="text-[#89b4fa]">{Math.round(progress)}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[#313244]">
                <div
                  className="h-full rounded-full bg-[#89b4fa] transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <p className="rounded-lg bg-[#f38ba8]/10 p-3 text-sm text-[#f38ba8]">
              {error}
            </p>
          )}
        </div>
      )}

      {/* Navigation buttons */}
      <div className="mt-8 flex justify-between">
        <button
          onClick={() => {
            if (step === 0) navigate("/");
            else setStep((s) => s - 1);
          }}
          disabled={generating}
          className="rounded-lg border border-[#45475a] px-5 py-2 text-sm font-medium text-[#a6adc8] transition-colors hover:bg-[#313244] disabled:opacity-50"
        >
          {step === 0 ? t("wizard.cancel") : t("wizard.back")}
        </button>

        {step < 2 ? (
          <button
            onClick={() => setStep((s) => s + 1)}
            disabled={!canNext()}
            className="rounded-lg bg-[#89b4fa] px-5 py-2 text-sm font-medium text-[#1e1e2e] transition-colors hover:bg-[#89b4fa]/80 disabled:opacity-50"
          >
            {t("wizard.next")}
          </button>
        ) : (
          <button
            onClick={() => void handleGenerate()}
            disabled={generating}
            className="rounded-lg bg-[#89b4fa] px-5 py-2 text-sm font-medium text-[#1e1e2e] transition-colors hover:bg-[#89b4fa]/80 disabled:opacity-50"
          >
            {generating ? `${Math.round(progress)}%` : t("wizard.start_training")}
          </button>
        )}
      </div>
    </div>
  );
}
