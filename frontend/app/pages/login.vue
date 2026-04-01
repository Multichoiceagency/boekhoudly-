<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const api = useApi()
const router = useRouter()

// Steps: 'email' | 'code' | 'name'
const step = ref<'email' | 'code' | 'name'>('email')
const email = ref('')
const code = ref(['', '', '', '', '', ''])
const fullName = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const isNewUser = ref(false)
const countdown = ref(0)
const codeInputRefs = ref<HTMLInputElement[]>([])

let countdownTimer: ReturnType<typeof setInterval> | null = null

// Send verification code
async function sendCode() {
  if (!email.value || !email.value.includes('@')) {
    error.value = 'Vul een geldig e-mailadres in'
    return
  }
  loading.value = true
  error.value = ''
  success.value = ''

  try {
    const data = await api.post<{ message: string; is_new_user: boolean }>('/auth/send-code', {
      email: email.value,
    })
    isNewUser.value = data.is_new_user
    step.value = 'code'
    success.value = `Verificatiecode verzonden naar ${email.value}`
    startCountdown()

    // Focus first code input after render
    nextTick(() => codeInputRefs.value[0]?.focus())
  } catch (e: any) {
    error.value = e.message || 'Kon geen code versturen'
  } finally {
    loading.value = false
  }
}

// Handle code input
function onCodeInput(index: number, event: Event) {
  const input = event.target as HTMLInputElement
  const val = input.value.replace(/\D/g, '')
  code.value[index] = val.slice(-1)

  if (val && index < 5) {
    nextTick(() => codeInputRefs.value[index + 1]?.focus())
  }

  // Auto-submit when all digits filled
  if (code.value.every(d => d !== '')) {
    verifyCode()
  }
}

function onCodeKeydown(index: number, event: KeyboardEvent) {
  if (event.key === 'Backspace' && !code.value[index] && index > 0) {
    nextTick(() => codeInputRefs.value[index - 1]?.focus())
  }
}

function onCodePaste(event: ClipboardEvent) {
  event.preventDefault()
  const text = event.clipboardData?.getData('text')?.replace(/\D/g, '') || ''
  if (text.length >= 6) {
    for (let i = 0; i < 6; i++) {
      code.value[i] = text[i] || ''
    }
    nextTick(() => verifyCode())
  }
}

// Verify code
async function verifyCode() {
  const fullCode = code.value.join('')
  if (fullCode.length !== 6) {
    error.value = 'Voer de volledige 6-cijferige code in'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // If new user, ask for name first
    if (isNewUser.value && !fullName.value && step.value === 'code') {
      step.value = 'name'
      loading.value = false
      return
    }

    const data = await api.post<{ access_token: string; is_new_user: boolean }>('/auth/verify-code', {
      email: email.value,
      code: fullCode,
      full_name: fullName.value || undefined,
    })
    localStorage.setItem('auth_token', data.access_token)

    if (data.is_new_user) {
      router.push('/onboarding')
    } else {
      router.push('/dashboard')
    }
  } catch (e: any) {
    error.value = e.message || 'Verificatie mislukt'
    // Clear code on error
    code.value = ['', '', '', '', '', '']
    nextTick(() => codeInputRefs.value[0]?.focus())
  } finally {
    loading.value = false
  }
}

// Complete registration (name step)
async function completeRegistration() {
  if (!fullName.value.trim()) {
    error.value = 'Vul je naam in'
    return
  }
  await verifyCode()
}

// Resend code
async function resendCode() {
  if (countdown.value > 0) return
  code.value = ['', '', '', '', '', '']
  error.value = ''
  await sendCode()
}

// Go back to email step
function goBack() {
  if (step.value === 'name') {
    step.value = 'code'
  } else {
    step.value = 'email'
    code.value = ['', '', '', '', '', '']
    error.value = ''
    success.value = ''
  }
}

function startCountdown() {
  countdown.value = 60
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer!)
      countdownTimer = null
    }
  }, 1000)
}

// Google login
const googleLoading = ref(false)
async function handleGoogleLogin() {
  googleLoading.value = true
  error.value = ''
  try {
    const data = await api.get<{ url: string }>('/auth/google/url')
    window.location.href = data.url
  } catch {
    error.value = 'Google login is momenteel niet beschikbaar'
    googleLoading.value = false
  }
}

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<template>
  <div>
    <!-- Mobile logo -->
    <div class="lg:hidden flex items-center gap-2.5 mb-8">
      <div class="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
      </div>
      <span class="text-xl font-bold text-gray-900">FiscalFlow</span>
    </div>

    <!-- ==================== STEP 1: EMAIL ==================== -->
    <template v-if="step === 'email'">
      <h2 class="text-2xl font-bold text-gray-900 mb-1">Inloggen of registreren</h2>
      <p class="text-gray-500 mb-8">Voer je e-mailadres in om een verificatiecode te ontvangen</p>

      <!-- Google Login -->
      <button
        @click="handleGoogleLogin"
        :disabled="googleLoading"
        class="w-full flex items-center justify-center gap-3 px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        {{ googleLoading ? 'Even geduld...' : 'Doorgaan met Google' }}
      </button>

      <!-- Divider -->
      <div class="flex items-center gap-4 my-6">
        <div class="flex-1 h-px bg-gray-200"></div>
        <span class="text-xs text-gray-400 font-medium">OF</span>
        <div class="flex-1 h-px bg-gray-200"></div>
      </div>

      <!-- Error -->
      <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
        {{ error }}
      </div>

      <!-- Email form -->
      <form @submit.prevent="sendCode" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">E-mailadres</label>
          <input
            v-model="email"
            type="email"
            placeholder="naam@bedrijf.nl"
            class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
            autocomplete="email"
            autofocus
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          {{ loading ? 'Code versturen...' : 'Verificatiecode versturen' }}
        </button>
      </form>

      <!-- Info text -->
      <p class="mt-6 text-center text-xs text-gray-400 leading-relaxed">
        We sturen een 6-cijferige code naar je e-mailadres.<br>
        Geen wachtwoord nodig - veilig en snel inloggen.
      </p>
    </template>

    <!-- ==================== STEP 2: CODE ==================== -->
    <template v-if="step === 'code'">
      <button @click="goBack" class="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        Terug
      </button>

      <h2 class="text-2xl font-bold text-gray-900 mb-1">Verificatiecode invoeren</h2>
      <p class="text-gray-500 mb-2">We hebben een code gestuurd naar</p>
      <p class="text-emerald-600 font-semibold mb-8">{{ email }}</p>

      <!-- Success -->
      <div v-if="success" class="mb-4 p-3 bg-emerald-50 border border-emerald-100 rounded-xl text-sm text-emerald-600 flex items-center gap-2">
        <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
        {{ success }}
      </div>

      <!-- Error -->
      <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
        {{ error }}
      </div>

      <!-- Code inputs -->
      <div class="flex gap-3 justify-center mb-6">
        <input
          v-for="(_, i) in 6"
          :key="i"
          :ref="el => { if (el) codeInputRefs[i] = el as HTMLInputElement }"
          type="text"
          inputmode="numeric"
          maxlength="1"
          :value="code[i]"
          @input="onCodeInput(i, $event)"
          @keydown="onCodeKeydown(i, $event)"
          @paste="onCodePaste"
          class="w-12 h-14 text-center text-xl font-bold bg-white border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all"
          :class="code[i] ? 'border-emerald-300 text-emerald-700' : 'border-gray-200 text-gray-900'"
        />
      </div>

      <!-- Verify button -->
      <button
        @click="verifyCode"
        :disabled="loading || code.some(d => !d)"
        class="w-full py-3 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
        {{ loading ? 'Verifying...' : 'Verifieer en ga verder' }}
      </button>

      <!-- Resend -->
      <div class="mt-6 text-center">
        <p class="text-sm text-gray-500 mb-1">Geen code ontvangen?</p>
        <button
          @click="resendCode"
          :disabled="countdown > 0 || loading"
          class="text-sm font-semibold transition-colors"
          :class="countdown > 0 ? 'text-gray-400 cursor-not-allowed' : 'text-emerald-600 hover:text-emerald-700'"
        >
          {{ countdown > 0 ? `Opnieuw versturen (${countdown}s)` : 'Opnieuw versturen' }}
        </button>
      </div>
    </template>

    <!-- ==================== STEP 3: NAME (new users) ==================== -->
    <template v-if="step === 'name'">
      <button @click="goBack" class="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        Terug
      </button>

      <h2 class="text-2xl font-bold text-gray-900 mb-1">Welkom bij FiscalFlow!</h2>
      <p class="text-gray-500 mb-8">Vul je naam in om je account aan te maken</p>

      <!-- Error -->
      <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
        {{ error }}
      </div>

      <form @submit.prevent="completeRegistration" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">Volledige naam</label>
          <input
            v-model="fullName"
            type="text"
            placeholder="Jan de Vries"
            class="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
            autocomplete="name"
            autofocus
          />
        </div>

        <!-- Account info -->
        <div class="p-3 bg-gray-50 border border-gray-100 rounded-xl">
          <div class="flex items-center gap-2 text-sm text-gray-600">
            <svg class="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
            {{ email }}
          </div>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          {{ loading ? 'Account aanmaken...' : 'Account aanmaken' }}
        </button>
      </form>

      <p class="mt-6 text-center text-xs text-gray-400 leading-relaxed">
        Door je aan te melden ga je akkoord met onze<br>
        <a href="#" class="text-emerald-600 hover:underline">Algemene Voorwaarden</a> en <a href="#" class="text-emerald-600 hover:underline">Privacybeleid</a>
      </p>
    </template>
  </div>
</template>
