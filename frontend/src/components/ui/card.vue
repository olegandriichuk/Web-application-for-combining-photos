<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
  class?: string
}

const props = defineProps<Props>()
</script>

<template>
  <div :class="cn('bg-white rounded-2xl shadow-sm border border-[#e5e7eb]', props.class)">
    <slot />
  </div>
</template>
