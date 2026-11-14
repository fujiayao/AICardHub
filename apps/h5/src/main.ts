import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import 'vant/lib/index.css'
import 'virtual:uno.css'
import './styles/tokens.css'
import './styles/base.css'
createApp(App).use(createPinia()).use(router).mount('#app')
if (import.meta.env.DEV && import.meta.env.VITE_DEBUG === 'true') import('vconsole').then(({ default: VConsole }) => new VConsole())
