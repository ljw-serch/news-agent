<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">修改密码</div>
        <div class="page-sub">建议使用字母 + 数字组合，修改后请妥善保管</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-head">
          <div class="card-title">
            <van-icon name="lock" />
            密码设置
          </div>
        </div>

        <div class="form-item" style="margin-bottom: 13px">
          <label class="form-label">原密码</label>
          <input
            v-model="form.oldPassword"
            class="input"
            type="password"
            placeholder="请输入原密码"
            autocomplete="current-password"
          />
        </div>
        <div class="form-item" style="margin-bottom: 13px">
          <label class="form-label">新密码</label>
          <input
            v-model="form.newPassword"
            class="input"
            type="password"
            placeholder="至少 6 位"
            autocomplete="new-password"
          />
        </div>
        <div class="form-item">
          <label class="form-label">确认新密码</label>
          <input
            v-model="form.confirm"
            class="input"
            type="password"
            placeholder="再次输入新密码"
            autocomplete="new-password"
          />
        </div>

        <div v-if="errorText" class="form-error" style="margin-top: 10px">
          {{ errorText }}
        </div>

        <div class="form-actions">
          <van-button size="small" @click="reset">清空</van-button>
          <van-button size="small" type="primary" :loading="loading" @click="submit">
            确认修改
          </van-button>
        </div>
      </div>

      <div class="stack">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="shield-o" />
              安全建议
            </div>
          </div>
          <div class="tip-list">
            <div><van-icon name="passed" /> 不要使用 123456、生日等弱密码</div>
            <div><van-icon name="passed" /> 新密码不能与原密码相同</div>
            <div><van-icon name="passed" /> 管理员重置密码后请立即修改</div>
            <div><van-icon name="passed" /> 不要在公共设备保存登录状态</div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="info-o" />
              账号
            </div>
          </div>
          <div class="muted" style="font-size: 12px; line-height: 1.8">
            当前账号：{{ userStore.userInfo?.username || '—' }}<br />
            角色：{{ userStore.roleLabel }}<br />
            修改成功后当前登录状态仍然有效。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { showToast } from 'vant'
import { updatePasswordApi } from '@/api/user'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const form = reactive({ oldPassword: '', newPassword: '', confirm: '' })
const loading = ref(false)
const errorText = ref('')

function reset() {
  form.oldPassword = ''
  form.newPassword = ''
  form.confirm = ''
  errorText.value = ''
}

async function submit() {
  errorText.value = ''
  if (!form.oldPassword || !form.newPassword) {
    errorText.value = '请填写完整的密码信息'
    return
  }
  if (form.newPassword.length < 6) {
    errorText.value = '新密码至少 6 位'
    return
  }
  if (form.newPassword !== form.confirm) {
    errorText.value = '两次输入的新密码不一致'
    return
  }
  loading.value = true
  try {
    await updatePasswordApi({
      old_password: form.oldPassword,
      new_password: form.newPassword
    })
    showToast({ message: '密码修改成功', position: 'top' })
    reset()
  } catch (error) {
    errorText.value = error?.message || '修改失败，请检查原密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.tip-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 12px;
  color: var(--sub);
  line-height: 1.6;
}

.tip-list > div {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.tip-list .van-icon {
  color: #10b981;
  margin-top: 2px;
  flex-shrink: 0;
}
</style>
