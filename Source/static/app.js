'use strict';

const $ = id => document.getElementById(id);
const themeButton = $('theme-toggle');
function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const label = theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme';
  themeButton.setAttribute('aria-label', label);
  themeButton.title = label;
  themeButton.setAttribute('aria-pressed', String(theme === 'dark'));
}
const systemTheme = matchMedia('(prefers-color-scheme: dark)');
setTheme(localStorage.getItem('bootpd-theme') || (systemTheme.matches ? 'dark' : 'light'));
themeButton.onclick = () => {
  const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('bootpd-theme', theme);
  setTheme(theme);
};
systemTheme.addEventListener('change', event => {
  if (!localStorage.getItem('bootpd-theme')) setTheme(event.matches ? 'dark' : 'light');
});

const form = $('settings');
const field = name => form.querySelector(`[name="${name}"]`);
let refreshTask = null;
const events = {
  clear_discovered: 'Devices and ARP cleared', clear_arp: 'ARP cleared',
  restore_network: 'Ethernet settings restored', waiting_link: 'Waiting for Ethernet connection', start_failed: 'DHCP start failed', start: 'DHCP started', stop: 'DHCP stopped', save: 'Configuration saved',
  lease_observed: 'Lease observed', lease_changed: 'Lease changed'
};
const state = {initialized: false, loading: false, pending: false, demo: false, running: false, scanning: false, saved: null, link: false, networkBackups: []};
const token = location.hash.slice(1) || sessionStorage.getItem('bootpd-token') || '';
if (token) sessionStorage.setItem('bootpd-token', token);
history.replaceState(null, '', '/');
const date = value => new Date(value * 1000).toLocaleString('en-GB');

function node(tag, value) {
  const element = document.createElement(tag);
  element.textContent = value;
  return element;
}

function table(id, rows, columns, empty) {
  const target = $(id);
  target.replaceChildren(...rows.map(values => {
    const row = document.createElement('tr');
    values.forEach(value => row.append(node('td', value)));
    return row;
  }));
  if (!rows.length) {
    const row = document.createElement('tr');
    const cell = node('td', empty);
    cell.colSpan = columns;
    row.append(cell);
    target.append(row);
  }
}

async function api(payload) {
  const response = await fetch('/api', {
    method: 'POST', signal: AbortSignal.timeout(20000),
    headers: {'Content-Type': 'application/json', 'X-Session': token},
    body: JSON.stringify(payload)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  return result;
}

function currentConfig() {
  return Object.fromEntries(['interface', 'subnet', 'server', 'lease', 'start', 'end'].map(key => [key, key === 'lease' ? Number(field(key).value) : field(key).value.trim()]));
}

function settingsSaved() {
  const config = currentConfig();
  return state.saved && Object.keys(config).every(key => config[key] === state.saved[key]);
}

function controls() {
  const blocked = state.demo || state.pending;
  $('clear-history').disabled = blocked;
  const available = state.available !== false;
  const selected = Boolean(field('interface').value);
  const saved = selected && settingsSaved();
  $('settings-state').textContent = !selected ? 'Select an Ethernet interface.' : saved ? 'Network settings saved.' : 'Unsaved network settings. Click Save and apply Ethernet IP before starting DHCP or discovery.';
  form.querySelectorAll('input,select').forEach(element => {element.disabled = state.pending || state.running || state.scanning;});
  $('save').disabled = blocked || state.running || state.scanning || !selected;
  $('start').disabled = blocked || state.running || !saved || !available;
  $('stop').disabled = blocked || !state.running;
  $('scan').disabled = blocked || state.scanning || !saved || !state.link;
  $('scan').textContent = state.scanning ? 'Scanning...' : 'Scan now';
  $('clear-arp').disabled = blocked || state.scanning || !selected;
  $('clear-discovered').disabled = blocked || state.scanning || !selected;
  $('auto-scan').disabled = blocked || !saved || !state.link;
  if (!saved || !state.link) $('auto-scan').checked = false;
  $('restore-network').disabled = blocked || state.running || state.scanning || !state.networkBackups.includes(field('interface').value);
}

function refresh(reset = false) {
  if (!refreshTask) refreshTask = loadStatus(reset).finally(() => { refreshTask = null; });
  return refreshTask;
}

async function loadStatus(reset = false) {
  if (state.loading) return;
  state.loading = true;
  try {
    const data = await api({op: 'status'});
    Object.assign(state, {demo: Boolean(data.demo), running: data.running, scanning: Boolean(data.scan?.running), link: Boolean(data.link_active), networkBackups: data.network_backups || []});
    state.saved = data.config;
    state.available = data.interfaces.some(item => item.id === data.config.interface);
    const selection = field('interface').value;
    const placeholder = node('option', selection && !data.interfaces.some(item => item.id === selection) ? 'Ethernet adapter disconnected' : 'Select Ethernet interface');
    placeholder.value = '';
    field('interface').replaceChildren(placeholder, ...data.interfaces.map(item => {
      const option = node('option', `${item.name} / ${item.id} / ${item.active ? 'Cable connected' : 'Cable disconnected'}`);
      option.value = item.id;
      return option;
    }));
    if (!state.initialized || reset) {
      for (const [key, value] of Object.entries(data.config)) field(key).value = value;
      state.initialized = true;
    } else {
      field('interface').value = selection;
    }
    $('state').textContent = state.demo ? 'Demo mode' : state.running ? (data.pid && state.link ? 'DHCP running' : 'Waiting for connection') : 'DHCP stopped';
    $('state').className = state.running ? 'on' : '';
    $('notice').textContent = state.demo ? 'Demo mode. Hardware access and all management commands are disabled.' : 'DHCP only. No NAT or Internet Sharing. Use an isolated Ethernet network without another DHCP server.';
    table('leases', data.leases.map(item => [item.ip, item.mac, item.hostname || '-', date(item.expiry), item.status === 'expired' ? 'Expired' : 'Active', item.arp_seen ? 'Present' : 'Unknown']), 6, 'No leases');
    table('discovered', (data.discovered || []).map(item => [item.ip, item.mac, item.hostname || '-', date(item.last_seen), item.cached ? 'Present' : 'Absent']), 5, 'No devices observed');
    $('history').replaceChildren(...data.history.map(item => node('p', `${date(item.ts)} / ${events[item.kind] || item.kind} / ${item.data.ip || item.data.interface || ''} ${item.data.mac || item.data.error || ''}`)));
    if (!data.history.length) $('history').append(node('p', 'No activity'));
    $('backups').replaceChildren(...data.backups.map(name => node('p', name)));
    if (!data.backups.length) $('backups').append(node('p', 'No backups'));
    $('scan-state').textContent = data.scan?.error || (!state.link ? 'Discovery requires a connected Ethernet cable' : data.scan?.running ? 'Discovery in progress' : data.scan?.last_finished ? `Last scan completed: ${date(data.scan.last_finished)}` : 'No active scan completed');
    $('updated').textContent = `Updated: ${new Date().toLocaleTimeString('en-GB')} / every 5 seconds`;
  } catch (error) {
    $('error').textContent = error.message;
    $('state').textContent = 'Status unavailable';
  } finally {
    state.loading = false;
    controls();
  }
}

async function command(payload, reset = false) {
  if (state.pending) return;
  if (['start', 'scan'].includes(payload.op) && !settingsSaved()) {
    $('error').textContent = 'Save network settings before starting DHCP or discovery.';
    return;
  }
  state.pending = true;
  controls();
  try {
    if (refreshTask) await refreshTask;
    $('error').textContent = '';
    await api(payload);
    await refresh(reset);
  } catch (error) {
    $('error').textContent = error.message;
  } finally {
    state.pending = false;
    controls();
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const config = currentConfig();
  const labels = {interface: 'Ethernet interface', subnet: 'Subnet (CIDR)', server: 'Mac IPv4 address', start: 'Pool start', end: 'Pool end'};
  for (const [key, label] of Object.entries(labels)) {
    if (!config[key]) {
      $('error').textContent = `${label} is empty. Enter a value before saving.`;
      field(key).focus();
      return;
    }
  }
  if (!confirm(`Apply ${config.server} (${config.subnet}) to ${config.interface}? Existing IPv4 settings will be backed up. This may interrupt connections on this Ethernet adapter.`)) return;
  command({op: 'save', config}, true);
});
form.addEventListener('input', controls);
form.addEventListener('change', controls);
$('start').onclick = () => command({op: 'start'});
$('stop').onclick = () => command({op: 'stop'});
$('refresh').onclick = () => { $('error').textContent = ''; refresh(); };
$('scan').onclick = () => command({op: 'scan'});
$('auto-scan').onchange = () => {if ($('auto-scan').checked) command({op: 'scan'});};
for (const [id, op, message] of [
  ['clear-arp', 'clear_arp', 'Clear ARP entries'],
  ['clear-discovered', 'clear_discovered', 'Clear saved device observations and ARP entries']
]) {
  $(id).onclick = () => {
    const device = field('interface').value;
    if (confirm(`${message} on ${device}? DHCP leases are preserved. Devices may reappear after network traffic.`)) command({op, interface: device});
  };
}
refresh();
setInterval(() => { if (!state.pending) refresh(); }, 5000);
setInterval(() => {if ($('auto-scan').checked && !state.scanning && state.link) command({op: 'scan'});}, 60000);

$('restore-network').onclick = () => {
  const device = field('interface').value;
  if (confirm(`Restore the previous IPv4 configuration of ${device}? This may interrupt its network connections.`)) command({op: 'restore_network', interface: device});
};

$('clear-history').onclick = () => {
  if (confirm('Clear all activity events? DHCP leases, discovered devices and settings are preserved.')) command({op: 'clear_history'});
};
