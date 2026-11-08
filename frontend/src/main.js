import { createApp } from 'vue'
import Vant from 'vant'
import 'vant/lib/index.css'

import App from './App.vue'
import router from './router'
import pinia from './store'
import {setupI18n} from './i18n'
import {useThemeStore} from './store/theme'
import '@/assets/css/global.css'

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(setupI18n())
app.use(Vant)
useThemeStore(pinia).initTheme
app.mount('#app')
