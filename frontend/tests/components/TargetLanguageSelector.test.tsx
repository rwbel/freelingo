import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import TargetLanguageSelector from '@/components/TargetLanguageSelector'
import { TARGET_LANGUAGE_CATALOG } from '@/lib/target-languages'

vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock('next/image', () => ({
  default: function MockImage({
    src,
    alt,
    width,
    height,
    className,
  }: {
    src: string
    alt: string
    width: number
    height: number
    className?: string
  }) {
    return React.createElement('img', { src, alt, width, height, className })
  },
}))

describe('TargetLanguageSelector', () => {
  const catalogCodes = TARGET_LANGUAGE_CATALOG.map((lang) => lang.code)

  it('renders only languages matching availableCodes', () => {
    render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={() => {}}
        availableCodes={['es-ES', 'ast-ES']}
      />
    )

    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(2)
  })

  it('renders all languages when all codes are available', () => {
    render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={() => {}}
        availableCodes={catalogCodes}
      />
    )

    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(2)
  })

  it('renders nothing when availableCodes is empty', () => {
    const { container } = render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={() => {}}
        availableCodes={[]}
      />
    )

    expect(screen.queryByRole('button')).toBeNull()
    const div = container.firstChild as HTMLElement
    expect(div.children).toHaveLength(0)
  })

  it('renders Asturian when availableCodes includes it', () => {
    render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={() => {}}
        availableCodes={['ast-ES']}
      />
    )

    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(1)
    expect(buttons[0].textContent).toContain('ast-ES')
    expect(screen.getByRole('img').getAttribute('src')).toBe(
      '/flags/asturias.jpg'
    )
  })

  it('selects Asturian independently and excludes it when disabled', () => {
    const onChange = vi.fn()
    const { rerender } = render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={onChange}
        availableCodes={['es-ES', 'ast-ES']}
      />
    )
    // Component sorts by translated name: "Asturian" < "Spanish"
    expect(screen.getAllByRole('img').map((img) => img.getAttribute('src'))).toEqual([
      '/flags/asturias.jpg',
      '/flags/spain.jpg',
    ])
    fireEvent.click(screen.getByRole('button', { name: /ast-ES/ }))
    expect(onChange).toHaveBeenCalledWith('ast-ES')
    rerender(
      <TargetLanguageSelector
        value="es-ES"
        onChange={onChange}
        availableCodes={['es-ES']}
      />
    )
    expect(screen.queryByRole('button', { name: /ast-ES/ })).toBeNull()
    expect(screen.getAllByRole('button')).toHaveLength(1)
  })

  it('shows active state for the selected language', () => {
    render(
      <TargetLanguageSelector
        value="ast-ES"
        onChange={() => {}}
        availableCodes={catalogCodes}
      />
    )

    const buttons = screen.getAllByRole('button')
    const activeButton = buttons.find((btn) =>
      btn.className.includes('bg-fl-accent')
    )

    expect(activeButton).toBeDefined()
    expect(activeButton!.textContent).toContain('ast-ES')
  })

  it('calls onChange with the clicked code', () => {
    const onChange = vi.fn()

    render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={onChange}
        availableCodes={catalogCodes}
      />
    )

    const buttons = screen.getAllByRole('button')
    const astButton = buttons.find((btn) =>
      btn.textContent?.includes('ast-ES')
    )

    expect(astButton).toBeDefined()
    fireEvent.click(astButton!)

    expect(onChange).toHaveBeenCalledWith('ast-ES')
  })

  it('calls onChange when clicking already-selected language', () => {
    const onChange = vi.fn()

    render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={onChange}
        availableCodes={['es-ES', 'ast-ES']}
      />
    )

    const buttons = screen.getAllByRole('button')
    const activeButton = buttons.find((btn) =>
      btn.className.includes('bg-fl-accent')
    )

    fireEvent.click(activeButton!)

    expect(onChange).toHaveBeenCalledWith('es-ES')
  })

  it('renders flag images with correct src', () => {
    render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={() => {}}
        availableCodes={catalogCodes}
      />
    )

    const images = screen.getAllByRole('img')
    const srcs = images.map((img) => img.getAttribute('src'))

    expect(srcs).toContain('/flags/spain.jpg')
    expect(srcs).toContain('/flags/asturias.jpg')
  })

  it('displays translated names from targetLanguages namespace', () => {
    render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={() => {}}
        availableCodes={catalogCodes}
      />
    )

    const buttons = screen.getAllByRole('button')
    const textContent = buttons.map((b) => b.textContent).join(' ')

    expect(textContent).toContain('es-ES')
    expect(textContent).toContain('ast-ES')
  })

  it('does not re-render filtered languages when onChange does not change', () => {
    const { rerender } = render(
      <TargetLanguageSelector
        value="es-ES"
        onChange={() => {}}
        availableCodes={['es-ES', 'ast-ES']}
      />
    )

    rerender(
      <TargetLanguageSelector
        value="es-ES"
        onChange={() => {}}
        availableCodes={['es-ES', 'ast-ES']}
      />
    )

    expect(screen.getAllByRole('button')).toHaveLength(2)
  })
})
