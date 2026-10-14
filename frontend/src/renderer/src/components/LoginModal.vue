<template>
    <n-modal
        v-model:show="account.loginVisible"
        preset="card"
        title="登录"
        :style="{ width: '560px' }"
        :bordered="false"
        :mask-closable="false"
        :closable="!submitting"
        @after-enter="focusFirstEmpty"
        @after-leave="reset"
    >
        <div class="login-form">
            <p class="login-desc">
                用网页版（TMB 系统）的工号和密码登录，服务器上存的历史记录要登录后才能读。
            </p>
            <div class="field">
                <span class="field-label">工号</span>
                <n-input
                    ref="usernameRef"
                    v-model:value="username"
                    placeholder="6 位工号"
                    :disabled="submitting"
                    :input-props="{ autocomplete: 'username' }"
                    @keydown.enter.prevent="passwordRef?.focus()"
                >
                    <template #prefix><User class="input-prefix" :size="15" /></template>
                </n-input>
            </div>
            <div class="field">
                <span class="field-label">密码</span>
                <n-input
                    ref="passwordRef"
                    v-model:value="password"
                    type="password"
                    show-password-on="click"
                    placeholder="网页版的登录密码"
                    :disabled="submitting"
                    :input-props="{ autocomplete: 'current-password' }"
                    @keydown.enter.prevent="submit"
                >
                    <template #prefix><LockKeyhole class="input-prefix" :size="15" /></template>
                </n-input>
                <div class="field-hint">同一账号只能在一处登录，这里登录后网页版会退出登录</div>
            </div>
            <p v-if="error" class="login-error">
                <CircleAlert :size="13" />
                <span>{{ error }}</span>
            </p>
        </div>
        <template #footer>
            <div class="modal-actions">
                <n-button :disabled="submitting" @click="account.loginVisible = false">
                    取消
                </n-button>
                <n-button
                    type="primary"
                    :loading="submitting"
                    :disabled="!canSubmit"
                    @click="submit"
                >
                    登录
                </n-button>
            </div>
        </template>
    </n-modal>
</template>

<script setup lang="ts">
// 登录 TMB 服务器的弹窗，挂在 App.vue；哪里要登录就把 account.loginVisible 设成 true
import { computed, ref } from 'vue'
import { NButton, NInput, NModal, useMessage } from 'naive-ui'
import { CircleAlert, LockKeyhole, User } from '@lucide/vue'
import { useAccountStore } from '@renderer/stores/account'

const account = useAccountStore()
const message = useMessage()

const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

const usernameRef = ref<InstanceType<typeof NInput> | null>(null)
const passwordRef = ref<InstanceType<typeof NInput> | null>(null)

const canSubmit = computed(() => !!username.value.trim() && !!password.value && !submitting.value)

// 上次登录过就预填工号，光标直接落在密码上
const focusFirstEmpty = (): void => {
    if (!username.value) username.value = account.lastUsername
    if (username.value) passwordRef.value?.focus()
    else usernameRef.value?.focus()
}

const reset = (): void => {
    password.value = ''
    error.value = ''
}

const submit = async (): Promise<void> => {
    if (!canSubmit.value) return
    submitting.value = true
    error.value = ''
    try {
        await account.login(username.value.trim(), password.value)
        account.loginVisible = false
        message.success(`已登录：${account.user?.name}`)
    } catch (err) {
        error.value = (err as Error).message
        password.value = ''
        passwordRef.value?.focus()
    } finally {
        submitting.value = false
    }
}
</script>

<style scoped>
.login-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.login-desc {
    margin: 0;
    font-size: 12.5px;
    color: var(--text-3);
}

.input-prefix {
    color: var(--text-3);
}

.login-error {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0 0 0 96px;
    font-size: 12px;
    color: var(--danger);
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}
</style>
