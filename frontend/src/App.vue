<template>
  <AppShell v-if="showShell">
    <router-view v-slot="{ Component }">
      <transition name="page" appear mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </AppShell>
  <router-view v-else />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppShell from './components/common/AppShell.vue'

const route = useRoute()
const showShell = computed(() => !route.meta.public)
</script>
