const API_LOGIN_URL = "api/login";
const API_LOGOUT_URL = "api/logout";
const API_ME_URL = "api/me";
const API_ADMIN_STATS_URL = "api/admin/stats";
const API_ADMIN_RESPONSES_URL = "api/admin/responses";
const API_ADMIN_EXPORT_CSV_URL = "api/admin/export.csv";
const API_ADMIN_EXPORT_JSONL_URL = "api/admin/export.jsonl";
const API_STUDY_URL = "api/study";
const API_RESPONSES_URL = "api/responses";
const OPTION_KEYS = ["A", "B", "C", "D"];

const I18N = {
  zh: {
    pilotLabel: "合成交互示例", appTitle: "CDSS 医生答题系统", username: "账号", password: "密码",
    login: "登录", logout: "退出", progress: "进度", completed: "已完成", saveStatus: "保存状态",
    retrySync: "重试同步", jump: "题目跳转", waiting: "等待开始", noQuestions: "当前账号暂无题目",
    beforeYouStart: "答题前信息", readBeforeStart: "开始作答前请先阅读", start: "开始作答", finished: "答题结束",
    allFinished: "您已完成本次全部题目", review: "返回检查题目", cdssAdvice: "CDSS 建议", chooseAnswer: "选择答案",
    previous: "上一题", next: "下一题", admin: "后台管理", statistics: "答题统计",
    timeRemaining: "剩余时间", timeLimitHint: "从点击“开始作答”起计时", timeExpired: "时间到，系统已停止继续作答。", timeExpiredTitle: "作答时间已结束",
    timeWarning: "剩余时间不足 10 分钟", introText: "本次作答包含病例单选题，部分题目附带由 CDSS（临床决策支持系统）生成的诊疗建议可供参考。",
    introRule: "选择、浏览并修改答案以体验流程。此合成示例仅用于软件演示，不用于临床。",
    introPrivacy: "请仅使用虚构作答；临时会话将在服务停止后清空。可用 admin / demo 查看统计并导出。",
    completionHint: "感谢您的参与。您可以关闭本页面，或点击「退出登录」结束本次会话。",
    synced: "已同步", syncing: "同步中…", unsynced: "未同步", completedSummary: (total, answered) => `共 ${total} 题，您已作答 ${answered} 题。`,
    questionNumber: (n, total) => `第 ${n} / ${total} 题`, questionHint: (n) => `第 ${n} 题`, startHint: "请先阅读题前信息并开始作答",
    invalidJump: (total) => `请输入 1 到 ${total} 之间的题号。`, chooseBeforeFinish: "请先选择答案，再点击完成。",
    remaining: (n) => `仍有 ${n} 题未作答，请继续完成或跳转到未作答题。`, chooseAnswerError: "请先选择答案。",
    finish: "完成", noMatch: "没有匹配的作答记录", noRecords: "暂无作答记录", delete: "删除",
    exportCsv: "导出作答 CSV", exportJsonl: "导出作答 JSONL", downloadStats: "下载统计", refresh: "刷新",
    completionRate: "完成率", overallAccuracy: "总体正确率", t2CdssMatch: "T2 采纳 CDSS", byCondition: "按条件", byDoctor: "按医生",
    doctor: "医生", responses: "作答", accuracy: "正确率", matchRate: "采纳率", avgMinTime: "均/最短耗时",
    responseManagement: "作答记录管理", loading: "加载中…", searchPlaceholder: "搜索记录、医生、用户题序或条件", searchResponses: "搜索作答记录",
    deleteAll: "全删记录", recordId: "记录 ID", questionOrder: "用户题序", condition: "条件", answer: "答案", responseTime: "作答用时", savedAt: "保存时间", operation: "操作",
    byQuestion: "按题目", question: "题目", difficulty: "难度", t2Match: "T2采纳", jumpTo: "跳转到第", questionSuffix: "题", jumpButton: "跳转",
    recordSummary: (total, shown, filtered) => filtered ? `共 ${total} 条，当前显示 ${shown} 条` : `共 ${total} 条作答记录`,
    orderLabel: (n) => `第 ${n} 题`, unknownOrder: "题序未知", deleteConfirm: (label) => `确定删除作答记录 ${label}？\n\n删除后统计会立即更新。`, deleteAllConfirm: (count) => `确定删除当前全部 ${count} 条作答记录？\n\n此操作会清空当前测试的所有作答。`, deleted: (count) => `已删除 ${count} 条作答记录。`, speedWarning: (seconds) => `存在作答时间过短的记录（< ${seconds}s）`, t1Advice: "T1 正确建议：", t2Advice: "T2 错误建议：", doctorRecordLabel: (doctor, question) => `医生 ${doctor} 的${question}`
  },
  en: {
    pilotLabel: "Synthetic interactive demo", appTitle: "CDSS Case Response System", username: "Username", password: "Password",
    login: "Sign in", logout: "Sign out", progress: "Progress", completed: "Completed", saveStatus: "Save status",
    retrySync: "Retry sync", jump: "Jump to question", waiting: "Waiting to start", noQuestions: "No questions assigned",
    beforeYouStart: "Before you start", readBeforeStart: "Read before starting", start: "Start", finished: "Finished",
    allFinished: "You have completed all questions", review: "Review answers", cdssAdvice: "CDSS advice", chooseAnswer: "Choose an answer",
    previous: "Previous", next: "Next", admin: "Administration", statistics: "Response statistics",
    timeRemaining: "Time remaining", timeLimitHint: "The timer starts when you select Start.", timeExpired: "Time is up. Further responses are disabled.", timeExpiredTitle: "The response time has ended",
    timeWarning: "Less than 10 minutes remaining", introText: "Explore three fictional anaemia questions: T0 has no advice, T1 has correct scripted advice, and T2 has deliberately incorrect scripted advice.",
    introRule: "Choose an answer, move between questions, and revise an answer to try the workflow. This synthetic example is for software demonstration, not clinical use.",
    introPrivacy: "Use fictional responses only. This temporary session resets when the server stops. Sign in as admin / demo to inspect and export your responses.",
    completionHint: "Review and revise your answers, or sign out and use admin / demo to inspect statistics and download your responses.",
    synced: "Synced", syncing: "Syncing…", unsynced: "Not synced", completedSummary: (total, answered) => `${answered} of ${total} questions answered.`,
    questionNumber: (n, total) => `Question ${n} / ${total}`, questionHint: (n) => `Question ${n}`, startHint: "Read the instructions and start the session first",
    invalidJump: (total) => `Enter a question number from 1 to ${total}.`, chooseBeforeFinish: "Select an answer before finishing.",
    remaining: (n) => `${n} questions remain unanswered. Continue or jump to an unanswered question.`, chooseAnswerError: "Select an answer first.",
    finish: "Finish", noMatch: "No matching response records", noRecords: "No response records", delete: "Delete",
    exportCsv: "Export responses CSV", exportJsonl: "Export responses JSONL", downloadStats: "Download statistics", refresh: "Refresh",
    completionRate: "Completion rate", overallAccuracy: "Overall accuracy", t2CdssMatch: "T2 CDSS match", byCondition: "By condition", byDoctor: "By participant",
    doctor: "Participant", responses: "Responses", accuracy: "Accuracy", matchRate: "Match rate", avgMinTime: "Mean / shortest time",
    responseManagement: "Response records", loading: "Loading…", searchPlaceholder: "Search records, participants, order, or condition", searchResponses: "Search response records",
    deleteAll: "Delete all records", recordId: "Record ID", questionOrder: "Question order", condition: "Condition", answer: "Answer", responseTime: "Response time", savedAt: "Saved at", operation: "Action",
    byQuestion: "By question", question: "Question", difficulty: "Difficulty", t2Match: "T2 match", jumpTo: "Jump to question", questionSuffix: "", jumpButton: "Go",
    recordSummary: (total, shown, filtered) => filtered ? `${shown} of ${total} records shown` : `${total} response records`,
    orderLabel: (n) => `Question ${n}`, unknownOrder: "Unknown order", deleteConfirm: (label) => `Delete response record ${label}?\n\nStatistics will be updated immediately.`, deleteAllConfirm: (count) => `Delete all ${count} response records?\n\nThis clears all responses in the current test.`, deleted: (count) => `${count} response records deleted.`, speedWarning: (seconds) => `Very short response time detected (< ${seconds}s)`, t1Advice: "T1 correct advice: ", t2Advice: "T2 incorrect advice: ", doctorRecordLabel: (doctor, question) => `participant ${doctor}, ${question}`
  }
};
let currentLanguage = "en";
function t(key) { return I18N[currentLanguage]?.[key] ?? I18N.zh[key] ?? key; }
function setLanguage(language) {
  currentLanguage = language === "zh" ? "zh" : "en";
  localStorage.setItem("cdss-language", currentLanguage);
  document.documentElement.lang = currentLanguage === "zh" ? "zh-CN" : "en";
  document.title = t("appTitle");
  document.querySelectorAll("[data-i18n]").forEach((node) => { node.textContent = t(node.dataset.i18n); });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => { node.placeholder = t(node.dataset.i18nPlaceholder); });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => { node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel)); });
  document.querySelectorAll("#languageToggle, #languageToggleApp, #languageToggleAdmin").forEach((button) => {
    button.textContent = currentLanguage === "zh" ? "English" : "中文";
  });
  if (state.assignments?.length) {
    renderSyncStatus();
    renderTimer();
    render();
  }
  if (state.adminStats) {
    renderAdminStats(state.adminStats);
    renderAdminResponses();
  }
}

const state = {
  study: null,
  user: null,
  assignments: [],
  currentIndex: 0,
  responses: {},
  questionStartedAt: Date.now(),
  startedAt: null,
  timeLimitSeconds: 90 * 60,
  timerId: null,
  timeExpired: false,
  started: false,
  completed: false,
  unsyncedAssignments: new Set(),
  syncInFlight: false,
  adminResponses: [],
  adminStats: null,
};

const els = {
  appShell: document.querySelector("#appShell"),
  adminShell: document.querySelector("#adminShell"),
  loginView: document.querySelector("#loginView"),
  loginForm: document.querySelector("#loginForm"),
  usernameInput: document.querySelector("#usernameInput"),
  passwordInput: document.querySelector("#passwordInput"),
  loginError: document.querySelector("#loginError"),
  logoutBtn: document.querySelector("#logoutBtn"),
  adminLogoutBtn: document.querySelector("#adminLogoutBtn"),
  refreshAdminBtn: document.querySelector("#refreshAdminBtn"),
  exportCsvBtn: document.querySelector("#exportCsvBtn"),
  exportJsonlBtn: document.querySelector("#exportJsonlBtn"),
  downloadStatsBtn: document.querySelector("#downloadStatsBtn"),
  deleteAllResponsesBtn: document.querySelector("#deleteAllResponsesBtn"),
  recordSearchInput: document.querySelector("#recordSearchInput"),
  adminRecordSummary: document.querySelector("#adminRecordSummary"),
  adminResponsesBody: document.querySelector("#adminResponsesBody"),
  syncStatus: document.querySelector("#syncStatus"),
  retrySyncBtn: document.querySelector("#retrySyncBtn"),
  adminCompletionRate: document.querySelector("#adminCompletionRate"),
  adminAccuracy: document.querySelector("#adminAccuracy"),
  adminT1Delta: document.querySelector("#adminT1Delta"),
  adminT2Delta: document.querySelector("#adminT2Delta"),
  adminT2Match: document.querySelector("#adminT2Match"),
  conditionChart: document.querySelector("#conditionChart"),
  doctorStatsBody: document.querySelector("#doctorStatsBody"),
  questionStatsBody: document.querySelector("#questionStatsBody"),
  progressBar: document.querySelector("#progressBar"),
  answeredCount: document.querySelector("#answeredCount"),
  emptyState: document.querySelector("#emptyState"),
  introView: document.querySelector("#introView"),
  startStudyBtn: document.querySelector("#startStudyBtn"),
  questionView: document.querySelector("#questionView"),
  questionTitle: document.querySelector("#questionTitle"),
  questionText: document.querySelector("#questionText"),
  cdssPanel: document.querySelector("#cdssPanel"),
  cdssAdvice: document.querySelector("#cdssAdvice"),
  optionList: document.querySelector("#optionList"),
  prevBtn: document.querySelector("#prevBtn"),
  nextBtn: document.querySelector("#nextBtn"),
  jumpForm: document.querySelector("#jumpForm"),
  jumpToInput: document.querySelector("#jumpToInput"),
  jumpError: document.querySelector("#jumpError"),
  questionNavGrid: document.querySelector("#questionNavGrid"),
  completionView: document.querySelector("#completionView"),
  completionSummary: document.querySelector("#completionSummary"),
  completionTitle: document.querySelector("#completionTitle"),
  introText: document.querySelector("#introText"),
  reviewAnswersBtn: document.querySelector("#reviewAnswersBtn"),
  completionLogoutBtn: document.querySelector("#completionLogoutBtn"),
  languageToggle: document.querySelector("#languageToggle"),
  languageToggleApp: document.querySelector("#languageToggleApp"),
  languageToggleAdmin: document.querySelector("#languageToggleAdmin"),
  timeRemaining: document.querySelector("#timeRemaining"),
  timerHint: document.querySelector("#timerHint"),
  timerPanel: document.querySelector(".timer-panel"),
};

function storageKey() {
  return `cdss-doctor-responses:${state.study?.batch_id || state.study?.study_id || "unknown"}:${state.user?.doctor_id || "anonymous"}`;
}

function startTimeStorageKey() {
  return `${storageKey()}:started-at`;
}

function formatClock(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  if (hours) return `${hours}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

function renderTimer() {
  if (!els.timeRemaining) return;
  if (state.timeExpired) {
    els.timeRemaining.textContent = formatClock(0);
    els.timerPanel?.classList.remove("timer-warning");
    els.timerPanel?.classList.add("timer-expired");
    if (els.timerHint) els.timerHint.textContent = t("timeExpired");
    return;
  }
  if (!state.startedAt || state.completed) {
    els.timeRemaining.textContent = formatClock(state.timeLimitSeconds);
    els.timerPanel?.classList.remove("timer-warning", "timer-expired");
    if (els.timerHint) els.timerHint.textContent = t("timeLimitHint");
    return;
  }
  const remaining = Math.max(0, state.timeLimitSeconds - Math.floor((Date.now() - state.startedAt) / 1000));
  els.timeRemaining.textContent = formatClock(remaining);
  els.timerPanel?.classList.toggle("timer-warning", remaining > 0 && remaining <= 600);
  els.timerPanel?.classList.toggle("timer-expired", remaining <= 0);
  if (els.timerHint) els.timerHint.textContent = remaining <= 0 ? t("timeExpired") : remaining <= 600 ? t("timeWarning") : t("timeLimitHint");
  if (remaining <= 0 && !state.timeExpired) {
    state.timeExpired = true;
    saveCurrentResponse();
    showCompletionView();
    updateProgress();
    renderQuestionNavigator();
  }
}

function startTimer() {
  if (!state.startedAt) {
    state.startedAt = Date.now();
    localStorage.setItem(startTimeStorageKey(), String(state.startedAt));
  }
  state.timeExpired = false;
  clearInterval(state.timerId);
  state.timerId = setInterval(renderTimer, 1000);
  renderTimer();
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `${url} returned ${response.status}`);
  }
  return data;
}

function loadLocalResponses() {
  try {
    state.responses = JSON.parse(localStorage.getItem(storageKey()) || "{}");
  } catch {
    state.responses = {};
  }
}

async function loadResponses() {
  loadLocalResponses();
  try {
    const data = await fetchJson(API_RESPONSES_URL);
    if (Array.isArray(data.responses)) {
      state.responses = Object.fromEntries(data.responses.map((row) => [row.assignment_id, row]));
      localStorage.setItem(storageKey(), JSON.stringify(state.responses));
      state.unsyncedAssignments.clear();
      renderSyncStatus();
    }
  } catch {
    loadLocalResponses();
    renderSyncStatus();
  }
}

function renderSyncStatus() {
  if (!els.syncStatus) return;
  const hasUnsynced = state.unsyncedAssignments.size > 0;
  let status = "synced";
  let label = t("synced");
  if (state.syncInFlight) {
    status = "syncing";
    label = t("syncing");
  } else if (hasUnsynced) {
    status = "unsynced";
    label = `${t("unsynced")} (${state.unsyncedAssignments.size})`;
  }
  els.syncStatus.textContent = label;
  els.syncStatus.className = `sync-status sync-status--${status}`;
  if (els.retrySyncBtn) {
    els.retrySyncBtn.classList.toggle("hidden", state.syncInFlight || !hasUnsynced);
  }
}

async function saveResponseToServer(row) {
  const response = await fetch(API_RESPONSES_URL, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ response: row }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "server save failed");
  }
  return data;
}

async function syncResponseRow(row) {
  if (!row?.assignment_id) return;
  state.syncInFlight = true;
  renderSyncStatus();
  try {
    await saveResponseToServer(row);
    state.unsyncedAssignments.delete(row.assignment_id);
  } catch {
    state.unsyncedAssignments.add(row.assignment_id);
    throw new Error("save failed");
  } finally {
    state.syncInFlight = false;
    renderSyncStatus();
  }
}

async function retryUnsyncedResponses() {
  const rows = [...state.unsyncedAssignments]
    .map((assignmentId) => state.responses[assignmentId])
    .filter(Boolean);
  if (!rows.length) {
    renderSyncStatus();
    return;
  }
  state.syncInFlight = true;
  renderSyncStatus();
  for (const row of rows) {
    try {
      await saveResponseToServer(row);
      state.unsyncedAssignments.delete(row.assignment_id);
    } catch {
      state.unsyncedAssignments.add(row.assignment_id);
    }
  }
  state.syncInFlight = false;
  renderSyncStatus();
}

function persistResponses(row = null) {
  localStorage.setItem(storageKey(), JSON.stringify(state.responses));
  if (!row) {
    renderSyncStatus();
    return;
  }
  syncResponseRow(row).catch(() => {
    // Keep local progress usable if the network briefly drops.
  });
}

function currentAssignment() {
  return state.assignments[state.currentIndex] || null;
}

function firstUnansweredIndex() {
  const index = state.assignments.findIndex((item) => !state.responses[item.assignment_id]?.doctor_answer_idx);
  return index >= 0 ? index : 0;
}

function responseFor(assignment) {
  return state.responses[assignment.assignment_id] || {};
}

function isAnswered(assignment) {
  return Boolean(state.responses[assignment.assignment_id]?.doctor_answer_idx);
}

function answeredCount() {
  return state.assignments.filter((item) => isAnswered(item)).length;
}

function allAnswered() {
  return state.assignments.length > 0 && answeredCount() === state.assignments.length;
}

function showLogin(message = "") {
  state.study = null;
  state.user = null;
  state.assignments = [];
  state.responses = {};
  state.unsyncedAssignments = new Set();
  state.syncInFlight = false;
  state.started = false;
  state.completed = false;
  state.startedAt = null;
  state.timeExpired = false;
  clearInterval(state.timerId);
  state.timerId = null;
  state.currentIndex = 0;
  els.loginView.classList.remove("hidden");
  els.appShell.classList.add("hidden");
  els.adminShell.classList.add("hidden");
  els.loginError.textContent = message;
  els.usernameInput.focus();
}

function showApp() {
  els.loginView.classList.add("hidden");
  els.appShell.classList.remove("hidden");
  els.adminShell.classList.add("hidden");
}

function showAdmin() {
  els.loginView.classList.add("hidden");
  els.appShell.classList.add("hidden");
  els.adminShell.classList.remove("hidden");
}

async function loadStudyForCurrentUser() {
  state.study = await fetchJson(API_STUDY_URL);
  state.user = state.study.current_user || state.user;
  state.assignments = [...(state.study.assignments || [])].sort((a, b) => Number(a.display_order) - Number(b.display_order));
  state.timeLimitSeconds = Number(state.study.summary?.time_limit_seconds || state.study.time_limit_seconds || 90 * 60);
  const storedStart = Number(localStorage.getItem(startTimeStorageKey()) || 0);
  state.startedAt = Number.isFinite(storedStart) && storedStart > 0 ? storedStart : null;
  state.timeExpired = false;
  await loadResponses();
  state.completed = allAnswered();
  state.started = state.completed || answeredCount() > 0 || Boolean(state.startedAt);
  if (state.started && !state.completed && !state.startedAt) {
    state.startedAt = Date.now();
    localStorage.setItem(startTimeStorageKey(), String(state.startedAt));
  }
  if (state.started && !state.completed) startTimer();
  state.currentIndex = state.completed ? 0 : firstUnansweredIndex();
  state.questionStartedAt = Date.now();
  if (els.jumpToInput) {
    els.jumpToInput.max = String(state.assignments.length || 1);
    els.jumpToInput.min = "1";
  }
}

async function login(username, password) {
  els.loginError.textContent = "";
  const data = await fetchJson(API_LOGIN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  state.user = data.user;
  if (state.user.role === "admin") {
    showAdmin();
    await loadAdminStats();
    return;
  }
  await loadStudyForCurrentUser();
  showApp();
  renderSyncStatus();
  render();
}

async function logout() {
  saveCurrentResponse();
  try {
    await fetchJson(API_LOGOUT_URL, { method: "POST" });
  } catch {
    // A local logout should still clear the current browser state.
  }
  showLogin();
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${Math.round(Number(value) * 100)}%`;
}

function formatDelta(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const percent = Math.round(Number(value) * 100);
  return `${percent > 0 ? "+" : ""}${percent}pp`;
}

function tableCell(value) {
  return value === null || value === undefined || value === "" ? "-" : String(value);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatDuration(value) {
  const seconds = Number(value);
  if (!Number.isFinite(seconds) || seconds < 0) return "-";
  const rounded = Math.round(seconds);
  const units = currentLanguage === "zh" ? {second: "秒", minute: "分"} : {second: "s", minute: "min"};
  if (rounded < 60) return currentLanguage === "zh" ? `${rounded} ${units.second}` : `${rounded}${units.second}`;
  const minutes = Math.floor(rounded / 60);
  const remainder = rounded % 60;
  if (currentLanguage === "zh") return remainder ? `${minutes} ${units.minute} ${remainder} ${units.second}` : `${minutes} ${units.minute}`;
  return remainder ? `${minutes}m ${remainder}s` : `${minutes}${units.minute}`;
}

function formatSavedAt(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat(currentLanguage === "zh" ? "zh-CN" : "en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

async function loadAdminStats() {
  const stats = await fetchJson(API_ADMIN_STATS_URL);
  const responseData = await fetchJson(API_ADMIN_RESPONSES_URL);
  state.adminStats = stats;
  state.adminResponses = Array.isArray(responseData.responses) ? responseData.responses : [];
  renderAdminStats(stats);
  renderAdminResponses();
  return stats;
}

function renderAdminResponses() {
  if (!els.adminResponsesBody) return;
  const query = (els.recordSearchInput?.value || "").trim().toLowerCase();
  // 纯数字或"第 N 题"形式的查询按用户题序精确匹配，避免搜 3 时误命中第 13 题或记录 ID 里的数字；
  // 其余查询仍对记录 ID、医生、条件做子串匹配。
  const orderQuery = query.match(/^第?\s*(\d+)\s*题?$/);
  const rows = state.adminResponses.filter((row) => {
    if (!query) return true;
    if (orderQuery) {
      return String(row.display_order || "") === orderQuery[1];
    }
    return [row.record_id, row.doctor_id, row.condition, row.assignment_id].some(
      (value) => String(value || "").toLowerCase().includes(query),
    );
  });
  els.adminRecordSummary.textContent = t("recordSummary")(state.adminResponses.length, rows.length, Boolean(query));
  els.adminResponsesBody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    const cells = [
      row.record_id,
      row.doctor_id,
      row.display_order ? t("orderLabel")(row.display_order) : "-",
      row.condition,
      row.doctor_answer_idx,
      formatDuration(row.response_time_seconds),
      formatSavedAt(row.updated_at),
    ];
    cells.forEach((value) => {
      const td = document.createElement("td");
      td.textContent = tableCell(value);
      tr.appendChild(td);
    });
    const actionCell = document.createElement("td");
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "danger compact";
    deleteButton.textContent = t("delete");
    deleteButton.addEventListener("click", () => {
      deleteAdminResponse(row).catch((error) => alert(error.message));
    });
    actionCell.appendChild(deleteButton);
    tr.appendChild(actionCell);
    els.adminResponsesBody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 8;
    td.className = "empty-table-cell";
    td.textContent = query ? t("noMatch") : t("noRecords");
    tr.appendChild(td);
    els.adminResponsesBody.appendChild(tr);
  }
  if (els.deleteAllResponsesBtn) {
    els.deleteAllResponsesBtn.disabled = state.adminResponses.length === 0;
  }
}

async function deleteResponses(payload) {
  const result = await fetchJson(API_ADMIN_RESPONSES_URL, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await loadAdminStats();
  return result;
}

async function deleteAdminResponse(row) {
  const userQuestion = row.display_order ? t("orderLabel")(row.display_order) : t("unknownOrder");
  const label = `${row.record_id || "-"} (${t("doctorRecordLabel")(row.doctor_id || "-", userQuestion)})`;
  if (!window.confirm(t("deleteConfirm")(label))) return;
  await deleteResponses({ record_id: row.record_id });
}

async function deleteAllAdminResponses() {
  const count = state.adminResponses.length;
  if (!count) return;
  if (!window.confirm(t("deleteAllConfirm")(count))) return;
  const result = await deleteResponses({ delete_all: true, confirmation: "DELETE_ALL" });
  alert(t("deleted")(result.deleted_count));
}

function parseDownloadFilename(response, fallback) {
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="([^"]+)"/);
  return match?.[1] || fallback;
}

function triggerBlobDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

async function downloadAdminExport(url, fallbackName) {
  const response = await fetch(url, { credentials: "same-origin" });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || (currentLanguage === "zh" ? `导出失败（${response.status}）` : `Export failed (${response.status})`));
  }
  const blob = await response.blob();
  triggerBlobDownload(blob, parseDownloadFilename(response, fallbackName));
}

async function downloadAdminStats() {
  const stats = await loadAdminStats();
  const batchId = stats.batch?.batch_id || stats.batch?.study_id || "stats";
  const blob = new Blob([`${JSON.stringify(stats, null, 2)}\n`], { type: "application/json" });
  triggerBlobDownload(blob, `doctor_stats_${batchId}.json`);
}

function renderAdminStats(stats) {
  els.adminCompletionRate.textContent = formatPercent(stats.batch.completion_rate);
  els.adminAccuracy.textContent = formatPercent(stats.metrics.overall.accuracy);
  els.adminT1Delta.textContent = formatDelta(stats.metrics.t1_minus_t0_accuracy);
  els.adminT2Delta.textContent = formatDelta(stats.metrics.t2_minus_t0_accuracy);
  els.adminT2Match.textContent = formatPercent(stats.metrics.t2_matches_cdss_rate);

  els.conditionChart.innerHTML = "";
  Object.entries(stats.metrics.by_condition).forEach(([condition, row]) => {
    const item = document.createElement("div");
    item.className = "bar-row";
    item.innerHTML = `
      <span>${escapeHtml(condition)}</span>
      <div class="bar-track"><div class="bar-fill" style="width: ${Math.round((row.accuracy || 0) * 100)}%"></div></div>
      <strong>${formatPercent(row.accuracy)}</strong>
      <em>${row.responses} ${currentLanguage === "zh" ? "条" : row.responses === 1 ? "response" : "responses"}</em>
    `;
    els.conditionChart.appendChild(item);
  });

  els.doctorStatsBody.innerHTML = "";
  stats.tables.by_doctor.forEach((row) => {
    const tr = document.createElement("tr");
    if (row.speed_warning) tr.classList.add("speed-warning-row");
    const warnBadge = row.speed_warning
      ? ` <span class="speed-warn" title="${t("speedWarning")(row.min_response_time_seconds)}">⚠</span>`
      : "";
    tr.innerHTML = `
      <td>${escapeHtml(tableCell(row.doctor_id))}${warnBadge}</td>
      <td>${tableCell(row.responses)}</td>
      <td>${formatPercent(row.accuracy)}</td>
      <td>${formatPercent(row.matches_cdss_rate)}</td>
      <td>${formatDuration(row.avg_response_time_seconds)} / ${formatDuration(row.min_response_time_seconds)}</td>
    `;
    els.doctorStatsBody.appendChild(tr);
  });

  els.questionStatsBody.innerHTML = "";
  stats.tables.by_question.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><button class="q-expand-btn quiet" type="button" aria-expanded="false">▶</button> ${tableCell(row.question_id)}</td>
      <td>${tableCell(row.difficulty)}</td>
      <td>${row.responses} / ${row.assigned}</td>
      <td>${formatPercent(row.accuracy)}</td>
      <td>${formatPercent(row.t0_accuracy)}</td>
      <td>${formatPercent(row.t1_accuracy)}</td>
      <td>${formatPercent(row.t2_accuracy)}</td>
      <td>${formatPercent(row.t2_matches_cdss_rate)}</td>
    `;

    const detailTr = document.createElement("tr");
    detailTr.classList.add("q-detail-row", "hidden");
    const options = row.options || {};
    const optionHtml = Object.entries(options)
      .map(([k, v]) => `<span class="q-option"><b>${escapeHtml(k)}.</b> ${escapeHtml(v)}</span>`)
      .join("");
    const cdssHtml = [
      row.cdss_t1 ? `<div class="q-cdss"><b>${escapeHtml(t("t1Advice"))}</b>${escapeHtml(row.cdss_t1)}</div>` : "",
      row.cdss_t2 ? `<div class="q-cdss q-cdss--wrong"><b>${escapeHtml(t("t2Advice"))}</b>${escapeHtml(row.cdss_t2)}</div>` : "",
    ].join("");
    detailTr.innerHTML = `<td colspan="8" class="q-detail-cell"><div class="q-detail-body"><p class="q-text">${escapeHtml(row.question_text)}</p>${optionHtml ? `<div class="q-options">${optionHtml}</div>` : ""}${cdssHtml}</div></td>`;

    tr.querySelector(".q-expand-btn").addEventListener("click", () => {
      const nowHidden = detailTr.classList.toggle("hidden");
      const btn = tr.querySelector(".q-expand-btn");
      btn.setAttribute("aria-expanded", String(!nowHidden));
      btn.textContent = nowHidden ? "▶" : "▼";
    });

    els.questionStatsBody.appendChild(tr);
    els.questionStatsBody.appendChild(detailTr);
  });
}

function showCompletionView() {
  state.completed = true;
  if (!state.timeExpired) clearInterval(state.timerId);
  els.emptyState.classList.add("hidden");
  if (els.introView) els.introView.classList.add("hidden");
  els.questionView.classList.add("hidden");
  els.completionView.classList.remove("hidden");
  const total = state.assignments.length;
  const answered = answeredCount();
  els.completionSummary.textContent = t("completedSummary")(total, answered);
  if (els.completionTitle) els.completionTitle.textContent = state.timeExpired ? t("timeExpiredTitle") : t("allFinished");
}

function showIntroView() {
  state.completed = false;
  els.emptyState.classList.add("hidden");
  els.questionView.classList.add("hidden");
  els.completionView.classList.add("hidden");
  if (els.introView) els.introView.classList.remove("hidden");
}

function showQuestionView() {
  state.completed = false;
  if (els.introView) els.introView.classList.add("hidden");
  els.completionView.classList.add("hidden");
  if (!state.assignments.length) {
    els.emptyState.classList.remove("hidden");
    els.questionView.classList.add("hidden");
    return;
  }
  els.emptyState.classList.add("hidden");
  els.questionView.classList.remove("hidden");
}

function jumpToIndex(index) {
  if (!state.assignments.length || !state.started) return;
  saveCurrentResponse();
  const target = Math.min(Math.max(index, 0), state.assignments.length - 1);
  state.currentIndex = target;
  state.completed = false;
  state.questionStartedAt = Date.now();
  if (els.jumpError) els.jumpError.textContent = "";
  render();
}

function jumpToNumber(questionNumber) {
  const total = state.assignments.length;
  const parsed = Number.parseInt(String(questionNumber), 10);
  if (!Number.isFinite(parsed) || parsed < 1 || parsed > total) {
    if (els.jumpError) els.jumpError.textContent = t("invalidJump")(total);
    return;
  }
  jumpToIndex(parsed - 1);
}

function renderQuestionNavigator() {
  if (!els.questionNavGrid) return;
  els.questionNavGrid.innerHTML = "";
  state.assignments.forEach((assignment, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "nav-item";
    button.textContent = String(index + 1);
    button.title = t("questionHint")(index + 1);
    if (isAnswered(assignment)) button.classList.add("answered");
    if (index === state.currentIndex && state.started && !state.completed) button.classList.add("current");
    button.disabled = !state.started || state.completed;
    if (!state.started) button.title = t("startHint");
    button.addEventListener("click", () => jumpToIndex(index));
    els.questionNavGrid.appendChild(button);
  });
}

function render() {
  if (!state.assignments.length) {
    els.emptyState.classList.remove("hidden");
    if (els.introView) els.introView.classList.add("hidden");
    els.questionView.classList.add("hidden");
    els.completionView.classList.add("hidden");
    updateProgress();
    renderQuestionNavigator();
    return;
  }

  if (state.completed) {
    showCompletionView();
    updateProgress();
    renderQuestionNavigator();
    return;
  }

  if (els.introText) {
    const adviceCount = state.assignments.filter((item) => item.cdss).length;
    const total = state.assignments.length;
    els.introText.textContent = currentLanguage === "zh"
      ? `本示例含 ${total} 道虚构贫血题，其中 ${adviceCount} 道附带预设建议：一条正确（T1），一条故意错误（T2）。`
      : `This synthetic demo contains ${total} fictional anaemia questions. ${adviceCount} include scripted advice: one correct suggestion (T1) and one deliberately incorrect suggestion (T2).`;
  }

  if (!state.started) {
    showIntroView();
    updateProgress();
    renderQuestionNavigator();
    return;
  }

  showQuestionView();
  renderQuestion();
  updateProgress();
  renderQuestionNavigator();
}

function renderQuestion() {
  const assignment = currentAssignment();
  const response = responseFor(assignment);
  const question = assignment.question;

  els.questionTitle.textContent = t("questionNumber")(state.currentIndex + 1, state.assignments.length);
  els.questionText.textContent = question.question;

  if (assignment.cdss) {
    els.cdssPanel.classList.remove("hidden");
    els.cdssAdvice.textContent = assignment.cdss.advice_text;
  } else {
    els.cdssPanel.classList.add("hidden");
    els.cdssAdvice.textContent = "";
  }

  els.optionList.innerHTML = "";
  OPTION_KEYS.forEach((key) => {
    const option = document.createElement("label");
    option.className = "option-item";
    if (response.doctor_answer_idx === key) option.classList.add("selected");

    const input = document.createElement("input");
    input.type = "radio";
    input.name = "answer";
    input.value = key;
    input.checked = response.doctor_answer_idx === key;
    input.addEventListener("change", () => {
      saveCurrentResponse({ doctor_answer_idx: key });
      renderQuestion();
      updateProgress();
      scheduleAutoAdvance();
    });

    const badge = document.createElement("span");
    badge.className = "option-key";
    badge.textContent = key;

    const text = document.createElement("span");
    text.textContent = question.options[key] || "";

    option.append(input, badge, text);
    els.optionList.appendChild(option);
  });

  els.prevBtn.disabled = state.currentIndex === 0;
  const isLast = state.currentIndex >= state.assignments.length - 1;
  els.nextBtn.textContent = isLast ? t("finish") : t("next");
  if (els.jumpToInput) {
    els.jumpToInput.value = String(state.currentIndex + 1);
    els.jumpToInput.max = String(state.assignments.length);
  }
}

function tryFinishStudy() {
  if (!state.started) return;
  saveCurrentResponse();
  const assignment = currentAssignment();
  if (assignment && !isAnswered(assignment)) {
    if (els.jumpError) els.jumpError.textContent = t("chooseBeforeFinish");
    return;
  }
  if (!allAnswered()) {
    const remaining = state.assignments.length - answeredCount();
    if (els.jumpError) {
      els.jumpError.textContent = t("remaining")(remaining);
    }
    return;
  }
  if (els.jumpError) els.jumpError.textContent = "";
  showCompletionView();
  updateProgress();
  renderQuestionNavigator();
}

function updateProgress() {
  const total = state.assignments.length;
  const answered = state.assignments.filter((item) => state.responses[item.assignment_id]?.doctor_answer_idx).length;
  const percent = total ? Math.round((answered / total) * 100) : 0;
  els.progressBar.style.width = `${percent}%`;
  els.answeredCount.textContent = `${answered} / ${total}`;
}

function saveCurrentResponse(patch = {}) {
  const assignment = currentAssignment();
  if (!assignment) return;

  const existing = responseFor(assignment);
  const answer = patch.doctor_answer_idx ?? existing.doctor_answer_idx ?? "";
  const note = patch.note ?? existing.note ?? "";
  if (!answer) {
    state.questionStartedAt = Date.now();
    return;
  }
  const elapsed = Math.max(0, Math.round((Date.now() - state.questionStartedAt) / 1000));
  const existingChanges = existing.changes || [];
  const changes =
    patch.doctor_answer_idx && existing.doctor_answer_idx && patch.doctor_answer_idx !== existing.doctor_answer_idx
      ? [...existingChanges, { from: existing.doctor_answer_idx, to: patch.doctor_answer_idx, changed_at: new Date().toISOString() }]
      : existingChanges;
  const row = {
    record_id: existing.record_id || `R-${assignment.assignment_id}`,
    assignment_id: assignment.assignment_id,
    doctor_answer_idx: answer,
    response_time_seconds: (existing.response_time_seconds || 0) + elapsed,
    note,
    changes,
    updated_at: new Date().toISOString(),
  };
  state.responses[assignment.assignment_id] = row;

  state.questionStartedAt = Date.now();
  persistResponses(row);
}

function move(delta) {
  if (!state.started) return;
  if (delta > 0 && state.currentIndex >= state.assignments.length - 1) {
    tryFinishStudy();
    return;
  }
  saveCurrentResponse();
  state.currentIndex = Math.min(Math.max(state.currentIndex + delta, 0), state.assignments.length - 1);
  state.questionStartedAt = Date.now();
  if (els.jumpError) els.jumpError.textContent = "";
  render();
}

let autoAdvanceTimer = null;

function scheduleAutoAdvance() {
  clearTimeout(autoAdvanceTimer);
  if (state.currentIndex >= state.assignments.length - 1) return;
  autoAdvanceTimer = setTimeout(() => {
    if (!els.appShell.classList.contains("hidden") && !state.completed) {
      move(1);
    }
  }, 300);
}

function isTypingTarget(element) {
  const tag = element?.tagName?.toLowerCase();
  return tag === "input" || tag === "textarea" || tag === "select";
}

function handleKeydown(event) {
  if (els.appShell.classList.contains("hidden")) return;
  if (state.completed) return;
  if (!state.started) return;
  if (isTypingTarget(document.activeElement)) return;

  const key = event.key.toUpperCase();
  if (OPTION_KEYS.includes(key)) {
    event.preventDefault();
    const input = els.optionList?.querySelector(`input[value="${key}"]`);
    if (input && !input.checked) {
      input.checked = true;
      input.dispatchEvent(new Event("change"));
    }
    return;
  }
  if (event.key === "Enter") {
    event.preventDefault();
    clearTimeout(autoAdvanceTimer);
    const assignment = currentAssignment();
    if (assignment && isAnswered(assignment)) {
      move(1);
    } else if (els.jumpError) {
      els.jumpError.textContent = t("chooseAnswerError");
    }
    return;
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    clearTimeout(autoAdvanceTimer);
    move(1);
    return;
  }
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    clearTimeout(autoAdvanceTimer);
    move(-1);
  }
}

function bindEvents() {
  setLanguage(currentLanguage);
  [els.languageToggle, els.languageToggleApp, els.languageToggleAdmin].filter(Boolean).forEach((button) => {
    button.addEventListener("click", () => setLanguage(currentLanguage === "zh" ? "en" : "zh"));
  });
  els.loginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    login(els.usernameInput.value, els.passwordInput.value).catch((error) => {
      els.loginError.textContent = error.message;
    });
  });
  els.logoutBtn.addEventListener("click", logout);
  els.adminLogoutBtn.addEventListener("click", logout);
  els.refreshAdminBtn.addEventListener("click", () => {
    loadAdminStats().catch((error) => {
      alert(error.message);
    });
  });
  if (els.exportCsvBtn) {
    els.exportCsvBtn.addEventListener("click", () => {
      downloadAdminExport(API_ADMIN_EXPORT_CSV_URL, "doctor_responses.csv").catch((error) => {
        alert(error.message);
      });
    });
  }
  if (els.exportJsonlBtn) {
    els.exportJsonlBtn.addEventListener("click", () => {
      downloadAdminExport(API_ADMIN_EXPORT_JSONL_URL, "doctor_responses.jsonl").catch((error) => {
        alert(error.message);
      });
    });
  }
  if (els.downloadStatsBtn) {
    els.downloadStatsBtn.addEventListener("click", () => {
      downloadAdminStats().catch((error) => {
        alert(error.message);
      });
    });
  }
  if (els.recordSearchInput) {
    els.recordSearchInput.addEventListener("input", renderAdminResponses);
  }
  if (els.deleteAllResponsesBtn) {
    els.deleteAllResponsesBtn.addEventListener("click", () => {
      deleteAllAdminResponses().catch((error) => alert(error.message));
    });
  }
  if (els.retrySyncBtn) {
    els.retrySyncBtn.addEventListener("click", () => {
      retryUnsyncedResponses().catch((error) => {
        alert(error.message);
      });
    });
  }
  els.prevBtn.addEventListener("click", () => { clearTimeout(autoAdvanceTimer); move(-1); });
  els.nextBtn.addEventListener("click", () => { clearTimeout(autoAdvanceTimer); move(1); });
  document.addEventListener("keydown", handleKeydown);
  if (els.jumpForm) {
    els.jumpForm.addEventListener("submit", (event) => {
      event.preventDefault();
      jumpToNumber(els.jumpToInput.value);
    });
  }
  if (els.reviewAnswersBtn) {
    els.reviewAnswersBtn.addEventListener("click", () => {
      state.completed = false;
      state.currentIndex = 0;
      state.questionStartedAt = Date.now();
      render();
    });
  }
  if (els.startStudyBtn) {
    els.startStudyBtn.addEventListener("click", () => {
      state.started = true;
      startTimer();
      state.currentIndex = state.completed ? 0 : firstUnansweredIndex();
      state.questionStartedAt = Date.now();
      if (els.jumpError) els.jumpError.textContent = "";
      render();
    });
  }
  if (els.completionLogoutBtn) {
    els.completionLogoutBtn.addEventListener("click", logout);
  }
}

async function init() {
  bindEvents();
  try {
    const me = await fetchJson(API_ME_URL);
    state.user = me.user;
    if (state.user.role === "admin") {
      showAdmin();
      await loadAdminStats();
      return;
    }
    await loadStudyForCurrentUser();
    showApp();
    renderSyncStatus();
    render();
  } catch {
    showLogin();
  }
}

init().catch((error) => {
  showLogin(error.message);
});
