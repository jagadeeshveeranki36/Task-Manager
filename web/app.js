/* ═══════════════════════════════════════════════════════
   Task Manager — Web App
   Author: Jagadeesh Veeranki
   Persists to localStorage, browser Notification API for reminders
═══════════════════════════════════════════════════════ */

'use strict';

// ── Storage helpers ───────────────────────────────────────
const STORAGE_KEY = 'taskmanager_tasks';

function loadTasks() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; }
  catch { return []; }
}
function saveTasks(tasks) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}
function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

// ── State ─────────────────────────────────────────────────
let tasks = loadTasks();
let editingId = null;
let deleteTargetId = null;
let reminderTaskId = null;
let openDropdownId = null;

// ── DOM refs ──────────────────────────────────────────────
const taskList       = document.getElementById('taskList');
const emptyState     = document.getElementById('emptyState');
const sortSelect     = document.getElementById('sortSelect');
const addBtn         = document.getElementById('addBtn');

// Dialog
const dialogOverlay  = document.getElementById('dialogOverlay');
const dialogTitle    = document.getElementById('dialogTitle');
const titleInput     = document.getElementById('titleInput');
const descInput      = document.getElementById('descInput');
const dateInput      = document.getElementById('dateInput');
const hourInput      = document.getElementById('hourInput');
const minInput       = document.getElementById('minInput');
const priorityGroup  = document.getElementById('priorityGroup');
const cancelBtn      = document.getElementById('cancelBtn');
const saveBtn        = document.getElementById('saveBtn');

// Delete dialog
const deleteOverlay     = document.getElementById('deleteOverlay');
const deleteMsg         = document.getElementById('deleteMsg');
const deleteCancelBtn   = document.getElementById('deleteCancelBtn');
const deleteConfirmBtn  = document.getElementById('deleteConfirmBtn');

// Reminder dialog
const reminderOverlay   = document.getElementById('reminderOverlay');
const reminderTitle     = document.getElementById('reminderTitle');
const reminderDue       = document.getElementById('reminderDue');
const reminderComplete  = document.getElementById('reminderComplete');
const reminderSnooze    = document.getElementById('reminderSnooze');
const reminderDismiss   = document.getElementById('reminderDismiss');

// Stats
const statTotal   = document.getElementById('statTotal');
const statPending = document.getElementById('statPending');
const statDone    = document.getElementById('statDone');
const statOverdue = document.getElementById('statOverdue');

// Toast
const toast = document.getElementById('toast');

// ── Priority selection ────────────────────────────────────
let selectedPriority = 'Medium';
priorityGroup.addEventListener('click', e => {
  const btn = e.target.closest('.prio-btn');
  if (!btn) return;
  selectedPriority = btn.dataset.priority;
  priorityGroup.querySelectorAll('.prio-btn').forEach(b => b.classList.remove('prio-selected'));
  btn.classList.add('prio-selected');
});

function setPriority(p) {
  selectedPriority = p;
  priorityGroup.querySelectorAll('.prio-btn').forEach(b => {
    b.classList.toggle('prio-selected', b.dataset.priority === p);
  });
}

// ── Dialog helpers ────────────────────────────────────────
function openDialog(task = null) {
  editingId = task ? task.id : null;
  dialogTitle.textContent = task ? '✏️ Edit Task' : '➕ New Task';

  titleInput.value = task ? task.title : '';
  descInput.value  = task ? (task.description || '') : '';

  if (task && task.due_datetime) {
    const dt = new Date(task.due_datetime);
    dateInput.value = dt.toISOString().slice(0, 10);
    hourInput.value = String(dt.getHours()).padStart(2, '0');
    minInput.value  = String(dt.getMinutes()).padStart(2, '0');
  } else {
    // Default date = today
    dateInput.value = new Date().toISOString().slice(0, 10);
    hourInput.value = '09';
    minInput.value  = '00';
  }

  setPriority(task ? task.priority : 'Medium');
  dialogOverlay.classList.add('open');
  dialogOverlay.setAttribute('aria-hidden', 'false');
  setTimeout(() => titleInput.focus(), 100);
}

function closeDialog() {
  dialogOverlay.classList.remove('open');
  dialogOverlay.setAttribute('aria-hidden', 'true');
  editingId = null;
}

function openDeleteDialog(id) {
  deleteTargetId = id;
  const t = tasks.find(t => t.id === id);
  deleteMsg.textContent = `Are you sure you want to delete "${t ? t.title : ''}"?`;
  deleteOverlay.classList.add('open');
  deleteOverlay.setAttribute('aria-hidden', 'false');
}
function closeDeleteDialog() {
  deleteOverlay.classList.remove('open');
  deleteOverlay.setAttribute('aria-hidden', 'true');
  deleteTargetId = null;
}

// ── Save task ─────────────────────────────────────────────
saveBtn.addEventListener('click', saveTask);
titleInput.addEventListener('keydown', e => { if (e.key === 'Enter') saveTask(); });

function saveTask() {
  const title = titleInput.value.trim();
  if (!title) { titleInput.focus(); titleInput.style.borderColor = 'var(--prio-high)'; return; }
  titleInput.style.borderColor = '';

  const h = parseInt(hourInput.value, 10);
  const m = parseInt(minInput.value, 10);
  if (isNaN(h) || isNaN(m) || h < 0 || h > 23 || m < 0 || m > 59) {
    hourInput.focus(); return;
  }

  const dateStr = dateInput.value;
  const due_datetime = dateStr ? `${dateStr}T${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:00` : null;

  if (editingId) {
    const idx = tasks.findIndex(t => t.id === editingId);
    if (idx !== -1) {
      tasks[idx] = { ...tasks[idx], title, description: descInput.value.trim(), due_datetime, priority: selectedPriority };
    }
  } else {
    tasks.unshift({
      id: genId(),
      title,
      description: descInput.value.trim(),
      due_datetime,
      priority: selectedPriority,
      completed: false,
      snoozed_until: null,
      last_notified_at: null,
      created_at: new Date().toISOString(),
    });
  }

  saveTasks(tasks);
  closeDialog();
  render();
}

// ── Delete task ───────────────────────────────────────────
deleteConfirmBtn.addEventListener('click', () => {
  if (deleteTargetId) {
    tasks = tasks.filter(t => t.id !== deleteTargetId);
    saveTasks(tasks);
    closeDeleteDialog();
    render();
  }
});

// ── Toggle complete ───────────────────────────────────────
function toggleComplete(id) {
  const t = tasks.find(t => t.id === id);
  if (!t) return;
  const wasCompleted = t.completed;
  t.completed = !t.completed;
  saveTasks(tasks);
  render();
  if (!wasCompleted) showToast('✅ Task completed!');
}

// ── Sorting ───────────────────────────────────────────────
const PRIORITY_ORDER = { High: 0, Medium: 1, Low: 2 };

function sortedTasks() {
  const sort = sortSelect.value;
  const copy = [...tasks];
  if (sort === 'due') {
    copy.sort((a, b) => {
      const da = a.due_datetime || '9999';
      const db = b.due_datetime || '9999';
      return da.localeCompare(db) || a.completed - b.completed;
    });
  } else if (sort === 'priority') {
    copy.sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 3) - (PRIORITY_ORDER[b.priority] ?? 3) || a.completed - b.completed);
  } else if (sort === 'created') {
    copy.sort((a, b) => b.created_at.localeCompare(a.created_at));
  } else if (sort === 'status') {
    copy.sort((a, b) => a.completed - b.completed || (a.due_datetime || '9999').localeCompare(b.due_datetime || '9999'));
  }
  return copy;
}

// ── Helpers ───────────────────────────────────────────────
function isOverdue(task) {
  if (task.completed || !task.due_datetime) return false;
  return new Date() > new Date(task.due_datetime);
}
function formatDue(iso) {
  const d = new Date(iso);
  return d.toLocaleString('en-IN', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit', hour12:false });
}

// ── Render ────────────────────────────────────────────────
function render() {
  const sorted = sortedTasks();
  updateStats(sorted);

  if (!sorted.length) {
    emptyState.classList.add('visible');
    taskList.innerHTML = '';
    return;
  }
  emptyState.classList.remove('visible');
  taskList.innerHTML = '';

  sorted.forEach(task => {
    const overdue = isOverdue(task);
    const card = document.createElement('div');
    card.className = `task-card${overdue ? ' overdue' : ''}${task.completed ? ' completed-card' : ''}`;
    card.dataset.id = task.id;

    const prio = task.priority || 'Low';
    const prioClass = prio === 'High' ? 'badge-high' : prio === 'Medium' ? 'badge-med' : 'badge-low';
    const prioIcon  = prio === 'High' ? '🔴' : prio === 'Medium' ? '🟡' : '⚪';

    card.innerHTML = `
      <div class="card-top">
        <div class="task-checkbox${task.completed ? ' checked' : ''}" data-action="toggle" data-id="${task.id}" role="checkbox" aria-checked="${task.completed}" tabindex="0"></div>
        <div class="card-title${task.completed ? ' done-text' : ''}">${escHtml(task.title)}</div>
        ${overdue ? '<span class="overdue-badge">OVERDUE</span>' : ''}
        <div class="card-relative">
          <button class="card-menu-btn" data-action="menu" data-id="${task.id}" aria-label="Task options">⋮</button>
        </div>
      </div>
      ${task.description ? `<div class="card-desc">${escHtml(task.description.slice(0,120))}${task.description.length>120?'…':''}</div>` : ''}
      <div class="card-bottom">
        <span class="card-due${overdue ? ' overdue-text' : ''}">${task.due_datetime ? '🕐 ' + formatDue(task.due_datetime) : ''}</span>
        <div class="card-badges">
          ${task.completed ? '<span class="badge badge-done">✅ Done</span>' : ''}
          <span class="badge ${prioClass}">${prioIcon} ${prio}</span>
        </div>
      </div>
    `;
    taskList.appendChild(card);
  });
}

// ── Stats ─────────────────────────────────────────────────
function updateStats(sorted) {
  const total   = sorted.length;
  const done    = sorted.filter(t => t.completed).length;
  const overdue = sorted.filter(t => isOverdue(t)).length;
  const pending = total - done;
  statTotal.textContent   = `📋 Total: ${total}`;
  statPending.textContent = `⏳ Pending: ${pending}`;
  statDone.textContent    = `✅ Done: ${done}`;
  statOverdue.textContent = `🔴 Overdue: ${overdue}`;
}

// ── Event delegation (card interactions) ─────────────────
document.addEventListener('click', e => {
  // Close open dropdown if clicking outside
  if (openDropdownId && !e.target.closest('.card-relative')) {
    closeDropdown();
  }

  const action = e.target.closest('[data-action]');
  if (!action) return;

  const id = action.dataset.id;
  const act = action.dataset.action;

  if (act === 'toggle') {
    toggleComplete(id);
  } else if (act === 'menu') {
    e.stopPropagation();
    toggleDropdown(id, action.closest('.card-relative'));
  } else if (act === 'edit') {
    closeDropdown();
    const t = tasks.find(t => t.id === id);
    if (t) openDialog(t);
  } else if (act === 'delete') {
    closeDropdown();
    openDeleteDialog(id);
  }
});

// Keyboard on checkbox
document.addEventListener('keydown', e => {
  if (e.key === ' ' || e.key === 'Enter') {
    const cb = e.target.closest('[data-action="toggle"]');
    if (cb) { e.preventDefault(); toggleComplete(cb.dataset.id); }
  }
});

// ── Dropdown ──────────────────────────────────────────────
function toggleDropdown(id, container) {
  if (openDropdownId === id) { closeDropdown(); return; }
  closeDropdown();
  openDropdownId = id;
  const dd = document.createElement('div');
  dd.className = 'dropdown';
  dd.id = 'openDropdown';
  dd.innerHTML = `
    <button class="dropdown-item" data-action="edit" data-id="${id}">✏️ Edit</button>
    <button class="dropdown-item danger" data-action="delete" data-id="${id}">🗑️ Delete</button>
  `;
  container.appendChild(dd);
}
function closeDropdown() {
  const dd = document.getElementById('openDropdown');
  if (dd) dd.remove();
  openDropdownId = null;
}

// ── Toolbar actions ───────────────────────────────────────
addBtn.addEventListener('click', () => openDialog());
cancelBtn.addEventListener('click', closeDialog);
deleteCancelBtn.addEventListener('click', closeDeleteDialog);
sortSelect.addEventListener('change', render);

// Close on overlay click
dialogOverlay.addEventListener('click', e => { if (e.target === dialogOverlay) closeDialog(); });
deleteOverlay.addEventListener('click', e => { if (e.target === deleteOverlay) closeDeleteDialog(); });

// Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeDialog(); closeDeleteDialog(); closeReminderDialog(); }
});

// ── Toast ─────────────────────────────────────────────────
let toastTimer;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2500);
}

// ── Reminder logic ────────────────────────────────────────
function checkReminders() {
  const now = new Date();
  for (const task of tasks) {
    if (task.completed || !task.due_datetime) continue;
    if (new Date(task.due_datetime) > now) continue;   // not yet due
    if (task.snoozed_until && new Date(task.snoozed_until) > now) continue;

    const interval = 60 * 1000; // 60 seconds between repeat alerts
    if (task.last_notified_at) {
      const elapsed = now - new Date(task.last_notified_at);
      if (elapsed < interval) continue;
    }

    // Mark notified
    task.last_notified_at = now.toISOString();
    saveTasks(tasks);

    // Show browser notification (if permitted)
    if (Notification.permission === 'granted') {
      new Notification('⏰ Task Reminder', { body: `Don't forget: ${task.title}`, icon: '' });
    }

    // Show in-app reminder popup
    showReminderDialog(task.id);
    break; // Show one at a time
  }
}

function showReminderDialog(id) {
  reminderTaskId = id;
  const task = tasks.find(t => t.id === id);
  if (!task) return;
  reminderTitle.textContent = task.title;
  reminderDue.textContent = task.due_datetime ? `🕐 Due: ${formatDue(task.due_datetime)}` : '';
  reminderOverlay.classList.add('open');
  reminderOverlay.setAttribute('aria-hidden', 'false');
  pulseReminder(3);
}
function closeReminderDialog() {
  reminderOverlay.classList.remove('open');
  reminderOverlay.setAttribute('aria-hidden', 'true');
  reminderTaskId = null;
}

reminderComplete.addEventListener('click', () => {
  if (!reminderTaskId) return;
  const t = tasks.find(t => t.id === reminderTaskId);
  if (t) { t.completed = true; saveTasks(tasks); render(); showToast('✅ Task completed!'); }
  closeReminderDialog();
});
reminderSnooze.addEventListener('click', () => {
  if (!reminderTaskId) return;
  const t = tasks.find(t => t.id === reminderTaskId);
  if (t) {
    t.snoozed_until = new Date(Date.now() + 60 * 60 * 1000).toISOString();
    saveTasks(tasks);
  }
  closeReminderDialog();
});
reminderDismiss.addEventListener('click', () => {
  if (!reminderTaskId) return;
  const t = tasks.find(t => t.id === reminderTaskId);
  if (t) { t.last_notified_at = new Date().toISOString(); saveTasks(tasks); }
  closeReminderDialog();
});

// Pulse animation on reminder banner
function pulseReminder(times) {
  const banner = document.querySelector('.reminder-banner');
  if (!banner || times <= 0) return;
  banner.style.background = times % 2 === 0 ? '#E67E22' : '#FFFFFF';
  banner.style.color = times % 2 === 0 ? '#fff' : '#E67E22';
  setTimeout(() => pulseReminder(times - 1), 150);
}

// ── Request notification permission ──────────────────────
function requestNotifPerm() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

// ── Escape HTML ───────────────────────────────────────────
function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Init ──────────────────────────────────────────────────
render();
requestNotifPerm();
setInterval(checkReminders, 30_000); // check every 30 seconds
checkReminders(); // check immediately on load
