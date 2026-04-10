import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAvatars } from "@/hooks/useAvatars";
import AvatarCard from "@/components/AvatarCard";

export default function GalleryPage() {
  const { t } = useTranslation();
  const { avatars, loading, error, fetchAvatars } = useAvatars();

  useEffect(() => {
    void fetchAvatars();
  }, [fetchAvatars]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#89b4fa] border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-[#f38ba8]">{error}</p>
      </div>
    );
  }

  if (avatars.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-6">
        <div className="flex h-24 w-24 items-center justify-center rounded-2xl bg-[#313244]">
          <svg className="h-12 w-12 text-[#89b4fa]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
          </svg>
        </div>
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-[#cdd6f4]">
            {t("gallery.welcome_title")}
          </h2>
          <p className="mt-2 max-w-md text-sm text-[#a6adc8]">
            {t("gallery.welcome_desc")}
          </p>
        </div>
        <Link
          to="/create"
          className="rounded-lg bg-[#89b4fa] px-6 py-2.5 text-sm font-medium text-[#1e1e2e] transition-colors hover:bg-[#89b4fa]/80"
        >
          {t("gallery.create_first")}
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t("gallery.title")}</h1>
        <Link
          to="/create"
          className="flex items-center gap-2 rounded-lg bg-[#89b4fa] px-4 py-2 text-sm font-medium text-[#1e1e2e] transition-colors hover:bg-[#89b4fa]/80"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          {t("sidebar.new_avatar")}
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {avatars.map((avatar) => (
          <AvatarCard key={avatar.id} avatar={avatar} />
        ))}
      </div>
    </div>
  );
}
