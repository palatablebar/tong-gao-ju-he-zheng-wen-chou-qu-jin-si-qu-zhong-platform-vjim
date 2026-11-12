<template>
  <span class="stamp" :class="[`stamp--${tone}`, { 'stamp--drop': animate }]">{{ label }}</span>
</template>

<script setup lang="ts">
type Tone = 'confirmed' | 'auto' | 'split'

withDefaults(
  defineProps<{
    label: string
    tone?: Tone
    animate?: boolean
  }>(),
  { tone: 'auto', animate: false },
)
</script>
