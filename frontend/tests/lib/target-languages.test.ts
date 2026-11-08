import { describe, it, expect } from 'vitest'
import {
  SUPPORTED_TARGET_LANGUAGES,
  TARGET_LANGUAGE_CATALOG,
  getLanguageByCode,
  DEFAULT_TARGET_LANGUAGE,
  TARGET_LANGUAGE_CAPABILITIES,
  getTargetLanguageCapability,
  getTargetLanguageTextClass,
} from '@/lib/target-languages'

describe('SUPPORTED_TARGET_LANGUAGES', () => {
  it('contains exactly 2 languages', () => {
    expect(SUPPORTED_TARGET_LANGUAGES).toHaveLength(2)
  })

  const expectedCodes = ['es-ES', 'ast-ES']

  it.each(expectedCodes)('%s has all required fields', (code) => {
    const lang = SUPPORTED_TARGET_LANGUAGES.find((l) => l.code === code)
    const catalogLang = TARGET_LANGUAGE_CATALOG.find((l) => l.code === code)
    expect(lang).toBeDefined()
    expect(catalogLang).toBeDefined()
    expect(lang!.code).toBeTypeOf('string')
    expect(lang!.name).toBeTypeOf('string')
    expect(lang!.nameEn).toBeTypeOf('string')
    expect(lang!.flagPath).toMatch(/^\/flags\/[a-zA-Z_]+\./)
    expect(lang!.iso639).toMatch(/^[a-z]{2,3}$/)
    expect(lang!.script).toBe(catalogLang!.script)
    expect(lang!.fontClass).toBe(catalogLang!.fontClass)
    expect(lang!.usesWordSpacing).toBe(catalogLang!.usesWordSpacing)
  })

  it('every code is unique', () => {
    const codes = SUPPORTED_TARGET_LANGUAGES.map((l) => l.code)
    expect(new Set(codes).size).toBe(codes.length)
  })

  it('flag paths match expected values', () => {
    const paths = SUPPORTED_TARGET_LANGUAGES.map((l) => l.flagPath)
    expect(paths).toContain('/flags/spain.jpg')
    expect(paths).toContain('/flags/asturias.jpg')
  })

  it('iso639 codes map to correct languages', () => {
    const esLangs = SUPPORTED_TARGET_LANGUAGES.filter((l) => l.iso639 === 'es')
    const astLangs = SUPPORTED_TARGET_LANGUAGES.filter((l) => l.iso639 === 'ast')
    expect(esLangs).toHaveLength(1)
    expect(astLangs).toHaveLength(1)
  })
})

describe('TARGET_LANGUAGE_CATALOG', () => {
  it('contains only es-ES and ast-ES', () => {
    expect(TARGET_LANGUAGE_CATALOG).toHaveLength(2)
    expect(TARGET_LANGUAGE_CATALOG.map((l) => l.code)).toEqual(['es-ES', 'ast-ES'])
  })

  it('contains complete Asturian display metadata', () => {
    expect(getLanguageByCode('ast-ES')).toMatchObject({
      name: 'Asturianu',
      nameEn: 'Asturian',
      flagPath: '/flags/asturias.jpg',
      iso639: 'ast',
      fontClass: 'font-target-latin',
      script: 'latin',
      usesWordSpacing: true,
    })
  })
})

describe('getLanguageByCode', () => {
  it('returns the correct language for a valid code', () => {
    const lang = getLanguageByCode('es-ES')
    expect(lang).toBeDefined()
    expect(lang!.code).toBe('es-ES')
    expect(lang!.name).toBe('Español')
    expect(lang!.nameEn).toBe('Spanish')
    expect(lang!.iso639).toBe('es')
  })

  it('returns Asturian for ast-ES', () => {
    const lang = getLanguageByCode('ast-ES')
    expect(lang).toBeDefined()
    expect(lang!.name).toBe('Asturianu')
  })

  it('returns undefined for an unknown code', () => {
    expect(getLanguageByCode('')).toBeUndefined()
  })

  it('matches codes case-insensitively', () => {
    expect(getLanguageByCode('ES-ES')?.code).toBe('es-ES')
    expect(getLanguageByCode('es-es')?.code).toBe('es-ES')
    expect(getLanguageByCode('AST-ES')?.code).toBe('ast-ES')
    expect(getLanguageByCode('ast-es')?.code).toBe('ast-ES')
  })
})

describe('DEFAULT_TARGET_LANGUAGE', () => {
  it('is es-ES', () => {
    expect(DEFAULT_TARGET_LANGUAGE).toBe('es-ES')
  })

  it('is present in SUPPORTED_TARGET_LANGUAGES', () => {
    const lang = getLanguageByCode(DEFAULT_TARGET_LANGUAGE)
    expect(lang).toBeDefined()
  })
})

describe('TargetLanguage interface compliance', () => {
  it('all languages have non-empty nameEn', () => {
    SUPPORTED_TARGET_LANGUAGES.forEach((lang) => {
      expect(lang.nameEn.length).toBeGreaterThan(0)
    })
  })

  it('all languages have non-empty name', () => {
    SUPPORTED_TARGET_LANGUAGES.forEach((lang) => {
      expect(lang.name.length).toBeGreaterThan(0)
    })
  })
})

describe('target language capabilities', () => {
  it('keeps Latin typography and word spacing for es-ES and ast-ES', () => {
    expect(getTargetLanguageCapability('es-ES')).toEqual({
      script: 'latin',
      fontClass: 'font-target-latin',
      usesWordSpacing: true,
    })
    expect(getTargetLanguageCapability('ast-ES')).toEqual({
      script: 'latin',
      fontClass: 'font-target-latin',
      usesWordSpacing: true,
    })
    expect(getTargetLanguageTextClass('es-ES')).toContain('font-target-latin')
    expect(getTargetLanguageTextClass('es-ES')).toContain('leading-relaxed')
    expect(getTargetLanguageTextClass('es-ES')).toContain('text-base')
    expect(getTargetLanguageTextClass('ast-ES')).toContain('font-target-latin')
  })

  it('returns safe Latin defaults for unknown codes', () => {
    expect(getTargetLanguageCapability('xx-XX')).toMatchObject({
      script: 'latin',
      fontClass: 'font-target-latin',
      usesWordSpacing: true,
    })
  })
})
