<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-900">Administratie importeren</h1>

    <!-- Drop Zone -->
    <div
      v-if="!isProcessing && !isComplete"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
      class="border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all"
      :class="isDragging ? 'border-primary-500 bg-primary-50' : 'border-surface-300 hover:border-primary-400 hover:bg-surface-50'"
    >
      <input ref="fileInput" type="file" multiple accept=".pdf,.csv,.xlsx,.mt940,.xml" class="hidden" @change="handleFileSelect" />
      <div class="flex flex-col items-center gap-4">
        <div class="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center">
          <svg class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </div>
        <div>
          <p class="text-lg font-semibold text-slate-900">Sleep bestanden hierheen of klik om te uploaden</p>
          <p class="text-sm text-slate-500 mt-1">Ondersteunde formaten: PDF, CSV, MT940, CAMT.053, Excel</p>
        </div>
      </div>
    </div>

    <!-- Selected files -->
    <div v-if="selectedFiles.length > 0 && !isProcessing && !isComplete" class="space-y-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Geselecteerde bestanden ({{ selectedFiles.length }})</h2>
        <div class="space-y-2">
          <div v-for="(file, i) in selectedFiles" :key="i" class="flex items-center justify-between py-2 px-3 bg-surface-50 rounded-lg">
            <div class="flex items-center gap-3">
              <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span class="text-sm font-medium text-slate-900">{{ file.name }}</span>
            </div>
            <span class="text-xs text-slate-500">{{ formatSize(file.size) }}</span>
          </div>
        </div>
        <button @click="startProcessing" class="mt-4 w-full bg-primary-600 text-white py-3 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center justify-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Start AI verwerking
        </button>
      </div>
    </div>

    <!-- Processing Status -->
    <div v-if="isProcessing" class="bg-white rounded-xl border border-surface-200 shadow-sm p-8">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">AI verwerkt je administratie...</h2>

      <div class="space-y-6">
        <div v-for="(step, i) in processingSteps" :key="step.name" class="flex items-center gap-4">
          <!-- Status icon -->
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
            :class="{
              'bg-emerald-100': step.status === 'done',
              'bg-primary-100': step.status === 'processing',
              'bg-surface-100': step.status === 'pending',
            }"
          >
            <svg v-if="step.status === 'done'" class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else-if="step.status === 'processing'" class="w-5 h-5 text-primary-600 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span v-else class="w-5 h-5 text-slate-400 text-center text-sm font-medium">{{ i + 1 }}</span>
          </div>

          <!-- Step info -->
          <div class="flex-1">
            <p class="text-sm font-semibold" :class="step.status === 'pending' ? 'text-slate-400' : 'text-slate-900'">
              {{ step.name }}
            </p>
            <p class="text-xs" :class="step.status === 'pending' ? 'text-slate-300' : 'text-slate-500'">
              {{ step.description }}
            </p>
          </div>

          <!-- Connector line -->
          <div v-if="i < processingSteps.length - 1" class="hidden"></div>
        </div>
      </div>

      <!-- Progress bar -->
      <div class="mt-8">
        <div class="flex justify-between text-sm text-slate-600 mb-2">
          <span>Voortgang</span>
          <span>{{ progress }}%</span>
        </div>
        <div class="w-full bg-surface-200 rounded-full h-2">
          <div class="bg-primary-600 h-2 rounded-full transition-all duration-500" :style="{ width: progress + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="isComplete" class="space-y-6">
      <!-- Summary cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p class="text-2xl font-bold text-emerald-700">{{ results.processed }}</p>
              <p class="text-sm text-emerald-600">Documenten verwerkt</p>
            </div>
          </div>
        </div>
        <div class="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <p class="text-2xl font-bold text-blue-700">{{ results.bookings }}</p>
              <p class="text-sm text-blue-600">Boekingen aangemaakt</p>
            </div>
          </div>
        </div>
        <div class="bg-amber-50 border border-amber-200 rounded-xl p-5">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div>
              <p class="text-2xl font-bold text-amber-700">{{ results.review }}</p>
              <p class="text-sm text-amber-600">Review nodig</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Processed items table -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-900">Verwerkte items</h2>
          <button @click="resetImport" class="text-sm text-primary-600 hover:text-primary-700 font-medium">
            Nieuwe import
          </button>
        </div>
        <table class="w-full">
          <thead>
            <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
              <th class="px-6 py-3">Document</th>
              <th class="px-6 py-3">Type</th>
              <th class="px-6 py-3">Categorie</th>
              <th class="px-6 py-3 text-right">Bedrag</th>
              <th class="px-6 py-3">BTW</th>
              <th class="px-6 py-3">Confidence</th>
              <th class="px-6 py-3">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-100">
            <tr
              v-for="item in processedItems"
              :key="item.id"
              class="hover:bg-surface-50"
              :class="item.confidence < 0.9 ? 'bg-amber-50/50' : ''"
            >
              <td class="px-6 py-3 text-sm font-medium text-slate-900">{{ item.document }}</td>
              <td class="px-6 py-3 text-sm text-slate-600">{{ item.type }}</td>
              <td class="px-6 py-3">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-slate-700">
                  {{ item.category }}
                </span>
              </td>
              <td class="px-6 py-3 text-sm text-right font-medium text-slate-900">€ {{ item.amount.toLocaleString('nl-NL', { minimumFractionDigits: 2 }) }}</td>
              <td class="px-6 py-3 text-sm text-slate-600">{{ item.btw }}%</td>
              <td class="px-6 py-3">
                <div class="flex items-center gap-2">
                  <div class="w-16 bg-surface-200 rounded-full h-1.5">
                    <div
                      class="h-1.5 rounded-full"
                      :class="item.confidence >= 0.9 ? 'bg-emerald-500' : item.confidence >= 0.7 ? 'bg-amber-500' : 'bg-red-500'"
                      :style="{ width: (item.confidence * 100) + '%' }"
                    ></div>
                  </div>
                  <span class="text-xs text-slate-500">{{ Math.round(item.confidence * 100) }}%</span>
                </div>
              </td>
              <td class="px-6 py-3">
                <span
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  :class="item.confidence >= 0.9 ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'"
                >
                  {{ item.confidence >= 0.9 ? 'Geboekt' : 'Review' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const fileInput = ref<HTMLInputElement>()
const selectedFiles = ref<File[]>([])
const isDragging = ref(false)
const isProcessing = ref(false)
const isComplete = ref(false)
const progress = ref(0)

const processingSteps = ref([
  { name: 'Upload', description: 'Bestanden worden geüpload...', status: 'pending' as const },
  { name: 'OCR Extractie', description: 'Tekst wordt uit documenten gehaald...', status: 'pending' as const },
  { name: 'AI Classificatie', description: 'Transacties worden gecategoriseerd...', status: 'pending' as const },
  { name: 'Boekingen aanmaken', description: 'Grootboekregels worden gegenereerd...', status: 'pending' as const },
])

const results = { processed: 8, bookings: 12, review: 2 }

const processedItems = [
  { id: 1, document: 'factuur-bakkerij.pdf', type: 'Factuur', category: 'Omzet', amount: 2450, btw: 21, confidence: 0.97 },
  { id: 2, document: 'google-workspace.pdf', type: 'Abonnement', category: 'Software', amount: 12.99, btw: 21, confidence: 0.95 },
  { id: 3, document: 'ns-businesscard.csv', type: 'Transport', category: 'Transport', amount: 156.80, btw: 9, confidence: 0.92 },
  { id: 4, document: 'webdesign-factuur.pdf', type: 'Factuur', category: 'Omzet', amount: 3800, btw: 21, confidence: 0.98 },
  { id: 5, document: 'onbekende-betaling.pdf', type: 'Overig', category: 'Overige kosten', amount: 1250, btw: 21, confidence: 0.52 },
  { id: 6, document: 'kantoorartikelen.pdf', type: 'Bon', category: 'Kantoor', amount: 34.50, btw: 21, confidence: 0.88 },
  { id: 7, document: 'facebook-ads.pdf', type: 'Factuur', category: 'Marketing', amount: 250, btw: 21, confidence: 0.94 },
  { id: 8, document: 'kpn-factuur.pdf', type: 'Factuur', category: 'Telefoon', amount: 45, btw: 21, confidence: 0.96 },
]

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    selectedFiles.value = Array.from(input.files)
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files) {
    selectedFiles.value = Array.from(event.dataTransfer.files)
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

async function startProcessing() {
  isProcessing.value = true
  progress.value = 0

  const steps = processingSteps.value
  for (let i = 0; i < steps.length; i++) {
    steps[i].status = 'processing'
    await sleep(1200)
    progress.value = Math.round(((i + 1) / steps.length) * 100)
    steps[i].status = 'done'
  }

  await sleep(500)
  isProcessing.value = false
  isComplete.value = true
}

function resetImport() {
  selectedFiles.value = []
  isProcessing.value = false
  isComplete.value = false
  progress.value = 0
  processingSteps.value.forEach((s) => (s.status = 'pending'))
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
</script>
