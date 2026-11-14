<script setup lang="ts">
// 匿名职业照占位：严格复刻原型 photo() 的 SVG 几何，明确是占位而非真人。
// 颜色来自 tokens.css（--c-portrait-*），不使用颜色字面量；几何坐标保持与原型一致。
// 渐变 id 按实例唯一，避免同页多实例冲突。
import { useId } from 'vue'
const uid = useId()
const l = `ap-${uid}-l`
const f = `ap-${uid}-f`
const s = `ap-${uid}-s`
</script>

<template>
  <svg class="portrait-illustration" viewBox="0 0 300 400" preserveAspectRatio="xMidYMax meet" role="img" aria-label="匿名人物插画占位，非真实照片">
    <defs>
      <radialGradient :id="l" cx="50%" cy="34%" r="45%">
        <stop offset="0" class="stop-highlight" stop-opacity=".22" />
        <stop offset="1" class="stop-highlight" stop-opacity="0" />
      </radialGradient>
      <linearGradient :id="f" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" class="stop-face-0" />
        <stop offset="1" class="stop-face-1" />
      </linearGradient>
      <linearGradient :id="s" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" class="stop-shoulder-0" />
        <stop offset="1" class="stop-shoulder-1" />
      </linearGradient>
    </defs>
    <circle cx="150" cy="150" r="150" :fill="`url(#${l})`" />
    <path class="fill-neck" d="M133 180h34v44c-6 8-28 8-34 0z" />
    <ellipse class="fill-ear" cx="103" cy="142" rx="8" ry="14" />
    <ellipse class="fill-ear" cx="197" cy="142" rx="8" ry="14" />
    <ellipse cx="150" cy="136" rx="47" ry="58" :fill="`url(#${f})`" />
    <path class="fill-hair" d="M103 128c-4-40 18-62 50-62 30 0 50 18 46 60-6-20-20-30-44-30-26 0-42 12-52 32z" />
    <path d="M28 400c4-86 44-138 122-150 78 12 118 64 122 150z" :fill="`url(#${s})`" />
    <path class="fill-shirt" d="M127 238l23 70 23-70-9-8-14 14-14-14z" />
    <path class="fill-tie" d="M146 246h8l5 52-9 18-9-18z" />
    <path class="fill-suit" d="M127 238l-20 18 33 86 10-34z" />
    <path class="fill-suit" d="M173 238l20 18-33 86-10-34z" />
  </svg>
</template>

<style scoped>
.portrait-illustration {
  display: block;
  width: 100%;
  height: 100%;
}
.stop-highlight { stop-color: var(--c-portrait-highlight); }
.stop-face-0 { stop-color: var(--c-portrait-face-0); }
.stop-face-1 { stop-color: var(--c-portrait-face-1); }
.stop-shoulder-0 { stop-color: var(--c-portrait-shoulder-0); }
.stop-shoulder-1 { stop-color: var(--c-portrait-shoulder-1); }
.fill-neck { fill: var(--c-portrait-neck); }
.fill-ear { fill: var(--c-portrait-ear); }
.fill-hair { fill: var(--c-portrait-hair); }
.fill-shirt { fill: var(--c-portrait-shirt); }
.fill-tie { fill: var(--c-portrait-tie); }
.fill-suit { fill: var(--c-portrait-suit); }
</style>
