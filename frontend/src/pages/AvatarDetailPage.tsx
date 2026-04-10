import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getAvatar, type Avatar } from "@/api/avatars";
import { useAvatars } from "@/hooks/useAvatars";

const statusStyles: Record<Avatar["status"], string> = {
  ready: "bg-[#a6e3a1] text-[#1e1e2e]",
  generating: "bg-[#f9e2af] text-[#1e1e2e]",
  error: "bg-[#f38ba8] text-[#1e1e2e]",
  draft: "bg-[#6c7086] text-[#cdd6f4]",
};

export default function AvatarDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { removeAvatar } = useAvatars();

  const [avatar, setAvatar] = useState<Avatar | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getAvatar(id)
      .then(setAvatar)
      .catch(() => setAvatar(null))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDelete = async () => {
    if (!id || !confirm(t("detail.confirm_delete"))) return;
    await removeAvatar(id);
    navigate("/");
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#89b4fa] border-t-transparent" />
      </div>
    );
  }

  if (!avatar) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <p className="text-[#a6adc8]">Avatar not found</p>
        <Link to="/" className="text-sm text-[#89b4fa] hover:underline">
          {t("detail.back")}
        </Link>
      </div>
    );
  }

  const videoUrl = avatar.status === "ready" ? avatar.loop_video_url : null;

  return (
    <div className="mx-auto max-w-4xl">
      <Link
        to="/"
        className="mb-6 inline-flex items-center gap-2 text-sm text-[#a6adc8] hover:text-[#cdd6f4]"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
        </svg>
        {t("detail.back")}
      </Link>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Live-looking video stream (seamless loop, no controls) */}
        <div className="relative overflow-hidden rounded-xl border border-[#313244] bg-[#181825]">
          {videoUrl ? (
            <video
              key={videoUrl}
              src={videoUrl}
              autoPlay
              loop
              muted
              playsInline
              disablePictureInPicture
              controlsList="nodownload noplaybackrate nofullscreen"
              onContextMenu={(e) => e.preventDefault()}
              className="w-full object-cover"
            />
          ) : (
            <div className="flex aspect-video items-center justify-center bg-[#313244]">
              <svg className="h-20 w-20 text-[#6c7086]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={0.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
              </svg>
            </div>
          )}
        </div>

        {/* Info panel */}
        <div className="space-y-6">
          <div className="flex items-start gap-4">
            {/* Uploaded icon photo (small) */}
            {avatar.source_photo_url && (
              <img
                src={avatar.source_photo_url}
                alt={`${avatar.name} icon`}
                className="h-16 w-16 flex-shrink-0 rounded-full border-2 border-[#313244] object-cover"
              />
            )}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-3">
                <h1 className="truncate text-2xl font-semibold text-[#cdd6f4]">
                  {avatar.name}
                </h1>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ${statusStyles[avatar.status]}`}
                >
                  {t(`detail.status_${avatar.status}`)}
                </span>
              </div>
              <p className="mt-2 text-sm text-[#6c7086]">
                Created: {new Date(avatar.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => void handleDelete()}
              className="inline-flex items-center gap-2 rounded-lg border border-[#f38ba8]/30 px-5 py-2.5 text-sm font-medium text-[#f38ba8] transition-colors hover:bg-[#f38ba8]/10"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>
              {t("detail.delete")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
