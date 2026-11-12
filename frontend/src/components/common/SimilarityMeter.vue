<template>
  <div class="meter">
    <div class="meter__track">
      <div class="meter__fill" :style="{ width: `${clamped * 100}%` }" />
      <div class="meter__ticks">
        <span
          class="meter__tick"
          :class="{ 'meter__tick--threshold': true }"
          :style="{ position: 'absolute', left: `${threshold * 100}%`, width: '2px' }"
          :title="`判重阈值 ${threshold}`"
        />
        <span
          class="meter__tick"
          :style="{ position: 'absolute', left: `${suspect * 100}%`, width: '1px' }"
          :title="`疑似阈值 ${suspect}`"
        />
      </div>
    </div>
    <div class="meter__legend">
      <span>jaccard {{ value.toFixed(3) }}</span>
      <span>阈值 {{ threshold.toFixed(2) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    value: number
    threshold?: number
    suspect?: number
  }>(),
  { threshold: 0.72, suspect: 0.55 },
)

const clamped = computed(() => Math.max(0, Math.min(1, props.value)))
</script>
