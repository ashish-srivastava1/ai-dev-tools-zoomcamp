// Shown when the backend can't be reached. On the deployed free-tier host
// that's usually a "cold start"; locally (or if the backend has crashed) it
// just means nothing is listening yet — those need different advice.
export default function ServerSleepingNotice({ reason = 'gateway' }) {
  if (reason === 'network') {
    return (
      <div className="server-notice" role="alert">
        <p className="server-notice-title">Can't reach the backend</p>
        <p>
          The app can't connect to the API right now. If you're running this locally, make sure
          the backend server is started.
        </p>
      </div>
    );
  }

  return (
    <div className="server-notice" role="alert">
      <p className="server-notice-title">The server is asleep (cold start)</p>
      <p>
        TableTurn is a demo project running on a free server, which shuts down after a period of
        inactivity. It is starting up again now.
      </p>
      <p>
        <strong>Please wait about 10 minutes and try again.</strong>
      </p>
    </div>
  );
}
