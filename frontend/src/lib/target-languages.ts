export interface TargetLanguage {
  code: string
  name: string
  nameEn: string
  flagPath: string
  iso639: string
  script: TargetLanguageScript
  fontClass: string
  usesWordSpacing: boolean
  romanization?: TargetLanguageRomanization
}

export type TargetLanguageScript =
  | 'latin'
  | 'cyrillic'
  | 'hiragana-katakana-kanji'
  | 'hangul'
  | 'simplified-hanzi'

export type TargetLanguageRomanization =
  'romaji' | 'revised-romanization' | 'pinyin'

interface TargetLanguageCapability {
  script: TargetLanguageScript
  fontClass: string
  usesWordSpacing: boolean
  romanization?: TargetLanguageRomanization
}

const LATIN_LANGUAGE_CAPABILITY: TargetLanguageCapability = {
  script: 'latin',
  fontClass: 'font-target-latin',
  usesWordSpacing: true,
}

export const TARGET_LANGUAGE_CAPABILITIES: Record<
  string,
  TargetLanguageCapability
> = {
  'es-ES': LATIN_LANGUAGE_CAPABILITY,
  'ast-ES': LATIN_LANGUAGE_CAPABILITY,
}

function withCapabilities(
  language: Omit<TargetLanguage, keyof TargetLanguageCapability>
): TargetLanguage {
  return {
    ...language,
    ...(TARGET_LANGUAGE_CAPABILITIES[language.code] ??
      LATIN_LANGUAGE_CAPABILITY),
  }
}

export const TARGET_LANGUAGE_CATALOG: TargetLanguage[] = [
  withCapabilities({
    code: 'es-ES',
    name: 'Español',
    nameEn: 'Spanish',
    flagPath: '/flags/spain.jpg',
    iso639: 'es',
  }),
  withCapabilities({
    code: 'ast-ES',
    name: 'Asturianu',
    nameEn: 'Asturian',
    flagPath: '/flags/asturias.jpg',
    iso639: 'ast',
  }),
]

export const SUPPORTED_TARGET_LANGUAGES: TargetLanguage[] =
  TARGET_LANGUAGE_CATALOG

export function getLanguageByCode(code: string): TargetLanguage | undefined {
  const upper = code.toUpperCase()
  return TARGET_LANGUAGE_CATALOG.find((l) => l.code.toUpperCase() === upper)
}

export function getTargetLanguageCapability(
  code: string
): TargetLanguageCapability {
  const canonicalCode = getLanguageByCode(code)?.code ?? code
  return (
    TARGET_LANGUAGE_CAPABILITIES[canonicalCode] ?? LATIN_LANGUAGE_CAPABILITY
  )
}

export function getTargetLanguageTextClass(code: string): string {
  const capability = getTargetLanguageCapability(code)
  if (capability.script === 'latin' || capability.script === 'cyrillic') {
    return `${capability.fontClass} text-base leading-relaxed tracking-normal normal-case`
  }
  return `${capability.fontClass} text-base leading-loose tracking-normal normal-case`
}

export const DEFAULT_TARGET_LANGUAGE = 'es-ES'

const LOCALES_CAPITALIZE_LANGUAGE = new Set(['en', 'de', 'nl', 'tr'])

export function formatLanguageName(name: string, locale: string): string {
  const lang = locale.split('-')[0]
  return LOCALES_CAPITALIZE_LANGUAGE.has(lang) ? name : name.toLowerCase()
}
