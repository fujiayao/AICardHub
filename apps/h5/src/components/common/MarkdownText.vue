<script setup lang="ts">
import { computed } from 'vue'
import { parseMarkdown } from '@/utils/markdown'
const props = defineProps<{ text: string }>()
const blocks = computed(() => parseMarkdown(props.text))
</script>
<template>
 <div class="md">
  <template v-for="(block, index) in blocks" :key="index">
   <p v-if="block.type === 'p'"><template v-for="(part, i) in block.items[0]" :key="i"><strong v-if="part.bold">{{ part.text }}</strong><template v-else>{{ part.text }}</template></template></p>
   <h4 v-else-if="block.type === 'h'">{{ block.items[0]?.map(p => p.text).join('') }}</h4>
   <ul v-else-if="block.type === 'ul'">
    <li v-for="(item, li) in block.items" :key="li"><template v-for="(part, i) in item" :key="i"><strong v-if="part.bold">{{ part.text }}</strong><template v-else>{{ part.text }}</template></template></li>
   </ul>
   <ol v-else>
    <li v-for="(item, li) in block.items" :key="li"><template v-for="(part, i) in item" :key="i"><strong v-if="part.bold">{{ part.text }}</strong><template v-else>{{ part.text }}</template></template></li>
   </ol>
  </template>
 </div>
</template>
<style scoped>
.md{display:grid;gap:var(--sp-2);overflow-wrap:anywhere;line-height:1.7}
.md :is(p,h4,ul,ol){margin:0}
.md h4{font-size:var(--fs-base);color:var(--c-ink);font-weight:600}
.md ul,.md ol{padding-left:var(--sp-5);display:grid;gap:var(--sp-1)}
.md strong{font-weight:600}
</style>
