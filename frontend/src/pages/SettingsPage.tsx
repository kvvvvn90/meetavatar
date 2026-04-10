import { useState } from "react";
import { useTranslation } from "react-i18next";

interface SettingsState {
  theme: "dark" | "light";
  language: "en" | "zh";
  device: "cpu" | "cuda";
  resolution: string;
  fps: number;
  loopMethod: "palindrome" | "crossfade";
  blendFrames: number;
}

const defaultSettings: SettingsState = {
  theme: "dark",
  language: "en",
  device: "cuda",
  resolution: "1280x720",
  fps: 30,
  loopMethod: "palindrome",
  blendFrames: 15,
};

function loadSettings(): SettingsState {
  try {
    const saved = localStorage.getItem("meetavatar-settings");
    if (saved) return { ...defaultSettings, ...JSON.parse(saved) as Partial<SettingsState> };
  } catch { /* use defaults */ }
  return defaultSettings;
}

const selectClass =
  "w-full rounded-lg border border-[#45475a] bg-[#313244] px-4 py-2.5 text-sm text-[#cdd6f4] outline-none transition-colors focus:border-[#89b4fa]";
const labelClass = "block text-sm font-medium text-[#a6adc8] mb-1.5";

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const [settings, setSettings] = useState<SettingsState>(loadSettings);
  const [saved, setSaved] = useState(false);

  const update = <K extends keyof SettingsState>(
    key: K,
    value: SettingsState[K],
  ) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = () => {
    localStorage.setItem("meetavatar-settings", JSON.stringify(settings));
    localStorage.setItem("meetavatar-lang", settings.language);
    void i18n.changeLanguage(settings.language);

    if (settings.theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }

    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="mb-8 text-2xl font-semibold">{t("settings.title")}</h1>

      <div className="space-y-6">
        {/* Theme */}
        <div>
          <label className={labelClass}>{t("settings.theme")}</label>
          <select
            value={settings.theme}
            onChange={(e) => update("theme", e.target.value as "dark" | "light")}
            className={selectClass}
          >
            <option value="dark">{t("settings.dark")}</option>
            <option value="light">{t("settings.light")}</option>
          </select>
        </div>

        {/* Language */}
        <div>
          <label className={labelClass}>{t("settings.language")}</label>
          <select
            value={settings.language}
            onChange={(e) => update("language", e.target.value as "en" | "zh")}
            className={selectClass}
          >
            <option value="en">English</option>
            <option value="zh">中文</option>
          </select>
        </div>

        {/* Device */}
        <div>
          <label className={labelClass}>{t("settings.device")}</label>
          <select
            value={settings.device}
            onChange={(e) => update("device", e.target.value as "cpu" | "cuda")}
            className={selectClass}
          >
            <option value="cuda">CUDA (GPU)</option>
            <option value="cpu">CPU</option>
          </select>
        </div>

        {/* Resolution */}
        <div>
          <label className={labelClass}>{t("settings.resolution")}</label>
          <select
            value={settings.resolution}
            onChange={(e) => update("resolution", e.target.value)}
            className={selectClass}
          >
            <option value="1280x720">1280 x 720 (720p)</option>
            <option value="1920x1080">1920 x 1080 (1080p)</option>
            <option value="640x480">640 x 480 (480p)</option>
          </select>
        </div>

        {/* FPS */}
        <div>
          <label className={labelClass}>{t("settings.fps")}</label>
          <select
            value={settings.fps}
            onChange={(e) => update("fps", Number(e.target.value))}
            className={selectClass}
          >
            <option value={15}>15</option>
            <option value={25}>25</option>
            <option value={30}>30</option>
          </select>
        </div>

        {/* Loop Method */}
        <div>
          <label className={labelClass}>{t("settings.loop_method")}</label>
          <select
            value={settings.loopMethod}
            onChange={(e) =>
              update("loopMethod", e.target.value as SettingsState["loopMethod"])
            }
            className={selectClass}
          >
            <option value="palindrome">Palindrome</option>
            <option value="crossfade">Crossfade</option>
          </select>
        </div>

        {/* Blend Frames */}
        <div>
          <label className={labelClass}>{t("settings.blend")}</label>
          <input
            type="number"
            min={0}
            max={30}
            value={settings.blendFrames}
            onChange={(e) => update("blendFrames", Number(e.target.value))}
            className={selectClass}
          />
        </div>
      </div>

      <div className="mt-8 flex items-center gap-4">
        <button
          onClick={handleSave}
          className="rounded-lg bg-[#89b4fa] px-6 py-2.5 text-sm font-medium text-[#1e1e2e] transition-colors hover:bg-[#89b4fa]/80"
        >
          {t("settings.save")}
        </button>
        {saved && (
          <span className="text-sm text-[#a6e3a1]">{t("settings.saved")}</span>
        )}
      </div>
    </div>
  );
}
