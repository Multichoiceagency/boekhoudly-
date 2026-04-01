<script setup lang="ts">
const emit = defineEmits<{
  (e: 'close'): void
}>()

const currentSlide = ref(0)

const slides = [
  {
    title: 'Welkom bij FiscalFlow!',
    description: 'Je AI-powered boekhoudplatform is klaar. Hier is een kort overzicht van wat je kunt doen.',
    icon: '🚀',
    color: 'from-emerald-500 to-emerald-700',
  },
  {
    title: 'Transacties importeren',
    description: 'Upload facturen, bonnetjes of bankafschriften. Onze AI categoriseert ze automatisch en boekt ze in.',
    icon: '📄',
    color: 'from-blue-500 to-blue-700',
    tip: 'Ga naar Import in het menu om te starten',
  },
  {
    title: 'Bank koppelen',
    description: 'Koppel je bankrekening via PSD2 voor automatische transactie-import. Veilig en beveiligd.',
    icon: '🏦',
    color: 'from-violet-500 to-violet-700',
    tip: 'Ga naar Instellingen > Integraties',
  },
  {
    title: 'Cloud opslag',
    description: 'Verbind Google Drive, Dropbox of OneDrive om documenten direct te importeren.',
    icon: '☁️',
    color: 'from-sky-500 to-sky-700',
    tip: 'Ga naar Instellingen > Integraties',
  },
  {
    title: 'AI Accountant',
    description: 'Stel vragen over je boekhouding, BTW of belastingzaken. Je persoonlijke AI-accountant staat voor je klaar.',
    icon: '🤖',
    color: 'from-amber-500 to-amber-700',
    tip: 'Klik op "AI Chat" rechtsboven',
  },
]

function next() {
  if (currentSlide.value < slides.length - 1) {
    currentSlide.value++
  } else {
    emit('close')
  }
}

function prev() {
  if (currentSlide.value > 0) {
    currentSlide.value--
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
    <div class="bg-white rounded-3xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
      <!-- Slide content -->
      <div class="p-8 text-center">
        <!-- Icon -->
        <div
          class="w-20 h-20 mx-auto rounded-3xl bg-gradient-to-br flex items-center justify-center text-4xl mb-6 shadow-lg"
          :class="slides[currentSlide].color"
        >
          {{ slides[currentSlide].icon }}
        </div>

        <h2 class="text-2xl font-bold text-gray-900 mb-2">{{ slides[currentSlide].title }}</h2>
        <p class="text-gray-500 text-sm leading-relaxed max-w-sm mx-auto">{{ slides[currentSlide].description }}</p>

        <div v-if="slides[currentSlide].tip" class="mt-4 inline-flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg text-xs text-gray-600">
          <svg class="w-3.5 h-3.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {{ slides[currentSlide].tip }}
        </div>
      </div>

      <!-- Footer -->
      <div class="px-8 pb-6 flex items-center justify-between">
        <!-- Dots -->
        <div class="flex gap-1.5">
          <button
            v-for="(_, i) in slides"
            :key="i"
            @click="currentSlide = i"
            class="w-2 h-2 rounded-full transition-all"
            :class="i === currentSlide ? 'bg-emerald-600 w-6' : 'bg-gray-200 hover:bg-gray-300'"
          />
        </div>

        <!-- Buttons -->
        <div class="flex items-center gap-2">
          <button
            v-if="currentSlide > 0"
            @click="prev"
            class="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 font-medium transition-colors"
          >
            Vorige
          </button>
          <button
            v-if="currentSlide === 0"
            @click="emit('close')"
            class="px-4 py-2 text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            Overslaan
          </button>
          <button
            @click="next"
            class="px-5 py-2 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-all"
          >
            {{ currentSlide === slides.length - 1 ? 'Aan de slag!' : 'Volgende' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
