import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import GalleryPage from "./pages/GalleryPage";
import CreateWizardPage from "./pages/CreateWizardPage";
import AvatarDetailPage from "./pages/AvatarDetailPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <div className="flex h-screen bg-[#1e1e2e] text-[#cdd6f4]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <Routes>
          <Route path="/" element={<GalleryPage />} />
          <Route path="/create" element={<CreateWizardPage />} />
          <Route path="/avatars/:id" element={<AvatarDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
