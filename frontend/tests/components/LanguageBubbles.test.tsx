import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { renderToString } from 'react-dom/server'
import { LanguageBubbles } from '@/components/LanguageBubbles'
import { SUPPORTED_TARGET_LANGUAGES } from '@/lib/target-languages'

vi.mock('next-intl', () => ({
  useTranslations: (namespace: string) => (key: string) =>
    namespace === 'targetLanguages'
      ? `Localized ${key}`
      : key === 'languageGreetings.ast-ES'
        ? '¡Hola!'
        : key,
}))

vi.mock('@/components/lingu/LinguAvatar', () => ({
  default: ({ onReady }: { onReady?: () => void }) => (
    <button data-testid="lingu-ready" onClick={onReady} />
  ),
}))

vi.mock('next/image', () => ({
  default: function MockImage(
    props: React.ImgHTMLAttributes<HTMLImageElement> & {
      unoptimized?: boolean
      priority?: boolean
    }
  ) {
    const { unoptimized, priority, ...imgProps } = props
    void unoptimized
    void priority
    return React.createElement('img', imgProps)
  },
}))

describe('LanguageBubbles', () => {
  it('reveals Lingu and the language bubbles together when the avatar is ready', () => {
    const { container } = render(<LanguageBubbles />)
    const group = container.firstElementChild

    expect(group).toHaveAttribute('aria-hidden', 'true')
    expect(group).toHaveClass('opacity-0')
    expect(screen.queryByRole('img', { name: 'FreeLingo' })).toBeNull()
    expect(screen.queryAllByRole('img', { name: /^Localized / })).toHaveLength(0)

    fireEvent.click(screen.getByTestId('lingu-ready'))

    expect(group).toHaveAttribute('aria-hidden', 'false')
    expect(group).toHaveClass('opacity-100')
    expect(screen.getByRole('img', { name: 'FreeLingo' })).toBeInTheDocument()
    expect(screen.getAllByRole('img', { name: /^Localized / })).toHaveLength(
      SUPPORTED_TARGET_LANGUAGES.length
    )
  })

  it('renders one bubble per supported target language', () => {
    render(<LanguageBubbles />)
    fireEvent.click(screen.getByTestId('lingu-ready'))

    expect(screen.getAllByRole('img', { name: /^Localized / })).toHaveLength(
      SUPPORTED_TARGET_LANGUAGES.length
    )
    expect(screen.getByAltText('Localized es-ES')).toBeInTheDocument()
    expect(screen.getByAltText('Localized ast-ES')).toHaveAttribute(
      'src',
      '/flags/asturias.jpg'
    )
    expect(screen.getByText('¡Hola!')).toHaveAttribute('lang', 'ast-ES')
    expect(screen.getByText('¡Hola!')).toHaveClass('font-target-latin')
    expect(screen.getByRole('img', { name: 'FreeLingo' })).toBeInTheDocument()
  })

  it('uses a wider desktop orbit and wrapping mobile layout for all languages', () => {
    const { container } = render(<LanguageBubbles />)
    const wrappers = Array.from(
      container.querySelectorAll<HTMLDivElement>('div[style]')
    ).filter((el) => el.style.getPropertyValue('--bubble-x'))

    expect(container.firstElementChild).toHaveClass('flex-wrap', 'gap-y-4')
    expect(wrappers).toHaveLength(SUPPORTED_TARGET_LANGUAGES.length)
    const xPositions = wrappers.map((el) =>
      Number.parseFloat(el.style.getPropertyValue('--bubble-x'))
    )
    const yPositions = wrappers.map((el) =>
      Number.parseFloat(el.style.getPropertyValue('--bubble-y'))
    )
    // With 2 languages on ellipse: one at top (y=-140), one at bottom (y=140)
    // x spread is 0, y spread is 280
    expect(Math.max(...yPositions) - Math.min(...yPositions)).toBeGreaterThan(200)
    for (const wrapper of wrappers) {
      expect(wrapper).toHaveClass('relative', 'sm:absolute')
      const x = Number.parseFloat(wrapper.style.getPropertyValue('--bubble-x'))
      const y = Number.parseFloat(wrapper.style.getPropertyValue('--bubble-y'))
      expect(Math.hypot(x / 215, y / 140)).toBeCloseTo(1, 2)
    }
  })

  it('hydrates server markup despite tiny differences in trigonometric precision', () => {
    const cos = Math.cos
    const sin = Math.sin
    const serverCos = vi.spyOn(Math, 'cos').mockImplementation((angle) => cos(angle) + 1e-15)
    const serverSin = vi.spyOn(Math, 'sin').mockImplementation((angle) => sin(angle) - 1e-15)
    const container = document.createElement('div')
    try {
      container.innerHTML = renderToString(<LanguageBubbles />)
    } finally {
      serverCos.mockRestore()
      serverSin.mockRestore()
    }

    const serverMarkup = container.innerHTML
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    try {
      render(<LanguageBubbles />, { container, hydrate: true })
      expect(consoleError).not.toHaveBeenCalled()
      expect(container.innerHTML).toBe(serverMarkup)
    } finally {
      consoleError.mockRestore()
    }
  })
})
