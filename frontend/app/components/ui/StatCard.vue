<template>
  <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
    <div class="flex items-center justify-between">
      <p class="text-sm font-medium text-slate-500">{{ title }}</p>
      <div
        class="w-10 h-10 rounded-lg flex items-center justify-center"
        :class="{
          'bg-primary-100': color === 'primary',
          'bg-amber-100': color === 'amber',
          'bg-emerald-100': color === 'emerald',
          'bg-green-100': color === 'green',
        }"
      >
        <svg
          class="w-5 h-5"
          :class="{
            'text-primary-600': color === 'primary',
            'text-amber-600': color === 'amber',
            'text-emerald-600': color === 'emerald',
            'text-green-600': color === 'green',
          }"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path v-if="color === 'primary'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          <path v-else-if="color === 'amber'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          <path v-else-if="color === 'emerald'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      </div>
    </div>
    <p class="text-2xl font-bold text-slate-900 mt-3">{{ value }}</p>
    <div class="flex items-center gap-1 mt-2">
      <svg v-if="trend === 'up'" class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
      <svg v-else-if="trend === 'down'" class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
      </svg>
      <span class="text-sm" :class="trend === 'up' ? 'text-emerald-600' : trend === 'down' ? 'text-red-600' : 'text-slate-500'">
        {{ change }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  value: string
  change: string
  color: 'primary' | 'amber' | 'emerald' | 'green'
  trend: 'up' | 'down' | 'neutral'
}>()
</script>
