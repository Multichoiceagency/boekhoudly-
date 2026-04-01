<template>
  <div class="flex h-screen bg-[#F5F6FA]">
    <!-- Mobile overlay -->
    <div v-if="sidebarOpen" class="fixed inset-0 bg-black/40 z-40 lg:hidden" @click="sidebarOpen = false" />

    <!-- Sidebar -->
    <aside
      class="fixed lg:static inset-y-0 left-0 z-50 w-[250px] bg-white border-r border-gray-100 flex flex-col flex-shrink-0 transform transition-transform duration-200 ease-in-out"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
    >
      <!-- Logo -->
      <div class="px-5 py-5 flex items-center justify-between">
        <NuxtLink to="/dashboard" class="flex items-center gap-2.5" @click="sidebarOpen = false">
          <div class="w-9 h-9 bg-emerald-600 rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          </div>
          <span class="text-[17px] font-bold text-gray-900">FiscalFlow</span>
        </NuxtLink>
        <button @click="sidebarOpen = false" class="lg:hidden p-1 text-gray-400 hover:text-gray-600">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>

      <!-- Search -->
      <div class="px-4 mb-2">
        <div class="relative">
          <svg class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input type="text" placeholder="Zoeken..." class="w-full pl-9 pr-3 py-2 bg-gray-50 border border-gray-100 rounded-xl text-[13px] text-gray-600 focus:outline-none focus:ring-1 focus:ring-emerald-500" />
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-2 overflow-y-auto sidebar-scroll">
        <p class="px-3 mb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Hoofdmenu</p>
        <SideItem v-for="item in mainItems" :key="item.path" :item="item" @click="sidebarOpen = false" />

        <p class="px-3 mt-5 mb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Boekhouding</p>
        <SideItem v-for="item in boekhoudItems" :key="item.path" :item="item" @click="sidebarOpen = false" />

        <p class="px-3 mt-5 mb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Financieel</p>
        <SideItem v-for="item in financialItems" :key="item.path" :item="item" @click="sidebarOpen = false" />

        <p class="px-3 mt-5 mb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">AI & Beheer</p>
        <SideItem v-for="item in aiItems" :key="item.path" :item="item" @click="sidebarOpen = false" />
      </nav>

      <!-- Upgrade card -->
      <div class="px-4 py-4 hidden lg:block">
        <div class="bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-2xl p-4 text-white">
          <p class="text-sm font-bold">FiscalFlow Pro</p>
          <p class="text-[11px] text-emerald-100 mt-1">Onbeperkt AI, alle modules</p>
          <div class="flex gap-2 mt-3">
            <NuxtLink to="/instellingen" class="text-[11px] bg-white text-emerald-700 px-3 py-1 rounded-lg font-semibold hover:bg-emerald-50">Upgrade</NuxtLink>
          </div>
        </div>
      </div>

      <!-- Settings & Logout -->
      <div class="px-3 py-3 border-t border-gray-100 space-y-0.5">
        <NuxtLink to="/instellingen" class="flex items-center gap-3 px-3 py-2 rounded-xl text-[13px] font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-900 transition-colors" @click="sidebarOpen = false">
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          Instellingen
        </NuxtLink>
        <button @click="handleLogout" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-[13px] font-medium text-red-500 hover:bg-red-50 transition-colors">
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
          Uitloggen
        </button>
      </div>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col overflow-hidden w-full">
      <!-- Top bar -->
      <header class="h-[60px] bg-white border-b border-gray-100 flex items-center justify-between px-4 md:px-6 flex-shrink-0">
        <div class="flex items-center gap-3">
          <!-- Hamburger -->
          <button @click="sidebarOpen = true" class="lg:hidden p-2 -ml-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-xl">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
          <div class="hidden sm:flex items-center gap-2 text-[13px] text-gray-400">
            <span>FiscalFlow</span>
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
            <span class="text-gray-900 font-medium">{{ pageTitle }}</span>
          </div>
          <span class="sm:hidden text-sm font-semibold text-gray-900">{{ pageTitle }}</span>
        </div>
        <div class="flex items-center gap-2 md:gap-3">
          <NuxtLink to="/ai-accountant" class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-xl text-[12px] font-semibold hover:bg-emerald-100 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            AI Chat
          </NuxtLink>
          <button class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-xl transition-colors relative">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
          </button>
          <div class="flex items-center gap-2 ml-1 pl-2 md:pl-3 border-l border-gray-100">
            <img :src="avatarUrl" class="w-8 h-8 rounded-full" alt="" />
            <span class="hidden md:inline text-[13px] font-medium text-gray-700">{{ userName }}</span>
          </div>
        </div>
      </header>

      <!-- Content -->
      <main class="flex-1 overflow-y-auto p-4 md:p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { user, logout } = useAuth()

const sidebarOpen = ref(false)

// Close sidebar on route change (mobile)
watch(() => route.path, () => { sidebarOpen.value = false })

const userName = computed(() => user.value?.full_name || 'Gebruiker')
const avatarUrl = computed(() => {
  if (user.value?.avatar_url) return user.value.avatar_url
  const name = encodeURIComponent(userName.value)
  return `https://ui-avatars.com/api/?name=${name}&background=059669&color=fff&size=32&rounded=true&bold=true`
})

function handleLogout() {
  sidebarOpen.value = false
  logout()
}

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/dashboard': 'Dashboard', '/facturen': 'Facturen', '/uitgaven': 'Uitgaven', '/bank': 'Bank',
    '/grootboek': 'Grootboek', '/debiteuren': 'Debiteuren', '/crediteuren': 'Crediteuren',
    '/btw': 'BTW Aangiftes', '/aangifte-ib': 'Aangifte IB', '/jaarrekening': 'Jaarrekening',
    '/rapportage': 'Rapportage', '/audit': 'Audit Rapport', '/uren': 'Uren', '/import': 'Import',
    '/ai-accountant': 'AI Accountant', '/bedrijven': 'Bedrijven', '/instellingen': 'Instellingen',
  }
  return titles[route.path] || 'Dashboard'
})

const SideItem = defineComponent({
  props: { item: { type: Object, required: true } },
  setup(props) {
    const route = useRoute()
    const active = computed(() => route.path === props.item.path || (props.item.path === '/dashboard' && route.path === '/'))
    return () => h(resolveComponent('NuxtLink'), {
      to: props.item.path,
      class: [
        'flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] font-medium transition-all mb-0.5',
        active.value ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-200' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
      ],
    }, () => [
      h('span', { innerHTML: props.item.icon, class: ['w-[18px] h-[18px] flex-shrink-0', active.value ? 'text-white' : 'text-gray-400'] }),
      h('span', { class: 'flex-1' }, props.item.label),
      props.item.badge ? h('span', { class: ['text-[10px] px-1.5 py-0.5 rounded-full font-semibold', active.value ? 'bg-white/20 text-white' : 'bg-emerald-100 text-emerald-700'] }, props.item.badge) : null,
    ])
  },
})

const mainItems = [
  { label: 'Dashboard', path: '/dashboard', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" /></svg>' },
  { label: 'Import', path: '/import', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>' },
]

const boekhoudItems = [
  { label: 'Grootboek', path: '/grootboek', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>' },
  { label: 'Facturen', path: '/facturen', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>' },
  { label: 'Uitgaven', path: '/uitgaven', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>' },
  { label: 'Debiteuren', path: '/debiteuren', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>' },
  { label: 'Crediteuren', path: '/crediteuren', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>' },
]

const financialItems = [
  { label: 'Bank', path: '/bank', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" /></svg>' },
  { label: 'BTW Aangiftes', path: '/btw', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" /></svg>' },
  { label: 'Aangifte IB', path: '/aangifte-ib', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>' },
  { label: 'Jaarrekening', path: '/jaarrekening', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>' },
  { label: 'Rapportage', path: '/rapportage', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>' },
  { label: 'Audit', path: '/audit', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>' },
  { label: 'Uren', path: '/uren', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>' },
]

const aiItems = [
  { label: 'AI Accountant', path: '/ai-accountant', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>' },
  { label: 'Bedrijven', path: '/bedrijven', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>' },
]
</script>

<style>
/* Hide sidebar scrollbar */
.sidebar-scroll {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}
.sidebar-scroll::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}
</style>
