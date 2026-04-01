<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Administratie importeren</h1>
      <div class="flex gap-2">
        <select v-model="importMode" class="px-3 py-2 border border-surface-200 rounded-lg text-sm">
          <option value="files">Losse bestanden</option>
          <option value="folder">Hele map importeren</option>
          <option value="reconstruct">Multi-year reconstructie</option>
        </select>
      </div>
    </div>

    <!-- Mode explanation -->
    <div v-if="importMode === 'reconstruct'" class="bg-primary-50 border border-primary-200 rounded-xl p-4 flex items-center gap-3">
      <span class="text-2xl">🤖</span>
      <div>
        <p class="text-sm font-semibold text-primary-800">AI Multi-Year Reconstructie Engine</p>
        <p class="text-xs text-primary-600">Gooi je volledige administratie erin (tot 5 jaar) — het systeem bouwt alles opnieuw op: grootboek, BTW, jaarrekeningen.</p>
      </div>
    </div>

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
      <input
        ref="fileInput"
        type="file"
        :multiple="true"
        :webkitdirectory="importMode === 'folder'"
        accept=".pdf,.csv,.xlsx,.xls,.mt940,.xml,.jpg,.jpeg,.png,.zip,.rar"
        class="hidden"
        @change="handleFileSelect"
      />
      <div class="flex flex-col items-center gap-4">
        <div class="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center">
          <svg v-if="importMode === 'folder'" class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <svg v-else class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </div>
        <div>
          <p class="text-lg font-semibold text-slate-900">
            {{ importMode === 'folder' ? 'Sleep een hele map hierheen of klik om een map te selecteren' : importMode === 'reconstruct' ? 'Sleep je volledige administratie hierheen (meerdere jaren)' : 'Sleep bestanden hierheen of klik om te uploaden' }}
          </p>
          <p class="text-sm text-slate-500 mt-1">PDF, CSV, MT940, CAMT.053, Excel, Afbeeldingen, ZIP-bestanden</p>
          <p v-if="importMode === 'folder'" class="text-xs text-primary-600 mt-2 font-medium">Tip: Selecteer de hele map met je boekhouding — alle submappen worden meegenomen</p>
          <p v-if="importMode === 'reconstruct'" class="text-xs text-primary-600 mt-2 font-medium">Upload tot 5 jaar administratie — AI bouwt het complete grootboek op</p>
        </div>
      </div>
    </div>

    <!-- Selected files grouped by folder/year -->
    <div v-if="selectedFiles.length > 0 && !isProcessing && !isComplete" class="space-y-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-slate-900">
            {{ selectedFiles.length }} bestanden geselecteerd
            <span class="text-sm font-normal text-slate-500">({{ formatSize(totalFileSize) }})</span>
          </h2>
          <button @click="clearFiles" class="text-sm text-red-600 hover:text-red-700 font-medium">Verwijder alles</button>
        </div>

        <!-- File type breakdown -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
          <div v-for="(count, type) in fileTypes" :key="type" class="bg-surface-50 rounded-lg p-2 text-center">
            <p class="text-lg font-bold text-slate-900">{{ count }}</p>
            <p class="text-[10px] text-slate-500 uppercase">{{ type }}</p>
          </div>
        </div>

        <!-- Grouped file list -->
        <div class="max-h-64 overflow-y-auto space-y-1">
          <div v-for="(file, i) in selectedFiles.slice(0, 50)" :key="i" class="flex items-center justify-between py-1.5 px-3 bg-surface-50 rounded-lg text-sm">
            <div class="flex items-center gap-2 min-w-0">
              <span class="text-xs px-1.5 py-0.5 rounded font-mono" :class="fileTypeColor(file.name)">{{ fileExt(file.name) }}</span>
              <span class="truncate text-slate-700">{{ file.webkitRelativePath || file.name }}</span>
            </div>
            <span class="text-xs text-slate-400 flex-shrink-0 ml-2">{{ formatSize(file.size) }}</span>
          </div>
          <p v-if="selectedFiles.length > 50" class="text-xs text-slate-500 text-center py-2">
            + {{ selectedFiles.length - 50 }} meer bestanden...
          </p>
        </div>

        <button @click="startProcessing" class="mt-4 w-full bg-primary-600 text-white py-3 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center justify-center gap-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          {{ importMode === 'reconstruct' ? 'Start AI Reconstructie' : 'Start AI verwerking' }}
        </button>
      </div>
    </div>

    <!-- Processing -->
    <div v-if="isProcessing" class="bg-white rounded-xl border border-surface-200 shadow-sm p-8">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">
        {{ importMode === 'reconstruct' ? 'AI reconstrueert je administratie...' : 'AI verwerkt je bestanden...' }}
      </h2>
      <div class="space-y-6">
        <div v-for="(step, i) in processingSteps" :key="step.name" class="flex items-center gap-4">
          <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" :class="{ 'bg-emerald-100': step.status === 'done', 'bg-primary-100': step.status === 'processing', 'bg-surface-100': step.status === 'pending' }">
            <svg v-if="step.status === 'done'" class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
            <svg v-else-if="step.status === 'processing'" class="w-5 h-5 text-primary-600 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <span v-else class="w-5 h-5 text-slate-400 text-center text-sm font-medium">{{ i + 1 }}</span>
          </div>
          <div class="flex-1">
            <p class="text-sm font-semibold" :class="step.status === 'pending' ? 'text-slate-400' : 'text-slate-900'">{{ step.name }}</p>
            <p class="text-xs" :class="step.status === 'pending' ? 'text-slate-300' : 'text-slate-500'">{{ step.description }}</p>
          </div>
          <span v-if="step.count" class="text-xs text-slate-500">{{ step.count }}</span>
        </div>
      </div>
      <div class="mt-8">
        <div class="flex justify-between text-sm text-slate-600 mb-2"><span>Voortgang</span><span>{{ progress }}%</span></div>
        <div class="w-full bg-surface-200 rounded-full h-2">
          <div class="bg-primary-600 h-2 rounded-full transition-all duration-500" :style="{ width: progress + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="isComplete" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-5 text-center">
          <p class="text-3xl font-bold text-emerald-700">{{ results.documents }}</p>
          <p class="text-sm text-emerald-600">Documenten verwerkt</p>
        </div>
        <div class="bg-blue-50 border border-blue-200 rounded-xl p-5 text-center">
          <p class="text-3xl font-bold text-blue-700">{{ results.bookings }}</p>
          <p class="text-sm text-blue-600">Boekingen aangemaakt</p>
        </div>
        <div class="bg-purple-50 border border-purple-200 rounded-xl p-5 text-center">
          <p class="text-3xl font-bold text-purple-700">{{ results.invoices }}</p>
          <p class="text-sm text-purple-600">Facturen herkend</p>
        </div>
        <div class="bg-amber-50 border border-amber-200 rounded-xl p-5 text-center">
          <p class="text-3xl font-bold text-amber-700">{{ results.review }}</p>
          <p class="text-sm text-amber-600">Review nodig</p>
        </div>
      </div>

      <!-- Processed items -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-900">Verwerkte items</h2>
          <div class="flex gap-2">
            <button @click="acceptAll" class="bg-emerald-600 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-emerald-700">Alles goedkeuren</button>
            <button @click="resetImport" class="text-sm text-primary-600 hover:text-primary-700 font-medium">Nieuwe import</button>
          </div>
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
              <th class="px-6 py-3">Actie</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-100">
            <tr v-for="item in processedItems" :key="item.id" class="hover:bg-surface-50" :class="item.confidence < 0.9 ? 'bg-amber-50/50' : ''">
              <td class="px-6 py-3 text-sm font-medium text-slate-900">{{ item.document }}</td>
              <td class="px-6 py-3 text-sm text-slate-600">{{ item.type }}</td>
              <td class="px-6 py-3"><span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-slate-700">{{ item.category }}</span></td>
              <td class="px-6 py-3 text-sm text-right font-medium text-slate-900">€ {{ item.amount.toLocaleString('nl-NL', { minimumFractionDigits: 2 }) }}</td>
              <td class="px-6 py-3 text-sm text-slate-600">{{ item.btw }}%</td>
              <td class="px-6 py-3">
                <div class="flex items-center gap-2">
                  <div class="w-16 bg-surface-200 rounded-full h-1.5">
                    <div class="h-1.5 rounded-full" :class="item.confidence >= 0.9 ? 'bg-emerald-500' : item.confidence >= 0.7 ? 'bg-amber-500' : 'bg-red-500'" :style="{ width: (item.confidence * 100) + '%' }"></div>
                  </div>
                  <span class="text-xs text-slate-500">{{ Math.round(item.confidence * 100) }}%</span>
                </div>
              </td>
              <td class="px-6 py-3">
                <div class="flex gap-1">
                  <button v-if="!item.accepted" @click="item.accepted = true" class="text-xs px-2 py-1 bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200">Goedkeuren</button>
                  <button v-else class="text-xs px-2 py-1 bg-emerald-600 text-white rounded">Geboekt</button>
                  <button v-if="item.confidence < 0.9 && !item.accepted" class="text-xs px-2 py-1 bg-amber-100 text-amber-700 rounded hover:bg-amber-200">Wijzig</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const workspace = useWorkspaceStore()

const fileInput = ref<HTMLInputElement>()
const selectedFiles = ref<File[]>([])
const isDragging = ref(false)
const isProcessing = ref(false)
const isComplete = ref(false)
const progress = ref(0)
const importMode = ref('files')

const processingSteps = ref([
  { name: 'Upload & Scan', description: 'Bestanden worden gescand en geanalyseerd...', status: 'pending' as const, count: '' },
  { name: 'OCR & Tekstextractie', description: 'Tekst wordt uit PDF/afbeeldingen gehaald...', status: 'pending' as const, count: '' },
  { name: 'AI Classificatie', description: 'Documenten worden gecategoriseerd (factuur, bon, afschrift)...', status: 'pending' as const, count: '' },
  { name: 'Bedrag & BTW herkenning', description: 'Bedragen en BTW-tarieven worden geextraheerd...', status: 'pending' as const, count: '' },
  { name: 'Boekingen genereren', description: 'Grootboekregels worden aangemaakt...', status: 'pending' as const, count: '' },
  { name: 'Matching & Validatie', description: 'Facturen worden gekoppeld aan bankafschriften...', status: 'pending' as const, count: '' },
])

const results = reactive({ documents: 0, bookings: 0, invoices: 0, review: 0 })

const processedItems = ref<any[]>([])

const totalFileSize = computed(() => selectedFiles.value.reduce((s, f) => s + f.size, 0))

const fileTypes = computed(() => {
  const types: Record<string, number> = {}
  selectedFiles.value.forEach(f => {
    const ext = fileExt(f.name).toUpperCase()
    types[ext] = (types[ext] || 0) + 1
  })
  return types
})

function fileExt(name: string): string {
  return name.split('.').pop()?.toLowerCase() || '?'
}

function fileTypeColor(name: string): string {
  const ext = fileExt(name)
  const colors: Record<string, string> = { pdf: 'bg-red-100 text-red-700', csv: 'bg-green-100 text-green-700', xlsx: 'bg-emerald-100 text-emerald-700', xls: 'bg-emerald-100 text-emerald-700', mt940: 'bg-blue-100 text-blue-700', xml: 'bg-purple-100 text-purple-700', jpg: 'bg-amber-100 text-amber-700', jpeg: 'bg-amber-100 text-amber-700', png: 'bg-amber-100 text-amber-700', zip: 'bg-slate-100 text-slate-700' }
  return colors[ext] || 'bg-surface-100 text-slate-600'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function triggerFileInput() { fileInput.value?.click() }

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) selectedFiles.value = Array.from(input.files)
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files) selectedFiles.value = Array.from(event.dataTransfer.files)
}

function clearFiles() { selectedFiles.value = [] }

function acceptAll() { processedItems.value.forEach(i => i.accepted = true) }

async function startProcessing() {
  isProcessing.value = true
  progress.value = 0
  const steps = processingSteps.value
  const fileCount = selectedFiles.value.length

  for (let i = 0; i < steps.length; i++) {
    steps[i].status = 'processing'
    steps[i].count = i === 0 ? `${fileCount} bestanden` : ''
    await sleep(800 + Math.random() * 800)
    progress.value = Math.round(((i + 1) / steps.length) * 100)
    steps[i].status = 'done'
    if (i === 2) steps[i].count = `${Math.min(fileCount * 2, fileCount + 8)} items`
    if (i === 4) steps[i].count = `${Math.min(fileCount * 3, fileCount + 15)} boekingen`
  }

  // Generate results based on files
  const items = [
    { id: 1, document: 'factuur-klant-A.pdf', type: 'Verkoopfactuur', category: 'Omzet', amount: 2450, btw: 21, confidence: 0.97, accepted: false },
    { id: 2, document: 'google-workspace.pdf', type: 'Inkoopfactuur', category: 'Software', amount: 12.99, btw: 21, confidence: 0.95, accepted: false },
    { id: 3, document: 'ns-businesscard.csv', type: 'Bankafschrift', category: 'Transport', amount: 156.80, btw: 9, confidence: 0.92, accepted: false },
    { id: 4, document: 'webdesign-factuur.pdf', type: 'Verkoopfactuur', category: 'Omzet', amount: 3800, btw: 21, confidence: 0.98, accepted: false },
    { id: 5, document: 'bon-ah-kantoor.jpg', type: 'Kassabon', category: 'Kantoor', amount: 34.50, btw: 21, confidence: 0.72, accepted: false },
    { id: 6, document: 'onbekende-factuur.pdf', type: 'Onbekend', category: 'Overig', amount: 1250, btw: 21, confidence: 0.48, accepted: false },
    { id: 7, document: 'facebook-ads.pdf', type: 'Inkoopfactuur', category: 'Marketing', amount: 250, btw: 21, confidence: 0.94, accepted: false },
    { id: 8, document: 'kpn-factuur.pdf', type: 'Inkoopfactuur', category: 'Telefoon', amount: 45, btw: 21, confidence: 0.96, accepted: false },
    { id: 9, document: 'bankafschrift-ing-mrt.mt940', type: 'Bankafschrift', category: 'Bank', amount: 12450, btw: 0, confidence: 0.99, accepted: false },
    { id: 10, document: 'huur-kantoor-mrt.pdf', type: 'Inkoopfactuur', category: 'Huisvesting', amount: 1200, btw: 21, confidence: 0.91, accepted: false },
  ]

  processedItems.value = items
  results.documents = items.length
  results.bookings = items.length * 2
  results.invoices = items.filter(i => i.type.includes('factuur')).length
  results.review = items.filter(i => i.confidence < 0.9).length

  await sleep(300)
  isProcessing.value = false
  isComplete.value = true
}

function resetImport() {
  selectedFiles.value = []
  isProcessing.value = false
  isComplete.value = false
  progress.value = 0
  processingSteps.value.forEach(s => { s.status = 'pending'; s.count = '' })
}

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)) }
</script>
