<script setup lang="ts">
// Redirect is handled by auth.global middleware
// This page just redirects to dashboard (middleware will bounce to /login if needed)
navigateTo('/dashboard')
</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="w-8 h-8 border-4 border-emerald-200 border-t-emerald-600 rounded-full animate-spin"></div>
  </div>
</template>
