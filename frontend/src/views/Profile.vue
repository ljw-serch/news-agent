<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">个人资料</div>
        <div class="page-sub">完善资料后，评论、收藏与 AI 对话都会显示最新昵称</div>
      </div>
      <div class="page-actions">
        <van-button size="small" icon="lock" @click="$router.push('/manager/password')">
          修改密码
        </van-button>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-head">
          <div class="card-title">
            <van-icon name="user-o" />
            基本资料
          </div>
          <span class="tag" :class="isAdmin ? 'warn' : ''">{{ roleLabel }}</span>
        </div>

        <div class="avatar-row">
          <van-uploader :after-read="onUpload" :max-count="1" :show-upload="false">
            <div class="avatar-preview">
              <img v-if="form.avatar" :src="form.avatar" alt="avatar" />
              <span v-else>{{ initials(userStore.displayName) }}</span>
              <div class="avatar-mask">更换</div>
            </div>
          </van-uploader>
          <div>
            <div style="font-size: 14px; font-weight: 700">{{ userStore.displayName }}</div>
            <div class="muted" style="font-size: 11.5px; margin-top: 4px">
              @{{ userInfo?.username }} · 注册于 {{ formatDate(userInfo?.created_at, false) }}
            </div>
            <div class="muted" style="font-size: 11px; margin-top: 3px">
              支持 jpg / png / webp，大小不超过 10MB
            </div>
          </div>
        </div>

        <div class="form-grid" style="margin-top: 18px">
          <div class="form-item">
            <label class="form-label">昵称</label>
            <input v-model.trim="form.nickname" class="input" placeholder="请输入昵称" />
          </div>
          <div class="form-item">
            <label class="form-label">性别</label>
            <select v-model="form.gender" class="select">
              <option value="unknown">保密</option>
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </div>
          <div class="form-item">
            <label class="form-label">手机号</label>
            <input v-model.trim="form.phone" class="input" placeholder="选填，需唯一" />
          </div>
          <div class="form-item">
            <label class="form-label">头像地址</label>
            <input v-model.trim="form.avatar" class="input" placeholder="上传后自动填入" />
          </div>
          <div class="form-item full">
            <label class="form-label">个人简介</label>
            <textarea
              v-model="form.bio"
              class="textarea"
              maxlength="500"
              placeholder="介绍一下自己关注的新闻领域"
            ></textarea>
          </div>
        </div>

        <div class="form-actions">
          <van-button size="small" @click="loadProfile">重置</van-button>
          <van-button size="small" type="primary" :loading="saving" @click="save">
            保存修改
          </van-button>
        </div>
      </div>

      <div class="stack">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="shield-o" />
              账号信息
            </div>
          </div>
          <div class="info-list">
            <div><span>账号</span><b>{{ userInfo?.username || '—' }}</b></div>
            <div><span>角色</span><b>{{ roleLabel }}</b></div>
            <div><span>状态</span><b>{{ userInfo?.status === 1 ? '正常' : '禁用' }}</b></div>
            <div><span>注册时间</span><b>{{ formatDate(userInfo?.created_at) }}</b></div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="info-o" />
              小提示
            </div>
          </div>
          <div class="muted" style="font-size: 12px; line-height: 1.8">
            管理员可以在「用户管理」中修改你的角色与状态。普通用户可收藏新闻、查看浏览历史并使用
            AI 助手；管理员额外拥有新闻与用户管理权限。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { showToast } from 'vant'
import { useUserStore } from '@/store/user'
import { getMeApi, updateMeApi } from '@/api/user'
import { uploadFileApi } from '@/api/file'
import { formatDate, initials } from '@/utils/format'

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)
const isAdmin = computed(() => userStore.isAdmin)
const roleLabel = computed(() => userStore.roleLabel)

const form = reactive({
  nickname: '',
  avatar: '',
  gender: 'unknown',
  phone: '',
  bio: ''
})
const saving = ref(false)

function fillForm(user) {
  if (!user) return
  form.nickname = user.nickname || ''
  form.avatar = user.avatar || ''
  form.gender = user.gender || 'unknown'
  form.phone = user.phone || ''
  form.bio = user.bio || ''
}

async function loadProfile() {
  fillForm(userStore.userInfo)
  try {
    const res = await getMeApi()
    if (res.code === 200 && res.data) {
      userStore.updateUser(res.data)
      fillForm(res.data)
    }
  } catch {
    // 拦截器已提示
  }
}

async function onUpload(item) {
  if (!item?.file) return
  try {
    const res = await uploadFileApi(item.file)
    if (res.code === 200 && res.data?.url) {
      form.avatar = res.data.url
      showToast({ message: '头像上传成功', position: 'top' })
    }
  } catch {
    // 拦截器已提示
  }
}

async function save() {
  if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone)) {
    showToast({ message: '手机号格式不正确', position: 'top' })
    return
  }
  saving.value = true
  try {
    const res = await updateMeApi({
      nickname: form.nickname || undefined,
      avatar: form.avatar || undefined,
      gender: form.gender,
      phone: form.phone || undefined,
      bio: form.bio || undefined
    })
    if (res.code === 200 && res.data) {
      userStore.updateUser(res.data)
      fillForm(res.data)
      showToast({ message: '资料已更新', position: 'top' })
    }
  } catch {
    // 拦截器已提示
  } finally {
    saving.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.avatar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0 2px;
}

.avatar-preview {
  position: relative;
  width: 78px;
  height: 78px;
  border-radius: 50%;
  overflow: hidden;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--primary), #7c3aed);
  color: #fff;
  font-size: 26px;
  font-weight: 800;
  cursor: pointer;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-mask {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 4px 0;
  text-align: center;
  font-size: 10px;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  opacity: 0;
  transition: 0.18s;
}

.avatar-preview:hover .avatar-mask {
  opacity: 1;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-list > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
}

.info-list span {
  color: var(--sub);
}

.info-list b {
  font-weight: 600;
  text-align: right;
}
</style>
