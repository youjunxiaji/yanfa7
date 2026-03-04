import { defineStore } from 'pinia'

export interface FileInfo {
    name: string
    path: string
    size: number
}

export interface ProcessConfig {
    peakThreshold: number
}

export interface ReportConfig {
    picWidth: number
    picHeight: number
    loadPolarMin: number
    pressPolarMin: number
}

export const useEdgeStressStore = defineStore('edgeStress', {
    state: () => ({
        files: [] as FileInfo[],
        fileType: 'htm' as 'htm' | 'xlsx',
        outputDir: '',

        processConfig: {
            peakThreshold: 0.00001
        } as ProcessConfig,

        reportConfig: {
            picWidth: 10,
            picHeight: 6,
            loadPolarMin: 0,
            pressPolarMin: 0
        } as ReportConfig,

        processStatus: 'idle' as 'idle' | 'processing' | 'done' | 'error',
        processError: '',
        progressCurrent: 0,
        progressTotal: 0,
        stageMessage: '',

        fileNames: [] as string[],
        currentFileName: '',
        stressPosition: 'inner' as 'inner' | 'outer',
        currentColumn: 1,
        columnOptions: [1] as number[],

        previewMap: {} as Record<string, { colIndex: number; path: string }[]>,
        resultColumns: {} as Record<string, number[]>
    }),

    getters: {
        hasFiles: (state) => state.files.length > 0,
        isProcessing: (state) => state.processStatus === 'processing',
        isDone: (state) => state.processStatus === 'done',
        progressPercent: (state) => {
            if (state.progressTotal === 0) return 0
            return Math.round((state.progressCurrent / state.progressTotal) * 100)
        }
    },

    actions: {
        setFiles(newFiles: FileInfo[], type: 'htm' | 'xlsx') {
            this.files = newFiles
            this.fileType = type
        },

        clearFiles() {
            this.files = []
            this.processStatus = 'idle'
            this.progressCurrent = 0
            this.progressTotal = 0
            this.stageMessage = ''
        },

        setProcessStatus(status: 'idle' | 'processing' | 'done' | 'error', error?: string) {
            this.processStatus = status
            if (error) this.processError = error
        },

        updateProgress(current: number, total?: number) {
            this.progressCurrent = current
            if (total !== undefined) this.progressTotal = total
        },

        setResultFileNames(names: string[]) {
            this.fileNames = names
            if (names.length > 0) {
                this.currentFileName = names[0]!
            }
        },

        setColumnOptions(cols: number[]) {
            this.columnOptions = cols
            if (cols.length > 0) {
                this.currentColumn = cols[0]!
            }
        },

        setPreviewMap(map: Record<string, { colIndex: number; path: string }[]>) {
            this.previewMap = map
        },

        setResultColumns(columns: Record<string, number[]>) {
            this.resultColumns = columns
        },

        getPreviewItems(fileName: string): { colIndex: number; path: string }[] {
            const stem = fileName.replace(/\.[^.]+$/, '')
            return this.previewMap[stem] ?? []
        },

        getGroupName(fileName: string): string {
            const stem = fileName.replace(/\.[^.]+$/, '')
            const idx = stem.indexOf('(')
            return idx > 0 ? stem.substring(0, idx).trimEnd() : stem
        },

        getReportBasePath(fileName: string): string {
            const group = this.getGroupName(fileName)
            return `${this.outputDir}/res-output/${group}`
        },

        getColumnsByFile(fileName: string): number[] {
            const stem = fileName.replace(/\.[^.]+$/, '')
            return this.resultColumns[stem] ?? []
        }
    }
})
