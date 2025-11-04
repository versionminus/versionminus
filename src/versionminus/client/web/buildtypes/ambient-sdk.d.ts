// Build-only ambient declaration to unblock production Docker builds
// when the published SDK version lacks bundled .d.ts files.
// Dev typechecking uses path mapping to the SDK sources and does not rely on this.
declare module '@versionminus/versionminus' {
  // Minimal surface to satisfy production builds when the published package
  // does not include .d.ts files. These are intentionally broad to avoid
  // coupling; local dev uses real types from source via path mapping.
  export type UseversionminusReturn = any;
  export type Note = any;
  export type Message = any;
  export type Thread = any;
  export type Source = any;
  export type AsyncState<T = any> = any;

  export function useversionminus(config: any): UseversionminusReturn;
  export function getVersion(): string;
}
