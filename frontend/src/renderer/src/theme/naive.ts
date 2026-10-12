import type { GlobalThemeOverrides } from 'naive-ui'

// 和 assets/tokens.css 是同一套设计变量。Naive 要在 JS 里推算悬停、按下等派生色，读不了 CSS 变量，
// 所以这里放一份字面值，两边一起改。textColor2 是控件和表格的文字色，比 tokens 的 --text-2 深一档。
interface Palette {
    panel: string
    subtle: string
    muted: string
    modal: string
    popover: string
    border: string
    borderStrong: string
    divider: string
    text1: string
    text2: string
    text3: string
    text4: string
    accent: string
    accentHover: string
    accentPressed: string
    accentRing: string
    success: string
    successHover: string
    successPressed: string
    warning: string
    warningHover: string
    warningPressed: string
    error: string
    errorHover: string
    errorPressed: string
    hover: string
    pressed: string
    input: string
    inputDisabled: string
    tooltip: string
    segRail: string
    segActive: string
    scrollbar: string
    scrollbarHover: string
    shadow1: string
    shadow2: string
    shadow3: string
}

const LIGHT: Palette = {
    panel: '#ffffff',
    subtle: '#fafafa',
    muted: '#f4f4f5',
    modal: '#ffffff',
    popover: '#ffffff',
    border: '#e4e4e7',
    borderStrong: '#d4d4d8',
    divider: '#ececee',
    text1: '#18181b',
    text2: '#27272a',
    text3: '#71717a',
    text4: '#a1a1aa',
    accent: '#2563eb',
    accentHover: '#3b82f6',
    accentPressed: '#1d4ed8',
    accentRing: 'rgba(37, 99, 235, 0.16)',
    success: '#16a34a',
    successHover: '#22c55e',
    successPressed: '#15803d',
    warning: '#d97706',
    warningHover: '#f59e0b',
    warningPressed: '#b45309',
    error: '#dc2626',
    errorHover: '#ef4444',
    errorPressed: '#b91c1c',
    hover: 'rgba(24, 24, 27, 0.045)',
    pressed: 'rgba(24, 24, 27, 0.08)',
    input: '#ffffff',
    inputDisabled: '#fafafa',
    tooltip: '#18181b',
    segRail: '#f4f4f5',
    segActive: '#ffffff',
    scrollbar: 'rgba(24, 24, 27, 0.2)',
    scrollbarHover: 'rgba(24, 24, 27, 0.32)',
    shadow1: '0 1px 2px rgba(24, 24, 27, 0.06)',
    shadow2: '0 8px 24px rgba(24, 24, 27, 0.1), 0 1px 3px rgba(24, 24, 27, 0.08)',
    shadow3: '0 24px 64px rgba(24, 24, 27, 0.18), 0 0 0 1px rgba(24, 24, 27, 0.06)'
}

const DARK: Palette = {
    panel: '#141416',
    subtle: '#18181b',
    muted: '#1f1f23',
    modal: '#18181b',
    popover: '#1f1f23',
    border: '#2e2e33',
    borderStrong: '#46464d',
    divider: '#222226',
    text1: '#fafafa',
    text2: '#e4e4e7',
    text3: '#a1a1aa',
    text4: '#71717a',
    accent: '#3b82f6',
    accentHover: '#60a5fa',
    accentPressed: '#2563eb',
    accentRing: 'rgba(59, 130, 246, 0.28)',
    success: '#22c55e',
    successHover: '#4ade80',
    successPressed: '#16a34a',
    warning: '#f59e0b',
    warningHover: '#fbbf24',
    warningPressed: '#d97706',
    error: '#ef4444',
    errorHover: '#f87171',
    errorPressed: '#dc2626',
    hover: 'rgba(255, 255, 255, 0.05)',
    pressed: 'rgba(255, 255, 255, 0.09)',
    input: 'rgba(255, 255, 255, 0.03)',
    inputDisabled: 'rgba(255, 255, 255, 0.02)',
    tooltip: '#2a2a2e',
    segRail: 'rgba(255, 255, 255, 0.05)',
    segActive: 'rgba(255, 255, 255, 0.12)',
    scrollbar: 'rgba(255, 255, 255, 0.18)',
    scrollbarHover: 'rgba(255, 255, 255, 0.3)',
    shadow1: '0 1px 2px rgba(0, 0, 0, 0.5)',
    shadow2: '0 8px 24px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.06)',
    shadow3: '0 24px 64px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.07)'
}

const FONT_SANS =
    "'Inter Variable', 'Segoe UI Variable Text', 'Segoe UI', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei UI', 'Microsoft YaHei', sans-serif"
const FONT_MONO = "ui-monospace, 'SF Mono', 'Cascadia Mono', Menlo, Consolas, monospace"

type ButtonOverrides = NonNullable<GlobalThemeOverrides['Button']>

const SOLID_BUTTON_TYPES = ['Primary', 'Info', 'Success', 'Warning', 'Error']
const BUTTON_STATES = ['', 'Hover', 'Pressed', 'Focus', 'Disabled']

// Naive 暗色主题里实色按钮的文字是黑色，统一改成白字
const solidButtonText = (): ButtonOverrides => {
    const vars: Record<string, string> = {}
    for (const type of SOLID_BUTTON_TYPES) {
        for (const state of BUTTON_STATES) {
            vars[`textColor${state}${type}`] = '#ffffff'
        }
    }
    return vars as ButtonOverrides
}

const buildOverrides = (p: Palette): GlobalThemeOverrides => ({
    common: {
        fontFamily: FONT_SANS,
        fontFamilyMono: FONT_MONO,
        fontWeightStrong: '600',
        fontSize: '13px',
        fontSizeMini: '12px',
        fontSizeTiny: '12px',
        fontSizeSmall: '12.5px',
        fontSizeMedium: '13px',
        fontSizeLarge: '14px',
        fontSizeHuge: '15px',
        lineHeight: '1.55',
        heightMini: '18px',
        heightTiny: '22px',
        heightSmall: '28px',
        heightMedium: '32px',
        heightLarge: '36px',
        heightHuge: '40px',
        borderRadius: '6px',
        borderRadiusSmall: '4px',
        primaryColor: p.accent,
        primaryColorHover: p.accentHover,
        primaryColorPressed: p.accentPressed,
        primaryColorSuppl: p.accentHover,
        infoColor: p.accent,
        infoColorHover: p.accentHover,
        infoColorPressed: p.accentPressed,
        infoColorSuppl: p.accentHover,
        successColor: p.success,
        successColorHover: p.successHover,
        successColorPressed: p.successPressed,
        successColorSuppl: p.successHover,
        warningColor: p.warning,
        warningColorHover: p.warningHover,
        warningColorPressed: p.warningPressed,
        warningColorSuppl: p.warningHover,
        errorColor: p.error,
        errorColorHover: p.errorHover,
        errorColorPressed: p.errorPressed,
        errorColorSuppl: p.errorHover,
        textColor1: p.text1,
        textColor2: p.text2,
        textColor3: p.text3,
        textColorDisabled: p.text4,
        placeholderColor: p.text4,
        iconColor: p.text4,
        borderColor: p.border,
        dividerColor: p.divider,
        bodyColor: p.panel,
        cardColor: p.panel,
        tableColor: p.panel,
        modalColor: p.modal,
        popoverColor: p.popover,
        tableHeaderColor: p.panel,
        actionColor: p.subtle,
        tagColor: p.muted,
        tabColor: p.segRail,
        inputColor: p.input,
        inputColorDisabled: p.inputDisabled,
        hoverColor: p.hover,
        pressedColor: p.pressed,
        tableColorHover: p.hover,
        buttonColor2: p.hover,
        buttonColor2Hover: p.pressed,
        buttonColor2Pressed: p.pressed,
        railColor: p.muted,
        progressRailColor: p.muted,
        scrollbarColor: p.scrollbar,
        scrollbarColorHover: p.scrollbarHover,
        boxShadow1: p.shadow1,
        boxShadow2: p.shadow2,
        boxShadow3: p.shadow3
    },
    Button: {
        ...solidButtonText(),
        border: `1px solid ${p.border}`,
        borderHover: `1px solid ${p.borderStrong}`,
        borderPressed: `1px solid ${p.borderStrong}`,
        borderFocus: `1px solid ${p.borderStrong}`,
        textColorHover: p.text1,
        textColorPressed: p.text1,
        textColorFocus: p.text1,
        colorHover: p.hover,
        colorPressed: p.pressed,
        colorFocus: p.hover,
        rippleColor: p.text4,
        colorQuaternaryHover: p.hover,
        colorQuaternaryPressed: p.pressed,
        textColorTextHover: p.text1,
        textColorTextPressed: p.text1,
        textColorTextFocus: p.text1,
        paddingSmall: '0 10px',
        paddingMedium: '0 14px',
        paddingLarge: '0 18px',
        iconSizeSmall: '15px',
        iconSizeMedium: '16px',
        iconSizeLarge: '16px',
        borderRadiusSmall: '6px',
        borderRadiusMedium: '6px',
        borderRadiusLarge: '8px'
    },
    Input: {
        border: `1px solid ${p.border}`,
        borderHover: `1px solid ${p.borderStrong}`,
        borderFocus: `1px solid ${p.accent}`,
        boxShadowFocus: `0 0 0 3px ${p.accentRing}`,
        color: p.input,
        colorFocus: p.input,
        colorDisabled: p.inputDisabled,
        suffixTextColor: p.text3,
        paddingSmall: '0 8px',
        paddingMedium: '0 10px'
    },
    InternalSelection: {
        border: `1px solid ${p.border}`,
        borderHover: `1px solid ${p.borderStrong}`,
        borderFocus: `1px solid ${p.accent}`,
        borderActive: `1px solid ${p.accent}`,
        boxShadowFocus: `0 0 0 3px ${p.accentRing}`,
        boxShadowActive: `0 0 0 3px ${p.accentRing}`,
        color: p.input,
        colorActive: p.input
    },
    DataTable: {
        thColor: p.panel,
        tdColor: p.panel,
        thColorModal: p.modal,
        tdColorModal: p.modal,
        tdColorHover: p.hover,
        tdColorHoverModal: p.hover,
        borderColor: p.divider,
        borderColorModal: p.divider,
        thTextColor: p.text3,
        tdTextColor: p.text2,
        thFontWeight: '500',
        thPaddingSmall: '7px 12px',
        tdPaddingSmall: '7px 12px',
        fontSizeSmall: '13px'
    },
    Tabs: {
        colorSegment: p.segRail,
        tabColorSegment: p.segActive,
        tabTextColorSegment: p.text3,
        tabTextColorActiveSegment: p.text1,
        tabTextColorHoverSegment: p.text1,
        tabFontWeight: '400',
        tabFontWeightActive: '500',
        tabBorderRadius: '6px',
        tabFontSizeSmall: '12.5px',
        tabPaddingSmallSegment: '3px 0'
    },
    Card: {
        borderRadius: '12px',
        paddingMedium: '16px 20px 20px',
        titleFontSizeMedium: '15px',
        titleFontWeight: '600',
        colorModal: p.modal,
        borderColor: p.divider,
        actionColor: p.subtle
    },
    Dialog: {
        color: p.modal,
        titleFontSize: '15px',
        titleFontWeight: '600',
        padding: '20px 24px 18px',
        contentMargin: '8px 0 20px 0',
        closeMargin: '18px 18px 0 0'
    },
    Tooltip: {
        color: p.tooltip,
        textColor: '#fafafa',
        padding: '5px 9px',
        borderRadius: '6px',
        boxShadow: p.shadow2
    },
    Popover: {
        color: p.popover,
        padding: '10px 12px',
        borderRadius: '10px',
        boxShadow: p.shadow2
    },
    Message: {
        padding: '8px 14px',
        borderRadius: '10px',
        fontSize: '13px',
        iconSize: '18px',
        boxShadow: p.shadow2,
        boxShadowInfo: p.shadow2,
        boxShadowSuccess: p.shadow2,
        boxShadowWarning: p.shadow2,
        boxShadowError: p.shadow2,
        boxShadowLoading: p.shadow2
    },
    Progress: {
        railColor: p.muted,
        fillColor: p.accent
    },
    Split: {
        resizableTriggerColor: 'transparent',
        resizableTriggerColorHover: p.accentRing
    }
})

export const lightThemeOverrides = buildOverrides(LIGHT)
export const darkThemeOverrides = buildOverrides(DARK)
