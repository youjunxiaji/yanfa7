// 工具在页面图标和首页卡片上的色调，对应 tokens.css 的品牌蓝、绿、琥珀三组变量
export enum ToolTone {
    BLUE = 'blue',
    GREEN = 'green',
    AMBER = 'amber'
}

// 边缘应力文件表里单个文件的状态，由解析进度推出来（UI Skill 界面标准第八节）
export enum FileStatus {
    IDLE = 'idle',
    QUEUED = 'queued',
    PROCESSING = 'processing',
    DONE = 'done',
    SKIPPED = 'skipped',
    ERROR = 'error'
}
