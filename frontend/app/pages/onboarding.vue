<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const api = useApi()
const router = useRouter()
const currentStep = ref(1)
const totalSteps = 5
const loading = ref(false)
const error = ref('')

// Step 1: Welcome & bedrijfstype
const companyType = ref('')
const companyTypes = [
  { value: 'zzp', label: 'ZZP / Eenmanszaak', icon: '👤', desc: 'Zelfstandig ondernemer' },
  { value: 'bv', label: 'BV', icon: '🏢', desc: 'Besloten Vennootschap' },
  { value: 'vof', label: 'VOF', icon: '👥', desc: 'Vennootschap onder Firma' },
  { value: 'stichting', label: 'Stichting', icon: '🏛️', desc: 'Stichting of Vereniging' },
]

// Step 2: Company details
const companyName = ref('')
const kvkNumber = ref('')
const btwNumber = ref('')
const industry = ref('')
const industries = [
  'ICT & Software', 'Consultancy', 'Marketing & Design', 'Bouw & Techniek',
  'Horeca', 'Detailhandel', 'Gezondheidszorg', 'Onderwijs', 'Financiele dienstverlening',
  'Transport & Logistiek', 'Juridisch', 'Anders',
]

// Step 3: Address & contact
const address = ref('')
const city = ref('')
const postalCode = ref('')
const phone = ref('')
const iban = ref('')

// Step 4: Bank koppeling
const bankConnected = ref(false)
const selectedBank = ref<any>(null)
const banks = ref<any[]>([])
const banksLoading = ref(false)
const bankSearch = ref('')

const filteredBanks = computed(() => {
  if (!bankSearch.value) return banks.value.slice(0, 12)
  const q = bankSearch.value.toLowerCase()
  return banks.value.filter((b: any) => b.name.toLowerCase().includes(q)).slice(0, 12)
})

// Step 5: Preferences
const fiscalYearStart = ref('01-01')
const btwPeriod = ref('quarter')

async function loadBanks() {
  banksLoading.value = true
  try {
    banks.value = await api.get<any[]>('/bank/institutions?country=NL')
  } catch {
    banks.value = []
  } finally {
    banksLoading.value = false
  }
}

async function connectBank(bank: any) {
  selectedBank.value = bank
  try {
    const result = await api.post<{ link: string }>('/bank/connect', {
      institution_id: bank.id,
      institution_name: bank.name,
      institution_logo: bank.logo,
    })
    // Open bank auth in new window
    window.open(result.link, '_blank', 'width=600,height=700')
    bankConnected.value = true
  } catch (e: any) {
    error.value = e.message || 'Bankkoppeling mislukt'
  }
}

async function saveStep() {
  loading.value = true
  error.value = ''
  try {
    await api.put('/auth/onboarding', {
      step: currentStep.value,
      data: {
        company_type: companyType.value,
        company_name: companyName.value,
        kvk_number: kvkNumber.value,
        btw_number: btwNumber.value,
        industry: industry.value,
        address: address.value,
        city: city.value,
        postal_code: postalCode.value,
        phone: phone.value,
        iban: iban.value,
        fiscal_year_start: fiscalYearStart.value,
        btw_period: btwPeriod.value,
      },
    })
  } catch {
    // Non-critical, continue anyway
  } finally {
    loading.value = false
  }
}

async function nextStep() {
  if (currentStep.value === 1 && !companyType.value) {
    error.value = 'Kies een bedrijfsvorm'
    return
  }
  if (currentStep.value === 2 && !companyName.value) {
    error.value = 'Vul je bedrijfsnaam in'
    return
  }
  error.value = ''

  await saveStep()

  if (currentStep.value === 4) {
    loadBanks()
  }

  if (currentStep.value < totalSteps) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
    error.value = ''
  }
}

async function completeOnboarding() {
  loading.value = true
  error.value = ''
  try {
    await api.post('/auth/onboarding/complete', {
      company_name: companyName.value,
      kvk_number: kvkNumber.value || null,
      btw_number: btwNumber.value || null,
      address: address.value || null,
      city: city.value || null,
      postal_code: postalCode.value || null,
      iban: iban.value || null,
      phone: phone.value || null,
      industry: industry.value || null,
      company_type: companyType.value || null,
      fiscal_year_start: fiscalYearStart.value || null,
    })
    router.push('/dashboard?welcome=true')
  } catch (e: any) {
    error.value = e.message || 'Er ging iets mis'
  } finally {
    loading.value = false
  }
}

// Load banks when reaching step 4
watch(currentStep, (step) => {
  if (step === 4 && banks.value.length === 0) {
    loadBanks()
  }
})
</script>

<template>
  <div class="max-w-lg mx-auto">
    <!-- Progress bar -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-3">
        <span class="text-sm font-medium text-gray-700">Stap {{ currentStep }} van {{ totalSteps }}</span>
        <span class="text-sm text-gray-400">{{ Math.round((currentStep / totalSteps) * 100) }}%</span>
      </div>
      <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          class="h-full bg-emerald-600 rounded-full transition-all duration-500 ease-out"
          :style="{ width: `${(currentStep / totalSteps) * 100}%` }"
        />
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
      {{ error }}
    </div>

    <!-- Step 1: Welcome & Company Type -->
    <div v-if="currentStep === 1" class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 mb-1">Welkom bij FiscalFlow!</h2>
        <p class="text-gray-500">Laten we je account instellen. Wat voor type bedrijf heb je?</p>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <button
          v-for="type in companyTypes"
          :key="type.value"
          @click="companyType = type.value"
          class="p-4 rounded-2xl border-2 text-left transition-all hover:shadow-md"
          :class="companyType === type.value ? 'border-emerald-500 bg-emerald-50 shadow-sm' : 'border-gray-100 bg-white hover:border-gray-200'"
        >
          <span class="text-2xl">{{ type.icon }}</span>
          <p class="text-sm font-semibold text-gray-900 mt-2">{{ type.label }}</p>
          <p class="text-xs text-gray-500 mt-0.5">{{ type.desc }}</p>
        </button>
      </div>
    </div>

    <!-- Step 2: Company Details -->
    <div v-if="currentStep === 2" class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 mb-1">Bedrijfsgegevens</h2>
        <p class="text-gray-500">Vul je belangrijkste bedrijfsinformatie in</p>
      </div>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Bedrijfsnaam *</label>
          <input v-model="companyName" type="text" placeholder="Je bedrijfsnaam" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">KvK-nummer</label>
            <input v-model="kvkNumber" type="text" placeholder="12345678" maxlength="8" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">BTW-nummer</label>
            <input v-model="btwNumber" type="text" placeholder="NL123456789B01" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Branche</label>
          <select v-model="industry" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
            <option value="">Selecteer je branche</option>
            <option v-for="ind in industries" :key="ind" :value="ind">{{ ind }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Step 3: Address & Contact -->
    <div v-if="currentStep === 3" class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 mb-1">Adres & Contactgegevens</h2>
        <p class="text-gray-500">Deze gegevens verschijnen op je facturen</p>
      </div>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Adres</label>
          <input v-model="address" type="text" placeholder="Straatnaam 123" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Postcode</label>
            <input v-model="postalCode" type="text" placeholder="1234 AB" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">Plaats</label>
            <input v-model="city" type="text" placeholder="Amsterdam" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Telefoonnummer</label>
          <input v-model="phone" type="tel" placeholder="+31 6 12345678" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">IBAN</label>
          <input v-model="iban" type="text" placeholder="NL00 INGB 0000 0000 00" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>
      </div>
    </div>

    <!-- Step 4: Bank Connection -->
    <div v-if="currentStep === 4" class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 mb-1">Bank koppelen</h2>
        <p class="text-gray-500">Koppel je bankrekening voor automatische transactie-import</p>
      </div>

      <!-- Bank connected state -->
      <div v-if="bankConnected" class="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-3">
        <div class="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
          <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
        </div>
        <div>
          <p class="text-sm font-semibold text-emerald-900">{{ selectedBank?.name || 'Bank' }} wordt gekoppeld</p>
          <p class="text-xs text-emerald-700">Voltooi de autorisatie in het bankvenster</p>
        </div>
      </div>

      <!-- Bank selection -->
      <div v-else>
        <div class="relative mb-4">
          <svg class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input v-model="bankSearch" type="text" placeholder="Zoek je bank..." class="w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
        </div>

        <div v-if="banksLoading" class="flex items-center justify-center py-8">
          <svg class="w-6 h-6 text-emerald-600 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>

        <div v-else class="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
          <button
            v-for="bank in filteredBanks"
            :key="bank.id"
            @click="connectBank(bank)"
            class="flex items-center gap-3 p-3 bg-white border border-gray-100 rounded-xl hover:border-emerald-300 hover:bg-emerald-50 transition-all text-left"
          >
            <img v-if="bank.logo" :src="bank.logo" :alt="bank.name" class="w-8 h-8 rounded-lg object-contain" />
            <div v-else class="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center text-xs font-bold text-gray-400">{{ bank.name?.charAt(0) }}</div>
            <span class="text-xs font-medium text-gray-700 truncate">{{ bank.name }}</span>
          </button>
        </div>

        <p class="text-xs text-gray-400 mt-4 text-center">Beveiligd via PSD2 (GoCardless). Je bankgegevens worden versleuteld opgeslagen.</p>
      </div>

      <!-- Skip option -->
      <button
        @click="currentStep++"
        class="w-full text-center text-sm text-gray-400 hover:text-gray-600 transition-colors"
      >
        Sla over, ik koppel later
      </button>
    </div>

    <!-- Step 5: Preferences & Done -->
    <div v-if="currentStep === 5" class="space-y-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 mb-1">Bijna klaar!</h2>
        <p class="text-gray-500">Stel je boekhoudvoorkeuren in</p>
      </div>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Boekjaar begint op</label>
          <select v-model="fiscalYearStart" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
            <option value="01-01">1 januari (standaard)</option>
            <option value="04-01">1 april</option>
            <option value="07-01">1 juli</option>
            <option value="10-01">1 oktober</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">BTW-aangifte periode</label>
          <select v-model="btwPeriod" class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
            <option value="quarter">Per kwartaal (meest voorkomend)</option>
            <option value="month">Per maand</option>
            <option value="year">Per jaar</option>
          </select>
        </div>
      </div>

      <!-- Summary card -->
      <div class="bg-gray-50 rounded-2xl p-5 space-y-3">
        <p class="text-sm font-semibold text-gray-900">Samenvatting</p>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between"><span class="text-gray-500">Bedrijfsvorm</span><span class="font-medium text-gray-900">{{ companyTypes.find(t => t.value === companyType)?.label || '-' }}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">Bedrijfsnaam</span><span class="font-medium text-gray-900">{{ companyName || '-' }}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">KvK-nummer</span><span class="font-medium text-gray-900">{{ kvkNumber || '-' }}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">Bank gekoppeld</span><span class="font-medium" :class="bankConnected ? 'text-emerald-600' : 'text-gray-400'">{{ bankConnected ? 'Ja' : 'Nee' }}</span></div>
        </div>
      </div>

      <!-- Complete button -->
      <button
        @click="completeOnboarding"
        :disabled="loading"
        class="w-full py-3.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
        {{ loading ? 'Afronden...' : 'Start met FiscalFlow' }}
      </button>
    </div>

    <!-- Navigation -->
    <div v-if="currentStep < 5" class="flex items-center justify-between mt-8">
      <button
        v-if="currentStep > 1"
        @click="prevStep"
        class="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        Vorige
      </button>
      <div v-else></div>
      <button
        @click="nextStep"
        :disabled="loading"
        class="flex items-center gap-1 px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-all disabled:opacity-50"
      >
        {{ loading ? 'Opslaan...' : 'Volgende' }}
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
      </button>
    </div>
  </div>
</template>
