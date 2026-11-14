import { VantResolver } from '@vant/auto-import-resolver'
import legacy from '@vitejs/plugin-legacy'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import Components from 'unplugin-vue-components/vite'
import { mockDevServerPlugin } from 'vite-plugin-mock-dev-server'
import VueRouter from 'vue-router/vite'
export function createVitePlugins() {
  return [VueRouter({ routesFolder: 'src/pages', dts: 'src/types/route-map.d.ts' }), vue(),
    Components({ resolvers: [VantResolver()], dts: 'src/types/components.d.ts' }), UnoCSS(),
    mockDevServerPlugin(), legacy({ targets: ['defaults', 'not IE 11'] })]
}
