// Shown when the backend can't be reached. TableTurn is a demo on a free
// host that shuts the server down after a period of inactivity, so the usual
// cause is a "cold start" rather than a real outage.
export default function ServerSleepingNotice() {
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
