<script setup lang="ts">
// 匿名职业照占位：严格复刻原型 photo() 的 SVG 形状，明确是占位而非真人。
// 仅当 PublicCard 未提供真实职业照时使用。渐变 id 按实例唯一，避免同页冲突。
import { useId } from 'vue'
const uid = useId()
const l = `ap-${uid}-l`
const f = `ap-${uid}-f`
const s = `ap-${uid}-s`
</script>

<template>
  <svg class="portrait-illustration" viewBox="0 0 300 400" preserveAspectRatio="xMidYMax meet" role="img" aria-label="职业照占位图">
    <defs>
      <radialGradient :id="l" cx="50%" cy="34%" r="45%">
        <stop offset="0" stop-color="#fff" stop-opacity=".22" />
        <stop offset="1" stop-color="#fff" stop-opacity="0" />
      </radialGradient>
      <linearGradient :id="f" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#E3E9F1" />
        <stop offset="1" stop-color="#B7C4D6" />
      </linearGradient>
      <linearGradient :id="s" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#1A2F52" />
        <stop offset="1" stop-color="#0C1A33" />
      </linearGradient>
    </defs>
    <circle cx="150" cy="150" r="150" :fill="`url(#${l})`" />
    <path d="M133 180h34v44c-6 8-28 8-34 0z" fill="#A9B8CC" />
    <ellipse cx="103" cy="142" rx="8" ry="14" fill="#B9C6D8" />
    <ellipse cx="197" cy="142" rx="8" ry="14" fill="#B9C6D8" />
    <ellipse cx="150" cy="136" rx="47" ry="58" :fill="`url(#${f})`" />
    <path d="M103 128c-4-40 18-62 50-62 30 0 50 18 46 60-6-20-20-30-44-30-26 0-42 12-52 32z" fill="#27324A" />
    <path d="M28 400c4-86 44-138 122-150 78 12 118 64 122 150z" :fill="`url(#${s})`" />
    <path d="M127 238l23 70 23-70-9-8-14 14-14-14z" fill="#EEF2F7" />
    <path d="M146 246h8l5 52-9 18-9-18z" fill="#0E9E98" />
    <path d="M127 238l-20 18 33 86 10-34z" fill="#21385E" />
    <path d="M173 238l20 18-33 86-10-34z" fill="#21385E" />
  </svg>
</template>

<style scoped>
.portrait-illustration {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
