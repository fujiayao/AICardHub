import { defineConfig, presetIcons, presetWind4 } from 'unocss'
export default defineConfig({
  presets: [presetWind4({ preflights: { reset: false } }), presetIcons()],
  theme: { colors: Object.fromEntries(['ink', 'primary', 'ai', 'amber', 'danger', 'surface', 'bg', 'text'].map(name => [name, `var(--c-${name})`])) },
})
