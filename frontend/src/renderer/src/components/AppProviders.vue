<template>
    <n-config-provider
        :theme="isDark ? darkTheme : null"
        :theme-overrides="isDark ? darkThemeOverrides : lightThemeOverrides"
        :locale="zhCN"
        :date-locale="dateZhCN"
        abstract
    >
        <n-message-provider placement="top" :max="3">
            <slot />
        </n-message-provider>
    </n-config-provider>
</template>

<script setup lang="ts">
// 主窗口和预览窗口共用的根：Naive 主题、中文 locale、消息提示，图标默认线宽
import { NConfigProvider, NMessageProvider, darkTheme, dateZhCN, zhCN } from 'naive-ui'
import { setLucideProps } from '@lucide/vue'
import { useDarkClass } from '@renderer/composables/useDarkClass'
import { darkThemeOverrides, lightThemeOverrides } from '@renderer/theme/naive'

const isDark = useDarkClass()

setLucideProps({ strokeWidth: 1.75 })
</script>
