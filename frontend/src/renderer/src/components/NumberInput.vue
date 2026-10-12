<template>
    <n-input-number
        :value="model"
        :step="step"
        :min="min"
        :max="max"
        :size="size"
        :show-button="false"
        @update:value="handleUpdate"
    >
        <template v-if="prefix" #prefix>
            <span class="number-affix">{{ prefix }}</span>
        </template>
        <template v-if="suffix" #suffix>
            <span class="number-affix">{{ suffix }}</span>
        </template>
    </n-input-number>
</template>

<script setup lang="ts">
// 参数栏的数值框：不显示 +/- 按钮（键盘 ↑↓ 调值），单位写在 suffix，并列的两个值用 prefix 区分。
// 清空时不回写，失焦后显示回原值，所以绑定的字段始终是数字。
import { NInputNumber } from 'naive-ui'

withDefaults(
    defineProps<{
        step?: number
        min?: number
        max?: number
        size?: 'small' | 'medium'
        prefix?: string
        suffix?: string
    }>(),
    { step: 1, size: 'medium' }
)

const model = defineModel<number>({ required: true })

const handleUpdate = (value: number | null): void => {
    if (value !== null) model.value = value
}
</script>

<style scoped>
.number-affix {
    font-size: 12px;
    color: var(--text-3);
}
</style>
