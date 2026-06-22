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
  columns?: number
}

const SECTIONS: SectionDef[] = [
  {
    title: 'Thông tin hành chính',
    icon: 'person',
    columns: 2,
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
    columns: 2,
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
      { key: 'isbn_ut', label: 'Số BHYT' },
      { key: 'lydobnvaonoitru', label: 'Lý do vào nội trú' },
      { key: 'lydobnvaonoitru_code', label: 'Mã lý do vào nội trú' },
      { key: 'huongdieutri_out', label: 'Hướng điều trị ra viện' },
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
      { key: 'chandoantuyenduoi', label: 'Chẩn đoán tuyến dưới', type: 'long' },
      { key: 'chandoantuyenduoi_icd10', label: 'ICD-10 tuyến dưới' },
      { key: 'chandoantuyenduoi_kemtheo', label: 'Chẩn đoán tuyến dưới kèm theo', type: 'long' },
      { key: 'chandoantuyenduoi_kemtheo_icd10', label: 'ICD-10 tuyến dưới kèm theo' },
      { key: 'chandoan_in', label: 'Chẩn đoán vào viện', type: 'long' },
      { key: 'chandoan_in_icd10', label: 'ICD-10 vào viện' },
      { key: 'chandoan_in_kemtheo', label: 'Chẩn đoán vào viện kèm theo', type: 'long' },
      { key: 'chandoan_in_icd10_kemtheo', label: 'ICD-10 vào viện kèm theo' },
      { key: 'chandoan_kb_main', label: 'Chẩn đoán khám bệnh chính', type: 'long' },
      { key: 'chandoan_kb_main_icd10', label: 'ICD-10 khám bệnh chính' },
      { key: 'chandoan_kb_ex', label: 'Chẩn đoán khám bệnh phụ', type: 'long' },
      { key: 'chandoan_kb_ex_icd10', label: 'ICD-10 khám bệnh phụ' },
      { key: 'chandoan_out_main', label: 'Chẩn đoán ra viện chính', type: 'long' },
      { key: 'chandoan_out_main_icd10', label: 'ICD-10 ra viện chính' },
      { key: 'chandoan_out_ex', label: 'Chẩn đoán ra viện phụ', type: 'long' },
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
      { key: 'sub_chandoan_out_main', label: 'Chẩn đoán ra viện chính (phụ)', type: 'long' },
      { key: 'sub_chandoan_out_main_icd10', label: 'ICD-10 ra viện chính (phụ)' },
      { key: 'sub_chandoan_out_ex', label: 'Chẩn đoán ra viện phụ (phụ)', type: 'long' },
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

    try {
      const parsed = evalPythonLiteral(trimmed)
      if (Array.isArray(parsed)) return parsed as Record<string, string>[]
      if (parsed && typeof parsed === 'object') return [parsed as Record<string, string>]
    } catch { /* fall through */ }
  }

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

  const stripped = raw.trim().replace(/^\[\d+\s+mục\]\s*/i, '')

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
    return <span className="text-[13px] text-on-surface">{display || <Empty />}</span>
  }

  if (field.type === 'bool') {
    const display = isEmpty ? 'Không' : value === '0' ? 'Không' : 'Có'
    return (
      <span className={`text-[13px] font-medium ${display === 'Có' ? 'text-primary' : 'text-on-surface-variant'}`}>
        {display}
      </span>
    )
  }

  if (field.type === 'long') {
    if (isEmpty) return <Empty />
    return (
      <p className="text-[13px] text-on-surface leading-relaxed whitespace-pre-wrap col-span-2">{value}</p>
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
  return <span className="text-[13px] text-on-surface">{isEmpty ? <Empty /> : display}</span>
}

function Empty() {
  return <span className="text-xs text-on-surface-variant/40 italic">—</span>
}

function VitalsGrid({ section, data }: { section: SectionDef; data: Record<string, string> }) {
  const bpHigh = data['huyetap_high']
  const bpLow = data['huyetap_low']
  const bpValue = bpHigh && bpLow ? `${formatNumber(bpHigh)}/${formatNumber(bpLow)}` : bpHigh || bpLow || ''

  const vitals = [
    { l: 'Chiều cao', v: data['chieucao'] ? formatNumber(data['chieucao']) : '', u: 'cm' },
    { l: 'Cân nặng', v: data['cannang'] ? formatNumber(data['cannang']) : '', u: 'kg' },
    { l: 'Nhịp tim', v: data['nhiptim'] ? formatNumber(data['nhiptim']) : '', u: 'lần/phút' },
    { l: 'Nhiệt độ', v: data['nhietdo'] ? formatNumber(data['nhietdo']) : '', u: '°C' },
    { l: 'Huyết áp', v: bpValue, u: 'mmHg' },
    { l: 'Nhịp thở', v: data['nhiptho'] ? formatNumber(data['nhiptho']) : '', u: 'lần/phút' },
  ].filter(v => v.v)

  if (vitals.length === 0) return null

  return (
    <div className="bg-white border border-outline-variant rounded-[14px] overflow-hidden shadow-card">
      <div className="flex items-center gap-[9px] px-[18px] py-[14px] border-b border-outline-variant">
        <span className="w-[26px] h-[26px] rounded-[7px] bg-primary-container text-primary flex items-center justify-center flex-none">
          <span className="material-symbols-outlined text-[14px]">{section.icon}</span>
        </span>
        <h4 className="text-[14px] font-bold text-on-surface">{section.title}</h4>
      </div>
      <div className="p-[14px] grid grid-cols-3 gap-[10px]">
        {vitals.map((v) => (
          <div key={v.l} className="border border-outline-variant rounded-[10px] px-[13px] py-[11px] bg-surface-container-low">
            <div className="text-[10px] uppercase tracking-[0.05em] text-on-surface-variant font-semibold">{v.l}</div>
            <div className="flex items-baseline gap-1 mt-[5px]">
              <span className="text-[19px] font-bold text-on-surface">{v.v}</span>
              <span className="text-[11px] text-on-surface-variant">{v.u}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function InlineField({ field, value }: { field: FieldDef; value: string }) {
  return (
    <div className="flex-1 min-w-0 flex gap-3">
      <div className="w-[130px] flex-none">
        <span className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-[0.05em]">
          {field.label}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <FieldValue field={field} value={value} />
      </div>
    </div>
  )
}

function SectionCard({ section, data }: { section: SectionDef; data: Record<string, string> }) {
  const hasAnyValue = section.fields.some((f) => data[f.key])
  if (!hasAnyValue) return null

  const isLongOrTable = (f: FieldDef) =>
    f.type === 'long' || f.type === 'list' || f.type === 'xetnghiem_table' ||
    f.type === 'thuoc_table' || f.type === 'dichvu_table' || f.type === 'cdha_accordion'

  const paired = section.columns === 2

  type RowItem =
    | { kind: 'pair'; fields: FieldDef[] }
    | { kind: 'full'; field: FieldDef }

  const rows: RowItem[] = []
  if (paired) {
    const shortBuf: FieldDef[] = []
    const flush = () => {
      while (shortBuf.length > 0) {
        rows.push({ kind: 'pair', fields: shortBuf.splice(0, 2) })
      }
    }
    for (const f of section.fields) {
      if (!data[f.key]) continue
      if (isLongOrTable(f)) {
        flush()
        rows.push({ kind: 'full', field: f })
      } else {
        shortBuf.push(f)
      }
    }
    flush()
  }

  return (
    <div className="bg-white border border-outline-variant rounded-[14px] overflow-hidden shadow-card">
      <div className="flex items-center gap-[9px] px-[18px] py-[14px] border-b border-outline-variant">
        <span className="w-[26px] h-[26px] rounded-[7px] bg-primary-container text-primary flex items-center justify-center flex-none">
          <span className="material-symbols-outlined text-[14px]">{section.icon}</span>
        </span>
        <h4 className="text-[14px] font-bold text-on-surface">{section.title}</h4>
      </div>
      <div className="px-[18px] pb-3">
        <div className="flex flex-col">
          {paired ? rows.map((row, i) => (
            <div key={i} className="py-[11px] border-b border-[#f3f6fa] last:border-b-0">
              {row.kind === 'pair' ? (
                <div className="flex gap-4">
                  {row.fields.map((f) => (
                    <InlineField key={f.key} field={f} value={data[f.key] ?? ''} />
                  ))}
                  {row.fields.length === 1 && <div className="flex-1" />}
                </div>
              ) : (
                <div className="flex flex-col gap-1 w-full">
                  <span className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-[0.05em]">
                    {row.field.label}
                  </span>
                  <FieldValue field={row.field} value={data[row.field.key] ?? ''} />
                </div>
              )}
            </div>
          )) : section.fields.map((field) => {
            const value = data[field.key] ?? ''
            if (!value) return null
            return (
              <div
                key={field.key}
                className="flex gap-7 py-[11px] border-b border-[#f3f6fa] last:border-b-0"
              >
                {isLongOrTable(field) ? (
                  <div className="flex flex-col gap-1 w-full">
                    <span className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-[0.05em]">
                      {field.label}
                    </span>
                    <FieldValue field={field} value={value} />
                  </div>
                ) : (
                  <>
                    <div className="w-[160px] flex-none">
                      <span className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-[0.05em]">
                        {field.label}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <FieldValue field={field} value={value} />
                    </div>
                  </>
                )}
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
    <div className="flex flex-col gap-4 animate-pulse">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="bg-white border border-outline-variant rounded-[14px] shadow-card p-lg">
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

function extractStage(diag: string): string | null {
  const m = diag.match(/giai\s*đoạn\s*(IV|III|II|I|[0-9]+)/i)
  return m ? `Giai đoạn ${m[1].toUpperCase()}` : null
}

function formatDateTime(raw: string): string {
  if (!raw) return ''
  const d = new Date(raw)
  if (isNaN(d.getTime())) return raw
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${day}/${month}/${year} ${hh}:${mm}`
}

export default function PatientData({ data, loading, error, patientId }: Props) {
  if (loading) return <Skeleton />

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center space-y-md">
          <span className="material-symbols-outlined text-error text-[48px]">error</span>
          <p className="text-title-md font-semibold text-on-surface">{error}</p>
          <p className="text-body-sm text-on-surface-variant">Mã bệnh nhân: {patientId}</p>
        </div>
      </div>
    )
  }

  if (!data) return null

  const patientIdDisplay = data['ma_bn_an'] || patientId || ''
  // const birthYear = data['birthdayyear']
  const mainDiag = data['chandoan_out_main'] || data['chandoan_in'] || data['lydobnvaonoitru'] || ''
  const stageBadge = mainDiag ? extractStage(mainDiag) : null
  const dateIn = formatDateTime(data['medicalrecorddate_in'] || '')
  const dateOut = formatDateTime(data['medicalrecorddate_out'] || '')
  const treatmentDays = data['so_ngay_dieu_tri'] ? data['so_ngay_dieu_tri'].replace(/\.0$/, '') : ''

  return (
    <div className="flex flex-col gap-4">
      {/* Patient banner */}
      <div
        className="bg-white border border-outline-variant rounded-[14px] shadow-card px-[22px] py-[18px] flex justify-between gap-6"
        style={{ borderLeft: '4px solid #2f6fed' }}
      >
        <div className="min-w-0">
          <div className="flex items-center gap-[10px]">
            <span className="text-[24px] font-bold text-on-surface">{patientIdDisplay}</span>
            {stageBadge && (
              <span className="text-[11px] font-semibold text-[#b5544b] bg-[#fdf0ee] border border-[#f3d9d4] rounded-full px-[10px] py-[3px]">
                {stageBadge}
              </span>
            )}
            {/* {birthYear && (
              <span className="text-[12px] text-on-surface-variant">Năm sinh {birthYear}</span>
            )} */}
          </div>
          {mainDiag && (
            <div className="mt-3 text-[13px] leading-relaxed text-on-surface bg-surface-container rounded-[9px] px-[13px] py-[9px]">
              {mainDiag}
            </div>
          )}
        </div>
        <div className="flex-none text-right flex flex-col gap-[7px] text-[12px]">
          {dateIn && (
            <div>
              <span className="text-on-surface-variant">Vào viện&nbsp;</span>
              <b className="text-on-surface">{dateIn}</b>
            </div>
          )}
          {dateOut && (
            <div>
              <span className="text-on-surface-variant">Ra viện&nbsp;</span>
              <b className="text-on-surface">{dateOut}</b>
            </div>
          )}
          {treatmentDays && (
            <div className="self-end mt-[2px]">
              <span className="text-[11px] font-semibold text-primary bg-primary-container rounded-full px-[11px] py-[4px]">
                {treatmentDays} ngày điều trị
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Sections */}
      {SECTIONS.map((section) => {
        if (section.title === 'Sinh hiệu & Nhân trắc') {
          return <VitalsGrid key={section.title} section={section} data={data} />
        }
        return <SectionCard key={section.title} section={section} data={data} />
      })}
    </div>
  )
}
