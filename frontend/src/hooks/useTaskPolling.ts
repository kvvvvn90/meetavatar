import { useEffect, useRef, useState, useCallback } from "react";
import { getTaskStatus, type TaskStatus } from "@/api/avatars";

const POLL_INTERVAL = 2000;

interface UseTaskPollingOptions {
  onComplete?: (status: TaskStatus) => void;
  onError?: (status: TaskStatus) => void;
}

export function useTaskPolling(
  taskId: string | null,
  options?: UseTaskPollingOptions,
) {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [polling, setPolling] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setPolling(false);
  }, []);

  useEffect(() => {
    if (!taskId) {
      stopPolling();
      setStatus(null);
      return;
    }

    setPolling(true);

    const poll = async () => {
      try {
        const result = await getTaskStatus(taskId);
        setStatus(result);

        if (result.status === "completed") {
          stopPolling();
          optionsRef.current?.onComplete?.(result);
        } else if (result.status === "failed") {
          stopPolling();
          optionsRef.current?.onError?.(result);
        }
      } catch {
        stopPolling();
      }
    };

    void poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL);

    return stopPolling;
  }, [taskId, stopPolling]);

  return { status, polling };
}
