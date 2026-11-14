import js from '@eslint/js';
import ts from 'typescript-eslint';
import vue from 'eslint-plugin-vue';
export default ts.config({ ignores: ['dist/**', 'node_modules/**', 'src/api/generated/**'] }, js.configs.recommended,
 ...ts.configs.recommended, ...vue.configs['flat/essential'],
 { files: ['**/*.vue'], languageOptions: { parserOptions: { parser: ts.parser } } },
 { files: ['**/*.{ts,vue,mjs}'], languageOptions: { globals: { window:'readonly', document:'readonly', sessionStorage:'readonly', fetch:'readonly', URL:'readonly', URLSearchParams:'readonly', AbortController:'readonly', setTimeout:'readonly', clearTimeout:'readonly', console:'readonly', process:'readonly', Buffer:'readonly' } }, rules: { 'vue/multi-word-component-names':'off', '@typescript-eslint/no-explicit-any':'error', '@typescript-eslint/ban-ts-comment':'error' } });
