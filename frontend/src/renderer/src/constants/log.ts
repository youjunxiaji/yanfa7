// 「日志」页的级别，和 backend/common/constants.py 的 LogLevel 一致
export enum LogLevel {
    INFO = 'INFO',
    WARNING = 'WARNING',
    ERROR = 'ERROR'
}

// 一条日志从哪来，和 backend/common/constants.py 的 LogSource 一致
export enum LogSource {
    BACKEND = '后端',
    REQUEST = '请求',
    UI = '界面'
}

export const LOG_LEVEL_LABEL: Record<LogLevel, string> = {
    [LogLevel.INFO]: '信息',
    [LogLevel.WARNING]: '警告',
    [LogLevel.ERROR]: '错误'
}

// 按级别筛选时从低到高比：选「警告」时警告和错误都显示
export const LOG_LEVEL_RANK: Record<LogLevel, number> = {
    [LogLevel.INFO]: 0,
    [LogLevel.WARNING]: 1,
    [LogLevel.ERROR]: 2
}
