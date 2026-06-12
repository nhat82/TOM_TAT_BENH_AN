export default function Footer() {
  return (
    <footer className="w-full py-md px-xl flex justify-between items-center border-t border-outline-variant bg-white mt-auto">
      <p className="text-[11px] font-medium text-on-surface-variant/60 uppercase tracking-wider">
        © 2026 Hệ thống AI Lâm sàng • Lead Consulting
      </p>
      <div className="flex gap-lg">
        <a href="#" className="text-[11px] text-on-surface-variant hover:text-primary transition-colors">Bảo mật</a>
        <a href="#" className="text-[11px] text-on-surface-variant hover:text-primary transition-colors">Hỗ trợ</a>
      </div>
    </footer>
  )
}
