/**
 * Utility to verify whether the current web client is running locally on the host machine.
 * Returns true strictly for localhost, 127.0.0.1, [::1], and *.localhost.
 * Returns false for any LAN / network client (e.g. 192.168.x.x, 10.x.x.x, 172.x.x.x).
 */
export function isLocalhost() {
  if (typeof window === 'undefined') return false;
  const hostname = window.location.hostname;
  return (
    hostname === 'localhost' ||
    hostname === '127.0.0.1' ||
    hostname === '[::1]' ||
    hostname.endsWith('.localhost')
  );
}

export default isLocalhost;
