import { defineStore } from 'pinia'

const STORAGE_KEY = 'app-theme'

export const themes = {
  light: {
    label: '浅色模式',
    primary: '#2f6bff',
    bg: '#f5f7fa',
    card: '#ffffff',
    text: '#1f2d3d',
    sub: '#7a8699',
    border: '#e8edf5',
    soft: 'rgba(47, 107, 255, 0.10)'
  },
  dark: {
    label: '深色模式',
    primary: '#6d9bff',
    bg: '#0f1420',
    card: '#161d2b',
    text: '#e8eef8',
    sub: '#93a0b5',
    border: '#243044',
    soft: 'rgba(109, 155, 255, 0.16)'
  },
  blue: {
    label: '海蓝主题',
    primary: '#1677ff',
    bg: '#eef6ff',
    card: '#ffffff',
    text: '#183153',
    sub: '#5d789c',
    border: '#d6e6fb',
    soft: 'rgba(22, 119, 255, 0.12)'
  },
  green: {
    label: '青绿主题',
    primary: '#10a37f',
    bg: '#f0faf6',
    card: '#ffffff',
    text: '#173a30',
    sub: '#5c7f73',
    border: '#d5eee4',
    soft: 'rgba(16, 163, 127, 0.12)'
  }
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    currentTheme: localStorage.getItem(STORAGE_KEY) || 'light'
  }),

  getters: {
    theme: (state) => themes[state.currentTheme] || themes.light,
    themeList: () =>
      Object.entries(themes).map(([key, value]) => ({ key, ...value }))
  },

  actions: {
    setTheme(name) {
      if (!themes[name]) return
      this.currentTheme = name
      localStorage.setItem(STORAGE_KEY, name)
      this.applyTheme()
    },

    applyTheme() {
      const theme = themes[this.currentTheme] || themes.light
      const root = document.documentElement
      root.style.setProperty('--primary', theme.primary)
      root.style.setProperty('--primary-soft', theme.soft)
      root.style.setProperty('--bg', theme.bg)
      root.style.setProperty('--card', theme.card)
      root.style.setProperty('--text', theme.text)
      root.style.setProperty('--sub', theme.sub)
      root.style.setProperty('--border', theme.border)
      root.style.setProperty('--van-primary-color', theme.primary)
      root.dataset.theme = this.currentTheme === 'dark' ? 'dark' : 'light'
    },

    initTheme() {
      this.applyTheme()
    }
  }
})
