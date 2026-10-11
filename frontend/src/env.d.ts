/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_COORDINATOR_API?: string
  readonly VITE_SITE1_API?: string
  readonly VITE_SITE2_API?: string
  readonly VITE_SITE3_API?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
