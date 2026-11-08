import React from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { NextIntlClientProvider } from 'next-intl'
import { TARGET_LANGUAGE_CATALOG } from '@/lib/target-languages'
import { useAuthStore } from '@/store/auth'
import { useConfigStore } from '@/store/config'
import { useLanguageStore } from '@/store/language'
import en from '../../../messages/en.json'
import es from '../../../messages/es.json'

const { searchParams, apiFetch } = vi.hoisted(() => ({
  searchParams: new URLSearchParams(),
  apiFetch: vi.fn(),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => searchParams,
}))

vi.mock('@/lib/api', () => ({ apiFetch }))

import OnboardingPage from '@/app/(auth)/onboarding/page'

const catalogs = {
  en,
  es,
}
type Locale = keyof typeof catalogs

const spanishSubtitles: Record<Locale, string> = {
  en: 'Language: Spanish. What do you want to use it for? Select all that apply.',
  es: 'Idioma: español. ¿Para qué quieres utilizarlo? Selecciona todos los objetivos que correspondan.',
}

const asturianSubtitles: Record<Locale, string> = {
  en: 'Language: Asturian. What do you want to use it for? Select all that apply.',
  es: 'Idioma: asturianu. ¿Pera qué quies usalu? Escoye tolos oxetivos que correspondan.',
}

function languageResponse(
  codes = TARGET_LANGUAGE_CATALOG.map((language) => language.code)
) {
  return new Response(
    JSON.stringify({ languages: [], all_supported_languages: codes })
  )
}

function renderOnboarding(locale: Locale = 'en') {
  return render(
    <NextIntlClientProvider
      locale={locale}
      messages={catalogs[locale]}
      timeZone="UTC"
      onError={vi.fn()}
    >
      <OnboardingPage />
    </NextIntlClientProvider>
  )
}

beforeEach(() => {
  for (const key of Array.from(searchParams.keys())) searchParams.delete(key)
  apiFetch.mockReset()
  apiFetch.mockImplementation(async () => languageResponse())
  useAuthStore.setState({ ...useAuthStore.getInitialState() }, true)
  useConfigStore.setState(
    { ...useConfigStore.getInitialState(), loaded: true },
    true
  )
  useLanguageStore.setState({ ...useLanguageStore.getInitialState() }, true)
})

afterEach(() => {
  cleanup()
})

describe('onboarding goals subtitle', () => {
  it.each(Object.keys(catalogs) as Locale[])(
    'names the selected language with natural wording in the %s UI',
    async (locale) => {
      const messages = catalogs[locale]
      renderOnboarding(locale)

      fireEvent.click(
        await screen.findByRole('button', {
          name: /es-ES/,
        })
      )
      fireEvent.click(
        screen.getByRole('button', { name: messages.common.next })
      )

      expect(screen.getByText(spanishSubtitles[locale])).toBeInTheDocument()
    }
  )

  it('names Asturian with natural wording in the en UI', async () => {
    renderOnboarding('en')

    fireEvent.click(
      await screen.findByRole('button', {
        name: /ast-ES/,
      })
    )
    fireEvent.click(
      screen.getByRole('button', { name: en.common.next })
    )

    expect(screen.getByText(asturianSubtitles['en'])).toBeInTheDocument()
  })

  const languageNameCases = [
    [null, 'Spanish'] as const,
    ['es-ES', 'Spanish'] as const,
    ['ast-ES', 'Asturian'] as const,
  ]

  it.each(languageNameCases)(
    'uses the language-level name for query language=%s',
    async (code, name) => {
      if (code) searchParams.set('language', code)
      renderOnboarding()
      await screen.findByRole('button', { name: new RegExp(code || 'es-ES') })
      fireEvent.click(screen.getByRole('button', { name: 'Next' }))

      expect(
        screen.getByText(
          `Language: ${name}. What do you want to use it for? Select all that apply.`
        )
      ).toBeInTheDocument()
    }
  )

  it.each(['', 'unknown-language'] as const)(
    'safely displays the default for language=%s while languages load',
    async (code) => {
      searchParams.set('language', code)
      let resolveLanguages!: (response: Response) => void
      apiFetch.mockReturnValueOnce(
        new Promise<Response>((resolve) => {
          resolveLanguages = resolve
        })
      )
      renderOnboarding()
      fireEvent.click(screen.getByRole('button', { name: 'Next' }))

      expect(screen.getByText(spanishSubtitles['en'])).toBeInTheDocument()

      await act(async () => resolveLanguages(languageResponse(['es-ES'])))

      expect(
        screen.getByText(
          'Language: Spanish. What do you want to use it for? Select all that apply.'
        )
      ).toBeInTheDocument()
    }
  )

  it.each(['HTTP', 'network'] as const)(
    'safely displays the default for an invalid query after a %s failure',
    async (failure) => {
      searchParams.set('language', 'unknown-language')
      if (failure === 'HTTP') {
        apiFetch.mockResolvedValueOnce(new Response('', { status: 503 }))
      } else {
        apiFetch.mockRejectedValueOnce(new Error('offline'))
      }
      renderOnboarding()
      await screen.findByText(en.onboarding.saveFailed)
      fireEvent.click(screen.getByRole('button', { name: 'Next' }))

      expect(screen.getByText(spanishSubtitles['en'])).toBeInTheDocument()
    }
  )
})
