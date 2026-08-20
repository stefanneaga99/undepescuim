/** Network profiles used by the mobile matrix and native-device handoff. */
export const MOBILE_NETWORK_PROFILES = {
  fast3g: { label: 'fast-3g', downloadKbps: 1600, uploadKbps: 750, latencyMs: 150, cpuThrottle: 4 },
  slow2g: { label: 'slow-2g', downloadKbps: 50, uploadKbps: 50, latencyMs: 300, cpuThrottle: 4 },
} as const;

export type MobileNetworkProfile = keyof typeof MOBILE_NETWORK_PROFILES;

export function networkProfile(name: MobileNetworkProfile) {
  return MOBILE_NETWORK_PROFILES[name];
}
