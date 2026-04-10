import { create } from "zustand";
import {
  listAvatars,
  createAvatar as apiCreateAvatar,
  deleteAvatar as apiDeleteAvatar,
  type Avatar,
} from "@/api/avatars";

interface AvatarsState {
  avatars: Avatar[];
  loading: boolean;
  error: string | null;
  fetchAvatars: () => Promise<void>;
  addAvatar: (name: string) => Promise<Avatar>;
  removeAvatar: (id: string) => Promise<void>;
  updateAvatar: (id: string, patch: Partial<Avatar>) => void;
}

export const useAvatars = create<AvatarsState>((set, get) => ({
  avatars: [],
  loading: false,
  error: null,

  fetchAvatars: async () => {
    set({ loading: true, error: null });
    try {
      const avatars = await listAvatars();
      set({ avatars, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to fetch avatars",
        loading: false,
      });
    }
  },

  addAvatar: async (name: string) => {
    const avatar = await apiCreateAvatar(name);
    set({ avatars: [avatar, ...get().avatars] });
    return avatar;
  },

  removeAvatar: async (id: string) => {
    await apiDeleteAvatar(id);
    set({ avatars: get().avatars.filter((a) => a.id !== id) });
  },

  updateAvatar: (id: string, patch: Partial<Avatar>) => {
    set({
      avatars: get().avatars.map((a) =>
        a.id === id ? { ...a, ...patch } : a,
      ),
    });
  },
}));
