<template>
    <div class="param-section">
        <div class="section-head">
            <span class="section-title">齿轮级</span>
            <n-popconfirm
                :show-icon="false"
                positive-text="删除"
                negative-text="取消"
                @positive-click="store.removeLastStage()"
            >
                <template #trigger>
                    <button class="link-btn is-danger" :disabled="store.stageCount <= 1">
                        删除最后一级
                    </button>
                </template>
                删除 Stage {{ stageName(store.stageCount - 1) }}？这一级填的参数一起删掉。
            </n-popconfirm>
        </div>

        <div class="stage-tabs">
            <!-- 分段控件的白色滑块只在选中项变了、或者挂载时定位；级数变了而选中项没变（删的不是当前级、回填历史记录），
                 滑块还停在原来的位置。级数一变就重建它 -->
            <n-tabs
                :key="store.stageCount"
                :value="store.current"
                type="segment"
                size="small"
                :animated="false"
                @update:value="selectStage"
            >
                <n-tab v-for="(key, index) in store.stages" :key="key" :name="index">
                    <span class="stage-tab">
                        {{ stageName(index) }}
                        <span
                            v-if="store.missing(index).length"
                            class="stage-dot"
                            :title="`还有 ${store.missing(index).length} 项没填`"
                        />
                    </span>
                </n-tab>
            </n-tabs>
            <n-tooltip :delay="300">
                <template #trigger>
                    <button class="icon-btn" aria-label="加一级" @click="store.addStage()">
                        <Plus :size="15" />
                    </button>
                </template>
                加一级
            </n-tooltip>
        </div>

        <div class="stage-field is-block">
            <span class="stage-label">{{ InputParam.ARRANGEMENT }}</span>
            <n-tabs
                :value="cell(InputParam.ARRANGEMENT)"
                type="segment"
                size="small"
                :animated="false"
                @update:value="(value: string) => setText(InputParam.ARRANGEMENT, value)"
            >
                <n-tab v-for="arrangement in ARRANGEMENTS" :key="arrangement" :name="arrangement">
                    {{ arrangement }}
                </n-tab>
            </n-tabs>
        </div>
        <div class="stage-field is-block">
            <span class="stage-label">{{ InputParam.HELIX_HAND }}</span>
            <n-tabs
                :value="cell(InputParam.HELIX_HAND)"
                type="segment"
                size="small"
                :animated="false"
                @update:value="(value: string) => setText(InputParam.HELIX_HAND, value)"
            >
                <n-tab v-for="hand in HANDS" :key="hand" :name="hand">{{ hand }}</n-tab>
            </n-tabs>
        </div>

        <div v-for="parameter in NUMBER_PARAMS" :key="parameter" class="stage-field">
            <span class="stage-label" :class="{ 'is-unused': unused(parameter) }">
                {{ parameter }}
            </span>
            <n-input-number
                :value="numberOf(parameter)"
                size="small"
                :show-button="false"
                placeholder=""
                @update:value="(value: number | null) => setNumber(parameter, value)"
            />
        </div>
        <div v-if="isHelical" class="section-note">
            Helical 级用不到灰掉的三项，但和网页版一样也要填（如 0），不填这一级不算
        </div>
    </div>
</template>

<script setup lang="ts">
// 参数栏的「齿轮级」：一次填一级，分段切换当前级，后面可以加一级、删最后一级。参数名照网页版的英文原名
import { computed } from 'vue'
import { NInputNumber, NPopconfirm, NTab, NTabs, NTooltip } from 'naive-ui'
import { Plus } from '@lucide/vue'
import {
    GearArrangement,
    HelixHand,
    InputParam,
    NUMBER_PARAMS,
    PLANETARY_ONLY_PARAMS,
    stageName
} from '@renderer/constants/gearLoad'
import { useGearLoadStore } from '@renderer/stores/gearLoad'

const ARRANGEMENTS = Object.values(GearArrangement)
const HANDS = Object.values(HelixHand)

const store = useGearLoadStore()

const cell = (parameter: InputParam): string => store.cell(parameter, store.currentKey)

const isHelical = computed(() => cell(InputParam.ARRANGEMENT) === GearArrangement.HELICAL)

const unused = (parameter: InputParam): boolean =>
    isHelical.value && PLANETARY_ONLY_PARAMS.includes(parameter)

const selectStage = (value: string | number): void => {
    store.current = Number(value)
}

const setText = (parameter: InputParam, value: string): void => {
    store.setCell(parameter, store.currentKey, value)
}

// 输入表里是字符串，空串是没填；填了认不出的数（历史记录里可能有）当没填显示
const numberOf = (parameter: InputParam): number | null => {
    const text = cell(parameter).trim()
    const value = Number(text)
    return text && Number.isFinite(value) ? value : null
}

const setNumber = (parameter: InputParam, value: number | null): void => {
    setText(parameter, value === null ? '' : String(value))
}
</script>

<style scoped>
.stage-tabs {
    display: flex;
    align-items: center;
    gap: 6px;
}

.stage-tabs > .n-tabs {
    flex: 1;
    min-width: 0;
}

.stage-tab {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-variant-numeric: tabular-nums;
}

/* 这一级还有参数没填 */
.stage-dot {
    width: 6px;
    height: 6px;
    background: var(--warning);
    border-radius: 999px;
}

/* 参数名在左边，长的折行；数值框在右边 */
.stage-field {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 112px;
    align-items: center;
    column-gap: 10px;
}

.stage-field.is-block {
    grid-template-columns: minmax(0, 1fr);
    row-gap: 6px;
}

.stage-label {
    font-size: 12.5px;
    line-height: 1.35;
    color: var(--text-2);
}

.stage-label.is-unused {
    color: var(--text-3);
}
</style>
