/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** The Django API's address for a deployed build, e.g. https://backend.up.railway.app/api */
  readonly VITE_API_URL?: string;
}

/** amrpredict-lib's version (vite.config.ts) */
declare const __LIB_VERSION__: string;
