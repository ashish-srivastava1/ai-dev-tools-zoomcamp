import { useCallback, useEffect, useRef, useState } from 'react';
import { getStats, listQueue, subscribeToQueue } from '../api/client';

// Loads the queue + stats and keeps them in sync with backend changes,
// including ones made from another browser tab (the backend is polled on an
// interval and again after every local mutation).
//
// `serverDown` is true while the backend can't be reached — on the free
// host that usually means it went to sleep after inactivity (a cold start).
export function useLiveQueue() {
  const [queue, setQueue] = useState([]);
  const [stats, setStats] = useState({ waitingCount: 0, calledCount: 0, avgWaitTodayMinutes: null });
  const [loading, setLoading] = useState(true);
  const [serverDown, setServerDown] = useState(false);

  // Only one refresh at a time: while the server is asleep each request can
  // hang for a while, and polling every few seconds would pile them up.
  const inFlight = useRef(false);
  const rerunRequested = useRef(false);

  const refresh = useCallback(async () => {
    if (inFlight.current) {
      rerunRequested.current = true;
      return;
    }
    inFlight.current = true;
    try {
      // Loop (rather than recurse) so a refresh requested mid-flight still runs.
      do {
        rerunRequested.current = false;
        try {
          const [nextQueue, nextStats] = await Promise.all([listQueue(), getStats()]);
          setQueue(nextQueue);
          setStats(nextStats);
          setServerDown(false);
          setLoading(false);
        } catch (err) {
          if (err.isServerUnavailable) {
            setServerDown(true);
          } else {
            console.error(err);
            setLoading(false);
          }
        }
      } while (rerunRequested.current);
    } finally {
      inFlight.current = false;
    }
  }, []);

  useEffect(() => {
    refresh();
    const unsubscribe = subscribeToQueue(() => {
      refresh();
    });
    return unsubscribe;
  }, [refresh]);

  return { queue, stats, loading, serverDown, refresh };
}
