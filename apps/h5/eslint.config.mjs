import antfu from '@antfu/eslint-config'
export default antfu({ vue: true, pnpm: false, typescript: true, stylistic: false,
  ignores: ['src/api/generated/**', 'src/types/components.d.ts', 'src/types/route-map.d.ts', 'reports/**'],
  rules: { 'vue/max-attributes-per-line': 'off', 'vue/singleline-html-element-content-newline': 'off', 'vue/html-indent': 'off', 'antfu/if-newline': 'off', 'style/max-statements-per-line': 'off', 'ts/consistent-type-definitions': 'off' },
})
