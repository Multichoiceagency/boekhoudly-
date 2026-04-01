<script setup lang="ts">
// Registration is now handled in the login page via email verification
// Redirect to login
definePageMeta({ layout: 'auth' })
navigateTo('/login')
</script>

<template>
  <div class="text-center py-12">
    <p class="text-gray-500">Doorverwijzen naar inloggen...</p>
  </div>
</template>
