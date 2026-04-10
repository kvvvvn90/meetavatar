import { useCallback, useState, useRef } from "react";
import { useTranslation } from "react-i18next";

interface PhotoDropZoneProps {
  onFileSelected: (file: File) => void;
  previewUrl?: string | null;
}

export default function PhotoDropZone({
  onFileSelected,
  previewUrl,
}: PhotoDropZoneProps) {
  const { t } = useTranslation();
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("image/")) {
        onFileSelected(file);
      }
    },
    [onFileSelected],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onFileSelected(file);
      }
    },
    [onFileSelected],
  );

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`relative cursor-pointer rounded-xl border-2 border-dashed transition-colors ${
        dragging
          ? "border-[#89b4fa] bg-[#89b4fa]/10"
          : "border-[#45475a] hover:border-[#89b4fa]/50"
      } ${previewUrl ? "p-2" : "p-10"}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleInputChange}
        className="hidden"
      />

      {previewUrl ? (
        <img
          src={previewUrl}
          alt="Source photo"
          className="mx-auto max-h-64 rounded-lg object-contain"
        />
      ) : (
        <div className="flex flex-col items-center gap-3 text-[#6c7086]">
          <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
          </svg>
          <p className="text-sm font-medium">{t("wizard.upload_photo")}</p>
          <p className="text-xs">{t("wizard.drag_drop")}</p>
        </div>
      )}
    </div>
  );
}
