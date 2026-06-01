const state = {
  presets: [],
  selected: null,
  results: null,
  resultTab: 'overview',
  view: 'select',
  loading: false,
  error: null,
};

const CHAIN_LABELS = {
  classic: '经典推荐链路',
  llm_hybrid: '大模型混合推荐链路',
  composite_enhanced: '检索增强与智能体复合链路',
};

function $(selector) { return document.querySelector(selector); }

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

/* ---------------- shell ---------------- */

function renderBanner() {
  return `
    <div class="demo-banner">
      <div class="crumbs">
        <a href="../../index.html">← 返回主页</a>
        <a href="../recsys-eval.html">项目详情</a>
      </div>
      <h1>在线 Demo · 大模型增强推荐链路能力评测与归因系统</h1>
      <p>选择一份预置的 Trace 日志样例，即可直接体验从端到端结果评测、业务过程评测到大模型增强过程评测的三级评测体系，以及异常归因分析。无需上传，开箱即用。</p>
    </div>
  `;
}

function render() {
  const root = $('#app');
  root.innerHTML = `
    <div class="app-shell">
      ${renderBanner()}
      ${state.view === 'select' ? renderSelectPage() : renderResultPage()}
    </div>
  `;
  bindEvents();
  if (state.view === 'result' && state.results && state.resultTab === 'visualization') {
    renderVisualizationCharts();
  }
}

function renderSelectPage() {
  if (state.error) {
    return `<div class="card"><h2>加载失败</h2><p class="muted">${escapeHtml(state.error)}</p></div>`;
  }
  if (!state.presets.length) {
    return `<div class="card"><div class="empty">正在加载预置样例…</div></div>`;
  }
  return `
    <div class="demo-note">提示：以下样例为论文实验中使用的合成 Trace 日志，已离线完成评测与归因计算。点击任意样例即可查看完整评测结果。</div>
    <div class="preset-grid">
      ${state.presets.map(renderPresetCard).join('')}
    </div>
  `;
}

function renderPresetCard(preset) {
  const s = preset.primary_stats || {};
  const templates = Object.entries(s.template_distribution || {})
    .map(([k, v]) => `${CHAIN_LABELS[k] || k} ${v}条`).join('；');
  return `
    <div class="card preset-card">
      <span class="status-badge tag-default mode-pill">${preset.mode === 'compare' ? '链路对比评测' : '单链路评测'}</span>
      <div>
        <h3 style="margin-bottom:6px;">${escapeHtml(preset.title)}</h3>
        <div class="muted small" style="line-height:1.7;">${escapeHtml(preset.desc)}</div>
      </div>
      <div class="stat-row">
        <div class="mini-kv">主日志 trace<b>${s.trace_count ?? '-'}</b></div>
        <div class="mini-kv">异常样例<b>${s.faulty_count ?? '-'}</b></div>
        ${preset.mode === 'compare' ? `<div class="mini-kv">对比日志 trace<b>${preset.secondary_stats?.trace_count ?? '-'}</b></div>` : ''}
      </div>
      <div class="small muted">链路构成：${escapeHtml(templates || '—')}</div>
      <div class="spacer"></div>
      <div class="actions">
        <button class="primary" data-open-preset="${preset.id}">体验该样例 →</button>
      </div>
    </div>
  `;
}

function renderResultPage() {
  const preset = state.selected;
  if (state.loading || !state.results) {
    return `<div class="card"><div class="empty">正在加载评测结果…</div></div>`;
  }
  return `
    <div class="card">
      <div class="selected-head">
        <div>
          <div class="muted small">当前样例</div>
          <div style="font-size:22px;font-weight:800;margin-top:4px;">${escapeHtml(preset.title)}</div>
        </div>
        <div class="actions">
          <span class="status-badge tag-default">${preset.mode === 'compare' ? '链路对比评测' : '单链路评测'}</span>
          <button class="ghost" id="reselectBtn">重新选择样例</button>
        </div>
      </div>
      <div class="muted small" style="margin-top:8px;line-height:1.7;">${escapeHtml(preset.desc)}</div>
    </div>
    ${renderDatasetCard(preset)}
    ${renderResultsCard(state.results)}
  `;
}

function renderDatasetCard(preset) {
  const s = preset.primary_stats || {};
  const structures = preset.chain?.structures || [];
  return `
    <div class="card" style="margin-top:20px;">
      <h2>数据概览与链路结构</h2>
      <p class="muted">系统已对该样例完成结构校验与链路解析，下方展示日志构成与自动识别出的推荐链路结构。</p>
      <div class="kv-grid" style="margin-top:12px;">
        <div class="kv-card"><div class="label">日志数量</div><div class="value">${s.trace_count ?? '-'}</div></div>
        <div class="kv-card"><div class="label">正常样例</div><div class="value">${s.normal_count ?? '-'}</div></div>
        <div class="kv-card"><div class="label">异常样例</div><div class="value">${s.faulty_count ?? '-'}</div></div>
        <div class="kv-card"><div class="label">结构错误</div><div class="value">${s.error_count ?? 0}</div></div>
      </div>
      <div class="struct-wrap" style="margin-top:18px;">
        ${structures.map(struct => `
          <div class="structure-block">
            <h3>${escapeHtml(struct.label)}</h3>
            <div class="structure-flow">
              ${struct.nodes.map((node, idx) => `
                ${idx > 0 ? '<div class="structure-arrow">→</div>' : ''}
                <div class="structure-node">
                  <div class="title">${escapeHtml(node.label)}</div>
                  <div class="sub">${escapeHtml(node.subtitle || '')}</div>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

function renderResultsCard(results) {
  return `
    <div class="card" style="margin-top:20px;">
      <h2>评测结果</h2>
      <p class="muted">结果页保留“总览、评测详情、可视化分析”三个一级标签页。LLM 裁判评测与人工评测作为结果来源标签展示。</p>
      <div class="tabs">
        <div class="tab ${state.resultTab === 'overview' ? 'active' : ''}" data-result-tab="overview">总览</div>
        <div class="tab ${state.resultTab === 'details' ? 'active' : ''}" data-result-tab="details">评测详情</div>
        <div class="tab ${state.resultTab === 'visualization' ? 'active' : ''}" data-result-tab="visualization">可视化分析</div>
      </div>
      ${state.resultTab === 'overview' ? renderResultOverview(results) : ''}
      ${state.resultTab === 'details' ? renderResultDetails(results) : ''}
      ${state.resultTab === 'visualization' ? renderVisualization(results) : ''}
    </div>
  `;
}

/* ---------------- result renderers (ported from platform) ---------------- */

function renderResultOverview(results) {
  if (results.mode === 'compare') return renderCompareOverview(results);
  return renderSingleOverview(results.overview);
}

function renderSingleOverview(overview) {
  const statusCls = overview.overall_status_class === 'good' ? 'badge-good' : overview.overall_status_class === 'warn' ? 'badge-warn' : 'badge-bad';
  return `
    <div class="overview-grid">
      <div class="card">
        <div class="muted small">总体评分</div>
        <div class="score-big">${overview.overall_score.toFixed(4)}</div>
        <span class="status-badge ${statusCls}">${escapeHtml(overview.overall_status)}</span>
        <div style="margin-top: 14px; line-height: 1.8;">${escapeHtml(overview.diagnosis)}</div>
        <div class="compare-box">
          <div><strong>当前诊断结论</strong></div>
          <div class="small muted" style="margin-top:8px;">主要异常模块：${overview.major_anomaly_modules.join('、')}</div>
          <div class="small muted" style="margin-top:6px;">任务状态：${escapeHtml(overview.task_status)}</div>
          <div class="small muted" style="margin-top:6px;">阅读建议：${escapeHtml(overview.reading_suggestion)}</div>
        </div>
      </div>
      <div class="card">
        <h3>核心指标概览</h3>
        <div class="summary-grid">
          ${Object.entries(overview.headline_metrics).map(([label, value]) => `
            <div class="kv-card">
              <div class="label">${escapeHtml(label)}</div>
              <div class="value">${typeof value === 'number' ? (value <= 1 ? `${(value * 100).toFixed(2)}%` : value) : escapeHtml(value)}</div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}

function renderCompareOverview(results) {
  const overview = results.overview;
  const p = results.primary.overview;
  const s = results.secondary.overview;
  const cmp = overview.comparison || {};
  return `
    <div class="compare-overview-grid">
      <div class="card">
        <div class="muted small">主日志总体评分</div>
        <div class="score-big">${p.overall_score.toFixed(4)}</div>
        <span class="status-badge ${p.overall_status_class === 'good' ? 'badge-good' : p.overall_status_class === 'warn' ? 'badge-warn' : 'badge-bad'}">${escapeHtml(p.overall_status)}</span>
        <div class="compare-box">
          <div><strong>主日志主要异常模块</strong></div>
          <div class="small muted" style="margin-top:8px;">${p.major_anomaly_modules.join('、')}</div>
        </div>
      </div>
      <div class="card">
        <div class="muted small">对比日志总体评分</div>
        <div class="score-big">${s.overall_score.toFixed(4)}</div>
        <span class="status-badge ${s.overall_status_class === 'good' ? 'badge-good' : s.overall_status_class === 'warn' ? 'badge-warn' : 'badge-bad'}">${escapeHtml(s.overall_status)}</span>
        <div class="compare-box">
          <div><strong>对比日志主要异常模块</strong></div>
          <div class="small muted" style="margin-top:8px;">${s.major_anomaly_modules.join('、')}</div>
        </div>
      </div>
      <div class="card">
        <h3>对比结论</h3>
        <div class="kv-grid" style="grid-template-columns: repeat(2, 1fr);">
          <div class="kv-card"><div class="label">总体评分差值</div><div class="value">${cmp.delta?.toFixed(4) ?? '-'}</div></div>
          <div class="kv-card"><div class="label">更优结果</div><div class="value" style="font-size:22px;">${escapeHtml(cmp.better_side || '-')}</div></div>
        </div>
        <div style="margin-top: 14px; line-height: 1.8;">${escapeHtml(overview.diagnosis)}</div>
        <div class="compare-box">
          <div><strong>主要提升模块</strong></div>
          <div class="small muted" style="margin-top:8px;">${(cmp.major_improvements || []).length ? cmp.major_improvements.join('、') : '暂无明显提升'}</div>
          <div style="height:8px"></div>
          <div><strong>主要退化模块</strong></div>
          <div class="small muted" style="margin-top:8px;">${(cmp.major_regressions || []).length ? cmp.major_regressions.join('、') : '暂无明显退化'}</div>
        </div>
        <div class="small muted" style="margin-top:10px;">${escapeHtml(overview.reading_suggestion)}</div>
      </div>
    </div>
  `;
}

function renderResultDetails(results) {
  if (results.mode === 'compare') {
    return results.details.map(category => `
      <div class="detail-category">
        <h3>${escapeHtml(category.label)}</h3>
        ${category.modules.map(module => `
          <div class="module-card">
            <div class="module-head">
              <div>
                <div style="font-size:18px;font-weight:800;">${escapeHtml(module.label)}</div>
                <div class="small muted">主日志：${module.primary_score.toFixed(4)} ｜ 对比日志：${module.secondary_score.toFixed(4)} ｜ 差值：${module.delta.toFixed(4)}</div>
              </div>
              <span class="status-badge ${module.trend_class}">${escapeHtml(module.trend)}</span>
            </div>
            <div class="metric-grid compare-metric-grid">
              ${module.metrics.map(metric => renderCompareMetricCard(metric)).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    `).join('');
  }
  return results.details.map(category => `
    <div class="detail-category">
      <h3>${escapeHtml(category.label)}</h3>
      ${category.modules.map(module => `
        <div class="module-card">
          <div class="module-head">
            <div>
              <div style="font-size:18px;font-weight:800;">${escapeHtml(module.label)}</div>
              <div class="small muted">模块评分：${module.module_score.toFixed(4)}</div>
            </div>
            <span class="status-badge ${module.status_class === 'good' ? 'badge-good' : module.status_class === 'warn' ? 'badge-warn' : 'badge-bad'}">${escapeHtml(module.status)}</span>
          </div>
          <div class="metric-grid">
            ${module.metrics.map(metric => renderMetricCard(metric)).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  `).join('');
}

function renderMetricCard(metric) {
  return `
    <div class="metric-card">
      <div class="metric-top">
        <div class="metric-name">
          <span>${escapeHtml(metric.name)}</span>
          <span class="question">?
            <span class="tooltip">
              <strong>【指标含义】</strong><br/>${escapeHtml(metric.help.meaning)}<br/><br/>
              <strong>【计算逻辑】</strong><br/>${escapeHtml(metric.help.formula)}<br/><br/>
              <strong>【说明问题】</strong><br/>${escapeHtml(metric.help.diagnosis)}
            </span>
          </span>
        </div>
        <span class="status-badge ${metric.status_class === 'good' ? 'badge-good' : metric.status_class === 'warn' ? 'badge-warn' : 'badge-bad'}">${escapeHtml(metric.status)}</span>
      </div>
      <div class="metric-value">${escapeHtml(metric.display_value)}</div>
      <div class="metric-base">基线值：${escapeHtml(metric.baseline_display)}</div>
      <div class="source-tag tag">${escapeHtml(metric.source)}</div>
    </div>
  `;
}

function renderCompareMetricCard(metric) {
  return `
    <div class="metric-card compare-metric-card">
      <div class="metric-top">
        <div class="metric-name">
          <span>${escapeHtml(metric.name)}</span>
          <span class="question">?
            <span class="tooltip">
              <strong>【指标含义】</strong><br/>${escapeHtml(metric.help.meaning)}<br/><br/>
              <strong>【计算逻辑】</strong><br/>${escapeHtml(metric.help.formula)}<br/><br/>
              <strong>【说明问题】</strong><br/>${escapeHtml(metric.help.diagnosis)}
            </span>
          </span>
        </div>
        <span class="status-badge ${metric.trend_class}">${escapeHtml(metric.trend)}</span>
      </div>
      <div class="compare-value-grid">
        <div class="compare-value-box">
          <div class="label">主日志</div>
          <div class="value">${escapeHtml(metric.primary_display)}</div>
        </div>
        <div class="compare-value-box">
          <div class="label">对比日志</div>
          <div class="value">${escapeHtml(metric.secondary_display)}</div>
        </div>
      </div>
      <div class="metric-base">差值：${metric.delta.toFixed(4)} ｜ 来源：${escapeHtml(metric.source)}</div>
    </div>
  `;
}

function renderVisualization(results) {
  if (results.mode === 'compare') {
    return `
      <div class="chart-section">
        <div class="chart-card">
          <h3>模块评分对比柱状图</h3>
          <div class="small muted" style="margin-bottom:10px;">直接对比主日志与对比日志在各模块上的得分，便于查看哪一侧更优。</div>
          <div id="moduleCompareChart"></div>
        </div>
        <div class="chart-card">
          <h3>评测层级对比图</h3>
          <div class="small muted" style="margin-bottom:10px;">比较三类评测层级在两组日志中的总分差异。</div>
          <div id="layerCompareChart"></div>
        </div>
        <div class="chart-card" style="grid-column: 1 / -1;">
          <h3>评测详情指标对比可视化</h3>
          ${renderCompareVisualization(results.details)}
        </div>
        <div class="chart-card" style="grid-column: 1 / -1;">
          <h3>总体评分对比图</h3>
          <div id="overallCompareChart"></div>
        </div>
      </div>
    `;
  }
  return `
    <div class="chart-section">
      <div class="chart-card" style="grid-column: 1 / -1;">
        <h3>评测详情指标可视化</h3>
        ${renderDetailVisualization(results.details)}
      </div>
      <div class="chart-card" style="grid-column: 1 / -1;">
        <h3>整体评分对比折线图</h3>
        <div class="small muted" style="margin-bottom:10px;">用于比较不同任务或多轮运行后的整体评测得分变化。</div>
        <div id="taskTrendChart"></div>
      </div>
    </div>
  `;
}

function renderDetailVisualization(categories) {
  return categories.map(category => `
    <div class="viz-category-block">
      <div class="viz-category-title">${escapeHtml(category.label)}</div>
      ${category.modules.map(module => `
        <div class="viz-module-block">
          <div class="viz-module-head">
            <div>
              <div class="viz-module-title">${escapeHtml(module.label)}</div>
              <div class="small muted">模块评分：${module.module_score.toFixed(4)} ｜ 状态：${escapeHtml(module.status)}</div>
            </div>
            <span class="status-badge ${module.status_class === 'good' ? 'badge-good' : module.status_class === 'warn' ? 'badge-warn' : 'badge-bad'}">${escapeHtml(module.status)}</span>
          </div>
          <div class="viz-metric-grid">
            ${module.metrics.map(metric => renderMetricVizCard(metric)).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  `).join('');
}

function renderCompareVisualization(categories) {
  return categories.map(category => `
    <div class="viz-category-block">
      <div class="viz-category-title">${escapeHtml(category.label)}</div>
      ${category.modules.map(module => `
        <div class="viz-module-block">
          <div class="viz-module-head">
            <div>
              <div class="viz-module-title">${escapeHtml(module.label)}</div>
              <div class="small muted">主日志：${module.primary_score.toFixed(4)} ｜ 对比日志：${module.secondary_score.toFixed(4)} ｜ 差值：${module.delta.toFixed(4)}</div>
            </div>
            <span class="status-badge ${module.trend_class}">${escapeHtml(module.trend)}</span>
          </div>
          <div class="viz-metric-grid">
            ${module.metrics.map(metric => renderCompareMetricVizCard(metric)).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  `).join('');
}

function renderMetricVizCard(metric) {
  const current = Number(metric.current_value || 0);
  const baseline = Number(metric.baseline_value || 0);
  const maxVal = Math.max(current, baseline, 0.0001);
  const currentWidth = Math.max(6, (current / maxVal) * 100);
  const baselineWidth = Math.max(6, (baseline / maxVal) * 100);
  const delta = current - baseline;
  const deltaText = delta === 0 ? '与基线持平' : (delta > 0 ? `较基线上升 ${delta.toFixed(4)}` : `较基线下降 ${Math.abs(delta).toFixed(4)}`);
  return `
    <div class="viz-metric-card">
      <div class="viz-metric-title-row">
        <div class="viz-metric-title">${escapeHtml(metric.name)}</div>
        <span class="source-tag tag">${escapeHtml(metric.source)}</span>
      </div>
      <div class="viz-value-row">
        <div class="viz-value-current">当前值：${escapeHtml(metric.display_value)}</div>
        <div class="viz-value-base">基线值：${escapeHtml(metric.baseline_display)}</div>
      </div>
      <div class="viz-bar-group">
        <div class="viz-bar-line">
          <div class="viz-bar-label">当前</div>
          <div class="viz-bar-track"><div class="viz-bar-fill current" style="width:${currentWidth}%"></div></div>
        </div>
        <div class="viz-bar-line">
          <div class="viz-bar-label">基线</div>
          <div class="viz-bar-track"><div class="viz-bar-fill baseline" style="width:${baselineWidth}%"></div></div>
        </div>
      </div>
      <div class="small muted" style="margin-top:10px;line-height:1.6;">${deltaText}。${escapeHtml(metric.help.diagnosis)}</div>
    </div>
  `;
}

function renderCompareMetricVizCard(metric) {
  const p = Number(metric.primary_value || 0);
  const s = Number(metric.secondary_value || 0);
  const maxVal = Math.max(p, s, 0.0001);
  const pWidth = Math.max(6, (p / maxVal) * 100);
  const sWidth = Math.max(6, (s / maxVal) * 100);
  const deltaText = metric.delta === 0 ? '两组结果持平' : (metric.delta > 0 ? `主日志高于对比日志 ${metric.delta.toFixed(4)}` : `主日志低于对比日志 ${Math.abs(metric.delta).toFixed(4)}`);
  return `
    <div class="viz-metric-card">
      <div class="viz-metric-title-row">
        <div class="viz-metric-title">${escapeHtml(metric.name)}</div>
        <span class="source-tag tag">${escapeHtml(metric.source)}</span>
      </div>
      <div class="viz-value-row">
        <div class="viz-value-current">主日志：${escapeHtml(metric.primary_display)}</div>
        <div class="viz-value-base">对比日志：${escapeHtml(metric.secondary_display)}</div>
      </div>
      <div class="viz-bar-group">
        <div class="viz-bar-line">
          <div class="viz-bar-label">主日志</div>
          <div class="viz-bar-track"><div class="viz-bar-fill current" style="width:${pWidth}%"></div></div>
        </div>
        <div class="viz-bar-line">
          <div class="viz-bar-label">对比日志</div>
          <div class="viz-bar-track"><div class="viz-bar-fill baseline" style="width:${sWidth}%"></div></div>
        </div>
      </div>
      <div class="small muted" style="margin-top:10px;line-height:1.6;">${deltaText}。${escapeHtml(metric.help.diagnosis)}</div>
    </div>
  `;
}

/* ---------------- charts ---------------- */

function renderVisualizationCharts() {
  const results = state.results;
  if (results.mode === 'compare') {
    renderGroupedBarChart('#moduleCompareChart', results.visualization.module_scores_compare, 'primary_score', 'secondary_score', '主日志', '对比日志');
    renderGroupedBarChart('#layerCompareChart', results.visualization.layer_distribution_compare, 'primary_value', 'secondary_value', '主日志', '对比日志');
    renderOverallCompareChart('#overallCompareChart', results.visualization.overall_compare);
    return;
  }
  renderTrendChart('#taskTrendChart', results.visualization.task_trend);
}

function renderGroupedBarChart(selector, rows, primaryKey, secondaryKey, primaryLabel, secondaryLabel) {
  const root = document.querySelector(selector);
  if (!root) return;
  root.innerHTML = `
    <div class="grouped-bar-list">
      <div class="small muted grouped-legend">蓝色：${primaryLabel} ｜ 灰色：${secondaryLabel}</div>
      ${rows.map(row => {
        const p = Number(row[primaryKey] || 0);
        const s = Number(row[secondaryKey] || 0);
        return `
          <div class="grouped-bar-row">
            <div class="grouped-label">${escapeHtml(row.name)}</div>
            <div>
              <div class="grouped-bar-track"><div class="grouped-bar-fill primary" style="width:${Math.max(4, p * 100)}%"></div></div>
              <div class="grouped-bar-track second"><div class="grouped-bar-fill secondary" style="width:${Math.max(4, s * 100)}%"></div></div>
            </div>
            <div class="grouped-values">${p.toFixed(4)} / ${s.toFixed(4)}</div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

function renderTrendChart(selector, rows) {
  const root = document.querySelector(selector);
  if (!root) return;
  const width = 760;
  const height = 220;
  const padding = 42;
  const max = 1.0;
  const min = 0;
  const points = rows.map((row, idx) => {
    const x = padding + (idx * (width - padding * 2) / Math.max(rows.length - 1, 1));
    const y = height - padding - ((row.score - min) / (max - min)) * (height - padding * 2);
    return { ...row, x, y };
  });
  const polyline = points.map(p => `${p.x},${p.y}`).join(' ');
  root.innerHTML = `
    <svg class="line-svg" viewBox="0 0 ${width} ${height}">
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#cbd5e1" />
      <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" stroke="#cbd5e1" />
      <polyline points="${polyline}" fill="none" stroke="#2563eb" stroke-width="3" />
      ${points.map(point => `
        <g>
          <circle cx="${point.x}" cy="${point.y}" r="5" fill="#2563eb"></circle>
          <text x="${point.x}" y="${point.y - 10}" text-anchor="middle" font-size="12" fill="#0f172a">${point.score.toFixed(3)}</text>
          <text x="${point.x}" y="${height - padding + 20}" text-anchor="middle" font-size="12" fill="#64748b">${escapeHtml(point.name)}</text>
        </g>
      `).join('')}
    </svg>
  `;
}

function renderOverallCompareChart(selector, rows) {
  const root = document.querySelector(selector);
  if (!root) return;
  root.innerHTML = `<div class="bar-list">${rows.map(row => `
    <div class="bar-row">
      <div>${escapeHtml(row.name)}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(6, row.score * 100)}%"></div></div>
      <div style="text-align:right;">${row.score.toFixed(4)}</div>
    </div>
  `).join('')}</div>`;
}

/* ---------------- events / data ---------------- */

function bindEvents() {
  document.querySelectorAll('[data-open-preset]').forEach(btn => btn.addEventListener('click', () => {
    openPreset(btn.getAttribute('data-open-preset'));
  }));
  $('#reselectBtn')?.addEventListener('click', () => {
    state.view = 'select';
    state.results = null;
    state.selected = null;
    window.scrollTo({ top: 0 });
    render();
  });
  document.querySelectorAll('[data-result-tab]').forEach(tab => tab.addEventListener('click', () => {
    state.resultTab = tab.getAttribute('data-result-tab');
    render();
  }));
}

async function openPreset(id) {
  const preset = state.presets.find(p => p.id === id);
  if (!preset) return;
  state.selected = preset;
  state.view = 'result';
  state.resultTab = 'overview';
  state.loading = true;
  state.results = null;
  render();
  try {
    const res = await fetch(`data/${id}.json`);
    state.results = await res.json();
  } catch (e) {
    state.results = null;
    state.error = '结果数据加载失败：' + e.message;
  }
  state.loading = false;
  window.scrollTo({ top: 0 });
  render();
}

async function bootstrap() {
  try {
    const res = await fetch('data/manifest.json');
    state.presets = await res.json();
  } catch (e) {
    state.error = '预置样例清单加载失败：' + e.message + '（请通过本地服务器或线上环境访问，而非直接双击打开文件）';
  }
  render();
}

bootstrap();
