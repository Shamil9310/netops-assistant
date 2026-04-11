import { formatDateLabel } from "@/lib/date-format";
import type {
  DashboardAnalyticsResponse,
  DashboardDatePoint,
  DashboardServicePoint,
  DashboardWeekPoint,
} from "@/lib/api";

type Props = {
  analytics: DashboardAnalyticsResponse;
};

const LINE_WIDTH = 960;
const LINE_HEIGHT = 240;
const CHART_PADDING = 18;

function formatCompactCount(value: number): string {
  return new Intl.NumberFormat("ru-RU").format(value);
}

function buildPointPath(points: number[], width: number, height: number, padding: number): string {
  if (points.length === 0) {
    return "";
  }
  const max = Math.max(...points, 1);
  const step = points.length === 1 ? 0 : (width - padding * 2) / (points.length - 1);

  return points
    .map((value, index) => {
      const x = padding + step * index;
      const y = height - padding - (value / max) * (height - padding * 2);
      return `${x},${y}`;
    })
    .join(" ");
}

function DashboardMetric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="report-block" style={{ padding: 18, minHeight: 150 }}>
      <div className="badge task">{label}</div>
      <div
        className="page-title"
        style={{
          fontSize: "2.4rem",
          marginTop: 12,
          WebkitTextFillColor: "initial",
          background: "none",
          color: "var(--text)",
        }}
      >
        {value}
      </div>
      <div className="page-sub">{hint}</div>
    </div>
  );
}

function TrendChart({ points }: { points: DashboardDatePoint[] }) {
  const values = points.map((point) => point.total);
  const line = buildPointPath(values, LINE_WIDTH, LINE_HEIGHT, CHART_PADDING);
  const maxValue = Math.max(...values, 1);
  const firstPoint = points[0];
  const middlePoint = points[Math.floor(points.length / 2)];
  const lastPoint = points[points.length - 1];

  return (
    <div className="dashboard-chart">
      <div className="dashboard-chart-head">
        <div>
          <div className="dashboard-chart-title">История по дням</div>
          <div className="dashboard-chart-sub">Заявки за последние 30 дней</div>
        </div>
        <div className="dashboard-chart-value">{formatCompactCount(values.reduce((sum, value) => sum + value, 0))}</div>
      </div>

      <svg viewBox={`0 0 ${LINE_WIDTH} ${LINE_HEIGHT}`} className="dashboard-chart-svg" role="img" aria-label="График заявок по дням">
        <line x1={CHART_PADDING} y1={LINE_HEIGHT - CHART_PADDING} x2={LINE_WIDTH - CHART_PADDING} y2={LINE_HEIGHT - CHART_PADDING} stroke="rgba(182, 194, 214, 0.18)" />
        {values.map((value, index) => {
          const x = CHART_PADDING + (points.length === 1 ? 0 : ((LINE_WIDTH - CHART_PADDING * 2) / (points.length - 1)) * index);
          const y = LINE_HEIGHT - CHART_PADDING - (value / maxValue) * (LINE_HEIGHT - CHART_PADDING * 2);
          return <circle key={`${points[index]?.date ?? index}`} cx={x} cy={y} r="3.5" fill="var(--cyan)" />;
        })}
        {line && <polyline fill="none" stroke="rgba(127, 216, 234, 0.9)" strokeWidth="3.5" strokeLinejoin="round" strokeLinecap="round" points={line} />}
      </svg>

      <div className="dashboard-axis">
        <span>{firstPoint ? formatDateLabel(firstPoint.date) : "—"}</span>
        <span>{middlePoint ? formatDateLabel(middlePoint.date) : "—"}</span>
        <span>{lastPoint ? formatDateLabel(lastPoint.date) : "—"}</span>
      </div>
    </div>
  );
}

function WeeklyBarsChart({ points }: { points: DashboardWeekPoint[] }) {
  const maxValue = Math.max(...points.map((point) => point.total), 1);

  return (
    <div className="dashboard-chart">
      <div className="dashboard-chart-head">
        <div>
          <div className="dashboard-chart-title">Недели</div>
          <div className="dashboard-chart-sub">Историческая динамика по неделям</div>
        </div>
        <div className="dashboard-chart-value">{formatCompactCount(points.reduce((sum, point) => sum + point.total, 0))}</div>
      </div>

      <div className="dashboard-bars">
        {points.map((point) => {
          const height = Math.max(8, (point.total / maxValue) * 100);
          return (
            <div key={point.week_start} className="dashboard-bar-card">
              <div className="dashboard-bar-meta">
                <span>{formatDateLabel(point.week_start)}</span>
                <span>{formatCompactCount(point.total)}</span>
              </div>
              <div className="dashboard-bar-track">
                <div className="dashboard-bar-fill" style={{ height: `${height}%` }} />
              </div>
              <div className="dashboard-bar-foot">{formatDateLabel(point.week_end)}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ServiceBreakdownChart({ points }: { points: DashboardServicePoint[] }) {
  const maxValue = Math.max(...points.map((point) => point.total), 1);

  return (
    <div className="dashboard-chart">
      <div className="dashboard-chart-head">
        <div>
          <div className="dashboard-chart-title">По услугам</div>
          <div className="dashboard-chart-sub">Распределение заявок за выбранный период</div>
        </div>
        <div className="dashboard-chart-value">{formatCompactCount(points.length)}</div>
      </div>

      <div className="dashboard-service-list">
        {points.length === 0 && <div className="focus-note">Пока нет записей с услугой за выбранный период.</div>}
        {points.map((point) => {
          const width = (point.total / maxValue) * 100;
          return (
            <div key={point.service} className="dashboard-service-row">
              <div className="dashboard-service-name">{point.service}</div>
              <div className="dashboard-service-track">
                <div className="dashboard-service-fill" style={{ width: `${width}%` }} />
              </div>
              <div className="dashboard-service-value">
                {formatCompactCount(point.total)}
                <span>{Math.round(point.share * 100)}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function DashboardAnalyticsView({ analytics }: Props) {
  return (
    <>
      <div className="dashboard-hero">
        <div className="report-block dashboard-hero-main">
          <div className="badge acl">Дашборд</div>
          <div className="page-title dashboard-hero-title">Заявки, услуги и динамика</div>
          <div className="page-sub" style={{ maxWidth: 760 }}>
            Историческая сводка по журналу: заявки за сегодня, заявки за неделю, распределение по услугам и тренды по последним 30 дням.
          </div>
          <div className="dashboard-hero-meta">
            <div>
              <div className="dashboard-hero-meta-label">Период</div>
              <div className="dashboard-hero-meta-value">
                {formatDateLabel(analytics.period_start)} — {formatDateLabel(analytics.period_end)}
              </div>
            </div>
            <div>
              <div className="dashboard-hero-meta-label">Всего заявок</div>
              <div className="dashboard-hero-meta-value">{formatCompactCount(analytics.total_entries)}</div>
            </div>
            <div>
              <div className="dashboard-hero-meta-label">Сформировано</div>
              <div className="dashboard-hero-meta-value">{new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium", timeStyle: "short" }).format(new Date(analytics.generated_at))}</div>
            </div>
          </div>
        </div>

        <div className="dashboard-hero-side">
          <DashboardMetric label="Сегодня" value={formatCompactCount(analytics.today_total)} hint="Заявок за текущий день" />
          <DashboardMetric label="Неделя" value={formatCompactCount(analytics.week_total)} hint="Заявок с начала недели" />
        </div>
      </div>

      <div className="dashboard-chart-grid">
        <TrendChart points={analytics.daily_series} />
        <WeeklyBarsChart points={analytics.weekly_series} />
        <ServiceBreakdownChart points={analytics.service_breakdown} />
      </div>
    </>
  );
}
