type FieldType = 'text' | 'long' | 'list' | 'gender' | 'bool' | 'xetnghiem_table' | 'cdha_accordion' | 'thuoc_table' | 'dichvu_table'

interface FieldDef {
  key: string
  label: string
  type?: FieldType
  unit?: string
}

interface SectionDef {
  title: string
  icon: string
  fields: FieldDef[]
}

const SECTIONS: SectionDef[] = [
  {
    title: 'Thông tin hành chính',
    icon: 'person',
    fields: [
      { key: 'ma_bn_an', label: 'Mã bệnh án' },
      { key: 'ho_ten', label: 'Họ tên' },
      { key: 'cccd', label: 'CCCD/CMND' },
      { key: 'dm_gioitinhid', label: 'Giới tính', type: 'gender' },
      { key: 'birthdayyear', label: 'Năm sinh' },
      { key: 'dm_tinhcode', label: 'Mã tỉnh/TP' },
    ],
  },
  {
    title: 'Thông tin nhập/xuất viện',
    icon: 'local_hospital',
    fields: [
      { key: 'dm_medicalrecordtypeid', label: 'Loại hồ sơ' },
      { key: 'dm_hinhthucvaovienid', label: 'Hình thức vào viện' },
      { key: 'medicalrecorddate_in', label: 'Ngày vào viện' },
      { key: 'medicalrecorddate_out', label: 'Ngày ra viện' },
      { key: 'so_ngay_dieu_tri', label: 'Số ngày điều trị' },
      { key: 'departmentid', label: 'Khoa' },
      { key: 'roomid', label: 'Phòng' },
      { key: 'bedid', label: 'Giường' },
      { key: 'medicalrecorddate_kb', label: 'Ngày khám bệnh' },
      { key: 'lydobnvaonoitru', label: 'Lý do vào nội trú' },
      { key: 'lydobnvaonoitru_code', label: 'Mã lý do vào nội trú' },
      { key: 'huongdieutri_out', label: 'Hướng điều trị ra viện' },
      { key: 'isbn_ut', label: 'Số BHYT' },
    ],
  },
  {
    title: 'Sinh hiệu & Nhân trắc',
    icon: 'monitor_heart',
    fields: [
      { key: 'chieucao', label: 'Chiều cao', unit: 'cm' },
      { key: 'cannang', label: 'Cân nặng', unit: 'kg' },
      { key: 'nhiptim', label: 'Nhịp tim', unit: 'lần/phút' },
      { key: 'nhietdo', label: 'Nhiệt độ', unit: '°C' },
      { key: 'huyetap_high', label: 'Huyết áp tâm thu', unit: 'mmHg' },
      { key: 'huyetap_low', label: 'Huyết áp tâm trương', unit: 'mmHg' },
      { key: 'nhiptho', label: 'Nhịp thở', unit: 'lần/phút' },
    ],
  },
  {
    title: 'Chẩn đoán',
    icon: 'diagnosis',
    fields: [
      { key: 'lydodenkham', label: 'Lý do đến khám', type: 'long' },
      { key: 'chandoantuyenduoi', label: 'CĐ tuyến dưới', type: 'long' },
      { key: 'chandoantuyenduoi_icd10', label: 'ICD-10 tuyến dưới' },
      { key: 'chandoantuyenduoi_kemtheo', label: 'CĐ tuyến dưới kèm theo', type: 'long' },
      { key: 'chandoantuyenduoi_kemtheo_icd10', label: 'ICD-10 tuyến dưới kèm theo' },
      { key: 'chandoan_in', label: 'CĐ vào viện', type: 'long' },
      { key: 'chandoan_in_icd10', label: 'ICD-10 vào viện' },
      { key: 'chandoan_in_kemtheo', label: 'CĐ vào viện kèm theo', type: 'long' },
      { key: 'chandoan_in_icd10_kemtheo', label: 'ICD-10 vào viện kèm theo' },
      { key: 'chandoan_kb_main', label: 'CĐ khám bệnh chính', type: 'long' },
      { key: 'chandoan_kb_main_icd10', label: 'ICD-10 khám bệnh chính' },
      { key: 'chandoan_kb_ex', label: 'CĐ khám bệnh phụ', type: 'long' },
      { key: 'chandoan_kb_ex_icd10', label: 'ICD-10 khám bệnh phụ' },
      { key: 'chandoan_out_main', label: 'CĐ ra viện chính', type: 'long' },
      { key: 'chandoan_out_main_icd10', label: 'ICD-10 ra viện chính' },
      { key: 'chandoan_out_ex', label: 'CĐ ra viện phụ', type: 'long' },
      { key: 'chandoan_out_ex_icd10', label: 'ICD-10 ra viện phụ' },
    ],
  },
  {
    title: 'Lâm sàng',
    icon: 'stethoscope',
    fields: [
      { key: 'lydovaovien', label: 'Lý do vào viện', type: 'long' },
      { key: 'quatrinhbenhly', label: 'Quá trình bệnh lý', type: 'long' },
      { key: 'tiensubenh', label: 'Tiền sử bệnh', type: 'long' },
      { key: 'tomtatketquacls', label: 'Tóm tắt kết quả CLS', type: 'long' },
      { key: 'quatrinhbenhlyvadienbienlamsang', label: 'Diễn biến lâm sàng', type: 'long' },
    ],
  },
  {
    title: 'Điều trị',
    icon: 'medication',
    fields: [
      { key: 'phuongphapdieutri', label: 'Phương pháp điều trị', type: 'long' },
      { key: 'isphauthuat', label: 'Có phẫu thuật', type: 'bool' },
      { key: 'isthuthuat', label: 'Có thủ thuật', type: 'bool' },
      { key: 'pttt', label: 'Chi tiết phẫu thuật/thủ thuật', type: 'long' },
      { key: 'tinhtrangnguoiravien', label: 'Tình trạng ra viện', type: 'long' },
      { key: 'huongdieutritieptheo', label: 'Hướng điều trị tiếp theo', type: 'long' },
    ],
  },
  {
    title: 'Hồ sơ phụ',
    icon: 'folder_copy',
    fields: [
      { key: 'sub_patientrecorddate_begin', label: 'Ngày bắt đầu (phụ)' },
      { key: 'sub_patientrecorddate_end', label: 'Ngày kết thúc (phụ)' },
      { key: 'sub_chandoan_out_main', label: 'CĐ ra viện chính (phụ)', type: 'long' },
      { key: 'sub_chandoan_out_main_icd10', label: 'ICD-10 ra viện chính (phụ)' },
      { key: 'sub_chandoan_out_ex', label: 'CĐ ra viện phụ (phụ)', type: 'long' },
      { key: 'sub_chandoan_out_ex_icd10', label: 'ICD-10 ra viện phụ (phụ)' },
      { key: 'sub_dm_ketquadieutriid', label: 'Kết quả điều trị (phụ)' },
      { key: 'sub_dm_patientrecordstatusid', label: 'Trạng thái hồ sơ (phụ)' },
      { key: 'sub_dm_patientrecordtypeid', label: 'Loại hồ sơ (phụ)' },
      { key: 'sub_medicalrecordid_out', label: 'Mã hồ sơ ra viện (phụ)' },
    ],
  },
  {
    title: 'Xét nghiệm',
    icon: 'biotech',
    fields: [
      { key: 'ds_xet_nghiem', label: 'Danh sách xét nghiệm', type: 'xetnghiem_table' },
    ],
  },
  {
    title: 'Chẩn đoán hình ảnh',
    icon: 'radiology',
    fields: [
      { key: 'ds_cdha', label: 'Danh sách chẩn đoán hình ảnh', type: 'cdha_accordion' },
    ],
  },
  {
    title: 'Thuốc',
    icon: 'pill',
    fields: [
      { key: 'so_thuoc', label: 'Tổng số thuốc' },
      { key: 'ds_thuoc', label: 'Danh sách thuốc', type: 'thuoc_table' },
    ],
  },
  {
    title: 'Dịch vụ',
    icon: 'medical_services',
    fields: [
      { key: 'so_dich_vu', label: 'Tổng số dịch vụ' },
      { key: 'ds_dich_vu', label: 'Danh sách dịch vụ', type: 'dichvu_table' },
    ],
  },
]

const XN_HEADER_MAP: Record<string, string> = {
  ten_xn: 'Tên xét nghiệm',
  ket_qua: 'Kết quả',
  don_vi: 'Đơn vị',
  khoang_bt: 'Khoảng bình thường',
  ngay: 'Ngày',
}

const THUOC_HEADER_MAP: Record<string, string> = {
  ten: 'Tên thuốc',
  duong_dung: 'Đường dùng',
  lieu_dung: 'Liều dùng',
  lan_dung: 'Lần dùng',
  don_vi: 'Đơn vị',
}

const DICHVU_HEADER_MAP: Record<string, string> = {
  ten: 'Tên dịch vụ',
  ngay: 'Ngày',
  so_luong: 'Số lượng',
  don_gia: 'Đơn giá',
}

function evalPythonLiteral(s: string): unknown {
  const js = s
    .replace(/\bNone\b/g, 'null')
    .replace(/\bTrue\b/g, 'true')
    .replace(/\bFalse\b/g, 'false')
  // eslint-disable-next-line no-new-func
  return new Function(`return (${js})`)()
}

function parsePyDictList(raw: string): Record<string, string>[] | null {
  const trimmed = raw.trim()

  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    // Fast path: simple single-quote swap (works unless values contain apostrophes)
    try {
      const json = trimmed
        .replace(/'/g, '"')
        .replace(/\bNone\b/g, 'null')
        .replace(/\bTrue\b/g, 'true')
        .replace(/\bFalse\b/g, 'false')
      const parsed = JSON.parse(json)
      if (Array.isArray(parsed)) return parsed
      if (parsed && typeof parsed === 'object') return [parsed as Record<string, string>]
    } catch { /* fall through */ }

    // Robust path: handles mixed quotes and apostrophes (e.g. "Acetate Ringer's")
    try {
      const parsed = evalPythonLiteral(trimmed)
      if (Array.isArray(parsed)) return parsed as Record<string, string>[]
      if (parsed && typeof parsed === 'object') return [parsed as Record<string, string>]
    } catch { /* fall through */ }
  }

  // Newline-separated dicts
  const lines = trimmed.split('\n').map((l) => l.trim()).filter((l) => l.startsWith('{'))
  if (lines.length > 0) {
    const objs: Record<string, string>[] = []
    for (const line of lines) {
      try {
        const obj = evalPythonLiteral(line)
        if (obj && typeof obj === 'object') objs.push(obj as Record<string, string>)
      } catch { /* skip */ }
    }
    if (objs.length > 0) return objs
  }

  return null
}

function parseDictListToTable(
  raw: string,
  headerMap: Record<string, string>
): { headers: string[]; rows: string[][] } | null {
  if (!raw?.trim()) return null
  const lower = raw.trim().toLowerCase()
  if (lower === 'null' || lower === 'none' || lower === 'nan') return null

  // Strip "[N mục]" count prefix (e.g. "[543 mục]  {'ten': ...}")
  const stripped = raw.trim().replace(/^\[\d+\s+mục\]\s*/i, '')

  // Try Python-style dict/list (most common format from DB)
  const pyObjs = parsePyDictList(stripped)
  if (pyObjs && pyObjs.length > 0) {
    const keys = Object.keys(pyObjs[0])
    const headers = keys.map((k) => headerMap[k] ?? k)
    const NULL_VALS = new Set(['', '0001-01-01t00:00:00', '0001-01-01 00:00:00'])
    const rows = pyObjs.map((obj) =>
      keys.map((k) => {
        const v = String(obj[k] ?? '')
        return NULL_VALS.has(v.toLowerCase()) ? '' : v
      })
    )
    return { headers, rows }
  }

  // Try JSON array of objects
  try {
    const parsed = JSON.parse(stripped)
    if (Array.isArray(parsed) && parsed.length > 0 && typeof parsed[0] === 'object') {
      const keys = Object.keys(parsed[0])
      const headers = keys.map((k) => headerMap[k] ?? k)
      const rows = parsed.map((item: Record<string, unknown>) =>
        keys.map((k) => String(item[k] ?? ''))
      )
      return { headers, rows }
    }
  } catch { /* not JSON */ }

  const lines = stripped.split('\n').filter((l) => l.trim())
  if (lines.length < 2) return null

  // Detect delimiter: pipe, semicolon, or tab
  const firstLine = lines[0]
  let delimiter: string | null = null
  if (firstLine.includes('|')) delimiter = '|'
  else if (firstLine.includes(';')) delimiter = ';'
  else if (firstLine.includes('\t')) delimiter = '\t'

  if (delimiter) {
    const allRows = lines.map((l) => l.split(delimiter!).map((c) => c.trim()))
    if (allRows[0].length > 1) {
      return {
        headers: allRows[0],
        rows: allRows.slice(1).filter((r) => r.some((c) => c)),
      }
    }
  }

  return null
}

function DataTable({ value, headerMap }: { value: string; headerMap: Record<string, string> }) {
  const parsed = parseDictListToTable(value, headerMap)

  if (!parsed) {
    return <Empty />
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-outline-variant">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-surface-container-low">
            {parsed.headers.map((h, i) => (
              <th
                key={i}
                className="text-left px-sm py-xs font-semibold text-on-surface-variant border-b border-outline-variant text-[11px] uppercase tracking-wide whitespace-nowrap"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {parsed.rows.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-surface-container-low/30'}>
              {row.map((cell, j) => (
                <td key={j} className="px-sm py-xs text-on-surface border-b border-outline-variant/50 align-top">
                  {cell || <span className="text-on-surface-variant/40 italic">—</span>}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function formatDMY(raw: string): string {
  const d = new Date(raw)
  if (isNaN(d.getTime())) return raw
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  return `${day}/${month}/${year}`
}

function CdhaAccordion({ value }: { value: string }) {
  const items = parsePyDictList(value)

  if (!items) {
    return (
      <pre className="text-xs text-on-surface font-mono bg-surface-container-low rounded-lg p-md leading-relaxed whitespace-pre-wrap break-all col-span-2">
        {value}
      </pre>
    )
  }

  return (
    <div className="col-span-2 flex flex-col gap-xs">
      {items.map((item, i) => {
        const rawDate = item['ngay'] || item['Ngày'] || ''
        const date = rawDate ? formatDMY(rawDate) : `#${i + 1}`
        const description = item['mo_ta'] || item['Mô tả'] || ''
        return (
          <details key={i} className="group rounded-lg border border-outline-variant overflow-hidden">
            <summary className="flex items-center justify-between gap-md px-md py-sm cursor-pointer select-none bg-surface-container-low/50 hover:bg-surface-container-low list-none">
              <span className="text-xs font-semibold text-on-surface">{date}</span>
              <span className="material-symbols-outlined text-[16px] text-on-surface-variant transition-transform group-open:rotate-180">
                expand_more
              </span>
            </summary>
            <div className="px-md py-sm bg-white text-sm text-on-surface leading-relaxed whitespace-pre-wrap">
              {description || <Empty />}
            </div>
          </details>
        )
      })}
    </div>
  )
}

function formatNumber(val: string): string {
  const n = parseFloat(val)
  if (isNaN(n)) return val
  return Number.isInteger(n) ? String(n) : val.replace(/\.0$/, '')
}

function FieldValue({ field, value }: { field: FieldDef; value: string }) {
  const isEmpty = !value

  if (field.type === 'gender') {
    const display = value === '1' ? 'Nam' : value === '2' ? 'Nữ' : value
    return <span className="text-sm text-on-surface">{display || <Empty />}</span>
  }

  if (field.type === 'bool') {
    const display = isEmpty ? 'Không' : value === '0' ? 'Không' : 'Có'
    return (
      <span className={`text-sm font-medium ${display === 'Có' ? 'text-primary' : 'text-on-surface-variant'}`}>
        {display}
      </span>
    )
  }

  if (field.type === 'long') {
    if (isEmpty) return <Empty />
    return (
      <p className="text-sm text-on-surface leading-relaxed whitespace-pre-wrap col-span-2">{value}</p>
    )
  }

  if (field.type === 'xetnghiem_table') {
    if (isEmpty) return <Empty />
    return <DataTable value={value} headerMap={XN_HEADER_MAP} />
  }

  if (field.type === 'thuoc_table') {
    if (isEmpty) return <Empty />
    return <DataTable value={value} headerMap={THUOC_HEADER_MAP} />
  }

  if (field.type === 'dichvu_table') {
    if (isEmpty) return <Empty />
    return <DataTable value={value} headerMap={DICHVU_HEADER_MAP} />
  }

  if (field.type === 'cdha_accordion') {
    if (isEmpty) return <Empty />
    return <CdhaAccordion value={value} />
  }

  if (field.type === 'list') {
    if (isEmpty) return <Empty />
    return (
      <pre className="text-xs text-on-surface font-mono bg-surface-container-low rounded-lg p-md leading-relaxed whitespace-pre-wrap break-all col-span-2">
        {value}
      </pre>
    )
  }

  const display = field.unit ? `${formatNumber(value)} ${field.unit}` : value
  return <span className="text-sm text-on-surface">{isEmpty ? <Empty /> : display}</span>
}

function Empty() {
  return <span className="text-xs text-on-surface-variant/40 italic">—</span>
}

function SectionCard({ section, data }: { section: SectionDef; data: Record<string, string> }) {
  const hasAnyValue = section.fields.some((f) => data[f.key])
  if (!hasAnyValue) return null

  return (
    <div className="bg-white border border-outline-variant rounded-xl overflow-hidden">
      <div className="px-lg py-md border-b border-outline-variant flex items-center gap-md bg-surface-container-low/50">
        <span className="material-symbols-outlined text-primary text-[18px]">{section.icon}</span>
        <h4 className="text-title-sm font-semibold text-on-surface">{section.title}</h4>
      </div>
      <div className="p-lg">
        <div className="grid grid-cols-1 gap-md">
          {section.fields.map((field) => {
            const value = data[field.key] ?? ''
            const isLongOrList = field.type === 'long' || field.type === 'list' || field.type === 'xetnghiem_table' || field.type === 'thuoc_table' || field.type === 'dichvu_table'
            return (
              <div
                key={field.key}
                className={isLongOrList ? 'flex flex-col gap-xs' : 'grid grid-cols-[180px_1fr] gap-md items-start'}
              >
                <span className="text-[11px] font-semibold text-on-surface-variant uppercase tracking-wider shrink-0 pt-0.5">
                  {field.label}
                </span>
                <FieldValue field={field} value={value} />
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function Skeleton() {
  return (
    <div className="col-span-12 lg:col-span-8 flex flex-col gap-lg animate-pulse">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="bg-white border border-outline-variant rounded-xl p-lg">
          <div className="h-4 bg-surface-container rounded w-40 mb-md" />
          <div className="space-y-sm">
            {[...Array(4)].map((_, j) => (
              <div key={j} className="h-3 bg-surface-container rounded w-full" />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

interface Props {
  data: Record<string, string> | null
  loading: boolean
  error: string
  patientId?: string
}

export default function PatientData({ data, loading, error, patientId }: Props) {
  if (loading) return <Skeleton />

  if (error) {
    return (
      <div className="col-span-12 lg:col-span-8 flex items-center justify-center">
        <div className="text-center space-y-md">
          <span className="material-symbols-outlined text-error text-[48px]">error</span>
          <p className="text-title-md font-semibold text-on-surface">{error}</p>
          <p className="text-body-sm text-on-surface-variant">Mã bệnh nhân: {patientId}</p>
        </div>
      </div>
    )
  }

  if (!data) return null

  const name = data['ho_ten'] || patientId
  const gender = data['dm_gioitinhid'] === '1' ? 'Nam' : data['dm_gioitinhid'] === '2' ? 'Nữ' : ''
  const birthYear = data['birthdayyear']
  const mainDiag = data['chandoan_out_main'] || data['chandoan_in'] || ''

  return (
    <section className="col-span-12 lg:col-span-8 flex flex-col gap-lg">
      {/* Patient banner */}
      <div className="bg-white border border-outline-variant rounded-xl p-lg flex items-start justify-between">
        <div>
          <div className="flex items-center gap-md mb-xs">
            <span className="material-symbols-outlined text-primary">account_circle</span>
            <h3 className="text-headline-sm font-bold text-on-surface">{name}</h3>
            {gender && (
              <span className="text-xs font-semibold px-sm py-0.5 rounded-full bg-primary/10 text-primary">{gender}</span>
            )}
          </div>
          <div className="flex items-center gap-lg text-body-sm text-on-surface-variant flex-wrap">
            <span>Mã: <strong className="text-on-surface">{data['ma_bn_an'] || patientId}</strong></span>
            {birthYear && <span>Năm sinh: <strong className="text-on-surface">{birthYear}</strong></span>}
            {mainDiag && <span className="text-error font-medium">{mainDiag}</span>}
          </div>
        </div>
        <div className="text-right text-xs text-on-surface-variant space-y-xs">
          {data['medicalrecorddate_in'] && <p>Vào viện: <strong>{data['medicalrecorddate_in']}</strong></p>}
          {data['medicalrecorddate_out'] && <p>Ra viện: <strong>{data['medicalrecorddate_out']}</strong></p>}
          {data['so_ngay_dieu_tri'] && <p>Số ngày: <strong>{data['so_ngay_dieu_tri'].replace(/\.0$/, '')}</strong></p>}
        </div>
      </div>

      {/* All sections */}
      {SECTIONS.map((section) => (
        <SectionCard key={section.title} section={section} data={data} />
      ))}
    </section>
  )
}
