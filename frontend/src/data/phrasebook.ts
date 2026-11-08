export type { CEFRLevel, Register } from '@/data/types'

import { apiFetch } from '@/lib/api'

export interface Phrase {
  text: string
  context: string
  register: string
  unit_ref?: string
  romanization?: string
}

export interface PhrasebookCategory {
  id: string
  level: string
  situation: string
  icon: string
  phrases: Phrase[]
}

export interface PhrasebookNativeHelpPhraseNote {
  phrase: string
  note: string
}

export interface PhrasebookNativeHelpTrap {
  mistake: string
  fix: string
}

export interface PhrasebookNativeHelpGlossaryItem {
  term: string
  meaning: string
  note?: string
}

export interface PhrasebookNativeHelp {
  summary: string
  usage_tips: string[]
  register_notes: string[]
  phrase_notes: PhrasebookNativeHelpPhraseNote[]
  common_traps: PhrasebookNativeHelpTrap[]
  mini_glossary: PhrasebookNativeHelpGlossaryItem[]
}

export async function getPhrasebookCategories(
  targetLanguage: string = 'es-ES'
): Promise<PhrasebookCategory[]> {
  const res = await apiFetch(
    `/api/phrasebook?language=${encodeURIComponent(targetLanguage)}`
  )
  if (!res.ok) return []
  const data = await res.json()
  return data.categories ?? []
}

export async function getPhrasebookByLevel(
  level: string,
  targetLanguage: string = 'es-ES'
): Promise<PhrasebookCategory[]> {
  const res = await apiFetch(
    `/api/phrasebook/level/${encodeURIComponent(level)}?language=${encodeURIComponent(targetLanguage)}`
  )
  if (!res.ok) return []
  const data = await res.json()
  return data.categories ?? []
}

export async function getPhrasebookNativeHelp(
  categoryId: string,
  targetLanguage: string = 'es-ES'
): Promise<PhrasebookNativeHelp | null> {
  const res = await apiFetch(
    `/api/phrasebook/${encodeURIComponent(categoryId)}/native-help?language=${encodeURIComponent(targetLanguage)}`,
    { method: 'POST' }
  )
  if (!res.ok) return null
  const data = await res.json()
  return data.native_help ?? null
}
