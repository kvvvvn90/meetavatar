/**
 * Desktop bridge — communicates with the local MeetAvatar Camera client
 * running on localhost:18520.
 */

const DESKTOP_API = "http://localhost:18520";

export interface DesktopStatus {
  running: boolean;
  avatar: string;
  version: string;
}

/**
 * Check whether the desktop camera client is running.
 */
export async function isDesktopAppRunning(): Promise<boolean> {
  try {
    const resp = await fetch(`${DESKTOP_API}/api/status`, {
      signal: AbortSignal.timeout(1500),
    });
    return resp.ok;
  } catch {
    return false;
  }
}

/**
 * Get the desktop client's current status.
 */
export async function getDesktopStatus(): Promise<DesktopStatus | null> {
  try {
    const resp = await fetch(`${DESKTOP_API}/api/status`, {
      signal: AbortSignal.timeout(2000),
    });
    if (!resp.ok) return null;
    return resp.json();
  } catch {
    return null;
  }
}

/**
 * Push an avatar to the desktop camera client for immediate use.
 */
export async function pushAvatarToDesktop(
  avatarId: string,
  serverUrl = "",
): Promise<boolean> {
  try {
    const resp = await fetch(`${DESKTOP_API}/api/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ avatar_id: avatarId, server_url: serverUrl }),
      signal: AbortSignal.timeout(5000),
    });
    return resp.ok;
  } catch {
    return false;
  }
}
