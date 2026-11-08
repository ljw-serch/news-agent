import { defineStore } from 'pinia'

const STORAGE_KEY = 'language'

export const useLanguageStore = defineStore('language', {
  state: () => ({
    currentLanguage: localStorage.getItem(STORAGE_KEY) || 'zh-CN'
  }),

  actions: {
    setLanguage(language) {
      this.currentLanguage = language
      localStorage.setItem(STORAGE_KEY, language)
    }
  }
})
