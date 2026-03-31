export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  ssr: false,

  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@nuxtjs/color-mode',
    '@vueuse/nuxt',
  ],

  app: {
    head: {
      title: 'FiscalFlow AI',
      meta: [
        { name: 'description', content: 'AI-powered boekhoudplatform' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
      ],
    },
  },

  runtimeConfig: {
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000',
    },
  },

  tailwindcss: {
    cssPath: '~/assets/css/tailwind.css',
  },

  colorMode: {
    classSuffix: '',
  },
})
