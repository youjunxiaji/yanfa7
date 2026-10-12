import { onBeforeUnmount, ref, type Ref } from 'vue'

// 主题落在 <html> 的 .dark class 上，由 tauri-bridge 和各入口的 syncDarkClass 维护（见 Tauri Skill），这里只跟着读
export const useDarkClass = (): Ref<boolean> => {
    const root = document.documentElement
    const isDark = ref(root.classList.contains('dark'))
    const observer = new MutationObserver(() => {
        isDark.value = root.classList.contains('dark')
    })
    observer.observe(root, { attributes: true, attributeFilter: ['class'] })
    onBeforeUnmount(() => observer.disconnect())
    return isDark
}
