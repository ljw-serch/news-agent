<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">用户管理</div>
        <div class="page-sub">
          管理员可新增、编辑、禁用、删除用户；系统会保护当前登录账号与最后一名管理员
        </div>
      </div>
      <div class="page-actions">
        <van-button size="small" type="primary" icon="plus" @click="openCreate">
          新增用户
        </van-button>
      </div>
    </div>

    <div class="card" style="padding: 14px 16px; margin-bottom: 16px">
      <div class="toolbar" style="margin-bottom: 0">
        <div class="search-box" style="flex: 1; min-width: 220px">
          <van-icon name="search" />
          <input
            v-model.trim="filters.keywords"
            placeholder="搜索账号或昵称"
            @keyup.enter="handleSearch"
          />
        </div>
        <select v-model="filters.role" class="select" style="width: 130px" @change="handleSearch">
          <option value="">全部角色</option>
          <option value="admin">管理员</option>
          <option value="user">普通用户</option>
        </select>
        <select v-model="filters.status" class="select" style="width: 130px" @change="handleSearch">
          <option value="">全部状态</option>
          <option :value="1">正常</option>
          <option :value="0">禁用</option>
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
              <th style="width: 32%">用户</th>
              <th>角色</th>
              <th>状态</th>
              <th>手机号</th>
              <th>注册时间</th>
              <th style="width: 190px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6">
                <div class="empty-box"><van-loading size="20" /></div>
              </td>
            </tr>
            <tr v-else-if="!userList.length">
              <td colspan="6"><EmptyState text="没有匹配的用户" icon="friends-o" /></td>
            </tr>
            <tr v-for="row in userList" :key="row.id">
              <td>
                <div class="user-cell">
                  <div class="cell-avatar">
                    <img v-if="row.avatar" :src="row.avatar" alt="" />
                    <span v-else>{{ initials(row.nickname || row.username) }}</span>
                  </div>
                  <div style="min-width: 0">
                    <div class="cell-title-text">
                      {{ row.nickname || row.username }}
                      <span v-if="row.id === currentUserId" class="tag muted" style="margin-left: 4px">
                        当前账号
                      </span>
                    </div>
                    <div class="cell-sub">@{{ row.username }} · ID {{ row.id }}</div>
                  </div>
                </div>
              </td>
              <td>
                <span class="tag" :class="row.role === 'admin' ? 'warn' : ''">
                  {{ row.role === 'admin' ? '管理员' : '普通用户' }}
                </span>
              </td>
              <td>
                <span class="tag" :class="row.status === 1 ? 'success' : 'danger'">
                  {{ row.status === 1 ? '正常' : '禁用' }}
                </span>
              </td>
              <td class="mono">{{ row.phone || '—' }}</td>
              <td class="mono">{{ formatDate(row.created_at, false) }}</td>
              <td>
                <div class="table-actions">
                  <van-button size="mini" plain @click="openEdit(row)">编辑</van-button>
                  <van-button
                    size="mini"
                    plain
                    :type="row.status === 1 ? 'warning' : 'success'"
                    :disabled="row.id === currentUserId"
                    @click="toggleStatus(row)"
                  >
                    {{ row.status === 1 ? '禁用' : '启用' }}
                  </van-button>
                  <van-button
                    size="mini"
                    type="danger"
                    plain
                    :disabled="row.id === currentUserId"
                    @click="removeUser(row)"
                  >
                    删除
                  </van-button>
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
          @change="loadUsers"
        />
      </div>
    </div>

    <van-popup v-model:show="dialogVisible" round class="modal-card" :style="{ width: 'min(620px, 94vw)' }">
      <div class="modal-head">
        <div>
          <div class="modal-title">{{ editingId ? '编辑用户' : '新增用户' }}</div>
          <div class="modal-sub">
            {{ editingId ? `正在编辑 @${form.username}` : '新用户默认密码 123456，可在此修改' }}
          </div>
        </div>
        <div class="modal-close" @click="dialogVisible = false">
          <van-icon name="close" />
        </div>
      </div>

      <div class="form-grid">
        <div class="form-item">
          <label class="form-label">账号<span class="req">*</span></label>
          <input
            v-model.trim="form.username"
            class="input"
            :disabled="Boolean(editingId)"
            placeholder="2-50 位账号"
          />
        </div>
        <div class="form-item">
          <label class="form-label">
            {{ editingId ? '重置密码（可选）' : '密码' }}
            <span v-if="!editingId" class="req">*</span>
          </label>
          <input
            v-model="form.password"
            class="input"
            type="password"
            :placeholder="editingId ? '留空则不修改' : '至少 3 位，默认 123456'"
            autocomplete="new-password"
          />
        </div>
        <div class="form-item">
          <label class="form-label">昵称</label>
          <input v-model.trim="form.nickname" class="input" placeholder="显示名称" maxlength="50" />
        </div>
        <div class="form-item">
          <label class="form-label">角色</label>
          <select v-model="form.role" class="select">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
        </div>
        <div class="form-item">
          <label class="form-label">状态</label>
          <select v-model.number="form.status" class="select">
            <option :value="1">正常</option>
            <option :value="0">禁用</option>
          </select>
        </div>
        <div class="form-item">
          <label class="form-label">手机号</label>
          <input v-model.trim="form.phone" class="input" placeholder="选填，需唯一" maxlength="20" />
        </div>
        <div class="form-item full">
          <label class="form-label">头像 URL</label>
          <input v-model.trim="form.avatar" class="input" placeholder="选填" maxlength="255" />
        </div>
        <div class="form-item full">
          <label class="form-label">个人简介</label>
          <textarea
            v-model="form.bio"
            class="textarea"
            style="min-height: 70px"
            maxlength="500"
            placeholder="选填"
          ></textarea>
        </div>
      </div>

      <div class="form-actions">
        <van-button size="small" @click="dialogVisible = false">取消</van-button>
        <van-button size="small" type="primary" :loading="saving" @click="saveUser">
          保存
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import EmptyState from '@/components/EmptyState.vue'
import { useUserStore } from '@/store/user'
import {
  createUserApi,
  deleteUserApi,
  getUserPageApi,
  updateUserApi
} from '@/api/user'
import { formatDate, initials } from '@/utils/format'

const userStore = useUserStore()
const currentUserId = computed(() => userStore.userInfo?.id)

const userList = ref([])
const total = ref(0)
const loading = ref(false)

const filters = reactive({
  page: 1,
  page_size: 8,
  keywords: '',
  role: '',
  status: ''
})

const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref(null)

const emptyForm = () => ({
  username: '',
  password: '',
  nickname: '',
  role: 'user',
  status: 1,
  phone: '',
  avatar: '',
  bio: ''
})

const form = reactive(emptyForm())

async function loadUsers() {
  loading.value = true
  try {
    const res = await getUserPageApi({
      page: filters.page,
      page_size: filters.page_size,
      keywords: filters.keywords || undefined,
      role: filters.role || undefined,
      status: filters.status === '' ? undefined : Number(filters.status)
    })
    userList.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch {
    userList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  filters.page = 1
  loadUsers()
}

function resetFilters() {
  filters.keywords = ''
  filters.role = ''
  filters.status = ''
  filters.page = 1
  loadUsers()
}

function openCreate() {
  Object.assign(form, emptyForm())
  editingId.value = null
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, {
    username: row.username,
    password: '',
    nickname: row.nickname || '',
    role: row.role || 'user',
    status: row.status,
    phone: row.phone || '',
    avatar: row.avatar || '',
    bio: row.bio || ''
  })
  editingId.value = row.id
  dialogVisible.value = true
}

async function saveUser() {
  if (!editingId.value && (!form.username || form.username.length < 2)) {
    showToast({ message: '账号至少 2 个字符', position: 'top' })
    return
  }
  if (!editingId.value && form.password.length < 3) {
    showToast({ message: '密码至少 3 个字符', position: 'top' })
    return
  }
  if (editingId.value && form.password && form.password.length < 3) {
    showToast({ message: '新密码至少 3 个字符', position: 'top' })
    return
  }
  if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone)) {
    showToast({ message: '手机号格式不正确', position: 'top' })
    return
  }

  saving.value = true
  try {
    if (editingId.value) {
      const payload = {
        nickname: form.nickname || undefined,
        role: form.role,
        status: form.status,
        phone: form.phone || undefined,
        avatar: form.avatar || undefined,
        bio: form.bio || undefined
      }
      if (form.password) payload.password = form.password
      await updateUserApi(editingId.value, payload)
      showToast({ message: '用户信息已更新', position: 'top' })
    } else {
      await createUserApi({
        username: form.username,
        password: form.password || '123456',
        nickname: form.nickname || form.username,
        role: form.role,
        status: form.status,
        phone: form.phone || undefined,
        avatar: form.avatar || undefined,
        bio: form.bio || undefined
      })
      showToast({ message: '用户创建成功', position: 'top' })
    }
    dialogVisible.value = false
    await loadUsers()
  } catch {
    // 拦截器已提示
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row) {
  const next = row.status === 1 ? 0 : 1
  try {
    await showConfirmDialog({
      title: next === 0 ? '禁用用户' : '启用用户',
      message: `确认${next === 0 ? '禁用' : '启用'} @${row.username}？`,
      confirmButtonText: '确认'
    })
  } catch {
    return
  }
  try {
    await updateUserApi(row.id, { status: next })
    showToast({ message: next === 1 ? '用户已启用' : '用户已禁用', position: 'top' })
    await loadUsers()
  } catch {
    // 拦截器已提示
  }
}

async function removeUser(row) {
  try {
    await showConfirmDialog({
      title: '删除用户',
      message: `确认删除 @${row.username}？该用户的收藏、浏览历史与 AI 对话将一并删除。`,
      confirmButtonText: '确认删除',
      confirmButtonColor: '#ee0a24'
    })
  } catch {
    return
  }
  try {
    await deleteUserApi(row.id)
    showToast({ message: '用户已删除', position: 'top' })
    if (userList.value.length === 1 && filters.page > 1) filters.page -= 1
    await loadUsers()
  } catch {
    // 拦截器已提示
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 190px;
}

.cell-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--primary), #7c3aed);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.cell-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
