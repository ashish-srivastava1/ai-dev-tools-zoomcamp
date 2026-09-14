import { useCallback, useEffect, useState } from 'react';
import { getStats, listQueue, subscribeToQueue } from '../api/client';

// Loads the queue + stats and keeps them in sync with backend changes,
// including ones made from another browser tab (the mock backend persists
// to localStorage and notifies subscribers on every write).
export function useLiveQueue() {
  const [queue, setQueue] = useState([]);
  const [stats, setStats] = useState({ waitingCount: 0, calledCount: 0, avgWaitTodayMinutes: null });
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const [nextQueue, nextStats] = await Promise.all([listQueue(), getStats()]);
    setQueue(nextQueue);
    setStats(nextStats);
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
    const unsubscribe = subscribeToQueue(() => {
      refresh();
    });
    return unsubscribe;
  }, [refresh]);

  return { queue, stats, loading, refresh };
}
