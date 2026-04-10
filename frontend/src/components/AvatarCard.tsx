import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { Avatar } from "@/api/avatars";

const statusColors: Record<Avatar["status"], string> = {
  ready: "bg-[#a6e3a1] text-[#1e1e2e]",
  generating: "bg-[#f9e2af] text-[#1e1e2e]",
  error: "bg-[#f38ba8] text-[#1e1e2e]",
  draft: "bg-[#6c7086] text-[#cdd6f4]",
};

interface AvatarCardProps {
  avatar: Avatar;
}

export default function AvatarCard({ avatar }: AvatarCardProps) {
  const { t } = useTranslation();

  const statusKey = `detail.status_${avatar.status}` as const;

  return (
    <Link
      to={`/avatars/${avatar.id}`}
      className="group overflow-hidden rounded-xl border border-[#313244] bg-[#181825] transition-all hover:border-[#89b4fa]/50 hover:shadow-lg hover:shadow-[#89b4fa]/5"
    >
      <div className="relative aspect-square overflow-hidden bg-[#313244]">
        {(avatar.thumbnail_url || avatar.source_photo_url) ? (
          <img
            src={avatar.thumbnail_url ?? avatar.source_photo_url!}
            alt={avatar.name}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-4xl text-[#6c7086]">
            <svg className="h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={0.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
            </svg>
          </div>
        )}
        {/* Show uploaded icon photo as a small overlay when a generated thumbnail exists */}
        {avatar.thumbnail_url && avatar.source_photo_url && (
          <img
            src={avatar.source_photo_url}
            alt={`${avatar.name} icon`}
            className="absolute bottom-2 right-2 h-10 w-10 rounded-full border-2 border-[#181825] object-cover shadow-lg"
          />
        )}
      </div>
      <div className="flex items-center justify-between p-3">
        <span className="truncate text-sm font-medium text-[#cdd6f4]">
          {avatar.name}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[avatar.status]}`}
        >
          {t(statusKey)}
        </span>
      </div>
    </Link>
  );
}
