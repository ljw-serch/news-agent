<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">新闻管理</div>
        <div class="page-sub">
          管理员可新增、编辑、删除新闻；支持单条 / 批量生成 AI 摘要
        </div>
      </div>
      <div class="page-actions">
        <van-button size="small" icon="bulb-o" :loading="batchLoading" @click="batchSummarize">
          批量生成摘要
        </van-button>
        <van-button size="small" type="primary" icon="plus" @click="openCreate">
          新增新闻
        </van-button>
      </div>
    </div>

    <div class="card" style="padding: 14px 16px; margin-bottom: 16px">
      <div class="toolbar" style="margin-bottom: 0">
        <div class="search-box" style="flex: 1; min-width: 220px">
          <van-icon name="search" />
          <input
            v-model.trim="filters.keywords"
            placeholder="搜索标题 / 正文 / 作者"
            @keyup.enter="handleSearch"
          />
        </div>
        <select v-model="filters.category_id" class="select" style="width: 150px" @change="handleSearch">
          <option :value="0">全部分类</option>
          <option v-for="item in categories" :key="item.id" :value="item.id">
            {{ item.name }}（{{ item.news_count }}）
          </option>
        </select>
        <van-button size="small" type="primary" icon="search" @click="handleSearch">查询</van-button>
        <van-button size="small" @click="resetFilters">重置</van-button>
      </div>
    </div>

    <div class="card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th style="width: 46%">标题</th>
              <th>分类</th>
              <th>作者</th>
              <th>发布时间</th>
              <th>阅读</th>
              <th>AI 摘要</th>
              <th style="width: 190px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7">
                <div class="empty-box"><van-loading size="20" /></div>
              </td>
            </tr>
            <tr v-else-if="!newsList.length">
              <td colspan="7">
                <EmptyState text="没有新闻，点击右上角「新增新闻」开始" icon="notes-o" />
              </td>
            </tr>
            <tr v-for="row in newsList" :key="row.id">
              <td>
                <div class="cell-title">
                  <img v-if="row.image" class="cell-thumb" :src="row.image" alt="" @error="onImageError" />
                  <div v-else class="cell-thumb cell-fallback">{{ (row.category_name || '新').slice(0, 1) }}</div>
                  <div style="min-width: 0">
                    <div class="cell-title-text">{{ row.title }}</div>
                    <div class="cell-sub">ID {{ row.id }} · {{ row.description || '无简介' }}</div>
                  </div>
                </div>
              </td>
              <td><span class="tag">{{ row.category_name || '未分类' }}</span></td>
              <td>{{ row.author || '—' }}</td>
              <td class="mono">{{ formatDate(row.publish_time) }}</td>
              <td class="mono">{{ formatNumber(row.views) }}</td>
              <td>
                <span class="tag" :class="row.summary ? 'success' : 'muted'">
                  {{ row.summary ? '已生成' : '未生成' }}
                </span>
              </td>
              <td>
                <div class="table-actions">
                  <van-button
                    size="mini"
                    plain
                    type="primary"
                    :loading="summaryId === row.id"
                    @click="generateSummary(row)"
                  >
                    摘要
                  </van-button>
                  <van-button size="mini" plain @click="openEdit(row)">编辑</van-button>
                  <van-button size="mini" type="danger" plain @click="removeNews(row)">删除</van-button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="total > filters.page_size" class="pagination-row">
        <van-pagination
          v-model="filters.page"
          :total-items="total"
          :items-per-page="filters.page_size"
          :show-page-size="5"
          force-ellipses
          @change="loadNews"
        />
      </div>
    </div>

    <van-popup v-model:show="dialogVisible" round class="modal-card">
      <div class="modal-head">
        <div>
          <div class="modal-title">{{ editingId ? '编辑新闻' : '新增新闻' }}</div>
          <div class="modal-sub">
            {{ editingId ? `正在编辑 ID ${editingId}` : '发布后将立即出现在新闻列表与统计中' }}
          </div>
        </div>
        <div class="modal-close" @click="dialogVisible = false">
          <van-icon name="close" />
        </div>
      </div>

      <div class="form-grid">
        <div class="form-item full">
          <label class="form-label">标题<span class="req">*</span></label>
          <input v-model.trim="form.title" class="input" placeholder="请输入新闻标题" maxlength="255" />
        </div>
        <div class="form-item">
          <label class="form-label">分类<span class="req">*</span></label>
          <select v-model="form.category_id" class="select">
            <option :value="0" disabled>请选择分类</option>
            <option v-for="item in categories" :key="item.id" :value="item.id">
              {{ item.name }}
            </option>
          </select>
        </div>
        <div class="form-item">
          <label class="form-label">作者</label>
          <input v-model.trim="form.author" class="input" placeholder="例如：平台编辑" maxlength="50" />
        </div>
        <div class="form-item">
          <label class="form-label">发布时间</label>
          <input v-model="form.publish_time" type="datetime-local" class="input" />
        </div>
        <div class="form-item">
          <label class="form-label">浏览量</label>
          <input v-model.number="form.views" type="number" min="0" class="input" placeholder="0" />
        </div>
        <div class="form-item full">
          <label class="form-label">封面图</label>
          <div class="cover-row">
            <img v-if="form.image" :src="form.image" class="cover-preview" alt="封面" @error="onImageError" />
            <div v-else class="cover-preview cover-fallback">无封面</div>
            <div style="flex: 1; min-width: 0">
              <input v-model.trim="form.image" class="input" placeholder="图片 URL，或点击右侧上传" />
              <div style="margin-top: 8px; display: flex; gap: 8px; align-items: center">
                <van-uploader :after-read="onUpload" :show-upload="false">
                  <van-button size="mini" icon="photograph">上传封面</van-button>
                </van-uploader>
                <span class="form-hint">支持 jpg / png / webp，≤ 10MB</span>
              </div>
            </div>
          </div>
        </div>
        <div class="form-item full">
          <label class="form-label">简介</label>
          <textarea
            v-model="form.description"
            class="textarea"
            style="min-height: 70px"
            maxlength="500"
            placeholder="一句话概括新闻内容，留空则自动截取正文"
          ></textarea>
        </div>
        <div class="form-item full">
          <label class="form-label">正文<span class="req">*</span></label>
          <textarea
            v-model="form.content"
            class="textarea"
            style="min-height: 220px"
            placeholder="请输入新闻正文，建议按段落换行"
          ></textarea>
        </div>
      </div>

      <div class="form-actions">
        <van-button size="small" @click="dialogVisible = false">取消</van-button>
        <van-button size="small" type="primary" :loading="saving" @click="saveNews">
          保存
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import EmptyState from '@/components/EmptyState.vue'
import {
  batchSummaryApi,
  createNewsApi,
  deleteNewsApi,
  generateNewsSummaryApi,
  getCategoriesApi,
  getNewsDetailApi,
  getNewsPageApi,
  updateNewsApi
} from '@/api/news'
import { uploadFileApi } from '@/api/file'
import { formatDate, formatNumber } from '@/utils/format'

const route = useRoute()

const categories = ref([])
const newsList = ref([])
const total = ref(0)
const loading = ref(false)
const batchLoading = ref(false)
const summaryId = ref(null)

const filters = reactive({
  page: 1,
  page_size: 8,
  keywords: '',
  category_id: 0
})

const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)

const emptyForm = () => ({
  title: '',
  description: '',
  content: '',
  image: '',
  author: '',
  category_id: 0,
  publish_time: '',
  views: 0
})

const form = reactive(emptyForm())

function onImageError(event) {
  if (event?.target) event.target.style.visibility = 'hidden'
}

function toLocalInput(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`
}

function nowLocalInput() {
  return toLocalInput(new Date())
}

async function loadCategories() {
  try {
    const res = await getCategoriesApi()
    categories.value = res.data || []
  } catch {
    categories.value = []
  }
}

async function loadNews() {
  loading.value = true
  try {
    const res = await getNewsPageApi({
      page: filters.page,
      page_size: filters.page_size,
      keywords: filters.keywords || undefined,
      category_id: filters.category_id || undefined
    })
    newsList.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch {
    newsList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  filters.page = 1
  loadNews()
}

function resetFilters() {
  filters.keywords = ''
  filters.category_id = 0
  filters.page = 1
  loadNews()
}

function openCreate() {
  Object.assign(form, emptyForm())
  form.category_id = categories.value[0]?.id || 0
  form.publish_time = nowLocalInput()
  editingId.value = null
  dialogVisible.value = true
}

async function openEdit(row) {
  try {
    const res = await getNewsDetailApi(row.id)
    const data = res.data || {}
    Object.assign(form, {
      title: data.title || '',
      description: data.description || '',
      content: data.content || '',
      image: data.image || '',
      author: data.author || '',
      category_id: data.category_id || 0,
      publish_time: toLocalInput(data.publish_time),
      views: data.views || 0
    })
    editingId.value = row.id
    dialogVisible.value = true
  } catch {
    // 拦截器已提示
  }
}

async function onUpload(item) {
  if (!item?.file) return
  try {
    const res = await uploadFileApi(item.file)
    if (res.code === 200 && res.data?.url) {
      form.image = res.data.url
      showToast({ message: '封面上传成功', position: 'top' })
    }
  } catch {
    // 拦截器已提示
  }
}

async function saveNews() {
  if (!form.title.trim()) {
    showToast({ message: '请输入标题', position: 'top' })
    return
  }
  if (!form.category_id) {
    showToast({ message: '请选择分类', position: 'top' })
    return
  }
  if (!form.content.trim()) {
    showToast({ message: '请输入正文', position: 'top' })
    return
  }

  const payload = {
    title: form.title.trim(),
    description: form.description.trim() || undefined,
    content: form.content.trim(),
    image: form.image.trim() || undefined,
    author: form.author.trim() || undefined,
    category_id: form.category_id,
    views: Number(form.views) || 0
  }
  if (form.publish_time) {
    payload.publish_time = form.publish_time.length === 16 ? `${form.publish_time}:00` : form.publish_time
  }

  saving.value = true
  try {
    if (editingId.value) {
      await updateNewsApi(editingId.value, payload)
      showToast({ message: '新闻已更新', position: 'top' })
    } else {
      await createNewsApi(payload)
      showToast({ message: '新闻已发布', position: 'top' })
    }
    dialogVisible.value = false
    await Promise.all([loadNews(), loadCategories()])
  } catch {
    // 拦截器已提示
  } finally {
    saving.value = false
  }
}

async function removeNews(row) {
  try {
    await showConfirmDialog({
      title: '删除新闻',
      message: `确认删除《${row.title}》？相关收藏与浏览记录也会被级联删除。`,
      confirmButtonText: '确认删除',
      confirmButtonColor: '#ee0a24'
    })
  } catch {
    return
  }
  try {
    await deleteNewsApi(row.id)
    showToast({ message: '新闻已删除', position: 'top' })
    if (newsList.value.length === 1 && filters.page > 1) filters.page -= 1
    await Promise.all([loadNews(), loadCategories()])
  } catch {
    // 拦截器已提示
  }
}

async function generateSummary(row) {
  summaryId.value = row.id
  try {
    const res = await generateNewsSummaryApi(row.id, true)
    row.summary = res.data?.summary || row.summary
    row.highlight = res.data?.highlight || row.highlight
    showToast({ message: 'AI 摘要已生成', position: 'top' })
  } catch {
    // 拦截器已提示
  } finally {
    summaryId.value = null
  }
}

async function batchSummarize() {
  try {
    await showConfirmDialog({
      title: '批量生成摘要',
      message: '将为最近 5 条尚未生成摘要的新闻调用 AI，耗时约 10-30 秒，是否继续？',
      confirmButtonText: '开始生成'
    })
  } catch {
    return
  }
  batchLoading.value = true
  try {
    const res = await batchSummaryApi({ limit: 5, force: false })
    const data = res.data || {}
    showToast({
      message: `完成：成功 ${data.success_count || 0} 条，失败 ${data.failed_count || 0} 条`,
      position: 'top'
    })
    await loadNews()
  } catch {
    // 拦截器已提示
  } finally {
    batchLoading.value = false
  }
}

async function handleQueryEdit() {
  const id = Number(route.query.edit)
  if (!id) return
  await openEdit({ id })
}

onMounted(async () => {
  await loadCategories()
  await loadNews()
  await handleQueryEdit()
})
</script>

<style scoped>
.cell-fallback {
  display: grid;
  place-items: center;
  color: var(--primary);
  font-weight: 800;
  background: var(--primary-soft);
}

.cover-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.cover-preview {
  width: 140px;
  height: 92px;
  border-radius: 9px;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid var(--border);
  background: var(--bg);
}

.cover-fallback {
  display: grid;
  place-items: center;
  font-size: 11px;
  color: var(--sub);
}

.modal-card {
  width: min(820px, 94vw);
}

@media (max-width: 640px) {
  .cover-row {
    flex-direction: column;
  }

  .cover-preview {
    width: 100%;
    height: 140px;
  }
}
</style>
