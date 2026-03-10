<template>
    <div class="docs-page">
        <div class="docs-body">
            <div class="markdown-body" v-html="renderedHtml" />
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import markdownit from 'markdown-it'
import readmeRaw from '@root/README.md?raw'

const md = markdownit({ html: true, linkify: true, typographer: true })
const renderedHtml = computed(() => md.render(readmeRaw))
</script>

<style scoped>
.docs-page {
    height: 100%;
    overflow-y: auto;
    background: #ffffff;
}

.docs-body {
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 48px 80px;
}

.markdown-body {
    font-size: 15px;
    line-height: 1.7;
    color: #1d1d1f;
    word-wrap: break-word;
}

.markdown-body :deep(h1) {
    font-size: 28px;
    font-weight: 700;
    margin: 0 0 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e5e5ea;
    letter-spacing: -0.5px;
}

.markdown-body :deep(h2) {
    font-size: 22px;
    font-weight: 600;
    margin: 32px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f0f0f2;
}

.markdown-body :deep(h3) {
    font-size: 18px;
    font-weight: 600;
    margin: 24px 0 8px;
}

.markdown-body :deep(h4) {
    font-size: 16px;
    font-weight: 600;
    margin: 20px 0 8px;
}

.markdown-body :deep(p) {
    margin: 0 0 12px;
}

.markdown-body :deep(a) {
    color: var(--el-color-primary);
    text-decoration: none;
}

.markdown-body :deep(a:hover) {
    text-decoration: underline;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
    padding-left: 24px;
    margin: 0 0 12px;
}

.markdown-body :deep(li) {
    margin: 4px 0;
}

.markdown-body :deep(li > ul),
.markdown-body :deep(li > ol) {
    margin: 4px 0 0;
}

.markdown-body :deep(code) {
    font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    background: #f5f5f7;
    padding: 2px 6px;
    border-radius: 4px;
    color: #e45649;
}

.markdown-body :deep(pre) {
    background: #f5f5f7;
    border-radius: 8px;
    padding: 16px 20px;
    overflow-x: auto;
    margin: 0 0 16px;
}

.markdown-body :deep(pre code) {
    background: none;
    padding: 0;
    color: #1d1d1f;
    font-size: 13px;
    line-height: 1.6;
}

.markdown-body :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 0 0 16px;
    font-size: 14px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
    border: 1px solid #e5e5ea;
    padding: 8px 12px;
    text-align: left;
}

.markdown-body :deep(th) {
    background: #f5f5f7;
    font-weight: 600;
}

.markdown-body :deep(tr:nth-child(even)) {
    background: #fafafa;
}

.markdown-body :deep(blockquote) {
    border-left: 4px solid #e5e5ea;
    margin: 0 0 16px;
    padding: 4px 16px;
    color: #86868b;
}

.markdown-body :deep(blockquote p:last-child) {
    margin-bottom: 0;
}

.markdown-body :deep(hr) {
    border: none;
    border-top: 1px solid #e5e5ea;
    margin: 24px 0;
}

.markdown-body :deep(img) {
    max-width: 100%;
    border-radius: 8px;
}

.markdown-body :deep(strong) {
    font-weight: 600;
}
</style>
