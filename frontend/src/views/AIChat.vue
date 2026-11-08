<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">AI 智能助手</div>
        <div class="page-sub">
          已接入新闻数据库：可检索新闻、生成摘要、汇总热榜、统计新发布数量与趋势
        </div>
      </div>
      <div class="page-actions">
        <span class="tag" :class="aiStatus.enabled ? 'success' : 'muted'">
          {{ aiStatus.enabled ? `大模型 · ${aiStatus.model}` : '本地新闻引擎' }}
        </span>
        <van-button size="small" icon="clock-o" @click="openHistory">历史对话</van-button>
      </div>
    </div>

    <div class="chat-page">
      <div class="chat-card">
        <div class="chat-head">
          <div class="chat-head-title">
            <span class="dot"></span>
            <span>{{ aiStatus.enabled ? '在线' : '本地模式' }}</span>
            <span class="tag muted" style="margin-left: 2px">Tool Calling</span>
          </div>
          <div class="chat-head-actions">
            <van-button size="mini" icon="delete-o" :disabled="loading" @click="clearHistory">
              清空记录
            </van-button>
          </div>
        </div>

        <div ref="messagesRef" class="chat-messages">
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="msg-row"
            :class="{ user: message.role === 'user' }"
          >
            <div class="msg-avatar">
              <van-icon :name="message.role === 'user' ? 'user-o' : 'bulb-o'" />
            </div>
            <div class="bubble">
              <div v-if="message.role === 'assistant' && message.steps?.length" class="msg-steps">
                <div v-for="(step, stepIndex) in message.steps" :key="stepIndex">· {{ step }}</div>
              </div>
              <div v-if="message.role === 'assistant' && message.status" class="msg-status">
                {{ message.status }}
              </div>
              <div v-if="message.role === 'assistant' && !message.content && loading" class="typing">
                <span></span><span></span><span></span>
              </div>
              <div
                v-if="message.role === 'assistant'"
                class="markdown"
                v-html="renderMarkdown(message.content)"
              ></div>
              <div v-else>{{ message.content }}</div>
            </div>
          </div>
        </div>

        <div class="chat-input">
          <textarea
            v-model="input"
            rows="1"
            :placeholder="t('aiChat.placeholder')"
            @keydown.enter.exact.prevent="send"
            @keydown.enter.shift.stop
          ></textarea>
          <van-button
            type="primary"
            icon="guide-o"
            :loading="loading"
            :disabled="!input.trim() || loading"
            @click="send"
          >
            发送
          </van-button>
        </div>
      </div>

      <aside class="chat-side">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="bulb-o" />
              可以这样问
            </div>
          </div>
          <div class="stack" style="gap: 8px">
            <div
              v-for="item in suggestions"
              :key="item"
              class="suggestion"
              @click="applySuggestion(item)"
            >
              {{ item }}
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="info-o" />
              能力说明
            </div>
          </div>
          <div class="ability-list">
            <div><van-icon name="search" /> 检索新闻数据库</div>
            <div><van-icon name="fire-o" /> 汇总热榜并解释热度</div>
            <div><van-icon name="bar-chart-o" /> 统计今日 / 近 7 天新发布</div>
            <div><van-icon name="bulb-o" /> 生成新闻摘要与简报</div>
            <div><van-icon name="notes-o" /> 按分类、关键词、时间筛选</div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="clock-o" />
              最近对话
            </div>
            <span class="card-link" @click="openHistory">全部</span>
          </div>
          <div v-if="recentHistory.length">
            <div
              v-for="item in recentHistory"
              :key="item.id"
              class="history-item"
              @click="loadHistoryItem(item)"
            >
              <div class="history-q">{{ item.message }}</div>
              <div class="history-time">{{ formatDate(item.created_at) }}</div>
            </div>
          </div>
          <div v-else class="muted" style="font-size: 12px">还没有历史对话</div>
        </div>
      </aside>
    </div>

    <van-popup
      v-model:show="historyVisible"
      round
      position="right"
      :style="{ width: 'min(420px, 92vw)', height: '100%' }"
      class="history-popup"
    >
      <div class="modal-head">
        <div>
          <div class="modal-title">历史对话</div>
          <div class="modal-sub">每条记录包含你的问题与 AI 回复</div>
        </div>
        <div class="modal-close" @click="historyVisible = false">
          <van-icon name="close" />
        </div>
      </div>
      <div v-if="historyLoading" class="empty-box">
        <van-loading size="20" />
      </div>
      <div v-else-if="historyList.length">
        <div
          v-for="item in historyList"
          :key="item.id"
          class="history-block"
          @click="loadHistoryItem(item)"
        >
          <div class="history-q">Q：{{ item.message }}</div>
          <div class="history-a">A：{{ stripMarkdown(item.response).slice(0, 120) }}…</div>
          <div class="history-time">{{ formatDate(item.created_at) }}</div>
        </div>
      </div>
      <div v-else class="empty-box">
        <van-icon name="chat-o" />
        <div>还没有历史对话</div>
      </div>
      <div class="form-actions">
        <van-button size="small" block @click="historyVisible = false">关闭</van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import { useI18n } from 'vue-i18n'
import {
  chatStreamApi,
  clearChatHistoryApi,
  getAIStatusApi,
  getChatHistoryApi
} from '@/api/ai'
import { formatDate, renderMarkdown, stripMarkdown } from '@/utils/format'

const { t } = useI18n()

const messagesRef = ref()
const input = ref('')
const loading = ref(false)
const aiStatus = ref({ enabled: false, mode: 'local', model: '' })
const messages = ref([
  {
    role: 'assistant',
    content:
      '你好，我是新闻智能助手。可以问我「今天的热榜」「近 7 天发布了多少新闻」「总结最新新闻」，也可以让我检索某个关键词的报道。',
    status: '',
    steps: []
  }
])

const suggestions = [
  '汇总一下当前热榜，并说明为什么上榜',
  '统计新闻总量、今日新增和近 7 天新增',
  '总结最近发布的 5 条新闻，给出一句话看点',
  '帮我搜索和「人工智能」相关的新闻',
  '今天有哪些值得关注的新闻？生成一份简报'
]

const historyVisible = ref(false)
const historyLoading = ref(false)
const historyList = ref([])
const recentHistory = ref([])

function scrollToBottom() {
  nextTick(() => {
    const el = messagesRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function applySuggestion(text) {
  input.value = text
  send()
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  scrollToBottom()

  const assistant = reactive({
    role: 'assistant',
    content: '',
    status: '正在思考…',
    steps: []
  })
  messages.value.push(assistant)

  const history = messages.value
    .filter((item) => item.role === 'user' || item.role === 'assistant')
    .slice(0, -1)
    .map(({ role, content }) => ({ role, content }))

  try {
    await chatStreamApi({ messages: history }, (event) => {
      if (event.type === 'status') {
        assistant.status = event.message || '正在思考…'
      } else if (event.type === 'tool_start') {
        const label = event.label || event.name || '工具'
        assistant.status = `正在${label}…`
        assistant.steps.push(`开始：${label}`)
      } else if (event.type === 'tool_end') {
        const label = event.label || event.name || '工具'
        assistant.status = `${label}完成`
        assistant.steps.push(`完成：${label}`)
      } else if (event.type === 'token') {
        assistant.content += event.content || ''
        assistant.status = ''
      } else if (event.type === 'done') {
        assistant.status = ''
      } else if (event.type === 'error') {
        assistant.status = ''
        if (!assistant.content) {
          assistant.content = event.message || '请求失败，请稍后重试'
        }
        showToast({ message: event.message || '请求失败', position: 'top' })
      }
      scrollToBottom()
    })
  } catch (error) {
    assistant.status = ''
    if (!assistant.content) {
      assistant.content = error?.message || '网络异常，请稍后重试'
    }
    showToast({ message: error?.message || '网络异常', position: 'top' })
  } finally {
    loading.value = false
    assistant.status = ''
    scrollToBottom()
    loadRecentHistory()
  }
}

async function openHistory() {
  historyVisible.value = true
  historyLoading.value = true
  try {
    const res = await getChatHistoryApi({ page: 1, page_size: 20 })
    historyList.value = res.data?.list || []
  } catch {
    historyList.value = []
  } finally {
    historyLoading.value = false
  }
}

async function loadRecentHistory() {
  try {
    const res = await getChatHistoryApi({ page: 1, page_size: 4 })
    recentHistory.value = res.data?.list || []
  } catch {
    recentHistory.value = []
  }
}

function loadHistoryItem(item) {
  messages.value = [
    { role: 'user', content: item.message },
    { role: 'assistant', content: item.response, status: '', steps: [] }
  ]
  historyVisible.value = false
  scrollToBottom()
}

async function clearHistory() {
  try {
    await showConfirmDialog({
      title: '清空对话',
      message: '将删除数据库中的全部 AI 对话记录，当前页面消息也会清空，是否继续？',
      confirmButtonText: '清空'
    })
  } catch {
    return
  }
  try {
    await clearChatHistoryApi()
    historyList.value = []
    recentHistory.value = []
    messages.value = [
      {
        role: 'assistant',
        content: '对话记录已清空。你可以重新问我热榜、统计或新闻摘要。',
        status: '',
        steps: []
      }
    ]
    showToast({ message: '已清空对话记录', position: 'top' })
  } catch {
    // 拦截器已提示
  }
}

onMounted(async () => {
  try {
    const res = await getAIStatusApi()
    aiStatus.value = res.data || aiStatus.value
  } catch {
    // 状态接口失败不影响对话
  }
  await loadRecentHistory()
  scrollToBottom()
})
</script>

<style scoped>
.ability-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
  font-size: 12px;
  color: var(--sub);
}

.ability-list > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ability-list .van-icon {
  color: var(--primary);
  font-size: 14px;
}

.history-popup {
  background: var(--card);
  padding: 20px;
  overflow-y: auto;
}

.history-block {
  padding: 11px 0;
  border-bottom: 1px dashed var(--border);
  cursor: pointer;
}

.history-block:last-child {
  border-bottom: none;
}

.history-q {
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.55;
}

.history-a {
  font-size: 11.5px;
  color: var(--sub);
  line-height: 1.55;
  margin-top: 4px;
}

.history-time {
  font-size: 10.5px;
  color: var(--sub);
  margin-top: 4px;
}
</style>
