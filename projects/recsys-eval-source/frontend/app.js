const state = {
  tasks: [],
  selectedTask: null,
  view: 'task-list',
  search: '',
  resultTab: 'overview',
  loading: false,
};

const STEP_META = [
  { key: 'create', title: '新建任务', desc: '输入任务名称，创建评测任务。' },
  { key: 'mode', title: '评测模式', desc: '选择单链路评测或链路对比评测。' },
  { key: 'upload', title: 'Trace 日志上传', desc: '上传一组或两组 Trace 日志。' },
  { key: 'validate', title: '日志结构校验', desc: '检查字段完整性与结构合法性。' },
  { key: 'parse', title: '推荐链路解析', desc: '自动识别链路步骤与链路类型。' },
  { key: 'structure', title: '链路结构确认', desc: '查看并确认系统生成的链路结构图。' },
  { key: 'config', title: '评测配置', desc: '配置自动评测、LLM 裁判与人工评测。' },
  { key: 'results', title: '评测结果', desc: '查看总览、评测详情与可视化分析。' },
];

const STATUS_LABELS = {
  draft: '待创建',
  mode_selected: '已选择模式',
  uploaded: '已上传日志',
  validated: '校验通过',
  validation_failed: '校验未通过',
  parsed: '已解析链路',
  structure_confirmed: '已确认结构',
  configured: '已完成配置',
  running: '评测运行中',
  completed: '评测完成',
};

const CHAIN_LABELS = {
  classic: '经典推荐链路',
  llm_hybrid: '大模型混合推荐链路',
  composite_enhanced: '检索增强与智能体复合链路',
};

function $(selector) {
  return document.querySelector(selector);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

async function api(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || '请求失败');
  return data.data;
}

function taskStatusClass(status) {
  return `status-${status || 'draft'}`;
}

function render() {
  const root = $('#app');
  root.innerHTML = `
    <div class="app-shell">
      ${renderTopbar()}
      ${state.view === 'task-list' ? renderTaskListPage() : renderWorkflowPage()}
    </div>
  `;
  bindEvents();
  if (state.view === 'workflow' && state.selectedTask?.results && state.resultTab === 'visualization') {
    renderVisualizationCharts();
  }
}

function renderTopbar() {
  return `
    <div class="topbar">
      <div>
        <h1>评测平台</h1>
        <p>围绕推荐链路日志完成任务创建、结构校验、链路解析、评测配置与结果分析。</p>
      </div>
      <div class="actions">
        ${state.view === 'workflow' ? '<button class="ghost" id="backToTasksBtn">返回任务列表</button>' : ''}
        <button class="primary" id="newTaskBtn">新建评测任务</button>
      </div>
    </div>
  `;
}

function renderTaskListPage() {
  const filtered = state.tasks.filter(task => task.name.toLowerCase().includes(state.search.toLowerCase()));
  return `
    <div class="card">
      <div class="task-list-toolbar">
        <div>
          <h2>任务列表</h2>
          <div class="muted">展示已有评测任务，支持搜索、查看详情和继续配置。</div>
        </div>
        <div style="min-width: 320px;">
          <input id="searchInput" placeholder="搜索任务名称" value="${escapeHtml(state.search)}" />
        </div>
      </div>
      ${filtered.length === 0 ? '<div class="empty">当前还没有任务，点击右上角“新建评测任务”开始。</div>' : `
        <table class="task-table">
          <thead>
            <tr>
              <th>任务名称</th>
              <th>创建时间</th>
              <th>状态</th>
              <th>评测模式</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.map(task => `
              <tr>
                <td>
                  <div><strong>${escapeHtml(task.name)}</strong></div>
                  <div class="small muted">任务编号：${task.id}</div>
                </td>
                <td>${escapeHtml(task.created_at)}</td>
                <td><span class="status-badge ${taskStatusClass(task.status)}">${STATUS_LABELS[task.status] || task.status}</span></td>
                <td>${task.mode === 'compare' ? '链路对比评测' : '单链路评测'}</td>
                <td>
                  <div class="table-action-row">
                    <button data-open-task="${task.id}">进入任务</button>
                  </div>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `}
    </div>
  `;
}

function currentStepKey(task) {
  if (!task) return 'create';
  if (task.status === 'draft') return 'create';
  if (task.status === 'mode_selected') return 'mode';
  if (task.status === 'uploaded') return 'upload';
  if (task.status === 'validation_failed' || task.status === 'validated') return 'validate';
  if (task.status === 'parsed') return 'parse';
  if (task.status === 'structure_confirmed') return 'structure';
  if (task.status === 'configured') return 'config';
  if (task.status === 'running' || task.status === 'completed') return 'results';
  return 'create';
}

function renderWorkflowPage() {
  const task = state.selectedTask;
  const taskStepKey = currentStepKey(task);
  const activeStep = STEP_META.findIndex(step => step.key === state.viewStep) >= 0 ? state.viewStep : taskStepKey;
  state.viewStep = activeStep;
  return `
    <div class="workflow-layout">
      <div class="card stepper">
        <div style="margin-bottom: 16px;">
          <div class="muted small">当前任务</div>
          <div style="font-size: 22px; font-weight: 800; margin: 6px 0 8px;">${escapeHtml(task?.name || '')}</div>
          <div class="actions">
            <span class="status-badge ${taskStatusClass(task?.status)}">${STATUS_LABELS[task?.status] || task?.status || ''}</span>
            <span class="tag tag-default">${task?.mode === 'compare' ? '链路对比评测' : '单链路评测'}</span>
          </div>
        </div>
        ${STEP_META.map((step, idx) => {
          const taskIndex = STEP_META.findIndex(item => item.key === taskStepKey);
          const stepIndex = STEP_META.findIndex(item => item.key === step.key);
          const active = step.key === activeStep;
          const done = stepIndex < taskIndex || (task?.status === 'completed');
          return `
            <div class="step-item ${active ? 'active' : ''} ${done ? 'done' : ''}" data-step="${step.key}">
              <div class="step-index">${idx + 1}</div>
              <div>
                <div class="step-title">${step.title}</div>
                <div class="step-desc">${step.desc}</div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
      <div>${renderStepContent(task, activeStep)}</div>
    </div>
  `;
}

function renderStepContent(task, stepKey) {
  switch (stepKey) {
    case 'create': return renderCreateStep(task);
    case 'mode': return renderModeStep(task);
    case 'upload': return renderUploadStep(task);
    case 'validate': return renderValidateStep(task);
    case 'parse': return renderParseStep(task);
    case 'structure': return renderStructureStep(task);
    case 'config': return renderConfigStep(task);
    case 'results': return renderResultsStep(task);
    default: return renderCreateStep(task);
  }
}

function renderCreateStep(task) {
  return `
    <div class="card">
      <h2>新建评测任务</h2>
      <p class="muted">请输入任务名称，创建本次评测任务。</p>
      <div class="grid" style="max-width: 680px;">
        <div>
          <label>任务名称</label>
          <input id="taskNameInput" placeholder="例如：大模型增强推荐链路异常诊断评测" value="${escapeHtml(task?.name || '')}" />
        </div>
      </div>
      <div class="actions" style="margin-top: 18px;">
        <button class="primary" id="createTaskConfirmBtn">下一步</button>
      </div>
    </div>
  `;
}

function renderModeStep(task) {
  return `
    <div class="card">
      <h2>评测模式选择</h2>
      <p class="muted">请选择本次任务的评测模式。单链路评测上传一组 Trace 日志，链路对比评测上传两组 Trace 日志用于比较分析。</p>
      <div class="mode-grid">
        ${renderModeCard('single', '单链路评测', '上传一组 Trace 日志，对单个推荐链路进行完整评测。', task.mode)}
        ${renderModeCard('compare', '链路对比评测', '上传两组 Trace 日志，对不同链路或不同版本结果进行对比。', task.mode)}
      </div>
      <div class="actions" style="margin-top: 18px;">
        <button class="ghost" data-step-nav="create">返回</button>
        <button class="primary" id="saveModeBtn">下一步</button>
      </div>
    </div>
  `;
}

function renderModeCard(key, title, desc, currentMode) {
  return `
    <div class="mode-card ${currentMode === key ? 'selected' : ''}" data-mode-card="${key}">
      <h3>${title}</h3>
      <p class="muted">${desc}</p>
    </div>
  `;
}

function renderUploadStep(task) {
  const uploads = task.uploads || {};
  return `
    <div class="card">
      <h2>Trace 日志上传</h2>
      <p class="muted">请上传 JSON 或 JSONL 格式的 Trace 日志文件。用户输入即为生成的日志数据。</p>
      <div class="upload-panel">
        <div class="upload-box">
          <h3>主日志文件</h3>
          <input type="file" id="primaryFile" accept=".json,.jsonl" />
          <div class="small muted" style="margin-top:10px;">${uploads.primary ? `已上传：${escapeHtml(uploads.primary.filename)}（${uploads.primary.trace_count} 条）` : '尚未上传'}</div>
        </div>
        ${task.mode === 'compare' ? `
          <div class="upload-box">
            <h3>对比日志文件</h3>
            <input type="file" id="secondaryFile" accept=".json,.jsonl" />
            <div class="small muted" style="margin-top:10px;">${uploads.secondary ? `已上传：${escapeHtml(uploads.secondary.filename)}（${uploads.secondary.trace_count} 条）` : '尚未上传'}</div>
          </div>
        ` : '<div class="upload-box"><h3>上传说明</h3><p class="muted">单链路评测只需要上传一组 Trace 日志。若需要做版本对比，请返回上一步选择“链路对比评测”。</p></div>'}
      </div>
      <div class="actions" style="margin-top: 18px;">
        <button class="ghost" data-step-nav="mode">返回</button>
        <button class="primary" id="uploadBtn">上传并继续</button>
      </div>
    </div>
  `;
}

function renderValidateStep(task) {
  const validation = task.validation;
  const uploads = task.uploads || {};
  if (!validation) {
    return `
      <div class="card">
        <h2>日志结构校验</h2>
        <p class="muted">系统将对上传的 Trace 日志进行结构校验，检查关键字段和格式是否完整。</p>
        <div class="actions" style="margin-top: 18px;">
          <button class="ghost" data-step-nav="upload">返回</button>
          <button class="primary" id="validateBtn">开始校验</button>
        </div>
      </div>
    `;
  }
  return `
    <div class="card">
      <h2>日志结构校验</h2>
      <p class="muted">校验通过后，系统将进入推荐链路解析环节。</p>
      <div class="grid-2 grid">
        ${Object.entries(uploads).map(([key]) => renderValidationCard(key, validation[key])).join('')}
      </div>
      <div class="actions" style="margin-top: 18px;">
        <button class="ghost" data-step-nav="upload">重新上传</button>
        ${validation.passed ? '<button class="primary" id="goParseBtn">继续</button>' : '<button class="primary" id="revalidateBtn">重新校验</button>'}
      </div>
    </div>
  `;
}

function renderValidationCard(key, result) {
  const title = key === 'primary' ? '主日志文件' : '对比日志文件';
  return `
    <div class="card">
      <h3>${title}</h3>
      <div class="notice ${result.passed ? 'good' : 'bad'}">${result.passed ? '日志结构校验通过。' : '日志结构校验未通过，请根据错误提示检查上传内容。'}</div>
      <div class="kv-grid" style="margin-top: 12px;">
        <div class="kv-card"><div class="label">日志数量</div><div class="value">${result.trace_count}</div></div>
        <div class="kv-card"><div class="label">正常样例</div><div class="value">${result.normal_count}</div></div>
        <div class="kv-card"><div class="label">异常样例</div><div class="value">${result.faulty_count}</div></div>
        <div class="kv-card"><div class="label">错误条数</div><div class="value">${result.error_count}</div></div>
      </div>
      <div style="margin-top: 12px;">
        <div class="small muted">模板分布：${Object.entries(result.template_distribution || {}).map(([k, v]) => `${CHAIN_LABELS[k] || k} ${v}条`).join('；') || '无'}</div>
      </div>
      ${(result.warnings || []).length ? `<div class="notice warn" style="margin-top:12px;">${result.warnings.join('<br/>')}</div>` : ''}
      ${(result.errors || []).length ? `
        <ul class="error-list">
          ${result.errors.map(item => `<li><strong>${escapeHtml(item.trace_id || item.index)}</strong>：${escapeHtml((item.errors || []).join('；'))}</li>`).join('')}
        </ul>
      ` : ''}
    </div>
  `;
}

function renderParseStep(task) {
  const parsed = task.parsed_chain;
  if (!parsed) {
    return `
      <div class="card">
        <h2>推荐链路解析</h2>
        <p class="muted">系统将根据上传日志自动识别链路类型、关键模块以及步骤顺序。</p>
        <div class="actions" style="margin-top: 18px;">
          <button class="ghost" data-step-nav="validate">返回</button>
          <button class="primary" id="parseBtn">开始解析</button>
        </div>
      </div>
    `;
  }
  return `
    <div class="card">
      <h2>推荐链路解析</h2>
      <p class="muted">${escapeHtml(parsed.description)}</p>
      <div class="chain-cards" style="margin-top: 16px;">
        ${parsed.chain_types.map(item => `
          <div class="card">
            <h3>${escapeHtml(item.label)}</h3>
            <div class="small muted">样例数量：${item.sample_count}</div>
            <div class="pill-list" style="margin-top: 10px;">
              ${item.modules.map(module => `<span class="pill">${escapeHtml(module)}</span>`).join('')}
            </div>
          </div>
        `).join('')}
      </div>
      <div class="actions" style="margin-top: 18px;">
        <button class="ghost" data-step-nav="validate">返回</button>
        <button class="primary" id="goStructureBtn">下一步</button>
      </div>
    </div>
  `;
}

function renderStructureStep(task) {
  const parsed = task.parsed_chain;
  return `
    <div class="card">
      <h2>链路结构图确认</h2>
      <p class="muted">请确认系统生成的链路结构是否符合日志中的推荐流程。</p>
      ${(parsed?.structures || []).map(struct => `
        <div class="structure-block">
          <h3>${escapeHtml(struct.label)}</h3>
          <div class="structure-flow">
            ${struct.nodes.map((node, idx) => `
              ${idx > 0 ? '<div class="structure-arrow">→</div>' : ''}
              <div class="structure-node">
                <div class="title">${escapeHtml(node.label)}</div>
                <div class="sub">${escapeHtml(node.subtitle)}</div>
              </div>
            `).join('')}
          </div>
        </div>
      `).join('')}
      <div class="actions" style="margin-top: 18px;">
        <button class="ghost" data-step-nav="parse">返回修改</button>
        <button class="primary" id="confirmStructureBtn">确认链路结构</button>
      </div>
    </div>
  `;
}

function renderConfigStep(task) {
  const config = task.config || {};
  const autoCfg = config.auto_eval || { categories: [] };
  const llmCfg = config.llm_judge || {};
  const humanCfg = config.human_review || {};
  return `
    <div class="card">
      <h2>评测配置</h2>
      <p class="muted">本页包括自动评测配置、LLM 裁判评测配置和人工评测配置。LLM 裁判评测与人工评测属于评测方式，用于校正自动评测结果，不作为结果页一级标签页。</p>
      <div class="config-columns">
        <div class="card" style="padding:16px;">
          <h3>自动评测配置</h3>
          <div class="small muted">按“分类—模块—指标”配置自动评测项，可勾选或取消具体指标。</div>
          <div style="margin-top: 14px;">
            ${autoCfg.categories.map((category, cIdx) => `
              <div class="category-block">
                <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
                  <strong>${escapeHtml(category.label)}</strong>
                  <button type="button" class="ghost" data-recommend-category="${cIdx}">恢复推荐配置</button>
                </div>
                ${category.modules.map((module, mIdx) => `
                  <div class="module-block">
                    <div><strong>${escapeHtml(module.label)}</strong></div>
                    <div class="checkbox-grid">
                      ${allMetricKeysForModule(module.key).map(metricKey => `
                        <label class="checkbox-item">
                          <input type="checkbox" data-metric-check="${cIdx}|${mIdx}|${metricKey}" ${module.selected_metrics.includes(metricKey) ? 'checked' : ''} />
                          <span>${escapeHtml(metricName(metricKey))}</span>
                        </label>
                      `).join('')}
                    </div>
                  </div>
                `).join('')}
              </div>
            `).join('')}
          </div>
        </div>
        <div class="card" style="padding:16px;">
          <h3>LLM 裁判评测配置</h3>
          <div class="switch-row">
            <span>是否启用 LLM 裁判评测</span>
            <input type="checkbox" id="llmEnabled" ${llmCfg.enabled ? 'checked' : ''} />
          </div>
          <div>
            <label>适用模块</label>
            <div class="checkbox-grid" style="margin-top:10px;">
              ${judgeModuleOptions().map(module => `
                <label class="checkbox-item">
                  <input type="checkbox" data-llm-module="${module.key}" ${llmCfg.modules?.includes(module.key) ? 'checked' : ''} />
                  <span>${module.label}</span>
                </label>
              `).join('')}
            </div>
          </div>
          <div style="margin-top:12px;">
            <label>提示模板</label>
            <textarea id="llmPrompt">${escapeHtml(llmCfg.prompt_template || '')}</textarea>
          </div>
          <div style="margin-top:12px;">
            <label>评分方式</label>
            <input id="llmScoring" value="${escapeHtml(llmCfg.scoring || '')}" />
          </div>
          <div class="notice warn" style="margin-top:12px;">当前版本重点展示配置结构，复杂裁判逻辑可在后续版本继续补充。</div>
        </div>
        <div class="card" style="padding:16px;">
          <h3>人工评测配置</h3>
          <div class="switch-row">
            <span>是否启用人工评测</span>
            <input type="checkbox" id="humanEnabled" ${humanCfg.enabled ? 'checked' : ''} />
          </div>
          <div>
            <label>人工复核模块</label>
            <div class="checkbox-grid" style="margin-top:10px;">
              ${judgeModuleOptions().map(module => `
                <label class="checkbox-item">
                  <input type="checkbox" data-human-module="${module.key}" ${humanCfg.modules?.includes(module.key) ? 'checked' : ''} />
                  <span>${module.label}</span>
                </label>
              `).join('')}
            </div>
          </div>
          <div style="margin-top:12px;">
            <label>评测模式</label>
            <select id="humanSamplingMode">
              <option value="抽样评测" ${humanCfg.sampling_mode === '抽样评测' ? 'selected' : ''}>抽样评测</option>
              <option value="全量评测" ${humanCfg.sampling_mode === '全量评测' ? 'selected' : ''}>全量评测</option>
            </select>
          </div>
          <div style="margin-top:12px;">
            <label>抽样比例</label>
            <input type="number" step="0.05" min="0" max="1" id="humanSamplingRatio" value="${humanCfg.sampling_ratio ?? 0.2}" />
          </div>
          <div class="notice warn" style="margin-top:12px;">人工评测用于对关键样例进行复核，当前版本先支持配置保存与结果来源展示。</div>
        </div>
      </div>
      <div class="actions" style="margin-top: 18px;">
        <button class="ghost" data-step-nav="structure">返回</button>
        <button id="saveConfigBtn">保存配置</button>
        <button class="primary" id="runEvaluationBtn">运行评测</button>
      </div>
    </div>
  `;
}

function renderResultsStep(task) {
  const results = task.results;
  if (!results) {
    return `
      <div class="card">
        <h2>评测结果</h2>
        <div class="empty">当前任务尚未运行评测，请先完成配置并点击“运行评测”。</div>
      </div>
    `;
  }
  return `
    <div class="card">
      <h2>评测结果</h2>
      <p class="muted">结果页仅保留“总览、评测详情、可视化分析”三个一级标签页。LLM 裁判评测和人工评测作为结果来源标签展示。</p>
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
        <h3>多任务整体评分对比折线图</h3>
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

function bindEvents() {
  $('#newTaskBtn')?.addEventListener('click', () => {
    state.selectedTask = { name: '', mode: 'single', uploads: {}, config: null };
    state.view = 'workflow';
    state.viewStep = 'create';
    render();
  });
  $('#backToTasksBtn')?.addEventListener('click', () => {
    state.view = 'task-list';
    render();
  });
  $('#searchInput')?.addEventListener('input', (e) => {
    state.search = e.target.value;
    render();
  });
  document.querySelectorAll('[data-open-task]').forEach(btn => btn.addEventListener('click', async () => {
    const taskId = btn.getAttribute('data-open-task');
    await openTask(taskId);
  }));
  document.querySelectorAll('[data-step]').forEach(item => item.addEventListener('click', () => {
    state.viewStep = item.getAttribute('data-step');
    render();
  }));
  document.querySelectorAll('[data-step-nav]').forEach(btn => btn.addEventListener('click', () => {
    state.viewStep = btn.getAttribute('data-step-nav');
    render();
  }));

  $('#createTaskConfirmBtn')?.addEventListener('click', createTaskAction);
  document.querySelectorAll('[data-mode-card]').forEach(card => card.addEventListener('click', () => {
    state.selectedTask.mode = card.getAttribute('data-mode-card');
    render();
  }));
  $('#saveModeBtn')?.addEventListener('click', saveModeAction);
  $('#uploadBtn')?.addEventListener('click', uploadAction);
  $('#validateBtn')?.addEventListener('click', validateAction);
  $('#revalidateBtn')?.addEventListener('click', validateAction);
  $('#goParseBtn')?.addEventListener('click', async () => { state.viewStep = 'parse'; render(); });
  $('#parseBtn')?.addEventListener('click', parseAction);
  $('#goStructureBtn')?.addEventListener('click', async () => { state.viewStep = 'structure'; render(); });
  $('#confirmStructureBtn')?.addEventListener('click', confirmStructureAction);
  $('#saveConfigBtn')?.addEventListener('click', saveConfigAction);
  $('#runEvaluationBtn')?.addEventListener('click', runEvaluationAction);
  document.querySelectorAll('[data-result-tab]').forEach(tab => tab.addEventListener('click', () => {
    state.resultTab = tab.getAttribute('data-result-tab');
    render();
  }));
  document.querySelectorAll('[data-recommend-category]').forEach(btn => btn.addEventListener('click', () => {
    const idx = Number(btn.getAttribute('data-recommend-category'));
    const category = state.selectedTask.config.auto_eval.categories[idx];
    category.modules.forEach(module => module.selected_metrics = [...module.recommended_metrics]);
    render();
  }));
  document.querySelectorAll('[data-metric-check]').forEach(input => input.addEventListener('change', metricToggleAction));
}

async function loadTasks() {
  state.tasks = await api('/api/tasks');
  if (!state.selectedTask && state.tasks.length) {
    state.selectedTask = state.tasks[0];
  }
}

async function openTask(taskId) {
  state.selectedTask = await api(`/api/tasks/${taskId}`);
  state.view = 'workflow';
  state.viewStep = currentStepKey(state.selectedTask);
  state.resultTab = 'overview';
  render();
}

async function createTaskAction() {
  const name = $('#taskNameInput')?.value?.trim();
  if (!name) return alert('请输入任务名称');
  const task = await api('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  state.selectedTask = task;
  state.view = 'workflow';
  state.viewStep = 'mode';
  await refreshSelectedTask();
}

async function saveModeAction() {
  const task = await api(`/api/tasks/${state.selectedTask.id}/mode`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode: state.selectedTask.mode }),
  });
  state.selectedTask = task;
  state.viewStep = 'upload';
  await refreshTasksOnly();
}

async function uploadAction() {
  const primary = $('#primaryFile')?.files?.[0];
  const secondary = $('#secondaryFile')?.files?.[0];
  if (!primary) return alert('请上传主日志文件');
  if (state.selectedTask.mode === 'compare' && !secondary && !(state.selectedTask.uploads || {}).secondary) {
    return alert('链路对比评测需要同时上传两组日志');
  }
  const fd = new FormData();
  if (primary) fd.append('primary', primary);
  if (secondary) fd.append('secondary', secondary);
  const task = await api(`/api/tasks/${state.selectedTask.id}/upload`, { method: 'POST', body: fd });
  state.selectedTask = task;
  state.viewStep = 'validate';
  await refreshTasksOnly();
}

async function validateAction() {
  const task = await api(`/api/tasks/${state.selectedTask.id}/validate`, { method: 'POST' });
  state.selectedTask = task;
  await refreshTasksOnly();
  render();
}

async function parseAction() {
  const task = await api(`/api/tasks/${state.selectedTask.id}/parse`, { method: 'POST' });
  state.selectedTask = task;
  state.viewStep = 'structure';
  await refreshTasksOnly();
}

async function confirmStructureAction() {
  const task = await api(`/api/tasks/${state.selectedTask.id}/confirm-structure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirmed: true }),
  });
  state.selectedTask = task;
  state.viewStep = 'config';
  await refreshTasksOnly();
}

function metricToggleAction(e) {
  const [cIdx, mIdx, metricKey] = e.target.getAttribute('data-metric-check').split('|');
  const module = state.selectedTask.config.auto_eval.categories[Number(cIdx)].modules[Number(mIdx)];
  if (e.target.checked) {
    if (!module.selected_metrics.includes(metricKey)) module.selected_metrics.push(metricKey);
  } else {
    module.selected_metrics = module.selected_metrics.filter(item => item !== metricKey);
  }
}

function collectConfigFromForm() {
  const config = JSON.parse(JSON.stringify(state.selectedTask.config));
  config.llm_judge.enabled = $('#llmEnabled')?.checked || false;
  config.llm_judge.modules = [...document.querySelectorAll('[data-llm-module]:checked')].map(el => el.getAttribute('data-llm-module'));
  config.llm_judge.prompt_template = $('#llmPrompt')?.value || '';
  config.llm_judge.scoring = $('#llmScoring')?.value || '';
  config.human_review.enabled = $('#humanEnabled')?.checked || false;
  config.human_review.modules = [...document.querySelectorAll('[data-human-module]:checked')].map(el => el.getAttribute('data-human-module'));
  config.human_review.sampling_mode = $('#humanSamplingMode')?.value || '抽样评测';
  config.human_review.sampling_ratio = Number($('#humanSamplingRatio')?.value || 0.2);
  return config;
}

async function saveConfigAction() {
  const config = collectConfigFromForm();
  const task = await api(`/api/tasks/${state.selectedTask.id}/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ config }),
  });
  state.selectedTask = task;
  await refreshTasksOnly();
  render();
}

async function runEvaluationAction() {
  const config = collectConfigFromForm();
  state.selectedTask = await api(`/api/tasks/${state.selectedTask.id}/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ config }),
  });
  render();
  const task = await api(`/api/tasks/${state.selectedTask.id}/run`, { method: 'POST' });
  state.selectedTask = task;
  state.viewStep = 'results';
  state.resultTab = 'overview';
  await refreshTasksOnly();
}

async function refreshSelectedTask() {
  if (!state.selectedTask?.id) return;
  state.selectedTask = await api(`/api/tasks/${state.selectedTask.id}`);
  await refreshTasksOnly();
  render();
}

async function refreshTasksOnly() {
  state.tasks = await api('/api/tasks');
}

function metricName(key) {
  const map = {
    hit_at_k: '命中率@K',
    end2end_ndcg: '归一化折损累计增益@K',
    mrr: '平均倒数排名',
    diversity: '推荐多样性',
    intent_accuracy: '意图识别准确率',
    slot_f1: '槽位F1值',
    candidate_recall: '召回率@K',
    post_filter_recall: '过滤后召回率',
    evidence_coverage: '证据覆盖率',
    ranking_ndcg: '排序nDCG',
    pairwise_accuracy: '成对一致性',
    tool_health: '工具调用健康度',
    tool_param_accuracy: '参数正确率',
    system_latency_ms: '时延',
    system_error_count: '错误率',
    llm_estimated_cost: '令牌成本',
    system_retry_count: '重试次数'
  };
  return map[key] || key;
}

function allMetricKeysForModule(moduleKey) {
  const map = {
    final_result: ['hit_at_k', 'end2end_ndcg', 'mrr', 'diversity'],
    intent_understanding: ['intent_accuracy', 'slot_f1'],
    candidate_recall: ['candidate_recall', 'post_filter_recall', 'evidence_coverage'],
    ranking_decision: ['ranking_ndcg', 'pairwise_accuracy'],
    agent_execution: ['tool_health', 'tool_param_accuracy'],
    system_engineering: ['system_latency_ms', 'system_error_count', 'llm_estimated_cost', 'system_retry_count'],
  };
  return map[moduleKey] || [];
}

function judgeModuleOptions() {
  return [
    { key: 'final_result', label: '最终结果' },
    { key: 'intent_understanding', label: '意图理解' },
    { key: 'candidate_recall', label: '候选召回' },
    { key: 'ranking_decision', label: '排序决策' },
    { key: 'agent_execution', label: '智能体执行' },
    { key: 'system_engineering', label: '系统工程' },
  ];
}

function renderVisualizationCharts() {
  const results = state.selectedTask.results;
  if (results.mode === 'compare') {
    renderGroupedBarChart('#moduleCompareChart', results.visualization.module_scores_compare, 'primary_score', 'secondary_score', '主日志', '对比日志');
    renderGroupedBarChart('#layerCompareChart', results.visualization.layer_distribution_compare, 'primary_value', 'secondary_value', '主日志', '对比日志');
    renderOverallCompareChart('#overallCompareChart', results.visualization.overall_compare);
    return;
  }
  renderTrendChart('#taskTrendChart', results.visualization.task_trend);
}

function renderBarChart(selector, rows) {
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

async function bootstrap() {
  await loadTasks();
  state.view = 'task-list';
  render();
}

bootstrap().catch(error => {
  document.getElementById('app').innerHTML = `<div class="app-shell"><div class="card"><h2>页面加载失败</h2><p>${escapeHtml(error.message)}</p></div></div>`;
});