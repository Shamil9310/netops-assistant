import { Sidebar } from "@/components/sidebar";
import { requireUser } from "@/lib/auth";

const precheck = `show ip bgp summary
show run | sec router bgp
show ip route 10.246.150.0/24
ping 10.246.150.6 source loopback0`;

const config = `conf t
router bgp 65430
 neighbor 10.246.150.6 remote-as 65430
 neighbor 10.246.150.6 description UPLINK_DC4
 address-family ipv4 unicast
  neighbor 10.246.150.6 activate
 exit-address-family
end`;

const rollback = `conf t
router bgp 65430
 no neighbor 10.246.150.6 remote-as 65430
end`;

const savedPlans = [
  { id: 1, tpl: "bgp",  icon: "⇄", title: "WA00468580 — RST-DC4-BGW1 BGP Uplink",    sub: "7 апр 2026 · 01:00–03:00" },
  { id: 2, tpl: "vlan", icon: "⛓", title: "SR11600012 — VLAN 300 на транке",           sub: "4 апр 2026 · 23:00–01:00" },
  { id: 3, tpl: "ospf", icon: "↺", title: "Смена метрики OSPF зоны 0",                sub: "1 апр 2026 · 02:00–04:00" },
];

export default async function PlansPage() {
  const user = await requireUser();

  return (
    <div className="shell">
      <Sidebar user={user} />

      {/* Filter col */}
      <aside className="filter-col">
        <div className="filter-col-title">Шаблон</div>

        <div className="filter-group">
          <div className="filter-group-title">Тип</div>
          <button className="filter-chip active">
            <span className="chip-dot" style={{ background: "var(--text-2)" }} /> Все планы
            <span className="chip-count">3</span>
          </button>
          <button className="filter-chip">
            <span className="chip-dot" style={{ background: "var(--green)" }} /> BGP
            <span className="chip-count">1</span>
          </button>
          <button className="filter-chip">
            <span className="chip-dot" style={{ background: "var(--amber)" }} /> OSPF
            <span className="chip-count">1</span>
          </button>
          <button className="filter-chip">
            <span className="chip-dot" style={{ background: "var(--blue)" }} /> VLAN
            <span className="chip-count">1</span>
          </button>
          <button className="filter-chip">
            <span className="chip-dot" style={{ background: "var(--purple)" }} /> ACL
            <span className="chip-count">0</span>
          </button>
        </div>

        <div className="filter-divider" />

        <div className="focus-note">
          <div className="focus-note-label">Подсказка</div>
          <p>Выбери шаблон, заполни параметры — команды сформируются автоматически.</p>
        </div>
      </aside>

      {/* Content */}
      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Планы изменений</div>
            <div className="page-sub">Шаблоны и готовые планы работ</div>
          </div>
          <div className="toolbar">
            <button className="btn btn-primary">+ Новый план</button>
          </div>
        </div>

        {/* Saved plans */}
        <div className="section-label">Сохранённые планы</div>
        <div className="plan-list" style={{ marginBottom: 32 }}>
          {savedPlans.map((p) => (
            <div key={p.id} className="plan-item">
              <div className={`plan-icon ${p.tpl}`}>{p.icon}</div>
              <div className="plan-info">
                <div className="plan-title">{p.title}</div>
                <div className="plan-sub">{p.sub}</div>
              </div>
              <div className="plan-actions">
                <button className="export-btn" style={{ padding: "5px 9px" }}>📕 PDF</button>
                <button className="btn btn-sm">Открыть</button>
                <button className="btn btn-sm btn-danger">✕</button>
              </div>
            </div>
          ))}
        </div>

        {/* New plan form */}
        <div className="section-label">Новый план</div>
        <div className="plan-form-wrap">
          <div className="plan-form-header">
            <div className="plan-form-title">BGP — параметры</div>
            <div className="tpl-tabs">
              <button className="ttab active">BGP</button>
              <button className="ttab">OSPF</button>
              <button className="ttab">VLAN</button>
              <button className="ttab">ACL</button>
            </div>
          </div>
          <div className="plan-form-body">
            <div className="form-grid" style={{ marginBottom: 16 }}>
              <div className="field-row">
                <div className="field">
                  <label className="field-label">Устройство</label>
                  <input type="text" defaultValue="RST-DC4-BGW1" />
                </div>
                <div className="field">
                  <label className="field-label">Окно работ</label>
                  <input type="text" defaultValue="01:00–03:00" />
                </div>
              </div>
              <div className="field-row">
                <div className="field">
                  <label className="field-label">Local AS</label>
                  <input type="text" defaultValue="65430" />
                </div>
                <div className="field">
                  <label className="field-label">Remote AS</label>
                  <input type="text" defaultValue="65430" />
                </div>
              </div>
              <div className="field-row">
                <div className="field">
                  <label className="field-label">IP соседа</label>
                  <input type="text" defaultValue="10.246.150.6" />
                </div>
                <div className="field">
                  <label className="field-label">Описание</label>
                  <input type="text" defaultValue="UPLINK_DC4" />
                </div>
              </div>
            </div>

            <div className="form-actions" style={{ marginBottom: 20 }}>
              <button className="btn btn-ghost">Очистить</button>
              <button className="btn btn-primary">Сформировать →</button>
            </div>

            {/* Code panes */}
            <div className="plan-panes">
              <div className="code-wrap">
                <div className="code-head">
                  <div className="code-dots">
                    <div className="code-dot r" /><div className="code-dot y" /><div className="code-dot g" />
                  </div>
                  <span className="code-head-label precheck">Pre-check</span>
                </div>
                <pre className="code">{precheck}</pre>
              </div>
              <div className="code-wrap">
                <div className="code-head">
                  <div className="code-dots">
                    <div className="code-dot r" /><div className="code-dot y" /><div className="code-dot g" />
                  </div>
                  <span className="code-head-label config">Конфигурация</span>
                </div>
                <pre className="code">{config}</pre>
              </div>
              <div className="code-wrap">
                <div className="code-head">
                  <div className="code-dots">
                    <div className="code-dot r" /><div className="code-dot y" /><div className="code-dot g" />
                  </div>
                  <span className="code-head-label rollback">Rollback</span>
                </div>
                <pre className="code">{rollback}</pre>
              </div>
            </div>

            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <button className="btn btn-primary btn-sm">Сохранить план</button>
              <button className="export-btn">📄 TXT</button>
              <button className="export-btn">📝 MD</button>
              <button className="export-btn">📘 DOCX</button>
              <button className="export-btn">📕 PDF</button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
