<template>
    <div class="reading">
        <article class="markdown-body" v-html="renderedHtml" />
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
.markdown-body {
    max-width: 760px;
    margin: 0 auto;
    padding: 40px 40px 72px;
    font-size: 14px;
    line-height: 1.75;
    word-wrap: break-word;
}

.markdown-body :deep(h1) {
    margin: 0 0 12px;
    font-size: 26px;
    font-weight: 700;
    line-height: 1.3;
    letter-spacing: -0.02em;
}

.markdown-body :deep(h2) {
    margin: 36px 0 10px;
    padding-top: 22px;
    font-size: 18px;
    font-weight: 650;
    line-height: 1.4;
    border-top: 1px solid var(--divider);
}

.markdown-body :deep(h3) {
    margin: 24px 0 8px;
    font-size: 15px;
    font-weight: 600;
}

.markdown-body :deep(p),
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
    margin: 0 0 12px;
    color: var(--text-2);
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
    padding-left: 22px;
}

.markdown-body :deep(li) {
    margin: 4px 0;
}

.markdown-body :deep(li::marker) {
    color: var(--text-3);
}

.markdown-body :deep(strong) {
    font-weight: 600;
    color: var(--text-1);
}

.markdown-body :deep(a) {
    color: var(--accent);
    text-decoration: none;
}

.markdown-body :deep(a:hover) {
    text-decoration: underline;
}

.markdown-body :deep(code) {
    padding: 1px 6px;
    font-family: var(--font-mono);
    font-size: 12.5px;
    color: var(--text-1);
    background: var(--muted);
    border-radius: 4px;
}

.markdown-body :deep(pre) {
    margin: 0 0 16px;
    padding: 14px 16px;
    overflow-x: auto;
    background: var(--subtle);
    border: 1px solid var(--divider);
    border-radius: 8px;
}

.markdown-body :deep(pre code) {
    padding: 0;
    font-size: 12.5px;
    line-height: 1.65;
    background: none;
}

.markdown-body :deep(table) {
    width: 100%;
    margin: 0 0 16px;
    font-size: 13px;
    border-collapse: collapse;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid var(--divider);
}

.markdown-body :deep(th) {
    font-weight: 500;
    color: var(--text-3);
}

.markdown-body :deep(blockquote) {
    margin: 0 0 16px;
    padding: 4px 16px;
    color: var(--text-2);
    border-left: 3px solid var(--border);
}

.markdown-body :deep(hr) {
    margin: 24px 0;
    border: none;
    border-top: 1px solid var(--divider);
}

.markdown-body :deep(img) {
    max-width: 100%;
    border-radius: 8px;
}
</style>
